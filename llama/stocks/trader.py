import logging
from uuid import UUID
from alpaca.trading import TradingClient, Position, Order, Asset
from alpaca.trading.enums import AssetClass, OrderSide, TimeInForce
from alpaca.trading.requests import (
    GetAssetsRequest,
    GetOrdersRequest,
    LimitOrderRequest,
    MarketOrderRequest,
)
from .models import NullPosition
from alpaca.common.exceptions import APIError
from ..database import Orders, Positions, Assets
from ..settings import Settings
from ..tools import divide_chunks
from trekkers.statements import upsert
from trekkers.config import get_sync_sessionmaker
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import delete, select, update


class Trader:
    """Llama is created"""

    def __init__(
        self,
        client: TradingClient,
        pg_sessionmaker: sessionmaker[Session],
    ):
        self.client = client
        self.positions: dict[str, Position] = {}
        self.orders: dict[str, list[Order]] = {}
        self.pg_sessionmaker = pg_sessionmaker

    @classmethod
    def create(cls, settings: Settings):
        """Create class with data"""
        client = TradingClient(
            settings.api_key, settings.secret_key, paper=settings.paper
        )
        pg_sessionmaker = get_sync_sessionmaker(settings.db_settings)
        obj = cls(client, pg_sessionmaker)
        obj.get_orders(OrderSide.BUY)
        obj.get_orders(OrderSide.SELL)
        obj.get_positions()
        obj.get_all_assets(settings.force_get_all_assets)
        return obj

    def get_positions(self, force: bool = False):
        logging.info("getting positions...")
        if self.positions and not force:
            return self.positions
        positions = self.client.get_all_positions()
        self.positions = {position.symbol: position for position in positions}

        with self.pg_sessionmaker.begin() as session:
            session.execute(delete(Positions))
            if positions:
                upsert(self.pg_sessionmaker, [p.dict() for p in positions], Positions)
        return positions

    def get_position(self, symbol: str, force: bool = False):
        if (position := self.positions.get(symbol)) is not None and not force:
            return position
        try:
            position = self.client.get_open_position(symbol)
            self.positions[symbol] = position
            upsert(self.pg_sessionmaker, position.dict(), Positions)
            return position
        except APIError:
            logging.debug("No open position for %s", symbol)
            return NullPosition(symbol=symbol)

    def close_position(self, symbol: str):
        logging.info("closing positions %s...", symbol)

        self.client.close_position(symbol)
        with self.pg_sessionmaker.begin() as session:
            try:
                position = self.client.get_open_position(symbol)
                self.positions[symbol] = position
                upsert(self.pg_sessionmaker, position.dict(), Positions)
            except APIError:
                session.execute(delete(Positions).where(Positions.symbol == symbol))
                self.positions.pop(symbol)
                return True
        return False

    def get_orders(self, side: OrderSide, force: bool = False):
        """get all orders I have placed - Only ever set on start up"""
        logging.info("getting orders for %s side...", side)
        if side_orders := self.orders.get(side) and not force:
            return side_orders

        request_params = GetOrdersRequest(status="all", side=side)
        self.orders[side] = self.client.get_orders(filter=request_params)
        if self.orders[side]:
            upsert(self.pg_sessionmaker, [o.dict() for o in self.orders[side]], Orders)
        return self.orders[side]

    def get_all_assets(self, force: bool = False):
        """get all assets that can be bought"""
        if not force:
            return self.get_assets()
        logging.info("getting all tradable assets from api")
        search_params = GetAssetsRequest(asset_class=AssetClass.US_EQUITY)
        tradable_assets = self.client.get_all_assets(search_params)

        for entry in divide_chunks(tradable_assets, 4000):
            upsert(
                self.pg_sessionmaker,
                [a.dict() for a in entry],
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
        fields: list[str] | None = None,
    ):
        with self.pg_sessionmaker.begin() as session:
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
        with self.pg_sessionmaker.begin() as session:
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
        upsert(self.pg_sessionmaker, response.dict(), Orders)
        self.orders[side].append(response)
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
        upsert(self.pg_sessionmaker, response.dict(), Orders)
        self.orders[side].append(response)
        return response
