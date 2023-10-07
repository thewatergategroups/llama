from fastapi.routing import APIRouter
from fastapi import HTTPException
from pydantic import BaseModel
from sqlalchemy import delete, exists, select, update
from sqlalchemy.orm import Session
from alpaca.trading.enums import OrderSide
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
    does_exists = await session.scalar(
        select(exists(Strategies)).where(Strategies.alias == strat.alias)
    )
    if does_exists:
        raise HTTPException(400, f"Strategy with alias {strat.alias} already exists")
    await session.execute(
        insert(Strategies).values(
            {"name": strat.name, "alias": strat.alias, "active": strat.active}
        )
    )
    await session.execute(
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
    return {"detail": "success"}


@router.delete("")
async def del_strat(
    alias: str,
    session: AsyncSession = Depends(get_async_session),
):
    await session.execute(
        delete(StratConditionMap).where(StratConditionMap.strategy_alias == alias)
    )
    await session.execute(delete(Strategies).where(Strategies.alias == alias))
    return {"detail": "success"}


class PatchStrategy(BaseModel):
    alias: str
    name: str | None = None
    active: bool | None = None


@router.patch("/update")
async def update_strategy(
    update_strat: PatchStrategy,
    session: Session = Depends(get_sync_session),
):
    strat = get_all_strats().get(update_strat.alias)
    if not strat:
        raise HTTPException(404, "strategy not found")
    strat.ACTIVE = update_strat.active or strat.ACTIVE
    strat.NAME = update_strat.name or strat.NAME

    strat.upsert(session)
    return {"detail": "success"}


class PatchStratCondition(BaseModel):
    strategy_alias: str
    condition_name: str
    active: bool | None
    variables: dict | None


@router.patch("/strategy/conditions/update")
async def update_strategy_condition(
    update_cond: PatchStratCondition,
    session: Session = Depends(get_sync_session),
):
    strat = get_all_strats().get(update_cond.strategy_alias)
    if not strat:
        raise HTTPException(404, "strategy not found")
    cond = None
    for condition in strat.DEFAULT_CONDITIONS:
        if condition.name == update_cond.condition_name:
            cond = condition
            break
    if not cond:
        raise HTTPException(404, "Condition not found on strategy")
    cond.active = update_cond.active if update_cond.active is not None else cond.active

    cond.update_variables(update_cond.variables) if update_cond.variables else None
    cond.upsert(update_cond.strategy_alias, session)
    return {"detail": "success"}


class PatchCondition(BaseModel):
    name: str
    side: OrderSide | None
    variables: dict | None


@router.patch("/conditions/update")
async def update_condition(
    update_cond: PatchCondition,
    session: Session = Depends(get_sync_session),
):
    values = {}
    if update_cond.side:
        values["side"] = update_cond.side.value
    if update_cond.variables:
        values["default_variables"] = update_cond.variables
    try:
        await session.execute(
            update(Conditions).values(values).where(Conditions.name == update_cond.name)
        )
    except Exception:
        raise HTTPException(404, "failed to update condition")

    return {"detail": "success"}
