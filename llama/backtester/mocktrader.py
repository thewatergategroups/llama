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
    balance: float = 1_000
    starting_balance: float = 1_000
    buys: int = 0
    sells: int = 0
    timestamp: datetime = datetime.utcnow()


class MockTrader:
    """Llama is created"""

    def __init__(self):
        self.stats = MockStats()
        self.stats_record: list[MockStats] = []

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
    def get_stat_position(stats: MockStats):
        response = {
            "profit": stats.balance - stats.starting_balance,
            "buys": stats.buys,
            "sells": stats.sells,
            "total_positions_held": sum(
                [int(pos.qty) for pos in stats.positions.values()]
            ),
        }
        return response

    def aggregate(self, verbose: bool = False):
        response = {
            "profit": self.stats.balance - self.stats.starting_balance,
            "buys": self.stats.buys,
            "sells": self.stats.sells,
            "total_positions_held": sum(
                [int(pos.qty) for pos in self.stats.positions.values()]
            ),
        }
        if verbose:
            response["extra"] = {"positions_held": dict(self.stats.positions)}
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
        position = self.get_position(symbol)
        position.market_value = price
        if (side, quantity) == (None, None):
            self.stats_record.append(deepcopy(self.stats))
            return

        cost_basis = int(position.qty) * float(position.avg_entry_price)
        new_total = quantity * price
        new_cost_basis = 0
        new_qty = 0
        if side == OrderSide.BUY:
            self.stats.balance -= price * quantity
            self.stats.buys += quantity
            new_cost_basis = cost_basis + new_total
            new_qty = int(position.qty) + quantity

        elif side == OrderSide.SELL:
            self.stats.balance += price * quantity
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
        self.stats_record.append(deepcopy(self.stats))
