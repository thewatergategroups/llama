from .strats import get_predefined_strat_classes
from ..database import StratConditionMap, Strategies, Conditions
from ..settings import get_sync_sessionm
from trekkers.statements import upsert


def insert_strats():
    strats = get_predefined_strat_classes()
    sessionm = get_sync_sessionm()
    for strat in strats:
        upsert(
            sessionm,
            {"alias": strat.ALIAS, "name": strat.NAME, "active": strat.ACTIVE},
            Strategies,
        )
        upsert(
            sessionm,
            [
                {
                    "name": condition.name,
                    "side": condition.side,
                    "default_variables": condition.variables,
                }
                for condition in strat.DEFAULT_CONDITIONS
            ],
            Conditions,
        )
        upsert(
            sessionm,
            [
                {
                    "strategy_alias": strat.ALIAS,
                    "condition_name": condition.name,
                    "type": condition.type,
                    "active": condition.active,
                    "variables": condition.variables,
                }
                for condition in strat.DEFAULT_CONDITIONS
            ],
            StratConditionMap,
        )
