from alpaca.trading import TradingClient
from alpaca.trading.enums import AssetClass, OrderSide, TimeInForce
from alpaca.trading.requests import (
    GetAssetsRequest,
    GetOrdersRequest,
    LimitOrderRequest,
    MarketOrderRequest,
)
from ..settings import Settings
from collections import defaultdict
from ..database.config import get_sync_sessionmaker
from sqlalchemy.orm import Session, sessionmaker


def get_0():
    return 0


def get_inf():
    return 100000000


class MockLlamaTrader:
    def __init__(self, starting_balance: float = 2000):
        self.positions_held: dict[str, int] = defaultdict(get_0)
        self.buys = 0
        self.sells = 0
        self.starting_balance = starting_balance
        self.balance = starting_balance
        self.highest_price: dict[str, float] = defaultdict(get_0)
        self.lowest_price: dict[str, float] = defaultdict(get_inf)

    def place_order(
        self,
        symbol: str = "TSLA",
        time_in_force: TimeInForce = TimeInForce.FOK,
        side: OrderSide = OrderSide.BUY,
        quantity: int = 1,
        last_price: float = 0,
        **kwargs,
    ):
        if side == OrderSide.BUY:
            self.buys += quantity
            self.balance -= quantity * last_price
            self.highest_price[symbol] = (
                last_price
                if self.highest_price[symbol] < last_price
                else self.highest_price[symbol]
            )
            self.lowest_price[symbol] = (
                last_price
                if self.lowest_price[symbol] > last_price
                else self.lowest_price[symbol]
            )
            self.positions_held[symbol] += quantity
        elif side == OrderSide.SELL:
            self.sells += quantity
            self.balance += quantity * last_price
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
        self.positions_held: dict[str, bool] = defaultdict(lambda: False)
        self.pg_sessionmaker = pg_sessionmaker

    @classmethod
    def create(cls, settings: Settings):
        """Create class with data"""
        client = TradingClient(
            settings.api_key, settings.secret_key, paper=settings.paper
        )
        pg_sessionmaker = get_sync_sessionmaker(settings.db_settings)
        return cls(client, pg_sessionmaker)

    def get_all_orders(self, side: OrderSide = OrderSide.SELL):
        """get all orders I have placed"""
        request_params = GetOrdersRequest(status="all", side=side)
        return self.client.get_orders(filter=request_params)

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
        return self.client.submit_order(order_data=limit_order_data)

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
        if side == OrderSide.BUY:
            self.positions_held[symbol] += quantity
        elif side == OrderSide.SELL:
            self.positions_held[symbol] -= quantity
        return response
