from sqlalchemy import select
from .strats import get_predefined_strat_classes
from .conditions import get_all_conditions
from ..database import StratConditionMap, Strategies, Conditions
from ..settings import get_sync_sessionm
from trekkers.statements import upsert


def insert_conditions():
    sessionm = get_sync_sessionm()
    upsert(
        sessionm,
        [
            {
                "name": condition.name,
                "side": condition.side,
                "default_variables": condition.variables,
            }
            for condition in get_all_conditions().values()
        ],
        Conditions,
    )


def insert_strats():
    strats = get_predefined_strat_classes()
    sessionm = get_sync_sessionm()
    for strat in strats:
        upsert(
            sessionm,
            {"alias": strat.ALIAS, "name": strat.NAME, "active": strat.ACTIVE},
            Strategies,
        )
        with sessionm.begin() as session:
            stored_strats = session.scalars(
                select(StratConditionMap).where(
                    StratConditionMap.strategy_alias == strat.ALIAS
                )
            )
            stored_cond = {cond.condition_name: cond for cond in stored_strats}
            to_insert = []
            for condition in strat.DEFAULT_CONDITIONS:
                if (cond := stored_cond.get(condition.name)) is not None:
                    condition.variables = cond.variables
                    condition.active = cond.active
                    condition.type = cond.type
                to_insert += [
                    {
                        "strategy_alias": strat.ALIAS,
                        "condition_name": condition.name,
                        "type": condition.type,
                        "active": condition.active,
                        "variables": condition.variables,
                    }
                ]
        upsert(sessionm, to_insert, StratConditionMap)
