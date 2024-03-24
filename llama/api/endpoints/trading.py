"""
Account Trading information Endpoints 
"""

from uuid import UUID

from alpaca.trading.enums import OrderSide, TimeInForce
from fastapi import Depends
from fastapi.routing import APIRouter

from ...stocks import Trader
from ..deps import get_trader
from ..validator import has_admin_scope, validate_jwt

router = APIRouter(
    prefix="/trading",
    tags=["Trading"],
    dependencies=[Depends(validate_jwt), Depends(has_admin_scope())],
)


@router.get("/account")
async def get_trading_account(trader: Trader = Depends(get_trader)):
    """
    Get the account the bot is trading with from alpaca
    """
    return trader.get_account()


@router.get("/assets")
async def get_trading_assets(trader: Trader = Depends(get_trader)):
    """
    Get the assets we are currently trading
    """
    assets = trader.get_assets(trading=True)
    return {"count": len(assets), "data": assets}


@router.post("/assets")
async def set_trading_assets(
    asset_id: str, trading: bool, trader: Trader = Depends(get_trader)
):
    """
    Set assets to be traded by the bot
    """
    return trader.set_trading_asset(UUID(asset_id), trading)


@router.get("/positions")
async def get_positions(force: bool = False, trader: Trader = Depends(get_trader)):
    """
    Return current positions on all symbols
    """
    return trader.get_positions(force)


@router.get("/position")
async def get_position(
    symbol: str, force: bool = False, trader: Trader = Depends(get_trader)
):
    """
    Return position of a specific symbol
    """
    return trader.get_position(symbol, force)


@router.get("/orders")
async def get_orders(
    side: OrderSide, force: bool = False, trader: Trader = Depends(get_trader)
):
    """
    Return current orders
    """
    return trader.get_orders(side, force)


@router.post("/position/close")
async def close_position(symbol: str, trader: Trader = Depends(get_trader)):
    """
    Manually close a current position on a symbol
    """
    trader.close_position(symbol)


@router.post("/position/order")
async def place_order(
    symbol: str,
    time_in_force: TimeInForce,
    side: OrderSide,
    quantity: int,
    trader: Trader = Depends(get_trader),
):
    """
    Manually place an order on a symbol
    """
    return trader.place_order(symbol, time_in_force, side, quantity)
