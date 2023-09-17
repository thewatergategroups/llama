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
from collections import defaultdict
from alpaca.data.models import Bar
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from trekkers.statements import upsert, on_conflict_update
from alpaca.trading import OrderSide, TimeInForce
import logging
from ...history import History
from ...trader import Trader
from ....settings import get_sync_sessionm
from datetime import datetime, timedelta
from ....consts import BARSET_TYPE
from ....database import Strategies, StratConditionMap
from datetime import datetime, timedelta
from alpaca.data.timeframe import TimeFrame
from .conditions import get_base_conditions, ConditionType, LIVE_DATA, Condition
from sqlalchemy.dialects.postgresql import insert


class Strategy:
    DEFAULT_CONDITIONS = get_base_conditions()
    NAME = "Base"
    ALIAS = "bs"
    ACTIVE = False

    def __init__(
        self, history: History, data: BARSET_TYPE, conditions: list[Condition]
    ):
        self.history = history
        self.historic_data = data
        self.conditions = conditions
        self.condition_map: dict[
            str, dict[str, list[Condition]]
        ] = self.to_condition_map(conditions)
        self.active = True

    @staticmethod
    def to_condition_map(conditions: list[Condition]):
        condition_map = {
            OrderSide.BUY: {ConditionType.AND: [], ConditionType.OR: []},
            OrderSide.SELL: {ConditionType.AND: [], ConditionType.OR: []},
        }
        for condition in conditions:
            condition_map[condition.side][condition.type].append(condition)
        condition_map
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
        conditions = conditions or cls.DEFAULT_CONDITIONS
        with get_sync_sessionm().begin() as session:
            try:
                cls.get(session)
            except KeyError:
                cls.upsert(session)
        return cls(
            history,
            history.get_stock_bars(
                symbols, time_frame=timeframe, start_time=start_time, end_time=end_time
            ),
            conditions,
        )

    @classmethod
    def upsert(cls, session: Session):
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
        """Making buying decisions based on the VWAP"""
        position = trader.get_position(most_recent_bar.symbol, force=True)
        qty_avaliable = int(position.qty_available)

        if self._condition_check(most_recent_bar, trader, OrderSide.BUY):
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
