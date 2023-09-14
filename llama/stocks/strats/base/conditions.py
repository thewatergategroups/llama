import logging
from typing import Callable, Any
from pydantic import BaseModel
from enum import Enum
from alpaca.data.models import Bar

from alpaca.trading import OrderSide
from ...trader import Trader
from ...models import CustomBarSet

LIVE_DATA = CustomBarSet()


class ConditionType(Enum):
    AND = "and"
    OR = "or"


class Condition(BaseModel):
    func: Callable
    variables: dict

    def __call__(self, most_recent_bar: Bar, trader: Trader) -> bool:
        return self.func(most_recent_bar, trader, **self.variables)

    def get_variables(self):
        return self.variables

    def set_variables(self, key: str, value: Any):
        self.variables[key] = value

    def dict(self, **kwargs):
        return {"func": self.func.__name__, "variables": self.variables}


def quantity_sell(most_recent_bar: Bar, trader: Trader, qty: int):
    """sell condition based on quantity"""
    position = trader.get_position(most_recent_bar.symbol, force=True)
    qty_avail = int(position.qty_available)
    condition = qty_avail > qty
    return condition


def is_profitable_sell(most_recent_bar: Bar, trader: Trader, unrealized_pl: float):
    """purchase condition based on buy prices.. PURELY a sell condition"""

    position = trader.get_position(most_recent_bar.symbol, force=True)
    condition = float(position.unrealized_pl) > unrealized_pl
    logging.info(
        "is profitable sell condition on %s where unrealised profit/loss is %s condition response is %s",
        most_recent_bar.symbol,
        position.unrealized_pl,
        condition,
    )
    return condition


def stop_loss_sell(most_recent_bar: Bar, trader: Trader, unrealized_plpc: float):
    """purchase condition based on buy prices.. PURELY a sell condition"""

    position = trader.get_position(most_recent_bar.symbol, force=True)
    condition = float(position.unrealized_plpc) <= unrealized_plpc
    logging.info(
        "stop loss sell condition on %s where unrealised profit/loss percent is %s condition response is %s",
        most_recent_bar.symbol,
        position.unrealized_plpc,
        condition,
    )
    return condition


def quantity_buy(most_recent_bar: Bar, trader: Trader, qty: int):
    """buy condition based on quantity"""
    position = trader.get_position(most_recent_bar.symbol, force=True)
    qty_avail = int(position.qty_available)
    condition = qty_avail < qty
    return condition


def take_profit_buy(
    most_recent_bar: Bar,
    trader: Trader,
    unrealized_plpc: float,
):
    """purchase condition based on buy prices.. PURELY a sell condition"""

    position = trader.get_position(most_recent_bar.symbol, force=True)
    condition = float(position.unrealized_plpc) >= unrealized_plpc
    logging.info(
        "take profit condition on %s where unrealised profit/loss percent is %s condition response is %s",
        most_recent_bar.symbol,
        position.unrealized_plpc,
        condition,
    )
    return condition


def get_base_conditions():
    return {
        OrderSide.BUY: {
            ConditionType.AND: [
                Condition(func=quantity_buy, variables={"qty": 5}),
            ],
            ConditionType.OR: [
                Condition(func=take_profit_buy, variables={"unrealized_plpc": 2}),
            ],
        },
        OrderSide.SELL: {
            ConditionType.AND: [
                Condition(func=quantity_sell, variables={"qty": 0}),
                Condition(func=is_profitable_sell, variables={"unrealized_pl": 0}),
            ],
            ConditionType.OR: [
                Condition(func=stop_loss_sell, variables={"unrealized_plpc": -10}),
            ],
        },
    }
