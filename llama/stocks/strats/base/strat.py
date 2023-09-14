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
from alpaca.data.models import Bar

from alpaca.trading import OrderSide, TimeInForce
import logging
from ...history import History
from ...trader import Trader
from datetime import datetime, timedelta
from ....consts import BARSET_TYPE
from datetime import datetime, timedelta
from alpaca.data.timeframe import TimeFrame
from .conditions import get_base_conditions, ConditionType, LIVE_DATA


class Strategy:
    CONDITIONS = get_base_conditions()
    NAME = "Base"
    ALIAS = "BS"

    def __init__(self, history: History, data: BARSET_TYPE):
        self.history = history
        self.historic_data = data

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
        LIVE_DATA.append(most_recent_bar)
        return action, qty

    def _condition_check(
        self,
        most_recent_bar: Bar,
        trader: Trader,
        side: OrderSide,
    ):
        return any(
            [
                all(
                    [
                        condition(most_recent_bar, trader)
                        for condition in self.CONDITIONS[side][ConditionType.AND]
                    ]
                ),
                *[
                    condition(most_recent_bar, trader)
                    for condition in self.CONDITIONS[side][ConditionType.OR]
                ],
            ]
        )

    def trade(self, trader: Trader, most_recent_bar: Bar):
        """Making buying decisions based on the VWAP"""
        position = trader.get_position(most_recent_bar.symbol, force=True)
        qty_avaliable = int(position.qty_available)

        if self._condition_check(most_recent_bar, trader, OrderSide.BUY):
            logging.info(
                "buying a stock of %s with strat %s",
                most_recent_bar.symbol,
                self.__class__,
            )
            buy = -qty_avaliable if qty_avaliable < 0 else 1
            trader.place_order(
                most_recent_bar.symbol, time_in_force=TimeInForce.GTC, quantity=buy
            )
            return OrderSide.BUY, buy
        elif self._condition_check(most_recent_bar, trader, OrderSide.SELL):
            logging.info(
                "selling a share of %s with strat %s",
                most_recent_bar.symbol,
                self.__class__,
            )
            sell = qty_avaliable if qty_avaliable > 0 else 1
            trader.place_order(
                most_recent_bar.symbol,
                time_in_force=TimeInForce.GTC,
                side=OrderSide.SELL,
                quantity=sell,
            )
            return OrderSide.SELL, sell
        return None, None
