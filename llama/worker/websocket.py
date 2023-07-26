from alpaca.data.live import StockDataStream
from alpaca.data.models import QuoteSet, BarSet, TradeSet
import logging

from ..settings import Settings
from ..stocks import moving_average_strategy, LlamaTrader, MockLlamaTrader


class liveStockDataStream:
    def __init__(
        self, wss_client: StockDataStream, trader: LlamaTrader | MockLlamaTrader
    ):
        self.wss_client = wss_client
        self.trader = trader

    @classmethod
    def create(cls, settings: Settings):
        """Create an instance of this object"""
        return cls(
            StockDataStream(settings.api_key, settings.secret_key),
            LlamaTrader.create(settings),
        )

    async def handle_bars(self, data: BarSet):
        """Perform trades based on data"""
        moving_average_strategy(self.trader, data)

    @staticmethod
    async def handle_qoutes(data: QuoteSet):
        logging.info(data)

    @staticmethod
    async def handle_trades(data: TradeSet):
        logging.info(data)

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
