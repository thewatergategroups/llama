from fastapi import Depends, HTTPException, BackgroundTasks
from fastapi.routing import APIRouter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..deps import get_history, get_backtester, get_async_session
from ...stocks import History
from ...backtester import BackTester, BacktestDefinition
from ...database.models import Backtests, BacktestStats
from ...consts import Status
from .strats import get_strats
from ..validator import validate_jwt, has_admin_scope

router = APIRouter(
    prefix="/backtest",
    tags=["Backtesting"],
    dependencies=[Depends(validate_jwt), Depends(has_admin_scope())],
)


@router.post("/start")
async def run_backtest(
    data: BacktestDefinition,
    background_task: BackgroundTasks,
    history: History = Depends(get_history),
    backtester: BackTester = Depends(get_backtester),
    session: AsyncSession = Depends(get_async_session),
):
    if not data.symbols:
        raise HTTPException(400, {"details": "You can't backtest with no symbols"})
    running = (
        (
            await session.execute(
                select(Backtests.id).where(Backtests.status == Status.IN_PROGRESS)
            )
        )
        .scalars()
        .all()
    )
    if running:
        raise HTTPException(429, "backtest already running")
    strats = data.strategy_definitions or []
    if data.strategy_aliases is not None:
        strats += [await get_strats(strat) for strat in data.strategy_aliases]
    backtest_id = backtester.insert_start_of_backtest(data.symbols, strats)

    background_task.add_task(backtester.backtest_strats, backtest_id, history, data)
    return {"id": backtest_id}


@router.get("/result")
async def get_backtest(
    backtest_id: int, session: AsyncSession = Depends(get_async_session)
):
    return (
        (await session.execute(select(Backtests).where(Backtests.id == backtest_id)))
        .scalar()
        .as_dict()
    )


@router.get("/result/stats")
async def get_backtest(
    backtest_id: int, session: AsyncSession = Depends(get_async_session)
):
    response = (
        await session.execute(
            select(BacktestStats)
            .where(BacktestStats.backtest_id == backtest_id)
            .order_by(BacktestStats.timestamp.asc())
        )
    ).scalars()
    return [resp.as_dict() for resp in response]


@router.get("/results")
async def get_backtest(session: AsyncSession = Depends(get_async_session)):
    results = (
        (await session.execute(select(Backtests).order_by(Backtests.timestamp.desc())))
        .scalars()
        .all()
    )
    return [result.as_dict() for result in results]
