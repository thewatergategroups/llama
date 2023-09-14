from fastapi import Depends, HTTPException, BackgroundTasks
from fastapi.routing import APIRouter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..deps import get_history, get_backtester, get_async_session
from ...stocks import History, get_all_strats
from ...backtester import BackTester
from ...database.models import Backtests
from ...consts import Status

router = APIRouter(prefix="/backtest")


@router.post("/start")
async def run_backtest(
    symbols: list[str],
    background_task: BackgroundTasks,
    days_to_test_over: int = 30,
    history: History = Depends(get_history),
    backtester: BackTester = Depends(get_backtester),
    session: AsyncSession = Depends(get_async_session),
):
    if not symbols:
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
    backtest_id = backtester.insert_start_of_backtest(symbols)
    background_task.add_task(
        backtester.backtest_strats, backtest_id, history, symbols, days_to_test_over
    )
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


@router.get("/results")
async def get_backtest(session: AsyncSession = Depends(get_async_session)):
    results = (
        (await session.execute(select(Backtests).order_by(Backtests.timestamp.desc())))
        .scalars()
        .all()
    )
    return [result.as_dict() for result in results]


@router.get("/strategies")
async def get_strats():
    return {strat.NAME: strat.CONDITIONS for strat in get_all_strats()}
