"""
Application Entrypoint
"""

import asyncio
import json
import logging
from time import sleep
from datetime import datetime

import uvicorn
from trekkers import database
from yumi import Entrypoints
from alpaca.data.timeframe import TimeFrame
from .backtester import BackTester, BacktestDefinition
from .settings import Settings
from .stocks import History, Trader
from .strats import get_all_strats, insert_conditions, insert_strats
from .worker.websocket import LiveStockDataStream, LiveTradingStream
from .indicators.technical import Indicators


def api(*_, **__):
    """API for querying data"""
    uvicorn.run(
        "llama.api.app:create_app",
        workers=1,
        reload=True,
        host="0.0.0.0",
        factory=True,
        port=8000,
    )


def trade_stream(settings: Settings, *_, **__):
    """Websocket pulling listening for data about trades"""
    trader = Trader.create(settings)
    ls_object: LiveTradingStream = LiveTradingStream.create(settings, trader)
    ls_object.run()


def data_stream(settings: Settings, *_, **__):
    """
    Websocket Stream data about changes in stock data
    """
    trader = Trader.create(settings)
    history = History.create(settings)
    all_ = [asset.symbol for asset in trader.get_assets(trading=True)]
    while not all_:
        logging.warning(
            "Not trading any stocks.. sleeping and retrying in 10 seconds..."
        )
        sleep(10)
        all_ = [asset.symbol for asset in trader.get_assets(trading=True)]

    strats = [strat.create(history, all_) for strat in get_all_strats().values()]
    ls_object = LiveStockDataStream.create(settings, trader)
    ls_object.strategies = strats
    ls_object.subscribe(bars=all_, qoutes=all_)


def db(settings: Settings, action: str, revision: str | None, *_, **__):
    """
    Upgrade and downgrade the database tables
    """
    database(settings.db_settings, action, revision)
    insert_conditions()
    insert_strats()
    Trader.create(settings).get_all_assets(True)


def backtest(settings: Settings, *_, **__):
    """
    Run backtests from the command line
    """
    history = History.create(settings)
    backtester = BackTester.create()
    with open("./backtests/backtests.json", "r", encoding="utf-8") as f:
        list_json = json.loads(f.read())
    for item in list_json:
        definition = BacktestDefinition(**item)
        backtest_id = backtester.insert_start_of_backtest(definition.symbols)
        asyncio.run(backtester.backtest_strats(backtest_id, history, definition))


def debug(settings: Settings, *_, **__):
    """
    Boilter plate code to be ran directly by the command "$ make debug"
    """
    hist = History.create(settings)
    # history.get_stock_bars()
    nvidia_df = hist.get_stock_bars(
        symbols=["NVDA"],
        time_frame=TimeFrame.Day,
        start_time=datetime(2022, 9, 1),
        end_time=datetime(2023, 9, 7),
    )
    logging.info("===================================")
    logging.info(nvidia_df.df)
    technical_indicator = Indicators()
    dfn = nvidia_df.df
    dfn = technical_indicator.calculate_garman_klass_vol(dfn)
    logging.info(dfn)
    dfn = technical_indicator.calculate_rsi_indicator(dfn)
    logging.info(dfn.to_markdown())
    dfn = technical_indicator.calculate_bollinger_bands(dfn, level=0)
    logging.info(dfn.to_markdown())
    # dfn = technical_indicator.calculate_atr(dfn) # apply
    dfn = technical_indicator.calculate_stochastic(dfn, k_period=14)
    logging.info(dfn.to_markdown())
    dfn_short = technical_indicator.calculate_smas(
        dfn, short_window=50, long_window=200
    )
    logging.info(dfn_short)  # .style
    dfn_long = technical_indicator.calculate_smas(dfn, short_window=1, long_window=200)
    logging.info(dfn_long)  # .style
    logging.info("DONE")
    logging.info(dfn)  # .style


class Entry(Entrypoints):
    """Defining entrypoints to the application"""

    API = "api", api
    DATASTREAM = "datastream", data_stream
    TRADESTREAM = "tradestream", trade_stream
    DATABASE = "db", db
    BACKTEST = "backtest", backtest
    DEBUG = "debug", debug
