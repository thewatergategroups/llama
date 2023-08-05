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
        timeframe: TimeFrame = TimeFrame.Day,
        days: int = 50,
        force: bool = False,
    ):
        data_type = "data"
        historic_info = cls.get(data_type, force)
        if historic_info:
            return cls(data)

        data = history.get_stock_bars(
            symbols,
            time_frame=timeframe,
            start_time=(datetime.utcnow() - timedelta(days=days)),
        )
        cls.store(data_type, data)
        return cls(data)

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
    def storage_location(cls, data_type: str):
        return os.path.join(os.getcwd(), f"data/{cls.__name__}_{data_type}.json")

    @classmethod
    def store(cls, data_type: str, data: dict):
        to_store = {data_type: data, "collected_at": datetime.utcnow()}
        with open(cls.storage_location(data_type), "w") as f:
            f.write(json.dumps(to_store, default=custom_json_encoder))

    @classmethod
    def get(cls, data_type: str, force: bool, max_age_of_data_days: int = 1):
        try:
            with open(cls.storage_location(data_type), "r") as f:
                data = json.loads(f.read())
                if (
                    datetime.fromisoformat(data["collected_at"])
                    < datetime.utcnow() - timedelta(days=max_age_of_data_days)
                ) or force:
                    return None
            return data
        except Exception as exc:
            logging.error(str(exc))  # want a shorter version of the exception
            return None

    def get_last_x_bars_today(
        self, symbol: str, number_of_bars: int | None = None
    ) -> list[Bar]:
        last_x = []
        bars = self.current_data.data.get(symbol)
        if not bars:
            return last_x

        initial_day = bars[-1].timestamp.day
        for bar in reversed(bars):
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
        timeframe: TimeFrame = TimeFrame.Day,
        days: int = 50,
        force: bool = False,
    ):
        obj = super().create(history, symbols, timeframe, days, force)
        moving_averages_json = cls.get("moving_averages", force)
        if moving_averages_json:
            obj.moving_averages = {
                name: Metric(**value) for name, value in moving_averages_json.items()
            }
        else:
            obj.moving_averages = cls.calculate_moving_averages(obj.historic_data)
        cls.store("moving_averages", obj.moving_averages)
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
        last_closing_price = most_recent_bar.close
        if (current_bars := self.current_data.data.get(symbol)) is not None:
            last_closing_price = current_bars[-1].close
        vwap = self.vwap(self.get_last_x_bars_today(symbol))
        logging.debug("vwap: %s", vwap)
        logging.debug("last closing price %s", last_closing_price)
        buy_condition = vwap > last_closing_price and trader.positions_held[symbol] < 10
        sell_condition = vwap < last_closing_price and trader.positions_held[symbol] > 0
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