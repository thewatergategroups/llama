from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta
import logging
from copy import deepcopy
from trekkers import on_conflict_update
from dataclasses import asdict

from ..stocks import History
from ..strats import Strategy
from concurrent.futures import ThreadPoolExecutor, as_completed
from alpaca.data.models import Bar
from collections import defaultdict
from ..database.models import Backtests, BacktestStats
from ..settings import get_sync_sessionm
from ..consts import Status
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import update, select
from .mocktrader import MockTrader
from .consts import BacktestDefinition
from ..strats import (
    get_all_strats,
    get_all_conditions,
    StrategyDefinition,
    get_strategy_class,
)
from yumi import divide_chunks


class BackTester:
    @classmethod
    def create(cls):
        return cls()

    def insert_start_of_backtest(
        self, symbols: list[str], strategies: list[dict] | None = None
    ):
        """Insert an entry to start backtest"""
        with get_sync_sessionm().begin() as session:
            scans = (
                session.execute(
                    select(Backtests.id).where(Backtests.status == Status.IN_PROGRESS)
                )
                .scalars()
                .all()
            )
            if len(scans) > 0:
                raise RuntimeError("You can't run more than 1 backtest at a time")

            logging.info("inserting new backtest entry")
            backtest_id = session.execute(
                insert(Backtests)
                .values(
                    {
                        "symbols": symbols,
                        "status": Status.IN_PROGRESS,
                        "timestamp": datetime.utcnow(),
                        "strategies": strategies,
                    }
                )
                .returning(Backtests.id)
            ).scalar()
            return backtest_id

    async def backtest_strats(
        self, backtest_id: str, history: History, definition: BacktestDefinition
    ):
        logging.info(
            "Beginning backtesting over the last %s days...",
            definition.days_to_test_over,
        )
        try:
            """Check that the entry exists and is in progress"""
            with get_sync_sessionm().begin() as session:
                session.execute(
                    select(Backtests.id).where(Backtests.status == Status.IN_PROGRESS)
                ).scalar_one()
            start_time_backtest = datetime.utcnow() - timedelta(
                days=definition.days_to_test_over
            )
            end_time_backtest = datetime.utcnow() - timedelta(minutes=15)

            start_time_historic = start_time_backtest - timedelta(days=60)
            end_time_historic = start_time_backtest

            data = history.get_stock_bars(
                definition.symbols,
                time_frame=TimeFrame.Minute,
                start_time=start_time_backtest,
                end_time=end_time_backtest,
            )
            history.get_stock_bars(
                definition.symbols,
                time_frame=TimeFrame.Day,
                start_time=start_time_historic,
                end_time=end_time_historic,
            )

            strategies = definition.strategy_definitions or []
            if definition.strategy_aliases is not None:
                all_strats = get_all_strats()
                for strat in definition.strategy_aliases:
                    strate = all_strats.get(strat)
                    if not strate:
                        raise KeyError(f"Strategy with alias {strat} doesn't exist")
                    strategies.append(StrategyDefinition(**strate.dict()))

            all_conditions = get_all_conditions()
            strat_classes: list[Strategy] = []
            for strat in strategies:
                conditions = []
                for cond in strat.conditions:
                    if (condition := all_conditions.get(cond.name)) is None:
                        raise KeyError(f"condition {cond.name} doesn't exist")
                    new_condition = deepcopy(condition)
                    new_condition.update_variables(cond.variables)
                    new_condition.active = cond.active
                    new_condition.type = cond.type
                    conditions.append(new_condition)
                strat_classes.append(
                    get_strategy_class(
                        strat.name, strat.alias, strat.active, conditions
                    )
                )

            strat_data: list[tuple[Strategy, MockTrader, list[Bar]]] = []
            for strat in strat_classes:
                bars = []
                [bars.extend(value) for value in data.data.values()]
                bars.sort(key=lambda x: x.timestamp)
                strat_data.append(
                    (
                        strat.create(
                            history,
                            definition.symbols,
                            start_time_historic,
                            end_time_historic,
                            conditions=conditions,
                        ),
                        MockTrader.create(),
                        bars,
                    )
                )
            processes = []
            with ThreadPoolExecutor(max_workers=4) as xacuter:
                for strat, trader, bars in strat_data:
                    processes.append(
                        xacuter.submit(
                            self.test_strat,
                            strategy=strat,
                            trader=trader,
                            bars=bars,
                        )
                    )
            overall = defaultdict(MockTrader.get_aggregate_template)
            for future in as_completed(processes):
                result: tuple[MockTrader, Strategy] = future.result()
                trader, strat = result
                for key, value in trader.aggregate().items():
                    field = overall[strat.ALIAS][key]
                    if isinstance(field, dict):
                        field.update(value)
                    else:
                        field += value

            with get_sync_sessionm().begin() as session:
                session.execute(
                    update(Backtests)
                    .where(Backtests.id == backtest_id)
                    .values(result=overall, status=Status.COMPLETED)
                )
                for chunk in divide_chunks(
                    [
                        {**asdict(stat), "backtest_id": backtest_id}
                        for stat in trader.stats_record
                    ],
                    100,
                ):
                    session.execute(insert(BacktestStats).values(chunk))

            logging.info("backtest %s completed successfully", backtest_id)
        except Exception as exc:
            logging.exception(exc)
            logging.error("failed to complete backtest")
            with get_sync_sessionm().begin() as session:
                session.execute(
                    on_conflict_update(
                        insert(Backtests).values(
                            id=backtest_id,
                            symbols=definition.symbols,
                            result={},
                            status=Status.FAILED,
                            timestamp=datetime.utcnow(),
                        ),
                        Backtests,
                    )
                )

    @staticmethod
    def test_strat(
        strategy: Strategy,
        trader: MockTrader,
        bars: list[Bar],
    ):
        strat_name = type(strategy).__name__
        num_bars = len(bars)
        symbol = bars[0].symbol
        last_percent = 0
        for i in range(num_bars):
            percent_completed = int(i / num_bars * 100)
            if percent_completed > last_percent + 20:
                last_percent = percent_completed
                logging.debug(
                    "Progress of %s on %s: %s", strat_name, symbol, percent_completed
                )
            action, qty = strategy.run(trader, bars[i], False)
            trader.post_trade_update(
                symbol, action, qty, bars[i].close, bars[i].timestamp
            )

        return trader, strategy
