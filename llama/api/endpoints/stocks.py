from datetime import datetime, timedelta
from alpaca.trading.enums import OrderSide, TimeInForce

from alpaca.data.timeframe import TimeFrame, TimeFrameUnit
from fastapi import Response, Depends, Query
from typing import Annotated
from fastapi.routing import APIRouter
from ..deps import get_history, get_trader
from ...stocks import plot_stock_data, History, Trader

router = APIRouter(prefix="/stocks")


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


@router.get("/assets/price/latest")
async def latest_ask_price(
    symbols: Annotated[list[str], Query()], history: History = Depends(get_history)
):
    return history.get_latest_ask_price(symbols)


@router.get("/news")
async def latest_ask_price(
    start_time: datetime,
    end_time: datetime,
    symbols: Annotated[list[str], Query()],
    history: History = Depends(get_history),
    next_page: str | None = None,
):
    return history.get_news(start_time, end_time, symbols, next_page)


@router.get("/positions")
async def get_positions(force: bool = False, trader: Trader = Depends(get_trader)):
    """
    Api endpoint to returnmy current positions
    """
    return trader.get_positions(force)


@router.get("/position")
async def get_positions(
    symbol: str, force: bool = False, trader: Trader = Depends(get_trader)
):
    """
    Api endpoint to returnmy current positions
    """
    return trader.get_position(symbol, force)


@router.get("/orders")
async def get_orders(
    side: OrderSide, force: bool = False, trader: Trader = Depends(get_trader)
):
    """
    Api endpoint to returnmy current positions
    """
    return trader.get_orders(side, force)


@router.post("/position/close")
async def close_position(symbol: str, trader: Trader = Depends(get_trader)):
    trader.close_position(symbol)


@router.post("/position/order")
async def place_order(
    symbol: str,
    time_in_force: TimeInForce,
    side: OrderSide,
    quantity: int,
    trader: Trader = Depends(get_trader),
):
    return trader.place_order(symbol, time_in_force, side, quantity)


@router.get("/assets")
async def tradable_assets(trader: Trader = Depends(get_trader)):
    return trader.get_all_assets()
