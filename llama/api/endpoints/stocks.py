"""
Stock and asset Information 
"""

from datetime import datetime, timedelta
from typing import Annotated

from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from fastapi import Depends, Query, Response
from fastapi.routing import APIRouter

from ...stocks import History, Trader, plot_stock_data
from ..deps import get_history, get_trader
from ..validator import has_admin_scope, validate_jwt

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
    """
    Get the latest qoute for a stock
    """
    return {symbol: history.get_latest_qoute(symbol).dict() for symbol in symbols}


@router.get("/news")
async def get_news(
    start_time: datetime,
    end_time: datetime,
    symbols: Annotated[list[str], Query()],
    history: History = Depends(get_history),
    next_page: str | None = None,
):
    """
    Get news about a stock
    """
    return history.get_news(start_time, end_time, symbols, next_page)


@router.get("/assets")
async def tradable_assets(
    offset: int = 0, limit: int = 300, trader: Trader = Depends(get_trader)
):
    """Get all assets that are tradable through alpaca"""
    assets = trader.get_assets(limit=limit, offset=offset)
    return {"count": len(assets), "data": assets}


@router.get("/assets/search")
async def get_trading_assets(
    symbol: str | None = None,
    name: str | None = None,
    trader: Trader = Depends(get_trader),
):
    """Search within the tradable assets"""
    assets = trader.get_assets(symbol=symbol, name=name)
    return {"count": len(assets), "data": assets}
