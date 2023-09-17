from .vwap import Vwap
from .base import Strategy, ConditionType
from pydantic import BaseModel


def get_all_strats() -> dict[str, type[Strategy]]:
    return {Vwap.ALIAS: Vwap, Strategy.ALIAS: Strategy}


class ConditionDefinition(BaseModel):
    name: str
    type: ConditionType
    active: bool
    variables: dict


class StrategyDefinition(BaseModel):
    strategy_alias: str
    conditions: list[ConditionDefinition]
