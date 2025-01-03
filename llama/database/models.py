"""
Database Table Model definitions
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from alpaca.trading import AccountStatus
from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from trekkers import BaseSql


class Account(BaseSql):
    """Alpaca Bot Accounnt information"""

    __tablename__ = "account"
    __table_args__ = {"schema": "llama"}

    id: Mapped[UUID] = mapped_column(primary_key=True)
    account_number: Mapped[str]
    status: Mapped[AccountStatus]
    crypto_status: Mapped[Optional[AccountStatus]]
    currency: Mapped[Optional[str]]
    buying_power: Mapped[Optional[str]]
    regt_buying_power: Mapped[Optional[str]]
    daytrading_buying_power: Mapped[Optional[str]]
    non_marginable_buying_power: Mapped[Optional[str]]
    cash: Mapped[Optional[str]]
    accrued_fees: Mapped[Optional[str]]
    pending_transfer_out: Mapped[Optional[str]]
    pending_transfer_in: Mapped[Optional[str]]
    portfolio_value: Mapped[Optional[str]]
    pattern_day_trader: Mapped[Optional[bool]]
    trading_blocked: Mapped[Optional[bool]]
    transfers_blocked: Mapped[Optional[bool]]
    account_blocked: Mapped[Optional[bool]]
    created_at: Mapped[Optional[datetime]]
    trade_suspended_by_user: Mapped[Optional[bool]]
    multiplier: Mapped[Optional[str]]
    shorting_enabled: Mapped[Optional[bool]]
    equity: Mapped[Optional[str]]
    last_equity: Mapped[Optional[str]]
    long_market_value: Mapped[Optional[str]]
    short_market_value: Mapped[Optional[str]]
    initial_margin: Mapped[Optional[str]]
    maintenance_margin: Mapped[Optional[str]]
    last_maintenance_margin: Mapped[Optional[str]]
    sma: Mapped[Optional[str]]
    daytrade_count: Mapped[Optional[int]]
    options_buying_power: Mapped[Optional[str]]
    options_approved_level: Mapped[Optional[int]]
    options_trading_level: Mapped[Optional[int]]


class Bars(BaseSql):
    """Bar information for symbols over time"""

    __tablename__ = "bars"
    __table_args__ = {"schema": "llama"}

    symbol: Mapped[str] = mapped_column(primary_key=True)
    timeframe: Mapped[str] = mapped_column(primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(primary_key=True)
    open: Mapped[float]
    close: Mapped[float]
    high: Mapped[float]
    low: Mapped[float]
    trade_count: Mapped[int]
    vwap: Mapped[float]
    volume: Mapped[int]


class Trades(BaseSql):
    """Trade information for specific symbols"""

    __tablename__ = "trades"
    __table_args__ = {"schema": "llama"}

    id: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str]
    timestamp: Mapped[datetime]
    exchange: Mapped[str]
    price: Mapped[float]
    size: Mapped[int]
    conditions: Mapped[list] = mapped_column(type_=JSONB)
    tape: Mapped[str]


class Qoutes(BaseSql):
    """Qoute information for specific symbols"""

    __tablename__ = "qoutes"
    __table_args__ = {"schema": "llama"}

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    symbol: Mapped[str]
    timestamp: Mapped[datetime]
    ask_exchange: Mapped[str]
    ask_price: Mapped[float]
    ask_size: Mapped[int]
    bid_exchange: Mapped[str]
    bid_price: Mapped[float]
    bid_size: Mapped[int]
    conditions: Mapped[list] = mapped_column(type_=JSONB)
    tape: Mapped[str]


class Orders(BaseSql):
    """Bot order information from alpaca"""

    __tablename__ = "orders"
    __table_args__ = {"schema": "llama"}
    id: Mapped[UUID] = mapped_column(primary_key=True)
    client_order_id: Mapped[str]
    created_at: Mapped[datetime]
    updated_at: Mapped[datetime]
    submitted_at: Mapped[datetime]
    filled_at: Mapped[Optional[datetime]]
    expired_at: Mapped[Optional[datetime]]
    canceled_at: Mapped[Optional[datetime]]
    failed_at: Mapped[Optional[datetime]]
    replaced_at: Mapped[Optional[datetime]]
    replaced_by: Mapped[Optional[UUID]]
    replaces: Mapped[Optional[UUID]]
    asset_id: Mapped[UUID]
    symbol: Mapped[str]
    asset_class: Mapped[str]
    notional: Mapped[Optional[str]]
    qty: Mapped[Optional[str]]
    filled_qty: Mapped[Optional[str]]
    filled_avg_price: Mapped[Optional[str]]
    order_class: Mapped[str]
    order_type: Mapped[str]
    type: Mapped[str]
    side: Mapped[str]
    time_in_force: Mapped[str]
    limit_price: Mapped[Optional[str]]
    stop_price: Mapped[Optional[str]]
    status: Mapped[str]
    extended_hours: Mapped[bool]
    legs: Mapped[Optional[list]] = mapped_column(type_=JSONB)
    trail_percent: Mapped[Optional[str]]
    trail_price: Mapped[Optional[str]]
    hwm: Mapped[Optional[str]]


class TradeUpdates(BaseSql):
    """Market trade updates information"""

    __tablename__ = "trade_updates"
    __table_args__ = {"schema": "llama"}
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    execution_id: Mapped[Optional[UUID]]
    event: Mapped[str]
    order_id: Mapped[UUID] = mapped_column(ForeignKey("llama.orders.id"))
    timestamp: Mapped[datetime]
    position_qty: Mapped[Optional[float]]
    price: Mapped[Optional[float]]
    qty: Mapped[Optional[float]]


class Positions(BaseSql):
    """Bot Alpaca Positions"""

    __tablename__ = "positions"
    __table_args__ = {"schema": "llama"}

    asset_id: Mapped[UUID] = mapped_column(unique=True, index=True)
    symbol: Mapped[str] = mapped_column(primary_key=True)
    exchange: Mapped[str]
    asset_class: Mapped[str]
    asset_marginable: Mapped[Optional[bool]]
    avg_entry_price: Mapped[str]
    qty: Mapped[str]
    side: Mapped[str]
    market_value: Mapped[str]
    cost_basis: Mapped[str]
    unrealized_pl: Mapped[str]
    unrealized_plpc: Mapped[str]
    unrealized_intraday_pl: Mapped[str]
    unrealized_intraday_plpc: Mapped[str]
    current_price: Mapped[str]
    lastday_price: Mapped[str]
    change_today: Mapped[str]
    swap_rate: Mapped[Optional[str]]
    avg_entry_swap_rate: Mapped[Optional[str]]
    usd: Mapped[Optional[dict]] = mapped_column(type_=JSONB)
    qty_available: Mapped[Optional[str]]


class Backtests(BaseSql):
    """Backtest run information"""

    __tablename__ = "backtests"
    __table_args__ = {"schema": "llama"}
    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    symbols: Mapped[list[str]] = mapped_column(type_=JSONB)
    result: Mapped[Optional[dict]] = mapped_column(type_=JSONB, nullable=True)
    status: Mapped[str]
    timestamp: Mapped[datetime]
    strategies: Mapped[dict] = mapped_column(nullable=True, type_=JSONB)


class BacktestStats(BaseSql):
    """Backtest run stats"""

    __tablename__ = "backtest_stats"
    __table_args__ = {"schema": "llama"}
    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    backtest_id: Mapped[int] = mapped_column(ForeignKey("llama.backtests.id"))
    positions: Mapped[dict] = mapped_column(type_=JSONB)
    orders: Mapped[list] = mapped_column(type_=JSONB)
    buying_power: Mapped[float]
    equity: Mapped[float]
    starting_buying_power: Mapped[float]
    buys: Mapped[int]
    sells: Mapped[int]
    timestamp: Mapped[datetime]


class Assets(BaseSql):
    """Existing and tradable assets on Alpaca"""

    __tablename__ = "tradable_assets"
    __table_args__ = {"schema": "llama"}
    id: Mapped[UUID] = mapped_column(primary_key=True)
    bot_is_trading: Mapped[bool] = mapped_column(default=False)
    asset_class: Mapped[str]
    exchange: Mapped[str]
    symbol: Mapped[str] = mapped_column(index=True)
    name: Mapped[Optional[str]]
    status: Mapped[str]
    tradable: Mapped[bool]
    marginable: Mapped[bool]
    shortable: Mapped[bool]
    easy_to_borrow: Mapped[bool]
    fractionable: Mapped[bool]
    min_order_size: Mapped[Optional[float]]
    min_trade_increment: Mapped[Optional[float]]
    price_increment: Mapped[Optional[float]]
    maintenance_margin_requirement: Mapped[Optional[float]]


class Strategies(BaseSql):
    """Strategies definitions"""

    __tablename__ = "strategies"
    __table_args__ = {"schema": "llama"}

    alias: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]
    active: Mapped[bool] = mapped_column(default=False)


class Conditions(BaseSql):
    """Condition definitions"""

    __tablename__ = "conditions"
    __table_args__ = {"schema": "llama"}
    name: Mapped[str] = mapped_column(primary_key=True)
    side: Mapped[str]
    default_variables: Mapped[dict] = mapped_column(type_=JSONB)


class StratConditionMap(BaseSql):
    """Map of what conditions exist in what strategies"""

    __tablename__ = "strat_conditions"
    __table_args__ = {"schema": "llama"}
    strategy_alias: Mapped[str] = mapped_column(
        ForeignKey("llama.strategies.alias"), primary_key=True
    )
    condition_name: Mapped[str] = mapped_column(
        ForeignKey("llama.conditions.name"), primary_key=True
    )
    type: Mapped[str]
    active: Mapped[bool] = mapped_column(default=False)
    variables: Mapped[dict] = mapped_column(type_=JSONB)
