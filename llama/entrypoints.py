import asyncio
import uvicorn
from datetime import datetime, timedelta
from .worker.websocket import liveStockDataStream, liveTradingStream
from .settings import Settings
from .stocks import History, Trader
from .strats import insert_strats, get_all_strats, insert_conditions
from .backtester import BackTester
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


def debug(settings: Settings, *args, **kwargs):
    history = History.create(settings)
    print(
        history.get_closest_qoute_to_time(
            "AAPL", datetime.utcnow() - timedelta(minutes=15)
        )
    )
    print(history.get_latest_qoute("AAPL"))


def data_stream(settings: Settings, *args, **kwargs):
    """Websocket Stream data"""
    trader = Trader.create(settings)
    history = History.create(settings)
    all_ = [asset.symbol for asset in trader.get_assets(trading=True)]
    strats = [strat.create(history, all_) for strat in get_all_strats().values()]
    ls_object = liveStockDataStream.create(settings, trader)
    ls_object.strategies = strats
    ls_object.subscribe(bars=all_, qoutes=all_)


def db(settings: Settings, action: str, revision: str | None, *args, **kwargs):
    database(settings.db_settings, action, revision)
    insert_conditions()
    insert_strats()
    Trader.create(settings).get_all_assets(True)


def backtest(settings: Settings, *args, **kwargs):
    trader = Trader.create(settings)
    history = History.create(settings)
    backtester = BackTester.create(settings)
    symbols = [asset.symbol for asset in trader.get_assets(trading=True)]
    backtest_id = backtester.insert_start_of_backtest(symbols)
    asyncio.run(backtester.backtest_strats(backtest_id, history, symbols))


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
    DEBUG = "debug", debug

    @classmethod
    def get_entrypoint(cls, entrypoint: str):
        for entry in cls:
            if entrypoint == entry.entrypoint:
                return entry.function
        raise KeyError(f"Entrypoint {entrypoint} not found...")

    @classmethod
    def get_all_names(cls):
        return [value.entrypoint for value in cls]
