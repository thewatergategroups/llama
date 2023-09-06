import logging
from alpaca.trading import TradingClient, Position, Order
from alpaca.trading.enums import AssetClass, OrderSide, TimeInForce
from alpaca.trading.requests import (
    GetAssetsRequest,
    GetOrdersRequest,
    LimitOrderRequest,
    MarketOrderRequest,
)
from .models import NullPosition
from alpaca.common.exceptions import APIError
from ..database.models import Orders, Positions
from ..settings import Settings
from trekkers.config import get_sync_sessionmaker
from trekkers.statements import on_conflict_update
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import delete


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
        obj.get_orders()
        obj.get_positions()
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
                session.execute(
                    on_conflict_update(
                        insert(Positions).values([pos.dict() for pos in positions]),
                        Positions,
                    )
                )
        return positions

    def get_position(self, symbol: str, force: bool = False):
        if (position := self.positions.get(symbol)) is not None and not force:
            return position
        try:
            position = self.client.get_open_position(symbol)
            with self.pg_sessionmaker.begin() as session:
                session.execute(
                    on_conflict_update(insert(Positions).values(position.dict()))
                )
            return position
        except APIError:
            logging.info("No open position for %s", symbol)
            return NullPosition(symbol=symbol)

    def close_position(self, symbol: str):
        logging.info("closing positions %s...", symbol)

        self.client.close_position(symbol)
        with self.pg_sessionmaker.begin() as session:
            try:
                position = self.client.get_open_position(symbol)
            except APIError:
                session.execute(delete(Positions).where(Positions.symbol == symbol))
                self.positions = [
                    position
                    for position in self.positions.values()
                    if position.symbol != symbol
                ]
                return True
            session.execute(
                on_conflict_update(insert(Positions).values(position.dict()))
            )
        return False

    def get_orders(self, side: OrderSide | None = None, force: bool = False):
        """get all orders I have placed - Only ever set on start up"""
        logging.info("getting orders...")
        if side_orders := self.orders.get(side) and not force:
            return side_orders

        request_params = GetOrdersRequest(status="all", side=side)
        self.orders[side] = self.client.get_orders(filter=request_params)
        if self.orders[side]:
            with self.pg_sessionmaker.begin() as session:
                session.execute(
                    on_conflict_update(
                        insert(Orders).values(
                            [pos.dict() for pos in self.orders[side]]
                        ),
                        Orders,
                    )
                )
        return self.orders[side]

    def get_all_assets(self):
        """get all assets that can be bought"""
        search_params = GetAssetsRequest(asset_class=AssetClass.US_EQUITY)
        return self.client.get_all_assets(search_params)

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
        with self.pg_sessionmaker.begin() as session:
            session.execute(insert(Orders).values(response.dict()))
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
        with self.pg_sessionmaker.begin() as session:
            session.execute(insert(Orders).values(response.dict()))

        return response
