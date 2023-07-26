import logging
from alpaca.data.models import BarSet
from .tools import get_times_and_closing_p
import numpy as np
from alpaca.trading.enums import OrderSide, TimeInForce
import logging
from .trader import LlamaTrader, MockLlamaTrader


def moving_average_strategy(
    trader: LlamaTrader | MockLlamaTrader,
    data: BarSet,
):
    for key in data.data.keys():
        _, closing_prices = get_times_and_closing_p(key, data)
        last_closing_price = closing_prices[-1]
        np_closing = np.array(closing_prices, dtype=np.float64)
        moving_average = np.mean(np_closing)
        logging.debug("moving average: %s", moving_average)
        logging.debug("last closing price %s", last_closing_price)
        buy_condition = (
            moving_average > last_closing_price - 0.1 and trader.positions_held[key] < 5
        )
        sell_condition = (
            moving_average < last_closing_price + 0.2 and trader.positions_held[key] > 0
        )
        if buy_condition:
            logging.debug("buying a stock of %s", key)
            trader.place_order(
                key, time_in_force=TimeInForce.GTC, last_price=last_closing_price
            )
        elif sell_condition:
            logging.debug("selling a share of %s", key)
            trader.place_order(
                key,
                time_in_force=TimeInForce.GTC,
                side=OrderSide.SELL,
                last_price=last_closing_price,
            )
