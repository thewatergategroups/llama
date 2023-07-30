from alpaca.data.live import StockDataStream
from alpaca.data.models import Quote, Bar, Trade
from ..settings import Settings
from ..stocks import LlamaTrader, MockLlamaTrader
from ..stocks.models import CustomBarSet
from ..stocks.strats import Strategy


class liveStockDataStream:
    def __init__(
        self,
        wss_client: StockDataStream,
        trader: LlamaTrader | MockLlamaTrader,
    ):
        self.wss_client = wss_client
        self.trader = trader
        self.barset = CustomBarSet()
        self.strategies: list[Strategy] = []

    @classmethod
    def create(
        cls,
        settings: Settings,
        trader: LlamaTrader | MockLlamaTrader,
    ):
        """Create an instance of this object"""

        return cls(
            StockDataStream(settings.api_key, settings.secret_key),
            trader,
        )

    async def handle_bars(self, data: Bar):
        """Perform trades based on data"""
        self.barset.append(data)
        for strategy in self.strategies:
            strategy.run(self.trader, self.barset)

    @staticmethod
    async def handle_qoutes(data: Quote):
        # logging.info(data)
        # logging.info(type(data))
        ...

    @staticmethod
    async def handle_trades(data: Trade):
        # logging.info(data)
        # logging.info(type(data))
        ...

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
