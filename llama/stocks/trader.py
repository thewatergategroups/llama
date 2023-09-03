import logging
from alpaca.trading import TradingClient, Position, Order
from alpaca.trading.enums import AssetClass, OrderSide, TimeInForce
from alpaca.trading.requests import (
    GetAssetsRequest,
    GetOrdersRequest,
    LimitOrderRequest,
    MarketOrderRequest,
)
from alpaca.common.exceptions import APIError

from ..database.models import Orders, Positions
from ..settings import Settings
from collections import defaultdict
from trekkers.config import get_sync_sessionmaker
from trekkers.statements import on_conflict_update
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import delete


def get_0():
    return 0


def get_inf():
    return 100000000


class MockLlamaTrader:
    def __init__(self, starting_balance: float = 2000):
        self.buys = 0
        self.sells = 0
        self.starting_balance = starting_balance
        self.balance = starting_balance
        self.highest_price: dict[str, float] = defaultdict(get_0)
        self.lowest_price: dict[str, float] = defaultdict(get_inf)
        self.positions_held: dict[str, int] = defaultdict(get_0)

    def place_order(
        self,
        symbol: str = "TSLA",
        time_in_force: TimeInForce = TimeInForce.FOK,
        side: OrderSide = OrderSide.BUY,
        quantity: int = 1,
        **kwargs,
    ):
        if side == OrderSide.BUY:
            self.buys += quantity
            self.balance -= quantity * 1  # this should be buy/sell price
            self.highest_price[symbol] = (
                1  # this should be buy/sell price
                if self.highest_price[symbol] < 1  # this should be buy/sell price
                else self.highest_price[symbol]
            )
            self.lowest_price[symbol] = (
                1  # this should be buy/sell price
                if self.lowest_price[symbol] > 1  # this should be buy/sell price
                else self.lowest_price[symbol]
            )
            self.positions_held[symbol] += quantity
        elif side == OrderSide.SELL:
            self.sells += quantity
            self.balance += quantity * 1  # this should be buy/sell price
            self.positions_held[symbol] -= quantity

    def aggregate(self, verbose: bool = False):
        response = {
            "profit": self.balance - self.starting_balance,
            "buys": self.buys,
            "sells": self.sells,
            "total_positions_held": sum(self.positions_held.values()),
        }
        if verbose:
            response["extra"] = {
                "lowest_price": dict(self.lowest_price),
                "highest_price": dict(self.highest_price),
                "positions_held": dict(self.positions_held),
            }
        return response


class LlamaTrader:
    """Llama is created"""

    def __init__(
        self,
        client: TradingClient,
        pg_sessionmaker: sessionmaker[Session],
    ):
        self.client = client
        self.positions: list[Position] = []
        self.orders: list[Order] = []
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

    def get_positions(self):
        logging.info("getting positions...")
        positions = self.client.get_all_positions()
        self.positions = positions
        with self.pg_sessionmaker.begin() as session:
            session.execute(
                on_conflict_update(
                    insert(Positions).values([pos.dict() for pos in positions]),
                    Positions,
                )
            )
        return positions

    def close_position(self, symbol: str):
        logging.info("closing positions %s...", symbol)

        self.client.close_position(symbol)
        with self.pg_sessionmaker.begin() as session:
            try:
                position = self.client.get_open_position(symbol)
            except APIError:
                session.execute(delete(Positions).where(Positions.symbol == symbol))
                self.positions = [
                    position for position in self.positions if position.symbol != symbol
                ]
                return True
            session.execute(
                on_conflict_update(insert(Positions).values(position.dict()))
            )
        return False

    def get_orders(self, side: OrderSide | None = None):
        """get all orders I have placed"""
        logging.info("getting orders...")

        request_params = GetOrdersRequest(status="all", side=side)
        orders = self.client.get_orders(filter=request_params)
        self.orders = orders
        with self.pg_sessionmaker.begin() as session:
            session.execute(
                on_conflict_update(
                    insert(Orders).values([pos.dict() for pos in orders]),
                    Orders,
                )
            )
        return orders

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
