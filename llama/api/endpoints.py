from datetime import datetime, timedelta

from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from fastapi import Response, Depends
from fastapi.routing import APIRouter
from .deps import get_history
from ..stocks import plot_stock_data, LlamaHistory

router = APIRouter(prefix="/alpaca")


@router.get("/historic")
def get_historic_data(
    symbol: str,
    timeframe: TimeFrameUnit = TimeFrameUnit.Hour,
    start_date: datetime = (datetime.utcnow() - timedelta(days=900)),
    history: LlamaHistory = Depends(get_history),
):
    """
    Api endpoint to return historic data fig for a given stock
    """

    data = history.get_stock_bars(
        [symbol], TimeFrame(amount=1, unit=timeframe), start_date
    )
    bytes_ = plot_stock_data(data)
    return Response(content=bytes_[0], media_type="image/png")
