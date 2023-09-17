import logging
from typing import Callable, Any
from pydantic import BaseModel
from enum import Enum
from alpaca.data.models import Bar
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from ....database import Conditions, StratConditionMap

from trekkers.statements import on_conflict_update
from sqlalchemy.dialects.postgresql import insert
from alpaca.trading import OrderSide
from ...trader import Trader
from ...models import CustomBarSet

LIVE_DATA = CustomBarSet()


class ConditionType(Enum):
    AND = "and"
    OR = "or"


class Condition(BaseModel):
    name: str
    func: Callable
    variables: dict
    active: bool = False
    side: OrderSide
    type: ConditionType

    def __call__(self, most_recent_bar: Bar, trader: Trader) -> bool:
        return self.func(most_recent_bar, trader, **self.variables)

    def get_variables(self):
        return self.variables

    def set_variables(self, key: str, value: Any):
        self.variables[key] = value

    def update_variables(self, variables: dict):
        for key, value in variables.items():
            if key in self.variables:
                self.variables[key] = value

    def dict(self, **kwargs):
        return {
            "name": self.name,
            "active": self.active,
            "variables": self.variables,
        }

    def get(self, strat_alias: str, session: Session):
        condition = session.scalar(
            select(StratConditionMap).where(
                StratConditionMap.condition_name == self.name,
                StratConditionMap.strategy_alias == strat_alias,
            )
        )
        if condition is None:
            raise KeyError("condition doesn't exist")
        self.variables = condition.variables
        self.active = condition.active

    def upsert(self, strat_alias: str, session: Session):
        values = {
            "condition_name": self.name,
            "strategy_alias": strat_alias,
            "type": self.type.value,
            "variables": self.variables,
            "active": self.active,
        }
        try:
            session.execute(
                insert(Conditions).values(
                    {
                        "name": self.name,
                        "side": self.side,
                        "default_variables": self.variables,
                    }
                )
            )
        except IntegrityError:
            ...
        session.execute(
            on_conflict_update(
                insert(StratConditionMap).values(values), StratConditionMap
            )
        )


def quantity_sell(most_recent_bar: Bar, trader: Trader, min_quantity: int):
    """sell condition based on quantity"""
    position = trader.get_position(most_recent_bar.symbol, force=True)
    qty_avail = int(position.qty_available)
    condition = qty_avail > min_quantity
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


def quantity_buy(most_recent_bar: Bar, trader: Trader, max_quantity: int):
    """buy condition based on quantity"""
    position = trader.get_position(most_recent_bar.symbol, force=True)
    qty_avail = int(position.qty_available)
    condition = qty_avail < max_quantity
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
    return [
        Condition(
            name="max_quantity_allowed",
            func=quantity_buy,
            variables={"max_quantity": 5},
            active=True,
            side=OrderSide.BUY,
            type=ConditionType.AND,
        ),
        Condition(
            name="take_profit",
            func=take_profit_buy,
            variables={"unrealized_plpc": 2},
            active=True,
            side=OrderSide.BUY,
            type=ConditionType.OR,
        ),
        Condition(
            name="min_quantity_allowed",
            func=quantity_sell,
            variables={"min_quantity": 0},
            active=True,
            side=OrderSide.SELL,
            type=ConditionType.AND,
        ),
        Condition(
            name="is_profitable",
            func=is_profitable_sell,
            variables={"unrealized_pl": 0},
            active=True,
            side=OrderSide.SELL,
            type=ConditionType.AND,
        ),
        Condition(
            name="stop_loss",
            func=stop_loss_sell,
            variables={"unrealized_plpc": -10},
            active=True,
            side=OrderSide.SELL,
            type=ConditionType.OR,
        ),
    ]
