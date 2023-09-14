from .base import Strategy, Condition, ConditionType, get_base_conditions
from .vwap import Vwap


STRATEGIES: list[type[Strategy]] = [Vwap]
