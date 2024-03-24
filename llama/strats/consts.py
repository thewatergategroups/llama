"""
Strategy specific enums and models
"""

from pydantic import BaseModel

from .base.consts import ConditionType


class ConditionDefinition(BaseModel):
    """
    Definition of a condition in a model
    to be converted from a json input
    """

    name: str
    type: ConditionType
    active: bool
    variables: dict


class StrategyDefinition(BaseModel):
    """
    Definition of a strategy as a model or as a condition would be
    """

    alias: str
    name: str
    active: bool
    conditions: list[ConditionDefinition]
