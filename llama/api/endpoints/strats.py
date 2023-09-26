from fastapi.routing import APIRouter
from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import exists, select
from sqlalchemy.orm import Session
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends
from ..deps import get_async_session, get_sync_session
from ...strats import get_all_strats, StrategyDefinition
from ...database import Conditions, StratConditionMap, Strategies

router = APIRouter(prefix="/strategies")


@router.get("")
async def get_strats(
    alias: str | None = None,
) -> list[StrategyDefinition]:
    strats = get_all_strats().values()
    if alias:
        strats = [get_all_strats().get(alias)]
        if not strats[0]:
            raise HTTPException(404, "strategy not found")
    response = []
    for strat in strats:
        response.append(strat.dict())
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


@router.post("/create")
async def create_strat(
    strat: StrategyDefinition,
    session: AsyncSession = Depends(get_async_session),
):
    if await session.execute(
        select(exists(Strategies)).where(Strategies.alias == strat.alias)
    ):
        raise HTTPException(400, f"Strategy with alias {strat.alias} already exists")
    session.add(
        insert(Strategies).values(
            {"name": strat.name, "alias": strat.alias, "active": strat.active}
        )
    )
    session.add(
        insert(StratConditionMap).values(
            [
                {
                    "strategy_alias": strat.alias,
                    "condition_name": cond.name,
                    "type": cond.type,
                    "active": cond.active,
                    "variables": cond.variables,
                }
                for cond in strat.conditions
            ]
        )
    )
    session.commit()
    return {"detail": "success"}


class PatchStrategy(BaseModel):
    alias: str
    name: str | None = None
    active: bool | None = None


@router.patch("/update")
async def update_strategy(
    update: PatchStrategy,
    session: Session = Depends(get_sync_session),
):
    strat = get_all_strats().get(update.alias)
    if not strat:
        raise HTTPException(404, "strategy not found")
    strat.ACTIVE = update.active or strat.ACTIVE
    strat.NAME = update.name or strat.NAME

    strat.upsert(session)
    return {"detail": "success"}


class PatchCondition(BaseModel):
    strategy_alias: str
    condition_name: str
    active: bool | None
    variables: dict | None


@router.patch("/conditions/update")
async def update_strategy_condition(
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
