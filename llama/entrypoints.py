import uvicorn
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta
from time import sleep
import logging
from .worker.websocket import liveStockDataStream
from .settings import Settings
from .stocks import LlamaHistory, LlamaTrader, moving_average_strategy, MockLlamaTrader


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
    ls_object = liveStockDataStream.create(settings, trader)
    stocks = (
        "AAPL",
        "TSLA",
        "MSFT",
        "PFE",
        "XOM",
        "BAC",
        "INTC",
        "IBM",
        "CSCO",
        "HPQ",
        "JPM",
        "WML",
    )
    etfs = (
        "SPY",
        "VOO",
        "IVV",
        "QQQ",
        "VTWO",
        "DIA",
        "VTI",
        "ONEQ",
        "QQQE",
        "QQQJ",
    )
    all_ = stocks + etfs
    ls_object.subscribe(bars=all_)


def rest(settings: Settings):
    """REST api trading stratedgy"""
    trader = LlamaTrader.create(settings)
    history = LlamaHistory.create(settings)
    symbols = ["TSLA", "AAPL", "SPY"]
    while True:
        data = history.get_stock_bars(
            symbols,
            time_frame=TimeFrame.Minute,
            start_time=(datetime.utcnow() - timedelta(minutes=5)),
        )
        moving_average_strategy(trader, data)
        sleep(60)


def backtest_moving_average(settings: Settings):
    history = LlamaHistory.create(settings)
    mock_trader = MockLlamaTrader()

    symbols = ["TSLA", "AAPL", "SPY"]
    minutes_to_test = 300
    start_time = datetime.utcnow() - timedelta(minutes=minutes_to_test)
    end_time = start_time + timedelta(minutes=5)
    while end_time < (datetime.utcnow() - timedelta(minutes=15)):
        data = history.get_stock_bars(
            symbols,
            time_frame=TimeFrame.Minute,
            start_time=start_time,
            end_time=end_time,
        )
        start_time += timedelta(minutes=1)
        end_time += timedelta(minutes=1)
        moving_average_strategy(mock_trader, data)
    logging.info(mock_trader.aggregate())


ENTRYPOINTS = {
    "api": api,
    "live": live,
    "backtest": backtest_moving_average,
    "rest": rest,
}
