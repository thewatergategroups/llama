import uvicorn
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta
import logging
from .worker.websocket import liveStockDataStream
from .settings import Settings, STOCKS_TO_TRADE, ETFS_TO_TRADE
from .stocks import LlamaHistory, MockLlamaTrader, STRATEGIES, CustomBarSet
from alpaca.data.models import Bar


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


def backtest_strats(settings: Settings):
    history = LlamaHistory.create(settings)
    mock_trader = MockLlamaTrader()

    symbols = STOCKS_TO_TRADE + ETFS_TO_TRADE
    strats = [strat.create(history, symbols) for strat in STRATEGIES]
    minutes_to_test = 14679
    start_time = datetime.utcnow() - timedelta(minutes=minutes_to_test)
    overall_end_time = datetime.utcnow() - timedelta(minutes=2698)
    logging.info("getting data...")
    data = history.get_stock_bars(
        symbols,
        time_frame=TimeFrame.Minute,
        start_time=start_time,
        end_time=overall_end_time,
    )
    bar_lists: dict[str, list[list[Bar]]] = {}
    for key, item in data.data.items():
        bar_lists[key] = [item[i : i + 15] for i in range(0, len(item), 15)]
    logging.info("back testing data...")
    for key in bar_lists.keys():
        for item in bar_lists[key]:
            for strategy in strats:
                strategy.run(mock_trader, CustomBarSet(item))

    logging.info(mock_trader.aggregate())


ENTRYPOINTS = {
    "api": api,
    "live": live,
    "backtest": backtest_strats,
}
