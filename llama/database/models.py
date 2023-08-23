from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime


class BaseSql(DeclarativeBase):
    ...


class Bars(BaseSql):
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
    __tablename__ = "trades"
    __table_args__ = {"schema": "llama"}

    id_: Mapped[int] = mapped_column(primary_key=True)
    symbol: Mapped[str]
    timestamp: Mapped[datetime]
    exchange: Mapped[str]
    price: Mapped[float]
    size: Mapped[int]
    conditions: Mapped[list] = mapped_column(type_=JSONB)
    tape: Mapped[str]


class Qoutes(BaseSql):
    __tablename__ = "qoutes"
    __table_args__ = {"schema": "llama"}

    id_: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
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
