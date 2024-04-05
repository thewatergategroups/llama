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
