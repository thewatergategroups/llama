import logging
from ..stocks.models import NullPosition
from alpaca.trading import OrderSide
from alpaca.trading import Order
from alpaca.trading.enums import OrderSide, TimeInForce


class MockTrader:
    """Llama is created"""

    def __init__(self):
        self.positions: dict[str, NullPosition] = {}
        self.orders: list[Order] = []
        self.balance = 100_000
        self.starting_balance = self.balance
        self.buys = 0
        self.sells = 0

    @classmethod
    def create(cls):
        """Create class with data"""
        return cls()

    def get_position(self, symbol: str, force: bool = False):
        if (position := self.positions.get(symbol)) is not None:
            return position
        self.positions[symbol] = NullPosition(symbol=symbol)
        return self.positions[symbol]

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

    def aggregate(self, verbose: bool = False):
        response = {
            "profit": self.balance - self.starting_balance,
            "buys": self.buys,
            "sells": self.sells,
            "total_positions_held": sum(
                [int(pos.qty) for pos in self.positions.values()]
            ),
        }
        if verbose:
            response["extra"] = {"positions_held": dict(self.positions)}
        return response

    def update_stats(
        self, symbol: str, side: OrderSide, quantity: int, price: float, itteration: int
    ):
        if side == OrderSide.BUY:
            self.balance -= price * quantity
            self.buys += quantity
            logging.info("buy on itteration %s", itteration)
        elif side == OrderSide.SELL:
            self.balance += price * quantity
            self.sells += quantity
            logging.info("sell on itteration %s", itteration)

    def post_trade_update_position(
        self, symbol: str, side: OrderSide, quantity: int, price: float
    ):
        position = self.get_position(symbol)
        cost_basis = int(position.qty) * float(position.avg_entry_price)
        new_total = quantity * price
        new_cost_basis = 0
        new_qty = 0
        if side == OrderSide.BUY:
            new_cost_basis = cost_basis + new_total
            new_qty = int(position.qty) + quantity

        elif side == OrderSide.SELL:
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
