"""
So Easy It's Ridiculous
"""

from typing import Optional
from alpaca.data.models import Bar
from alpaca.trading import OrderSide

from ...stocks import Trader
from ..base import Condition, ConditionType


# TODO: Move this to a separate appropriate module + test
class ExtedndedBar(Bar):
    garman_klass_vol: Optional[float]
    rsi: Optional[float]
    bb_low: Optional[float]
    bb_mid: Optional[float]
    bb_high: Optional[float]
    stochastic_osci: Optional[float]
    sma_short: Optional[float]
    sma_log: Optional[float]


def sma_crossover_buy(most_recent_bar: ExtedndedBar, _: Trader) -> bool:
    """Condition for SMA crossover buy signa."""
    short_sma = most_recent_bar["sma_short"]
    long_sma = most_recent_bar["sma_long"]
    return short_sma > long_sma


def stochastic_not_overbought(
    most_recent_bar: ExtedndedBar, _: Trader, threshold: int = 80
) -> bool:
    """Condition that Stochastic is not in overbought territory"""
    stochastic_value = most_recent_bar["stochastic_osci"]
    return stochastic_value < threshold


def rsi_below_threshold(
    most_recent_bar: ExtedndedBar, _: Trader, threshold: int = 50
) -> bool:
    """Condition that RSI is below a certain threshold, suggesting potential upside"""
    rsi_value = most_recent_bar["rsi"]
    return rsi_value < threshold


def get_seir_conditions():
    """
    Get conditions integrating SMA, Stochastic, and RSI

    swing trading system and that we will trade on a daily chart
    we use simple moving averages to help us identify a new trend as early as possible.

    The Stochastic helps us determine if it`s still ok for us to enter a trade after
    a moving average crossover, and it also helps us avoid oversold and overbought areas

    RSI is an extra confirmation tool that helps us determine the strength of our trend
    After figuring out our trade setup, we then determined our risk for each trade

    (For this system, we are willing to risk 100 pips on each trade) <= TODO: implement
    """
    return [
        Condition(
            name="signal_sma_crossover_buy_signal",
            func=sma_crossover_buy,
            variables={},
            active=True,
            side=OrderSide.BUY,
            type=ConditionType.AND,
        ),
        Condition(
            name="signal_stochastic_not_overbought",
            func=stochastic_not_overbought,
            variables={"threshold": 80},
            active=True,
            side=OrderSide.BUY,
            type=ConditionType.AND,
        ),
        Condition(
            name="signal_rsi_below_50",
            func=rsi_below_threshold,
            variables={"threshold": 50},
            active=True,
            side=OrderSide.BUY,
            type=ConditionType.AND,
        ),
    ]
