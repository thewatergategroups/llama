import numpy as np
from ..consts import TRADER_CLIENT, HISTORY_CLIENT
from ..stocks.graph import get_times_and_closing_p
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta
from collections import defaultdict
import logging
from time import sleep


def run(symbols: list[str] = ["SPY"]):
    """Run the entrypoint of the stock trading bot"""
    pos_held = defaultdict(lambda: False)
    while True:
        data = HISTORY_CLIENT.get_stock_bars(
            symbols,
            time_frame=TimeFrame.Minute,
            start_date=(datetime.utcnow() - timedelta(minutes=5)),
        )
        for key in data.data.keys():
            _, closing_prices = get_times_and_closing_p(key, data)
            last_closing_price = closing_prices[-1]
            np_closing = np.array(closing_prices, dtype=np.float64)
            moving_average = np.mean(np_closing)
            if moving_average + 0.1 < last_closing_price and not pos_held[key]:
                logging.info("buying a stock of %s", key)
                TRADER_CLIENT.place_order(key, time_in_force=TimeInForce.GTC)
            elif moving_average - 0.1 > last_closing_price and pos_held[key]:
                logging.info("selling a share of %s", key)
                TRADER_CLIENT.place_order(
                    key, time_in_force=TimeInForce.GTC, side=OrderSide.SELL
                )
                pos_held[key] = False
        sleep(60)
