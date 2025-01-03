"""
Trader class for executing trades and keeping track of changes
"""

import logging
from uuid import UUID

from alpaca.common.exceptions import APIError
from alpaca.trading import Asset, Order, Position, TradingClient
from alpaca.trading.enums import AssetClass, OrderSide, TimeInForce
from alpaca.trading.requests import (
    GetAssetsRequest,
    GetOrdersRequest,
    LimitOrderRequest,
    MarketOrderRequest,
)
from sqlalchemy import delete, select, update
from trekkers.statements import upsert
from yumi import divide_chunks

from ..database import Account, Assets, Orders, Positions
from ..settings import Settings, get_sync_sessionm
from .models import NullPosition


class Trader:
    """Llama is created"""

    def __init__(self, client: TradingClient):
        self.client = client
        self.buying_power = 0

    @classmethod
    def create(cls, settings: Settings):
        """Create class with data"""
        client = TradingClient(
            settings.api_key, settings.secret_key, paper=settings.paper
        )
        obj = cls(client)
        # client.get_account_configurations()
        obj.get_orders(OrderSide.BUY)
        obj.get_orders(OrderSide.SELL)
        obj.get_positions(True)
        obj.get_all_assets(settings.force_get_all_assets)
        obj.get_account()
        return obj

    def get_account(self):
        """_summary_

        Returns:
            _type_: _description_
        """
        account = self.client.get_account()
        self.buying_power = account.buying_power
        upsert(get_sync_sessionm(), account.model_dump(), Account)
        return account

    def get_positions(self, force: bool = False):
        """_summary_

        Args:
            force (bool, optional): _description_. Defaults to False.

        Returns:
            _type_: _description_
        """
        logging.info("getting positions...")
        if not force:
            with get_sync_sessionm().begin() as session:
                return [
                    Position(**pos.as_dict())
                    for pos in session.scalars(select(Positions)).all()
                ]
        positions = self.client.get_all_positions()

        with get_sync_sessionm().begin() as session:
            session.execute(delete(Positions))
            if positions:
                upsert(
                    get_sync_sessionm(), [p.model_dump() for p in positions], Positions
                )
        return positions

    def get_position(self, symbol: str, force: bool = False):
        if not force:
            with get_sync_sessionm().begin() as session:
                position = session.scalar(
                    select(Positions).where(Positions.symbol == symbol)
                )
                if position:
                    return Position(**position.as_dict())
        try:
            position = self.client.get_open_position(symbol)
            upsert(get_sync_sessionm(), position.model_dump(), Positions)
            return position
        except APIError:
            logging.debug("No open position for %s", symbol)
            with get_sync_sessionm().begin() as session:
                session.execute(delete(Positions).where(symbol == symbol))
            return NullPosition(symbol=symbol)

    def close_position(self, symbol: str):
        """_summary_

        Args:
            symbol (str): _description_

        Returns:
            _type_: _description_
        """
        logging.info("closing positions %s...", symbol)

        self.client.close_position(symbol)
        with get_sync_sessionm().begin() as session:
            try:
                position = self.client.get_open_position(symbol)
                upsert(get_sync_sessionm(), position.model_dump(), Positions)
            except APIError:
                session.execute(delete(Positions).where(Positions.symbol == symbol))
                return True
        return False

    def get_orders(self, side: OrderSide, force: bool = False):
        """get all orders I have placed - Only ever set on start up"""
        logging.info("getting orders for %s side...", side)
        if not force:
            with get_sync_sessionm().begin() as session:
                orders = [
                    Order(**ord.as_dict())
                    for ord in session.scalars(
                        select(Orders).where(Orders.side == side.value)
                    ).all()
                ]
            return orders
        request_params = GetOrdersRequest(status="all", side=side)
        orders = self.client.get_orders(filter=request_params)
        if orders:
            upsert(get_sync_sessionm(), [o.model_dump() for o in orders], Orders)
        return orders

    def get_all_assets(self, force: bool = False):
        """get all assets that can be bought"""
        if not force:
            return self.get_assets()
        logging.info("getting all tradable assets from api")
        search_params = GetAssetsRequest(asset_class=AssetClass.US_EQUITY)
        tradable_assets = self.client.get_all_assets(search_params)

        for entry in divide_chunks(tradable_assets, 4000):
            upsert(
                get_sync_sessionm(),
                [a.model_dump(exclude=["attributes"]) for a in entry],
                Assets,
            )
        return self.get_assets()

    def get_assets(
        self,
        trading: bool | None = None,
        name: str | None = None,
        symbol: str | None = None,
        offset: int | None = None,
        limit: int | None = None,
    ):
        """_summary_

        Args:
            trading (bool | None, optional): _description_. Defaults to None.
            name (str | None, optional): _description_. Defaults to None.
            symbol (str | None, optional): _description_. Defaults to None.
            offset (int | None, optional): _description_. Defaults to None.
            limit (int | None, optional): _description_. Defaults to None.

        Returns:
            _type_: _description_
        """
        with get_sync_sessionm().begin() as session:
            stmt = select(Assets)
            if isinstance(trading, bool):
                stmt = stmt.where(Assets.bot_is_trading == trading)
            if symbol:
                stmt = stmt.where(Assets.symbol.contains(symbol))
            if name:
                stmt = stmt.where(Assets.symbol.contains(name))
            if limit:
                stmt = stmt.limit(limit)
            if offset:
                stmt = stmt.offset(offset)
            assets = session.scalars(stmt)
            return [
                Asset(**asset.as_dict({"asset_class": "class"})) for asset in assets
            ]

    def set_trading_asset(self, id: UUID, trading: bool):
        """_summary_

        Args:
            id (UUID): _description_
            trading (bool): _description_
        """
        with get_sync_sessionm().begin() as session:
            session.execute(
                update(Assets).where(Assets.id == id).values(bot_is_trading=trading)
            )

    def place_limit_order(
        self,
        symbol: str = "TSLA",
        limit_price: int = 17000,
        notional: int = 4000,
        time_in_force: TimeInForce = TimeInForce.FOK,
        side: OrderSide = OrderSide.SELL,
    ):
        """preparing limit order"""
        limit_order_data = LimitOrderRequest(
            symbol=symbol,
            limit_price=limit_price,
            notional=notional,
            side=side,
            time_in_force=time_in_force,
        )

        # Limit order
        response = self.client.submit_order(order_data=limit_order_data)
        upsert(get_sync_sessionm(), response.model_dump(), Orders)
        return response

    def place_order(
        self,
        symbol: str = "TSLA",
        time_in_force: TimeInForce = TimeInForce.FOK,
        side: OrderSide = OrderSide.BUY,
        quantity: int = 1,
    ):
        """place order"""
        market_order_data = MarketOrderRequest(
            symbol=symbol, qty=quantity, side=side, time_in_force=time_in_force
        )
        response = self.client.submit_order(market_order_data)
        upsert(get_sync_sessionm(), response.model_dump(), Orders)
        self.get_account()
        return response
