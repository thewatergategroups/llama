"""
Functions to dynamically build Strategy classes based off of db rows
"""

import copy

from sqlalchemy import select

from ..database import StratConditionMap, Strategies
from ..settings import get_sync_sessionm
from .base import Condition, Strategy
from .conditions import get_all_conditions
from .vwap import Vwap


def get_strategy_class(
    name: str, alias: str, active: bool, conditions: list[Condition]
):
    """Dynamically generates Strategy classes based on database rows"""

    class CustomStrat(Strategy):
        """CustomStrategy class"""

        DEFAULT_CONDITIONS = conditions
        NAME = name
        ALIAS = alias
        ACTIVE = active

    return CustomStrat


def get_predefined_strat_classes() -> list[type[Strategy]]:
    """Where you add Code defined strategies"""
    return [Vwap, Strategy]


def get_all_strats() -> dict[str, type[Strategy]]:
    """A dictionary of strategy alias to the strategy class"""
    all_conditions = get_all_conditions()
    all_strats = {}
    with get_sync_sessionm().begin() as session:
        strats = session.scalars(select(Strategies))
        for strat in strats:
            strat_cond_map = session.scalars(
                select(StratConditionMap).where(
                    StratConditionMap.strategy_alias == strat.alias
                )
            )
            conditions = []
            for str_cond in strat_cond_map:
                condition = copy.deepcopy(all_conditions[str_cond.condition_name])
                condition.active = str_cond.active
                condition.variables = str_cond.variables
                condition.type = str_cond.type
                conditions.append(condition)
            all_strats[strat.alias] = get_strategy_class(
                strat.name, strat.alias, strat.active, conditions
            )

    return all_strats
