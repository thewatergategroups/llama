from fastapi.routing import APIRouter
from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from ..deps import get_async_session, get_sync_session
from ...strats import get_all_strats
from ...database import Conditions, StratConditionMap

router = APIRouter(prefix="/strategies")


@router.get("")
async def get_strats(
    alias: str | None = None,
    session: AsyncSession = Depends(get_async_session),
):
    strats = get_all_strats().values()
    if alias:
        strats = [get_all_strats().get(alias)]
        if not strats[0]:
            raise HTTPException(404, "strategy not found")
    response = []
    for strat in strats:
        conditions = await session.scalars(
            select(StratConditionMap).where(
                StratConditionMap.strategy_alias == strat.ALIAS
            )
        )
        response.append(
            {
                "alias": strat.ALIAS,
                "name": strat.NAME,
                "active": strat.ACTIVE,
                "conditions": [
                    condition.as_dict(
                        column_name_aliases={"condition_name": "name"},
                        included_keys=StratConditionMap.get_all_keys(
                            ["strategy_alias"]
                        ),
                    )
                    for condition in conditions
                ],
            }
        )
    return response


@router.get("/conditions")
async def get_conds(
    name: str | None = None,
    session: AsyncSession = Depends(get_async_session),
):
    stmt = select(Conditions)
    if name:
        stmt = stmt.where(Conditions.name == name)
    conditions = await session.scalars(stmt)
    return [condition.as_dict() for condition in conditions]


class PatchStrategy(BaseModel):
    alias: str
    active: bool


@router.patch("/update")
async def update_strategy(
    update: PatchStrategy,
    session: Session = Depends(get_sync_session),
):
    strat = get_all_strats().get(update.alias)
    if not strat:
        raise HTTPException(404, "strategy not found")
    strat.ACTIVE = update.active
    strat.upsert(session)
    return {"detail": "success"}


class PatchCondition(BaseModel):
    strategy_alias: str
    condition_name: str
    active: bool | None
    variables: dict | None


@router.patch("/conditions/update")
async def update_condition(
    update: PatchCondition,
    session: Session = Depends(get_sync_session),
):
    strat = get_all_strats().get(update.strategy_alias)
    if not strat:
        raise HTTPException(404, "strategy not found")
    cond = None
    for condition in strat.DEFAULT_CONDITIONS:
        if condition.name == update.condition_name:
            cond = condition
            break
    if not cond:
        raise HTTPException(404, "Condition doesn't exist")
    cond.active = update.active if update.active is not None else cond.active

    cond.update_variables(update.variables) if update.variables else None
    cond.upsert(update.strategy_alias, session)
    return {"detail": "success"}
