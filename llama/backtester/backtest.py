from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta
import logging
from copy import deepcopy
from trekkers import on_conflict_update
from ..stocks import History, get_all_strats, Strategy, ConditionDefinition
from concurrent.futures import ProcessPoolExecutor, as_completed
from alpaca.data.models import Bar
from collections import defaultdict
from ..database.models import Backtests
from ..settings import get_sync_sessionm
from ..consts import Status
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import update, select
from .mocktrader import MockTrader
from .consts import BacktestDefinition


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

    def backtest_strats(
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
            strat_data: dict[str, list[Strategy, MockTrader, list[Bar]]] = defaultdict(
                lambda: []
            )

            strategies = get_all_strats().values()
            strats_and_conds: dict[str, dict[str, ConditionDefinition]] = {}
            if definition.strategies is not None:
                strategies = []
                for strat in definition.strategies:
                    strats_and_conds[strat.strategy_alias] = {
                        cond.name: cond for cond in strat.conditions
                    }
                    strategy = get_all_strats().get(strat.strategy_alias)
                    if strategy is None:
                        continue

                    strategies.append(strategy)

            for strat in strategies:
                conditions = []
                if (conds := strats_and_conds.get(strat.ALIAS)) is not None:
                    for value in strat.DEFAULT_CONDITIONS:
                        if (cond := conds.get(value.name)) is None:
                            continue
                        new_condition = deepcopy(value)
                        new_condition.update_variables(cond.variables)
                        new_condition.active = cond.active
                        new_condition.type = cond.type
                        conditions.append(new_condition)
                for symbol in definition.symbols:
                    strat_data[symbol].append(
                        (
                            strat.create(
                                history,
                                [symbol],
                                start_time_historic,
                                end_time_historic,
                                conditions=conditions,
                            ),
                            MockTrader.create(),
                            data.data[symbol],
                        )
                    )
            processes = []
            with ProcessPoolExecutor(max_workers=4) as xacuter:
                for symbol, strat_list in strat_data.items():
                    for strat, trader, bars in strat_list:
                        processes.append(
                            xacuter.submit(
                                self.test_strat,
                                strategy=strat,
                                trader=trader,
                                bars=bars,
                            )
                        )
            overall = defaultdict(lambda: defaultdict(lambda: 0))
            for future in as_completed(processes):
                result: tuple[MockTrader, Strategy] = future.result()
                trader, strat = result
                for key, value in trader.aggregate().items():
                    overall[type(strat).__name__][key] += value
            with get_sync_sessionm().begin() as session:
                session.execute(
                    update(Backtests)
                    .where(Backtests.id == backtest_id)
                    .values(result=overall, status=Status.COMPLETED)
                )
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
                            result=overall,
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
            if (action, qty) != (None, None):
                trader.post_trade_update_position(symbol, action, qty, bars[i].close)
                trader.update_stats(symbol, action, qty, bars[i].close, i)

        return trader, strategy