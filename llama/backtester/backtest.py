from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta
import logging

from trekkers import on_conflict_update
from ..stocks import History, STRATEGIES, Strategy
from concurrent.futures import ProcessPoolExecutor, as_completed
from alpaca.data.models import Bar
from collections import defaultdict
from ..database.models import Backtests
from ..settings import get_sync_sessionm
from ..consts import Status
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import update, select
from .mocktrader import MockTrader


class BackTester:
    def __init__(self):
        self.processes = []

    @classmethod
    def create(cls):
        return cls()

    def insert_start_of_backtest(self, symbols):
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
                    }
                )
                .returning(Backtests.id)
            ).scalar()
            return backtest_id

    def backtest_strats(
        self,
        backtest_id: str,
        history: History,
        symbols: list[str],
        days_to_test: int = 30,
    ):
        logging.info("Beginning backtesting over the last %s days...", days_to_test)
        try:
            """Check that the entry exists and is in progress"""
            with get_sync_sessionm().begin() as session:
                session.execute(
                    select(Backtests.id).where(Backtests.status == Status.IN_PROGRESS)
                ).scalar_one()
            start_time_backtest = datetime.utcnow() - timedelta(days=days_to_test)
            end_time_backtest = datetime.utcnow() - timedelta(minutes=15)

            start_time_historic = start_time_backtest - timedelta(days=60)
            end_time_historic = start_time_backtest

            data = history.get_stock_bars(
                symbols,
                time_frame=TimeFrame.Minute,
                start_time=start_time_backtest,
                end_time=end_time_backtest,
            )
            history.get_stock_bars(
                symbols,
                time_frame=TimeFrame.Day,
                start_time=start_time_historic,
                end_time=end_time_historic,
            )
            strat_data: dict[str, list[Strategy, MockTrader, list[Bar]]] = defaultdict(
                lambda: []
            )
            for strat in STRATEGIES:
                for symbol in symbols:
                    strat_data[symbol].append(
                        (
                            strat.create(
                                history,
                                [symbol],
                                start_time_historic,
                                end_time_historic,
                            ),
                            MockTrader.create(),
                            data.data[symbol],
                        )
                    )

            with ProcessPoolExecutor(max_workers=4) as xacuter:
                for symbol, strat_list in strat_data.items():
                    for strat, trader, bars in strat_list:
                        self.processes.append(
                            xacuter.submit(
                                self.test_strat,
                                strategy=strat,
                                trader=trader,
                                bars=bars,
                            )
                        )
            overall = defaultdict(lambda: defaultdict(lambda: 0))
            for future in as_completed(self.processes):
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
                            symbols=symbols,
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
            action, qty = strategy.run(trader, bars[i])
            update
            if (action, qty) != (None, None):
                trader.post_trade_update_position(symbol, action, qty, bars[i].close)
                trader.update_stats(symbol, action, qty, bars[i].close, i)

        return trader, strategy
