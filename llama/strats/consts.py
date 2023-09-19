from pydantic import BaseModel
from .base.consts import ConditionType


class ConditionDefinition(BaseModel):
    name: str
    type: ConditionType
    active: bool
    variables: dict


class StrategyDefinition(BaseModel):
    strategy_alias: str
    conditions: list[ConditionDefinition]
