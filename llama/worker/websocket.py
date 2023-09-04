import logging
from alpaca.data.live import StockDataStream
from alpaca.trading.stream import TradingStream
from alpaca.trading import TradeUpdate, TradeEvent
from alpaca.data.models import Quote, Bar, Trade
from alpaca.data.timeframe import TimeFrame


from ..settings import Settings
from ..stocks.strats import Strategy
from ..stocks.trader import Trader
from sqlalchemy.dialects.postgresql import insert
from ..database.models import Bars, Trades, Qoutes, Orders, TradeUpdates
from trekkers.statements import on_conflict_update


class liveStockDataStream:
    def __init__(
        self,
        wss_client: StockDataStream,
        trader: Trader,
    ):
        self.wss_client = wss_client
        self.trader = trader
        self.strategies: list[Strategy] = []

    @classmethod
    def create(
        cls,
        settings: Settings,
        trader: Trader,
    ):
        """Create an instance of this object"""

        return cls(
            StockDataStream(settings.api_key, settings.secret_key),
            trader,
        )

    async def handle_bars(self, data: Bar):
        """Perform trades based on data"""
        time_frame: TimeFrame = TimeFrame.Minute
        for strategy in self.strategies:
            strategy.run(self.trader, data)
        with self.trader.pg_sessionmaker.begin() as session:
            data_dict = data.dict()
            data_dict["timeframe"] = time_frame.value
            session.execute(insert(Bars).values(data_dict))

    async def handle_qoutes(self, data: Quote):
        with self.trader.pg_sessionmaker.begin() as session:
            session.execute(insert(Qoutes).values(data.dict()))

    async def handle_trades(self, data: Trade):
        with self.trader.pg_sessionmaker.begin() as session:
            session.execute(insert(Trades).values(data.dict()))

    def subscribe(
        self,
        qoutes: tuple[str] | None = None,
        trades: tuple[str] | None = None,
        bars: tuple[str] | None = None,
    ):
        if bars is not None:
            self.wss_client.subscribe_bars(self.handle_bars, *bars)
        if trades is not None:
            self.wss_client.subscribe_trades(self.handle_trades, *trades)
        if qoutes is not None:
            self.wss_client.subscribe_quotes(self.handle_qoutes, *qoutes)
        self.wss_client.run()


class liveTradingStream:
    def __init__(self, trading_stream: TradingStream, trader: Trader):
        self.trading_stream = trading_stream
        self.trader = trader

    @classmethod
    def create(cls, settings: Settings, trader: Trader):
        """Create an instance of this object"""

        return cls(
            TradingStream(settings.api_key, settings.secret_key, paper=settings.paper),
            trader,
        )

    async def handle_trade_updates(self, trade_update: TradeUpdate):
        logging.info(
            "received a trading update event %s on order %s for symbol %s",
            trade_update.event,
            trade_update.order.id,
            trade_update.order.symbol,
        )
        with self.trader.pg_sessionmaker.begin() as session:
            ordr_stmt = insert(Orders).values(trade_update.order.dict())
            session.execute(on_conflict_update(ordr_stmt, Orders))

            trade_update_dict = trade_update.dict()
            trade_update_dict.pop("order")
            trade_update_dict["order_id"] = trade_update.order.id
            trade_stmt = insert(TradeUpdates).values(trade_update_dict)
            session.execute(on_conflict_update(trade_stmt, TradeUpdates))

        if trade_update.event in {TradeEvent.FILL, TradeEvent.PARTIAL_FILL}:
            ...
        elif trade_update.event == TradeEvent.CANCELED:
            ...
        elif trade_update.event == TradeEvent.NEW:
            ...

    def run(self):
        self.trading_stream.subscribe_trade_updates(self.handle_trade_updates)
        logging.info("Running trading updates stream...")
        self.trading_stream.run()
