"""
Backtesting endpoints
"""

from fastapi import BackgroundTasks, Depends, HTTPException
from fastapi.routing import APIRouter
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...backtester import BacktestDefinition, BackTester
from ...consts import Status
from ...database.models import Backtests, BacktestStats
from ...stocks import History
from ..deps import get_async_session, get_backtester, get_history
from .strats import get_strats

router = APIRouter(prefix="/backtest", tags=["Backtesting"])


@router.post("/start")
async def run_backtest(
    data: BacktestDefinition,
    background_task: BackgroundTasks,
    history: History = Depends(get_history),
    backtester: BackTester = Depends(get_backtester),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Run a backtest
    """
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
        for strat in data.strategy_aliases:
            strats += await get_strats(strat)
    backtest_id = backtester.insert_start_of_backtest(data.symbols, strats)

    background_task.add_task(backtester.backtest_strats, backtest_id, history, data)
    return {"id": backtest_id}


@router.get("/result")
async def get_backtest(
    backtest_id: int, session: AsyncSession = Depends(get_async_session)
):
    """
    Get backtest results
    """
    return (
        (await session.execute(select(Backtests).where(Backtests.id == backtest_id)))
        .scalar()
        .as_dict()
    )


@router.get("/result/stats")
async def get_backtest_result_stats(
    backtest_id: int, session: AsyncSession = Depends(get_async_session)
):
    """
    Get stats about the backtest result
    """
    response = (
        await session.execute(
            select(BacktestStats)
            .where(BacktestStats.backtest_id == backtest_id)
            .order_by(BacktestStats.timestamp.asc())
        )
    ).scalars()
    return [resp.as_dict() for resp in response]


@router.get("/results")
async def get_backtest_results(session: AsyncSession = Depends(get_async_session)):
    """
    Get the results of a run
    """
    results = (
        (await session.execute(select(Backtests).order_by(Backtests.timestamp.desc())))
        .scalars()
        .all()
    )
    return [result.as_dict() for result in results]
