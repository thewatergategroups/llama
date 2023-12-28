from datetime import datetime, timedelta

from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from fastapi import Response, Depends, Query
from typing import Annotated
from fastapi.routing import APIRouter
from ..deps import get_history, get_trader
from ...stocks import plot_stock_data, History, Trader
from ..validator import validate_jwt, has_admin_scope

router = APIRouter(
    prefix="/stocks",
    tags=["Stock Information"],
    dependencies=[Depends(validate_jwt), Depends(has_admin_scope())],
)


@router.get("/historic/graph")
async def get_historic_graph(
    symbol: str,
    timeframe: TimeFrameUnit = TimeFrameUnit.Hour,
    start_date: datetime = (datetime.utcnow() - timedelta(days=900)),
    history: History = Depends(get_history),
):
    """
    Api endpoint to return historic data fig for a given stock
    """

    data = history.get_stock_bars(
        [symbol], TimeFrame(amount=1, unit=timeframe), start_date
    )
    bytes_ = plot_stock_data(data)
    return Response(content=bytes_[0], media_type="image/png")


@router.get("/historic/data")
async def get_historic_data(
    symbol: str,
    timeframe: TimeFrameUnit = TimeFrameUnit.Hour,
    start_date: datetime = (datetime.utcnow() - timedelta(days=900)),
    history: History = Depends(get_history),
):
    """
    Api endpoint to return historic data directly
    """

    data = history.get_stock_bars(
        [symbol], TimeFrame(amount=1, unit=timeframe), start_date
    )
    return data.data[symbol]


@router.get("/assets/qoute/latest")
async def latest_ask_price(
    symbols: Annotated[list[str], Query()], history: History = Depends(get_history)
):
    return {symbol: history.get_latest_qoute(symbol).dict() for symbol in symbols}


@router.get("/news")
async def latest_ask_price(
    start_time: datetime,
    end_time: datetime,
    symbols: Annotated[list[str], Query()],
    history: History = Depends(get_history),
    next_page: str | None = None,
):
    return history.get_news(start_time, end_time, symbols, next_page)


@router.get("/assets")
async def tradable_assets(
    offset: int = 0, limit: int = 300, trader: Trader = Depends(get_trader)
):
    assets = trader.get_assets(limit=limit, offset=offset)
    return {"count": len(assets), "data": assets}


@router.get("/assets/search")
async def get_trading_assets(
    symbol: str | None = None,
    name: str | None = None,
    trader: Trader = Depends(get_trader),
):
    assets = trader.get_assets(symbol=symbol, name=name)
    return {"count": len(assets), "data": assets}
