"""
Base Strategy models and Enums
"""

from enum import StrEnum
from typing import Any, Callable

from alpaca.trading import OrderSide
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from trekkers.statements import on_conflict_update

from ...database import Conditions, StratConditionMap
from ...stocks import CustomBarSet, Trader
from ...stocks.extendend_bars import ExtendedBar

LIVE_DATA = CustomBarSet()


class ConditionType(StrEnum):
    """Acceptable types of conditions"""

    AND = "and"
    OR = "or"


class Condition(BaseModel):
    """
    Definition of a condition
    """

    name: str
    func: Callable
    variables: dict
    active: bool = False
    side: OrderSide
    type: ConditionType

    def __call__(self, most_recent_bar: ExtendedBar, trader: Trader) -> bool:
        """What to do when you call a condition"""
        return self.func(most_recent_bar, trader, **self.variables)

    def get_variables(self):
        """Return condition variables"""
        return self.variables

    def set_variables(self, key: str, value: Any):
        """set condition variables"""
        self.variables[key] = value

    def update_variables(self, variables: dict):
        """update self variables based on input variables"""
        for key, value in variables.items():
            if key in self.variables:
                self.variables[key] = value

    def dict(self, **__):
        """Turn a condition into a dict"""
        return {
            "name": self.name,
            "type": self.type,
            "active": self.active,
            "variables": self.variables,
        }

    def get(self, strat_alias: str, session: Session):
        """Get self from database for a specific strategy"""
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
        self.type = condition.type

    def upsert(self, strat_alias: str, session: Session):
        """Insert or update self into the database"""
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
