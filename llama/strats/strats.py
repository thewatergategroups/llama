from sqlalchemy import select
from .base import Strategy
from ..settings import get_sync_sessionm
from ..database import Strategies, StratConditionMap
from .base import Condition
from .vwap import Vwap
from .conditions import get_all_conditions


def get_strategy_class(
    name: str, alias: str, active: bool, conditions: list[Condition]
):
    class CustomStrat(Strategy):
        DEFAULT_CONDITIONS = conditions
        NAME = name
        ALIAS = alias
        ACTIVE = active

    return CustomStrat


def get_predefined_strat_classes() -> list[type[Strategy]]:
    return [Vwap, Strategy]


def get_all_strats() -> dict[str, type[Strategy]]:
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
            conditions = [
                all_conditions[str_cond.condition_name] for str_cond in strat_cond_map
            ]
            all_strats[strat.alias] = get_strategy_class(
                strat.name, strat.alias, strat.active, conditions
            )

    return all_strats
