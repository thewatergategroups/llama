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
