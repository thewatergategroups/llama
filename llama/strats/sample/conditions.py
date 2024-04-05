"""
So Easy It's Ridiculous
"""

from alpaca.data.models import Bar
from alpaca.trading import OrderSide

from ...stocks import Trader
from ..base import Condition, ConditionType


def first_indicator(most_recent_bar: Bar, _: Trader):
    return True


def second_indicator(most_recent_bar: Bar, _: Trader) -> bool:
    return False


def get_second_indicator():
    """
    swing trading system and that we will trade on a daily chart
    we use simple moving averages to help us identify a new trend as early as possible.

    The Stochastic helps us determine if it`s still ok for us to enter a trade after
    a moving average crossover, and it also helps us avoid oversold and overbought areas.

    The RSI is an extra confirmation tool that helps us determine the strength of our trend.
    After figuring out our trade setup, we then determined our risk for each trade.

    (For this system, we are willing to risk 100 pips on each trade) <= TODO: implement


    Returns:
        _type_: _description_
    """
    return [
        Condition(
            name="first_indicator",
            func=first_indicator,
            variables={"param": 0},
            active=True,
            side=OrderSide.BUY,
            type=ConditionType.AND,
        ),
        Condition(
            name="second_indicator",
            func=second_indicator,
            variables={},
            active=True,
            side=OrderSide.BUY,
            type=ConditionType.AND,
        ),
    ]


# Assuming utility functions exist:
# calculate_sma_short, calculate_sma_long, calculate_stochastic, calculate_rsi


def sma_crossover_buy(most_recent_bar: Bar, _: Trader) -> bool:
    """Condition for SMA crossover buy signal."""
    # This assumes you have a way to calculate or retrieve the short and long SMA values
    short_sma = calculate_sma_short(most_recent_bar)
    long_sma = calculate_sma_long(most_recent_bar)
    return short_sma > long_sma


def stochastic_not_overbought(most_recent_bar: Bar, _: Trader):
    """Condition that Stochastic is not in overbought territory."""
    stochastic_value = calculate_stochastic(most_recent_bar)
    return stochastic_value < 80


def rsi_below_threshold(most_recent_bar: Bar, _: Trader):
    """Condition that RSI is below a certain threshold, suggesting potential upside."""
    rsi_value = calculate_rsi(most_recent_bar)
    return rsi_value < 50


def get_extended_conditions():
    """Get conditions integrating SMA, Stochastic, and RSI."""
    return [
        Condition(
            name="sma_crossover_buy_signal",
            func=sma_crossover_buy,
            variables={},
            active=True,
            side=OrderSide.BUY,
            type=ConditionType.AND,
        ),
        Condition(
            name="stochastic_not_overbought",
            func=stochastic_not_overbought,
            variables={},
            active=True,
            side=OrderSide.BUY,
            type=ConditionType.AND,
        ),
        Condition(
            name="rsi_below_50",
            func=rsi_below_threshold,
            variables={},
            active=True,
            side=OrderSide.BUY,
            type=ConditionType.AND,
        ),
        # Add more conditions as necessary for exit signals or sell side logic
    ]
