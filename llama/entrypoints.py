import uvicorn
from .worker.websocket import liveStockDataStream
from .settings import Settings, STOCKS_TO_TRADE, ETFS_TO_TRADE
from .database.config import get_db_config
from .stocks import LlamaHistory, MockLlamaTrader, STRATEGIES, BackTester
from .database.config import run_downgrade, run_upgrade
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


def live(settings: Settings, *args, **kwargs):
    """Websocket Stream data"""
    trader = MockLlamaTrader()
    history = LlamaHistory.create(settings)
    all_ = STOCKS_TO_TRADE + ETFS_TO_TRADE

    strats = [strat.create(history, all_) for strat in STRATEGIES]
    ls_object = liveStockDataStream.create(settings, trader)
    ls_object.strategies = strats
    ls_object.subscribe(bars=all_)


test_stocks = [
    "PFE",
    "META",
    "MSFT",
    "AMZN",
    "LMT",
    "UAL",
    "CMCSA",
    "BA",
    "GOOGL",
    "GD",
    "SO",
    "VZ",
    "FDX",
    "MO",
    "MRK",
    "ABT",
    "TMUS",
    "OXY",
    "T",
    "F",
]


def backtest(settings: Settings, *args, **kwargs):
    history = LlamaHistory.create(settings)
    backtester = BackTester()
    backtester.backtest_strats(history, test_stocks)


def database(settings: Settings, action: str, revision: str | None):
    if action == "upgrade":
        run_upgrade(settings=settings.db_settings, revision=revision)
    elif action == "downgrade":
        run_downgrade(settings=settings.db_settings, revision=revision)
    else:
        raise KeyError(f"No action {action} found.")


class Entrypoints(Enum):
    def __init__(self, entrypoint: str, function: Callable):
        super().__init__()
        self.entrypoint = entrypoint
        self.function = function

    API = "api", api
    LIVE = "live", live
    DATABASE = "db", database
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
