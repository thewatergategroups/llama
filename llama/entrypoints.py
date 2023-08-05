import uvicorn
from .worker.websocket import liveStockDataStream
from .settings import Settings, STOCKS_TO_TRADE, ETFS_TO_TRADE
from .stocks import LlamaHistory, MockLlamaTrader, STRATEGIES, BackTester


def api(settings: Settings):
    """API for querying data"""
    uvicorn.run(
        "llama.api.app:create_app",
        workers=1,
        reload=True,
        host="0.0.0.0",
        factory=True,
        port=8000,
    )


def live(settings: Settings):
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


def backtest(settings: Settings):
    history = LlamaHistory.create(settings)
    backtester = BackTester()
    backtester.backtest_strats(history, test_stocks)


ENTRYPOINTS = {
    "api": api,
    "live": live,
    "backtest": backtest,
}
