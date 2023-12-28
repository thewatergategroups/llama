from fastapi.routing import APIRouter
from fastapi import Depends
from uuid import UUID
from alpaca.trading.enums import OrderSide, TimeInForce

from ...stocks import Trader
from ..deps import get_trader
from ..validator import validate_jwt, has_admin_scope


router = APIRouter(
    prefix="/trading",
    tags=["Trading"],
    dependencies=[Depends(validate_jwt), Depends(has_admin_scope())],
)


@router.get("/account")
async def get_trading_account(trader: Trader = Depends(get_trader)):
    return trader.get_account()


@router.get("/assets")
async def get_trading_assets(trader: Trader = Depends(get_trader)):
    assets = trader.get_assets(trading=True)
    return {"count": len(assets), "data": assets}


@router.post("/assets")
async def set_trading_assets(
    asset_id: str, trading: bool, trader: Trader = Depends(get_trader)
):
    return trader.set_trading_asset(UUID(asset_id), trading)


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
