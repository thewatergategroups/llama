from alpaca.data.models import Bar
from alpaca.trading import OrderSide

from ...stocks import Trader
from ..base import Condition, ConditionType, LIVE_DATA


def crossover_buy(most_recent_bar: Bar, trader: Trader):
    return most_recent_bar.vwap < most_recent_bar.close


def crossover_sell(most_recent_bar: Bar, trader: Trader):
    return most_recent_bar.vwap > most_recent_bar.close


def _slope(most_recent_bar: Bar):
    previous_vwap = 0
    if (data := LIVE_DATA.data.get(most_recent_bar.symbol)) is not None:
        previous_vwap = data[-1].vwap
    current_vwap = most_recent_bar.vwap
    vwap_slope = 0
    if previous_vwap > 0:
        vwap_slope = (current_vwap - previous_vwap) / previous_vwap
    return vwap_slope


def slope_buy(most_recent_bar: Bar, trader: Trader, vwap_slope_threshold: float):
    """VWAP Slope condition"""
    vwap_slope = _slope(most_recent_bar)
    return vwap_slope > vwap_slope_threshold  # slope


def reversion_buy(most_recent_bar: Bar, trader: Trader, deviation_threshold: float):
    """Reversion"""
    deviation_threshold = 0.001
    return most_recent_bar.close < most_recent_bar.vwap * (1 - deviation_threshold)


def reversion_sell(most_recent_bar: Bar, trader: Trader, deviation_threshold: float):
    """Reversion"""
    return most_recent_bar.close > most_recent_bar.vwap * (1 + deviation_threshold)


def tolerance_buy(most_recent_bar: Bar, trader: Trader):
    return most_recent_bar.close < (most_recent_bar.vwap + most_recent_bar.vwap * 0.2)


def tolerance_sell(most_recent_bar: Bar, trader: Trader):
    return most_recent_bar.close < (
        most_recent_bar.vwap - (most_recent_bar.vwap * 0.2 / 2)
    )


def get_vwap_conditions():
    return [
        Condition(
            name="positive_vwap_slope",
            func=slope_buy,
            variables={"vwap_slope_threshold": 0.005},
            active=True,
            side=OrderSide.BUY,
            type=ConditionType.AND,
        ),
        Condition(
            name="positive_vwap_crossover",
            func=crossover_buy,
            variables={},
            active=True,
            side=OrderSide.BUY,
            type=ConditionType.AND,
        ),
        Condition(
            name="negative_vwap_crossover",
            func=crossover_sell,
            variables={},
            active=True,
            side=OrderSide.SELL,
            type=ConditionType.AND,
        ),
    ]
