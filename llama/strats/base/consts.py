from enum import StrEnum
from typing import Any, Callable

from alpaca.data.models import Bar
from alpaca.trading import OrderSide
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from trekkers.statements import on_conflict_update

from ...database import Conditions, StratConditionMap
from ...stocks import CustomBarSet, Trader

LIVE_DATA = CustomBarSet()


class ConditionType(StrEnum):
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
            "type": self.type,
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
        self.type = condition.type

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
