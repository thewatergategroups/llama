# ⢀⣠⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀⠀⠀⣠⣤⣶⣶
# ⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀⠀⢰⣿⣿⣿⣿
# ⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣧⣀⣀⣾⣿⣿⣿⣿
# ⣿⣿⣿⣿⣿⡏⠉⠛⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⣿
# ⣿⣿⣿⣿⣿⣿⠀⠀⠀⠈⠛⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⠛⠉⠁⠀⣿
# ⣿⣿⣿⣿⣿⣿⣧⡀⠀⠀⠀⠀⠙⠿⠿⠿⠻⠿⠿⠟⠿⠛⠉⠀⠀⠀⠀⠀⣸⣿
# ⣿⣿⣿⣿⣿⣿⣿⣷⣄⠀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⣿⣿
# ⣿⣿⣿⣿⣿⣿⣿⣿⣿⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⣴⣿⣿⣿⣿
# ⣿⣿⣿⣿⣿⣿⣿⣿⡟⠀⠀⢰⣹⡆⠀⠀⠀⠀⠀⠀⣭⣷⠀⠀⠀⠸⣿⣿⣿⣿
# ⣿⣿⣿⣿⣿⣿⣿⣿⠃⠀⠀⠈⠉⠀⠀⠤⠄⠀⠀⠀⠉⠁⠀⠀⠀⠀⢿⣿⣿⣿
# ⣿⣿⣿⣿⣿⣿⣿⣿⢾⣿⣷⠀⠀⠀⠀⡠⠤⢄⠀⠀⠀⠠⣿⣿⣷⠀⢸⣿⣿⣿
# ⣿⣿⣿⣿⣿⣿⣿⣿⡀⠉⠀⠀⠀⠀⠀⢄⠀⢀⠀⠀⠀⠀⠉⠉⠁⠀⠀⣿⣿⣿
# ⣿⣿⣿⣿⣿⣿⣿⣿⣧⠀⠀⠀⠀⠀⠀⠀⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⣿⣿
# ⣿⣿⣿⣿⣿⣿⣿⣿⣿⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿
import logging
from alpaca.data.models import Bar

from .models import CustomBarSet
from .tools import get_times_and_closing_p
import numpy as np
from alpaca.trading.enums import OrderSide, TimeInForce
import logging
from .history import LlamaHistory
from datetime import datetime, timedelta
from .tools import get_times_and_closing_p
from ..tools import custom_json_encoder
from ..consts import BARSET_TYPE, TRADER_TYPE
from .models import Metric
from datetime import datetime, timedelta
from alpaca.data.timeframe import TimeFrame
import numpy as np
import logging
from concurrent.futures import ProcessPoolExecutor
import os
import json


class Strategy:
    def __init__(self, data: BARSET_TYPE):
        self.historic_data = data
        self.current_data = CustomBarSet()

    @classmethod
    def create(
        cls,
        history: LlamaHistory,
        symbols: list[str],
        start_time: datetime = datetime.utcnow() - timedelta(days=60),
        end_time: datetime = datetime.utcnow() - timedelta(minutes=15),
        timeframe: TimeFrame = TimeFrame.Day,
    ):
        return cls(
            history.get_stock_bars(
                symbols, time_frame=timeframe, start_time=start_time, end_time=end_time
            )
        )

    def run(
        self,
        trader: TRADER_TYPE,
        most_recent_bar: Bar,
    ):
        """Standard strat run method to be overwritten"""
        self.trade(trader, most_recent_bar)
        self.current_data.append(most_recent_bar)

    def trade(self, trader: TRADER_TYPE, most_recent_bar: Bar):
        logging.info("trading %s", most_recent_bar.symbol)

    @classmethod
    def store(cls, data_type: str, data: dict):
        to_store = {data_type: data, "collected_at": datetime.utcnow()}
        storage_location = os.path.join(
            os.getcwd(), f"data/{cls.__name__}_{data_type}.json"
        )
        with open(storage_location, "w") as f:
            f.write(json.dumps(to_store, default=custom_json_encoder))

    def get_last_x_bars_today(
        self, symbol: str, number_of_bars: int | None = None, ignore_x_bars: int = 0
    ) -> list[Bar]:
        last_x = []
        bars = self.current_data.data.get(symbol)
        if not bars:
            return last_x
        num_bars = 0
        initial_day = bars[-1].timestamp.day
        for bar in reversed(bars):
            num_bars += 1
            if ignore_x_bars >= num_bars:
                continue
            if bar.timestamp.day != initial_day:
                break
            if isinstance(number_of_bars, int) and len(last_x) >= number_of_bars:
                break
            last_x.insert(0, bar)

        return last_x


class MovingAverage(Strategy):
    def __init__(self, data: BARSET_TYPE):
        super().__init__(data)
        self.moving_averages: dict[str, Metric] = {}

    @classmethod
    def create(
        cls,
        history: LlamaHistory,
        symbols: list[str],
        start_time: datetime = datetime.utcnow() - timedelta(days=60),
        end_time: datetime = datetime.utcnow() - timedelta(minutes=15),
        timeframe: TimeFrame = TimeFrame.Day,
    ):
        obj: "MovingAverage" = super().create(
            history, symbols, start_time, end_time, timeframe
        )
        obj.moving_averages = cls.calculate_moving_averages(obj.historic_data)
        return obj

    def trade(self, trader: TRADER_TYPE, most_recent_bar: Bar):
        symbol = most_recent_bar.symbol
        last_closing_price = most_recent_bar.close
        if (current_bars := self.current_data.data.get(symbol)) is not None:
            last_closing_price = current_bars[-1].close
        short_mean = self._calc_mean(
            (symbol, self.get_last_x_bars_today(symbol, 10))
        ).value
        historic_mean = self.moving_averages[symbol].value
        logging.debug("moving average: %s", historic_mean)
        logging.debug("last closing price %s", last_closing_price)
        buy_condition = historic_mean > last_closing_price
        sell_condition = historic_mean < last_closing_price
        if buy_condition:
            logging.info("buying a stock of %s with strat %s", symbol, self.__class__)
            trader.place_order(symbol, time_in_force=TimeInForce.GTC)
        elif sell_condition:
            logging.info("selling a share of %s with strat %s", symbol, self.__class__)
            trader.place_order(
                symbol,
                time_in_force=TimeInForce.GTC,
                side=OrderSide.SELL,
                quantity=1,
            )
        return symbol, buy_condition, sell_condition

    @staticmethod
    def _calc_mean(args: tuple[str, list[Bar]]):
        """Calculate mean from input data for specific symbol"""
        symbol, data = args
        _, closing_prices = get_times_and_closing_p(data)
        np_closing = np.array(closing_prices, dtype=np.float64)
        moving_average = np.mean(np_closing)
        return Metric(symbol, "moving_average", moving_average)

    @classmethod
    def calculate_moving_averages(cls, data: BARSET_TYPE):
        ma = {}
        with ProcessPoolExecutor(max_workers=4) as xacuter:
            for result in xacuter.map(
                cls._calc_mean,
                ((key, bars) for key, bars in data.data.items()),
            ):
                ma[result.symbol] = result
        return ma


class Vwap(Strategy):
    def trade(self, trader: TRADER_TYPE, most_recent_bar: Bar):
        symbol = most_recent_bar.symbol
        # vwap slope
        previous_vwap = 0
        if (data := self.current_data.data.get(symbol)) is not None:
            previous_vwap = data[-1].vwap
        current_vwap = most_recent_bar.vwap
        vwap_slope = 0
        if previous_vwap > 0:
            vwap_slope = (current_vwap - previous_vwap) / previous_vwap
        vwap_slope_threshold = 0.02
        # VWAP Reversion
        deviation_threshold = 0.001
        # vwap resistance
        # Define the tolerance level around the VWAP (e.g., ±2%)
        vwap_tolerance = current_vwap * 0.2

        buy_conditions: list = [
            current_vwap < most_recent_bar.close,  # vwap crossover
            # most_recent_bar.close
            # < current_vwap * (1 - deviation_threshold),  # vwap reversion
            # (most_recent_bar.close > current_vwap)
            # and (most_recent_bar.close < (current_vwap + vwap_tolerance)),  # resistance
            vwap_slope > vwap_slope_threshold,  # slope
        ]

        sell_conditions: list = [
            current_vwap > most_recent_bar.close,  # crossover
            # most_recent_bar.close
            # > current_vwap * (1 + deviation_threshold),  # reversion
            # most_recent_bar.close < (current_vwap - vwap_tolerance / 2),  # resistance
            # vwap_slope < -vwap_slope_threshold,  # slope
        ]

        if all(buy_conditions):
            logging.info("buying a stock of %s with strat %s", symbol, self.__class__)
            trader.place_order(
                symbol,
                time_in_force=TimeInForce.GTC,
            )
        elif all(sell_conditions):
            logging.info("selling a share of %s with strat %s", symbol, self.__class__)
            trader.place_order(
                symbol,
                time_in_force=TimeInForce.GTC,
                side=OrderSide.SELL,
                quantity=1,
            )
        return symbol, buy_conditions, sell_conditions

    @staticmethod
    def vwap(data: list[Bar]):
        """
        Calculate the Volume Weighted Average Price (VWAP) for a given set of prices and volumes.
        """
        cumulative_price_volume = 0
        total_volume = 1

        for item in data:
            cumulative_price_volume += item.close * item.volume
            total_volume += item.volume

        vwap = cumulative_price_volume / total_volume
        return vwap


STRATEGIES: list[type[Strategy]] = [Vwap, MovingAverage]
