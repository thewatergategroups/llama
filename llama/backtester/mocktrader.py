from copy import deepcopy
from datetime import datetime
import logging
from ..stocks.models import NullPosition
from alpaca.trading import OrderSide
from alpaca.trading import Order
from alpaca.trading.enums import OrderSide, TimeInForce
from dataclasses import dataclass, field


@dataclass
class MockStats:
    positions: dict[str, NullPosition] = field(default_factory=dict)
    orders: list[Order] = field(default_factory=list)
    buying_power: float = 1_000
    starting_buying_power: float = 1_000
    equity: float = 1_000
    buys: int = 0
    sells: int = 0
    timestamp: datetime = datetime.utcnow()


class MockTrader:
    """Llama is created"""

    def __init__(self):
        self.stats = MockStats()
        self.stats_record: list[MockStats] = []
        self.buying_power = self.stats.buying_power

    @classmethod
    def create(cls):
        """Create class with data"""
        return cls()

    def get_position(self, symbol: str, force: bool = False):
        if (position := self.stats.positions.get(symbol)) is not None:
            return position
        self.stats.positions[symbol] = NullPosition(symbol=symbol)
        return self.stats.positions[symbol]

    def place_order(
        self,
        symbol: str = "TSLA",
        time_in_force: TimeInForce = TimeInForce.GTC,
        side: OrderSide = OrderSide.BUY,
        quantity: int = 1,
    ):
        """
        placeholder for strat to call when a decision is made.
        Creates a position if one didn't exist already
        """
        self.get_position(symbol)

    @staticmethod
    def get_aggregate_template():
        return {
            "starting_buying_power": 0,
            "buying_power": 0,
            "equity": 0,
            "buys": 0,
            "sells": 0,
            "total_positions_held": 0,
            "positions": {},
        }

    def aggregate(self, verbose: bool = False):
        response = {
            "starting_buying_power": self.stats.starting_buying_power,
            "buying_power": self.stats.buying_power,
            "equity": self.stats.equity,
            "buys": self.stats.buys,
            "sells": self.stats.sells,
            "total_positions_held": sum(
                [int(pos.qty) for pos in self.stats.positions.values()]
            ),
            "positions": {"positions_held": dict(self.stats.positions)},
        }
        return response

    def post_trade_update(
        self,
        symbol: str,
        side: OrderSide,
        quantity: int,
        price: float,
        timestamp: datetime,
    ):
        self.stats.timestamp = timestamp
        new_cost_basis = 0
        new_qty = 0

        position = self.get_position(symbol)
        position.current_price = price
        position.market_value = price * int(position.qty)
        cost_basis = int(position.qty) * float(position.avg_entry_price)

        self.stats.equity = self.stats.buying_power + sum(
            [float(pos.market_value) for pos in self.stats.positions.values()]
        )
        if (side, quantity) != (None, None):
            new_total = quantity * price
            if side == OrderSide.BUY:
                self.stats.buying_power -= price * quantity
                self.stats.buys += quantity
                new_cost_basis = cost_basis + new_total
                new_qty = int(position.qty) + quantity

            elif side == OrderSide.SELL:
                self.stats.buying_power += price * quantity
                self.stats.sells += quantity
                new_cost_basis = cost_basis - new_total
                new_qty = int(position.qty) - quantity
            logging.info(f"{symbol},{side}, {quantity}, {new_qty}")
            position.avg_entry_price = str(new_cost_basis / (new_qty or 1))
            position.cost_basis = str(new_cost_basis)
            position.qty = str(new_qty)
            position.qty_available = str(new_qty)

            total_pl = (price * new_qty) - new_cost_basis

            position.unrealized_pl = str(0) if new_qty == 0 else str(total_pl)
            position.unrealized_plpc = (
                str(0) if new_qty == 0 else str(total_pl / (new_cost_basis or 1) * 100)
            )

        self.stats.equity = self.stats.buying_power + sum(
            [float(pos.market_value) for pos in self.stats.positions.values()]
        )
        self.stats_record.append(deepcopy(self.stats))
