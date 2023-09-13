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
from sqlalchemy import select


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
    def __init__(self, history: History, data: BARSET_TYPE):
        self.history = history
        self.historic_data = data
        self.current_data = CustomBarSet()
        self.and_buy_conditions = [self._quantity]
        self.or_buy_conditions = [self._take_profit]
        self.and_sell_conditions = [self._quantity, self._is_profitable]
        self.or_sell_conditions = [self._stop_loss]

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
            history,
            history.get_stock_bars(
                symbols, time_frame=timeframe, start_time=start_time, end_time=end_time
            ),
        )

    def run(self, trader: Trader, most_recent_bar: Bar):
        """Standard strat run method to be overwritten"""
        action, qty = self.trade(trader, most_recent_bar)
        self.current_data.append(most_recent_bar)
        return action, qty

    def _quantity(
        self, symbol: str, most_recent_bar: Bar, trader: Trader, side: OrderSide
    ):
        """purchase condition based on quantity"""
        position = trader.get_position(symbol, force=True)
        qty = int(position.qty_available)
        logging.debug(
            "Quantity condition on %s where side is %s and quantity is %s",
            symbol,
            side.value,
            qty,
        )
        if side == OrderSide.BUY:
            condition = qty < 5
            logging.debug(
                "Quantity condition on %s side %s is %s", symbol, side.value, condition
            )
            return condition
        condition = qty > 0
        logging.info(
            "Quantity condition on %s side %s is %s", symbol, side.value, condition
        )
        return condition

    def _is_profitable(
        self, symbol: str, most_recent_bar: Bar, trader: Trader, side: OrderSide
    ):
        """purchase condition based on buy prices.. PURELY a sell condition"""
        if side == OrderSide.BUY:
            raise RuntimeError("Can't use this condition on the buy side..")

        position = trader.get_position(symbol, force=True)
        condition = float(position.unrealized_pl) > 0
        logging.info(
            "is profitable sell condition on %s where unrealised profit/loss is %s condition response is %s",
            symbol,
            position.unrealized_pl,
            condition,
        )
        return condition

    def _stop_loss(
        self, symbol: str, most_recent_bar: Bar, trader: Trader, side: OrderSide
    ):
        """purchase condition based on buy prices.. PURELY a sell condition"""
        if side == OrderSide.BUY:
            raise RuntimeError("Can't use this condition on the buy side..")

        position = trader.get_position(symbol, force=True)
        condition = float(position.unrealized_plpc) <= -10
        logging.info(
            "stop loss sell condition on %s where unrealised profit/loss percent is %s condition response is %s",
            symbol,
            position.unrealized_plpc,
            condition,
        )
        return condition

    def _take_profit(
        self, symbol: str, most_recent_bar: Bar, trader: Trader, side: OrderSide
    ):
        """purchase condition based on buy prices.. PURELY a sell condition"""
        if side == OrderSide.SELL:
            raise RuntimeError("Can't use this condition on the buy side..")

        position = trader.get_position(symbol, force=True)
        condition = float(position.unrealized_plpc) >= 2
        logging.info(
            "take profit condition on %s where unrealised profit/loss percent is %s condition response is %s",
            symbol,
            position.unrealized_plpc,
            condition,
        )
        return condition

    @staticmethod
    def _condition_check(
        symbol: str,
        most_recent_bar: Bar,
        trader: Trader,
        side: OrderSide,
        and_conditions: list,
        or_conditions: list,
    ):
        return any(
            [
                all(
                    [
                        condition(symbol, most_recent_bar, trader, side)
                        for condition in and_conditions
                    ]
                ),
                *[
                    condition(symbol, most_recent_bar, trader, side)
                    for condition in or_conditions
                ],
            ]
        )

    def trade(self, trader: Trader, most_recent_bar: Bar):
        """Making buying decisions based on the VWAP"""
        symbol = most_recent_bar.symbol
        position = trader.get_position(symbol, force=True)
        qty_avaliable = int(position.qty_available)

        if self._condition_check(
            symbol,
            most_recent_bar,
            trader,
            OrderSide.BUY,
            self.and_buy_conditions,
            self.or_buy_conditions,
        ):
            logging.info("buying a stock of %s with strat %s", symbol, self.__class__)
            buy = -qty_avaliable if qty_avaliable < 0 else 1
            trader.place_order(symbol, time_in_force=TimeInForce.GTC, quantity=buy)
            return OrderSide.BUY, buy
        elif self._condition_check(
            symbol,
            most_recent_bar,
            trader,
            OrderSide.SELL,
            self.and_sell_conditions,
            self.or_sell_conditions,
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

    def __init__(self, history: History, data: BARSET_TYPE):
        super().__init__(history, data)
        self.and_buy_conditions += [self._slope, self._crossover]
        self.and_sell_conditions += [self._crossover]

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
