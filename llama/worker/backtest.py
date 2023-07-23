import numpy as np
from ..stocks.graph import get_times_and_closing_p
from ..consts import HISTORY_CLIENT
from alpaca.data.timeframe import TimeFrame
from datetime import datetime, timedelta
import logging
from time import sleep
from collections import defaultdict


def backtest_moving_average(symbols: list[str] = ["SPY"], hours_to_test: int = 2000):
    data = HISTORY_CLIENT.get_stock_bars(
        symbols,
        time_frame=TimeFrame.Minute,
        start_date=(datetime.utcnow() - timedelta(hours=hours_to_test)),
    )
    pos_held = defaultdict(lambda: False)
    for symbol in symbols:
        startBal = 2000  # Start out with 2000 dollars
        balance = startBal
        buys = 0
        sells = 0
        for i in range(
            4, 60 * hours_to_test
        ):  # Start four minutes in, so that MA can be calculated
            _, close_list = get_times_and_closing_p(symbol, data)
            ma = np.mean(close_list[i - 4 : i + 1])
            last_price = close_list[i]

            if ma + 0.1 < last_price and not pos_held[symbol]:
                logging.info("buying a stock of %s", symbol)
                balance -= last_price
                pos_held[symbol] = True
                buys += 1
            elif ma - 0.1 > last_price and pos_held[symbol]:
                logging.info("selling a share of %s", symbol)
                balance += last_price
                pos_held[symbol] = False
                sells += 1
            sleep(0.01)

        logging.info("Buys of %s: %s on itteration %s", symbol, buys, i)
        logging.info("Sells of %s: %s on itteration %s", symbol, sells, i)

        if buys > sells:
            balance += close_list[
                60 * hours_to_test - 1
            ]  # Add back your equity to your balance

        logging.info("Final Balance: %s", balance)

        logging.info(
            "Profit if held: %s",
            str(close_list[60 * hours_to_test - 1] - close_list[0]),
        )
        logging.info("Profit from algorithm: %s", str(balance - startBal))
