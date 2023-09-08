from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta
import logging

from trekkers import on_conflict_update
from . import History, STRATEGIES, Strategy
from .models import NullPosition
from concurrent.futures import ProcessPoolExecutor, as_completed
from alpaca.data.models import Bar
from collections import defaultdict
from alpaca.trading import OrderSide
from alpaca.trading import Position, Order
from alpaca.trading.enums import OrderSide, TimeInForce
from ..database.models import Backtests
from ..settings import Settings
from trekkers.config import get_sync_sessionmaker
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import update, select


class MockTrader:
    """Llama is created"""

    def __init__(self):
        self.positions: dict[str, Position] = {}
        self.orders: list[Order] = []
        self.balance = 100_000
        self.starting_balance = self.balance
        self.buys = 0
        self.sells = 0

    @classmethod
    def create(cls):
        """Create class with data"""
        return cls()

    def get_position(self, symbol: str):
        if (position := self.positions.get(symbol)) is not None:
            return position
        self.positions[symbol] = NullPosition(symbol=symbol)
        return self.positions[symbol]

    def place_order(
        self,
        symbol: str = "TSLA",
        time_in_force: TimeInForce = TimeInForce.GTC,
        side: OrderSide = OrderSide.BUY,
        quantity: int = 1,
    ):
        """place order"""
        position = self.get_position(symbol)

        if side == OrderSide.BUY:
            position.qty = str(int(position.qty) + quantity)
            position.qty_available = str(int(position.qty_available) + quantity)
        elif side == OrderSide.SELL:
            position.qty = str(int(position.qty) - quantity)
            position.qty_available = str(int(position.qty_available) - quantity)

    def aggregate(self, verbose: bool = False):
        response = {
            "profit": self.balance - self.starting_balance,
            "buys": self.buys,
            "sells": self.sells,
            "total_positions_held": sum(
                [int(pos.qty) for pos in self.positions.values()]
            ),
        }
        if verbose:
            response["extra"] = {"positions_held": dict(self.positions)}
        return response


class BackTester:
    def __init__(self, pg_sessionmaker: sessionmaker[Session]):
        self.processes = []
        self.pg_sessionmaker = pg_sessionmaker

    @classmethod
    def create(cls, settings: Settings):
        pg_sessionmaker = get_sync_sessionmaker(settings.db_settings)
        return cls(pg_sessionmaker)

    def insert_start_of_backtest(self, symbols):
        """Insert an entry to start backtest"""
        with self.pg_sessionmaker.begin() as session:
            scans = (
                session.execute(
                    select(Backtests.id).where(Backtests.status == "inprogress")
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
                        "status": "inprogress",
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
            with self.pg_sessionmaker.begin() as session:
                session.execute(
                    select(Backtests.id).where(Backtests.status == "inprogress")
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

            with self.pg_sessionmaker.begin() as session:
                session.execute(
                    update(Backtests)
                    .where(Backtests.id == backtest_id)
                    .values(result=overall, status="success")
                )
            logging.info("backtest %s completed successfully", backtest_id)
        except Exception as exc:
            logging.exception(exc)
            logging.error("failed to complete backtest")
            with self.pg_sessionmaker.begin() as session:
                session.execute(
                    on_conflict_update(
                        insert(Backtests).values(
                            id=backtest_id,
                            symbols=symbols,
                            result=overall,
                            status="failed",
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
            if action == OrderSide.BUY:
                trader.balance -= bars[i].close * qty
                trader.buys += qty
                logging.info("buy on itteration %s", i)
            elif action == OrderSide.SELL:
                trader.balance += bars[i].close * qty
                trader.sells += qty
                logging.info("sell on itteration %s", i)

        return trader, strategy
