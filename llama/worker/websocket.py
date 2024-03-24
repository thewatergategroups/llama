"""
Define the websocket classes to get trading and stock trading data
"""

import logging

from alpaca.data.live import StockDataStream
from alpaca.data.models import Bar, Quote, Trade
from alpaca.data.timeframe import TimeFrame
from alpaca.trading import TradeEvent, TradeUpdate
from alpaca.trading.stream import TradingStream
from sqlalchemy.dialects.postgresql import insert
from trekkers.statements import upsert

from ..database import Bars, Orders, Qoutes, Trades, TradeUpdates
from ..settings import Settings, get_sync_sessionm
from ..stocks.trader import Trader
from ..strats import Strategy


class LiveStockDataStream:
    """
    Get sent live updates for changes to stock bars,qoutes and trades
    """

    def __init__(self, wss_client: StockDataStream, trader: Trader):
        self.wss_client = wss_client
        self.trader = trader
        self.strategies: list[Strategy] = []

    @classmethod
    def create(cls, settings: Settings, trader: Trader):
        """Create an instance of this object"""

        return cls(StockDataStream(settings.api_key, settings.secret_key), trader)

    async def handle_bars(self, data: Bar):
        """Perform trades based on data"""
        time_frame: TimeFrame = TimeFrame.Minute
        for strategy in self.strategies:
            strategy.run(self.trader, data)
        with get_sync_sessionm().begin() as session:
            data_dict = data.model_dump()
            data_dict["timeframe"] = time_frame.value
            session.execute(insert(Bars).values(data_dict))

    async def handle_qoutes(self, data: Quote):
        """Handle incoming qoutes"""
        with get_sync_sessionm().begin() as session:
            session.execute(insert(Qoutes).values(data.model_dump()))

    async def handle_trades(self, data: Trade):
        """handle incoming trades"""
        with get_sync_sessionm().begin() as session:
            session.execute(insert(Trades).values(data.model_dump()))

    def subscribe(
        self,
        qoutes: tuple[str] | None = None,
        trades: tuple[str] | None = None,
        bars: tuple[str] | None = None,
    ):
        """Start up websockets and subscribe to data streams"""
        if bars is not None:
            self.wss_client.subscribe_bars(self.handle_bars, *bars)
        if trades is not None:
            self.wss_client.subscribe_trades(self.handle_trades, *trades)
        if qoutes is not None:
            self.wss_client.subscribe_quotes(self.handle_qoutes, *qoutes)
        self.wss_client.run()


class LiveTradingStream:
    """
    Websocket stream to recieve live updates about trade events
    """

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
        """Function that handles the incoming trade event"""
        logging.info(
            "received a trading update event %s on order %s for symbol %s",
            trade_update.event,
            trade_update.order.id,
            trade_update.order.symbol,
        )
        upsert(get_sync_sessionm(), trade_update.order.model_dump(), Orders)

        trade_update_dict = trade_update.model_dump()
        trade_update_dict.pop("order")
        trade_update_dict["order_id"] = trade_update.order.id
        upsert(get_sync_sessionm(), trade_update_dict, TradeUpdates)

        self.trader.get_position(trade_update.order.symbol, force=True)
        self.trader.get_account()
        if trade_update.event in {TradeEvent.FILL, TradeEvent.PARTIAL_FILL}:
            ...
        elif trade_update.event == TradeEvent.CANCELED:
            ...
        elif trade_update.event == TradeEvent.NEW:
            ...

    def run(self):
        """
        The startup function that starts the webhook and subscribes to updates
        """
        self.trading_stream.subscribe_trade_updates(self.handle_trade_updates)
        logging.info("Running trading updates stream...")
        self.trading_stream.run()
