import logging
from alpaca.data.models import BarSet

from llama.stocks.models import CustomBarSet
from .models import CustomBarSet
from .tools import get_times_and_closing_p
import numpy as np
from alpaca.trading.enums import OrderSide, TimeInForce
import logging
from .history import LlamaHistory
from datetime import datetime, timedelta
from alpaca.data.timeframe import TimeFrame
from .trader import LlamaTrader, MockLlamaTrader
from .history import LlamaHistory
from .tools import get_times_and_closing_p
from ..tools import custom_json_encoder
from alpaca.data.models import BarSet
from .models import Metric
from datetime import datetime, timedelta
from alpaca.data.timeframe import TimeFrame
import numpy as np
import logging
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import os
import json


class Strategy:
    def __init__(self, data: BarSet | CustomBarSet):
        self.historic_data = data

    @classmethod
    def create(
        cls,
        history: LlamaHistory,
        symbols: list[str],
        timeframe: TimeFrame = TimeFrame.Day,
        days: int = 50,
        force: bool = False,
    ):
        data = history.get_stock_bars(
            symbols,
            time_frame=timeframe,
            start_time=(datetime.utcnow() - timedelta(days=days)),
        )
        return cls(data)

    def run(
        self,
        trader: LlamaTrader | MockLlamaTrader,
        current_data: CustomBarSet | BarSet,
    ):
        """Standard strat run method to be overwritten"""
        raise RuntimeError("Unimplemented Method")

    @classmethod
    def storage_location(cls):
        return os.path.join(os.getcwd(), f"data/{cls.__name__}.json")

    @classmethod
    def store(cls, data: dict):
        with open(cls.storage_location(), "w") as f:
            f.write(json.dumps(data, default=custom_json_encoder))

    @classmethod
    def get(cls):
        try:
            with open(cls.storage_location(), "r") as f:
                data = json.loads(f.read())
            return data
        except Exception as exc:
            logging.error(str(exc))  # want a shorter version of the exception
            return None


class MovingAverageStrat(Strategy):
    def __init__(self, data: BarSet | CustomBarSet, moving_averages: dict[str, Metric]):
        super().__init__(data)
        self.moving_averages = moving_averages

    @classmethod
    def create(
        cls,
        history: LlamaHistory,
        symbols: list[str],
        timeframe: TimeFrame = TimeFrame.Day,
        days: int = 50,
        force: bool = False,
    ):
        historic_info = cls.get()
        if (
            historic_info
            and (
                datetime.fromisoformat(historic_info["collected_at"])
                > datetime.utcnow() - timedelta(days=1)
            )
            and not force
        ):
            return cls(
                historic_info["data"],
                {
                    name: Metric(**value)
                    for name, value in historic_info["moving_averages"].items()
                },
            )

        data = history.get_stock_bars(
            symbols,
            time_frame=timeframe,
            start_time=(datetime.utcnow() - timedelta(days=days)),
        )

        moving_averages = cls.calculate_moving_averages(data)
        cls.store(
            {
                "data": data,
                "moving_averages": moving_averages,
                "collected_at": datetime.utcnow(),
            }
        )
        return cls(data, moving_averages)

    def trade(self, args: tuple[dict, BarSet, LlamaTrader | MockLlamaTrader]):
        symbol, current_data, trader = args
        _, closing_prices = get_times_and_closing_p(symbol, current_data)
        last_closing_price = closing_prices[-1]

        short_mean = self._calc_mean((symbol, current_data)).value
        historic_mean = self.moving_averages[symbol].value
        logging.debug("moving average: %s", historic_mean)
        logging.debug("last closing price %s", last_closing_price)
        buy_condition = (
            historic_mean > last_closing_price and trader.positions_held[symbol] < 10
        )
        sell_condition = (
            historic_mean < last_closing_price and trader.positions_held[symbol] > 0
        )
        if buy_condition:
            logging.debug("buying a stock of %s", symbol)
            trader.place_order(
                symbol, time_in_force=TimeInForce.GTC, last_price=last_closing_price
            )
        elif sell_condition:
            logging.debug("selling a share of %s", symbol)
            trader.place_order(
                symbol,
                time_in_force=TimeInForce.GTC,
                side=OrderSide.SELL,
                last_price=last_closing_price,
                quantity=trader.positions_held[symbol],
            )
        return symbol, buy_condition, sell_condition

    def run(
        self,
        trader: LlamaTrader | MockLlamaTrader,
        current_data: CustomBarSet | BarSet,
    ):
        with ThreadPoolExecutor(max_workers=4) as xacuter:
            for symbol, buy, sell in xacuter.map(
                self.trade,
                ((key, current_data, trader) for key in current_data.data.keys()),
            ):
                logging.debug("%s was bought: %s sold: %s", symbol, buy, sell)

    @staticmethod
    def _calc_mean(args: tuple[str, BarSet | CustomBarSet]):
        """Calculate mean from input data for specific symbol"""
        symbol, data = args
        _, closing_prices = get_times_and_closing_p(symbol, data)
        np_closing = np.array(closing_prices, dtype=np.float64)
        moving_average = np.mean(np_closing)
        return Metric(symbol, "moving_average", moving_average)

    @classmethod
    def calculate_moving_averages(cls, data: BarSet | CustomBarSet):
        ma = {}
        with ProcessPoolExecutor(max_workers=4) as xacuter:
            for result in xacuter.map(
                cls._calc_mean,
                ((key, data) for key in data.data.keys()),
            ):
                ma[result.symbol] = result
        return ma


STRATEGIES: list[type[Strategy]] = [MovingAverageStrat]
