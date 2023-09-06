from fastapi import Depends, HTTPException, BackgroundTasks
from fastapi.routing import APIRouter
from ..deps import get_history, get_backtester
from ...stocks import History, BackTester

router = APIRouter(prefix="/backtest")


router.post("/start")


def run_backtest(
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
