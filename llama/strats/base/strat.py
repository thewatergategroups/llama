"""
Base Strategy class definition
"""

# ⢀⣠⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀⠀⠀⣠⣤⣶⣶
# ⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀⠀⢰⣿⣿⣿⣿
# ⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣧⣀⣀⣾⣿⣿⣿⣿
# ⣿⣿⣿⣿⣿⡏⠉⠛⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡿⣿
# ⣿⣿⣿⣿⣿⣿⠀⠀⠀⠈⠛⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠿⠛⠉⠁⠀⣿
# ⣿⣿⣿⣿⣿⣿⣧⡀⠀⠀⠀⠀⠙⠿⠿⠿⠻⠿⠿⠟⠿⠛⠉⠀⠀⠀⠀⠀⣸⣿
# ⣿⣿⣿⣿⣿⣿⣿⣷⣄⠀⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣴⣿⣿
# ⣿⣿⣿⣿⣿⣿⣿⣿⣿⠏⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠠⣴⣿⣿⣿⣿
# ⣿⣿⣿⣿⣿⣿⣿⣿⡟⠀⠀⢰⣹⡆⠀⠀⠀⠀⠀⠀⣭⣷⠀⠀⠀⠸⣿⣿⣿⣿
# ⣿⣿⣿⣿⣿⣿⣿⣿⠃⠀⠀⠈⠉⠀⠀⠤⠄⠀⠀⠀⠉⠁⠀⠀⠀⠀⢿⣿⣿⣿
# ⣿⣿⣿⣿⣿⣿⣿⣿⢾⣿⣷⠀⠀⠀⠀⡠⠤⢄⠀⠀⠀⠠⣿⣿⣷⠀⢸⣿⣿⣿
# ⣿⣿⣿⣿⣿⣿⣿⣿⡀⠉⠀⠀⠀⠀⠀⢄⠀⢀⠀⠀⠀⠀⠉⠉⠁⠀⠀⣿⣿⣿
# ⣿⣿⣿⣿⣿⣿⣿⣿⣧⠀⠀⠀⠀⠀⠀⠀⠈⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⣿⣿
# ⣿⣿⣿⣿⣿⣿⣿⣿⣿⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿
import logging
from datetime import datetime, timedelta

from alpaca.data.models import Bar
from alpaca.data.timeframe import TimeFrame
from alpaca.trading import OrderSide, TimeInForce
from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.orm import Session
from trekkers.statements import on_conflict_update

from ...consts import BARSET_TYPE
from ...database import StratConditionMap, Strategies
from ...settings import get_sync_sessionm
from ...stocks import History, Trader
from .conditions import get_base_conditions
from .consts import LIVE_DATA, Condition, ConditionType


class Strategy:
    """
    Strategy Parent class which defines how conditions are checked
    """

    DEFAULT_CONDITIONS = get_base_conditions()
    NAME = "Base"
    ALIAS = "bs"
    ACTIVE = False

    def __init__(
        self, history: History, data: BARSET_TYPE, conditions: list[Condition]
    ):
        """Initialising function of self"""
        self.history = history
        self.historic_data = data
        self.conditions = conditions
        self.condition_map: dict[str, dict[str, list[Condition]]] = (
            self.to_condition_map(conditions)
        )

    @staticmethod
    def to_condition_map(conditions: list[Condition]):
        """
        Return conditions in a map that is used for quantifying trade decision easily
        """
        condition_map = {
            OrderSide.BUY: {ConditionType.AND: [], ConditionType.OR: []},
            OrderSide.SELL: {ConditionType.AND: [], ConditionType.OR: []},
        }
        for condition in conditions:
            condition_map[condition.side][condition.type].append(condition)
        return condition_map

    @classmethod
    def create(
        cls,
        history: History,
        symbols: list[str],
        start_time: datetime = datetime.utcnow() - timedelta(days=60),
        end_time: datetime = datetime.utcnow() - timedelta(minutes=15),
        timeframe: TimeFrame = TimeFrame.Day,
        conditions: list[Condition] | None = None,
    ):
        """Create an instance of self using the inputs provided"""
        conditions = conditions or cls.DEFAULT_CONDITIONS
        with get_sync_sessionm().begin() as session:
            try:
                cls.get(session)
            except KeyError:
                logging.warning("strategy doesn't exist in database")
        return cls(
            history,
            history.get_stock_bars(
                symbols, time_frame=timeframe, start_time=start_time, end_time=end_time
            ),
            conditions,
        )

    @classmethod
    def upsert(cls, session: Session):
        """
        Update and insert self into the database
        """
        values = {"name": cls.NAME, "alias": cls.ALIAS, "active": cls.ACTIVE}
        session.execute(
            on_conflict_update(insert(Strategies).values(values), Strategies)
        )

        for condition in cls.DEFAULT_CONDITIONS:
            condition.upsert(cls.ALIAS, session)
        session.execute(
            delete(StratConditionMap).where(
                StratConditionMap.strategy_alias == cls.ALIAS,
                StratConditionMap.condition_name.notin_(
                    [condition.name for condition in cls.DEFAULT_CONDITIONS]
                ),
            )
        )

    @classmethod
    def get(cls, session: Session):
        """
        Get self and all conditions of self from the database
        """
        strat = session.scalar(select(Strategies).where(Strategies.alias == cls.ALIAS))
        if strat is None:
            raise KeyError("strat doesn't exist")
        cls.ACTIVE = strat.active
        for condition in cls.DEFAULT_CONDITIONS:
            try:
                condition.get(cls.ALIAS, session)
            except KeyError:
                condition.upsert(cls.ALIAS, session)

    def run(
        self, trader: Trader, most_recent_bar: Bar, live_update_strategy: bool = True
    ):
        """Standard strat run method to be overwritten"""
        if not self.ACTIVE:
            logging.debug("Strategy %s not active", self.ALIAS)
            return None, None

        if live_update_strategy:
            with get_sync_sessionm().begin() as session:
                self.get(session)

        action, qty = self.trade(trader, most_recent_bar)
        LIVE_DATA.append(most_recent_bar)
        return action, qty

    def _condition_check(
        self,
        most_recent_bar: Bar,
        trader: Trader,
        side: OrderSide,
    ):
        """
        Run the condition check against all strategy conditions
        """
        return any(
            [
                all(
                    [
                        condition(most_recent_bar, trader)
                        for condition in self.condition_map[side][ConditionType.AND]
                        if condition.active
                    ]
                ),
                *[
                    condition(most_recent_bar, trader)
                    for condition in self.condition_map[side][ConditionType.OR]
                    if condition.active
                ],
            ]
        )

    def trade(self, trader: Trader, most_recent_bar: Bar):
        """Making trade decisions based on the conditions"""
        position = trader.get_position(most_recent_bar.symbol, force=True)
        qty_avaliable = int(position.qty_available)

        if self._condition_check(most_recent_bar, trader, OrderSide.BUY):
            latest_qoute = self.history.get_latest_qoute(most_recent_bar.symbol)
            if (
                trader.buying_power
                < latest_qoute.ask_price + 0.02 * latest_qoute.ask_price
            ):
                logging.info(
                    "Balance %s is not enough money to buy %s at %s",
                    trader.buying_power,
                    most_recent_bar.symbol,
                    latest_qoute.ask_price,
                )
                return None, None

            logging.info(
                "buying a stock of %s with strat %s",
                most_recent_bar.symbol,
                self.__class__,
            )
            buy = -qty_avaliable if qty_avaliable < 0 else 1
            trader.place_order(
                most_recent_bar.symbol, time_in_force=TimeInForce.GTC, quantity=buy
            )
            return OrderSide.BUY, buy
        elif self._condition_check(most_recent_bar, trader, OrderSide.SELL):
            logging.info(
                "selling a share of %s with strat %s",
                most_recent_bar.symbol,
                self.__class__,
            )
            sell = qty_avaliable if qty_avaliable > 0 else 1
            trader.place_order(
                most_recent_bar.symbol,
                time_in_force=TimeInForce.GTC,
                side=OrderSide.SELL,
                quantity=sell,
            )
            return OrderSide.SELL, sell
        return None, None

    @classmethod
    def dict(cls):
        """
        Return the strategy as a dictionary
        """
        return {
            "alias": cls.ALIAS,
            "name": cls.NAME,
            "active": cls.ACTIVE,
            "conditions": [cond.dict() for cond in cls.DEFAULT_CONDITIONS],
        }
