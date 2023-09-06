from fastapi import Depends, HTTPException, BackgroundTasks
from fastapi.routing import APIRouter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from ..deps import get_history, get_backtester, get_async_session
from ...stocks import History, BackTester
from ...database.models import Backtests

router = APIRouter(prefix="/backtest")


@router.post("/start")
async def run_backtest(
    symbols: list[str],
    background_task: BackgroundTasks,
    days_to_test_over: int = 30,
    history: History = Depends(get_history),
    backtester: BackTester = Depends(get_backtester),
):
    if not symbols:
        raise HTTPException(400, {"details": "You can't backtest with no symbols"})
    background_task.add_task(
        backtester.backtest_strats, history, symbols, days_to_test_over
    )
    return {"details": "Backtest started"}


@router.get("/result")
async def get_backtest(
    backtest_id: int, session: AsyncSession = Depends(get_async_session)
):
    return await session.execute(select(Backtests).where(Backtests.id == backtest_id))


@router.get("/results")
async def get_backtest(session: AsyncSession = Depends(get_async_session)):
    return await session.execute(select(Backtests).order_by(Backtests.timestamp))
