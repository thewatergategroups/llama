import uvicorn

from .worker.websocket import liveStockDataStream, liveTradingStream
from .settings import Settings, STOCKS_TO_TRADE, ETFS_TO_TRADE
from .stocks import History, STRATEGIES, BackTester, Trader
from trekkers import database
from enum import Enum
from typing import Callable


def api(*args, **kwargs):
    """API for querying data"""
    uvicorn.run(
        "llama.api.app:create_app",
        workers=1,
        reload=True,
        host="0.0.0.0",
        factory=True,
        port=8000,
    )


def trade_stream(settings: Settings, *args, **kwargs):
    trader = Trader.create(settings)
    ls_object: liveTradingStream = liveTradingStream.create(settings, trader)
    ls_object.run()


def data_stream(settings: Settings, *args, **kwargs):
    """Websocket Stream data"""
    trader = Trader.create(settings)
    history = History.create(settings)
    all_ = STOCKS_TO_TRADE + ETFS_TO_TRADE
    strats = [strat.create(history, all_) for strat in STRATEGIES]
    ls_object = liveStockDataStream.create(settings, trader)
    ls_object.strategies = strats
    ls_object.subscribe(bars=all_)


def db(settings: Settings, action: str, revision: str | None, *args, **kwargs):
    database(settings.db_settings, action, revision)


def backtest(settings: Settings, *args, **kwargs):
    history = History.create(settings)
    backtester = BackTester.create(settings)
    backtester.backtest_strats(history, STOCKS_TO_TRADE + ETFS_TO_TRADE)


class Entrypoints(Enum):
    def __init__(self, entrypoint: str, function: Callable):
        super().__init__()
        self.entrypoint = entrypoint
        self.function = function

    API = "api", api
    DATASTREAM = "datastream", data_stream
    TRADESTREAM = "tradestream", trade_stream
    DATABASE = "db", db
    BACKTEST = "backtest", backtest

    @classmethod
    def get_entrypoint(cls, entrypoint: str):
        for entry in cls:
            if entrypoint == entry.entrypoint:
                return entry.function
        raise KeyError(f"Entrypoint {entrypoint} not found...")

    @classmethod
    def get_all_names(cls):
        return [value.entrypoint for value in cls]
