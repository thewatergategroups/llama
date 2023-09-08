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

from llama.consts import BARSET_TYPE


from .models import CustomBarSet
from alpaca.trading import OrderSide, TimeInForce
import logging
from .history import History
from .trader import Trader
from datetime import datetime, timedelta
from ..consts import BARSET_TYPE
from datetime import datetime, timedelta
from alpaca.data.timeframe import TimeFrame
import logging


class Strategy:
    def __init__(self, data: BARSET_TYPE):
        self.historic_data = data
        self.current_data = CustomBarSet()
        self.buy_conditions = [self._quantity]
        self.sell_conditions = [self._quantity]

    @classmethod
    def create(
        cls,
        history: History,
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

    def _quantity(
        self, symbol: str, most_recent_bar: Bar, trader: Trader, side: OrderSide
    ):
        """purchase condition based on quantity"""
        position = trader.get_position(symbol)
        qty = int(position.qty_available)
        if side == OrderSide.BUY:
            return qty < 20
        return qty > 0

    def run(self, trader: Trader, most_recent_bar: Bar):
        """Standard strat run method to be overwritten"""
        action, qty = self.trade(trader, most_recent_bar)
        self.current_data.append(most_recent_bar)
        return action, qty

    def trade(self, trader: Trader, most_recent_bar: Bar):
        """Making buying decisions based on the VWAP"""
        symbol = most_recent_bar.symbol
        position = trader.get_position(symbol)
        qty_avaliable = int(position.qty_available)

        if all(
            [
                condition(symbol, most_recent_bar, trader, OrderSide.BUY)
                for condition in self.buy_conditions
            ]
        ):
            logging.info("buying a stock of %s with strat %s", symbol, self.__class__)
            buy = -qty_avaliable if qty_avaliable < 0 else 1
            trader.place_order(symbol, time_in_force=TimeInForce.GTC, quantity=buy)
            return OrderSide.BUY, buy
        elif all(
            [
                condition(symbol, most_recent_bar, trader, OrderSide.SELL)
                for condition in self.sell_conditions
            ]
        ):
            logging.info("selling a share of %s with strat %s", symbol, self.__class__)
            sell = qty_avaliable if qty_avaliable > 0 else 1
            trader.place_order(
                symbol,
                time_in_force=TimeInForce.GTC,
                side=OrderSide.SELL,
                quantity=sell,
            )
            return OrderSide.SELL, sell
        return None, None


class Vwap(Strategy):
    """Stratedgy based on Volume Weighted Average Price"""

    def __init__(self, data: BARSET_TYPE):
        super().__init__(data)
        self.buy_conditions += [self._slope, self._crossover]
        self.sell_conditions += [self._crossover]

    def _slope(
        self, symbol: str, most_recent_bar: Bar, trader: Trader, side: OrderSide
    ):
        """VWAP Slope condition"""
        previous_vwap = 0
        if (data := self.current_data.data.get(symbol)) is not None:
            previous_vwap = data[-1].vwap
        current_vwap = most_recent_bar.vwap
        vwap_slope = 0
        if previous_vwap > 0:
            vwap_slope = (current_vwap - previous_vwap) / previous_vwap
        vwap_slope_threshold = 0.001
        if side == OrderSide.BUY:
            return vwap_slope > vwap_slope_threshold  # slope
        return vwap_slope < -vwap_slope_threshold

    def _crossover(
        self, symbol: str, most_recent_bar: Bar, trader: Trader, side: OrderSide
    ):
        """Crossover"""
        if side == OrderSide.BUY:
            return most_recent_bar.vwap < most_recent_bar.close
        return most_recent_bar.vwap > most_recent_bar.close

    def _reversion(
        self, symbol: str, most_recent_bar: Bar, trader: Trader, side: OrderSide
    ):
        """Reversion"""
        deviation_threshold = 0.001
        if side == OrderSide.BUY:
            return most_recent_bar.close < most_recent_bar.vwap * (
                1 - deviation_threshold
            )  # vwap reversion
        return most_recent_bar.close > most_recent_bar.vwap * (1 + deviation_threshold)

    def _tolerance(
        self, symbol: str, most_recent_bar: Bar, trader: Trader, side: OrderSide
    ):
        if side == OrderSide.BUY:
            return most_recent_bar.close < (
                most_recent_bar.vwap + most_recent_bar.vwap * 0.2
            )
        return most_recent_bar.close < (
            most_recent_bar.vwap - (most_recent_bar.vwap * 0.2 / 2)
        )


STRATEGIES: list[type[Strategy]] = [Vwap]
