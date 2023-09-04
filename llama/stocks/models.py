from alpaca.data.models.base import TimeSeriesMixin, BaseDataSet
from alpaca.data.models import Bar, BarSet
from collections import defaultdict
from datetime import datetime
from dataclasses import dataclass, field
from typing import Any, Optional
from ..database.models import Bars
from alpaca.trading import (
    Position,
    AssetExchange,
    AssetClass,
    PositionSide,
    USDPositionValues,
)
from uuid import UUID, uuid4


class CustomBarSet(BaseDataSet, TimeSeriesMixin):
    data: dict[str, list[Bar]]

    def __init__(
        self,
        bars: list[Bar] = [],
    ):
        parsed_bars = defaultdict(lambda: [])
        for item in bars:
            parsed_bars[item.symbol].append(item)

        super().__init__(data=dict(parsed_bars))

    @classmethod
    def from_barset(cls, barset: BarSet):
        bars = []
        for bset in barset.data.values():
            bars += bset
        return cls(bars)

    @classmethod
    def from_postgres_bars(cls, bars: list[Bars]):
        return cls(
            [
                Bar(
                    bar.symbol,
                    {
                        "t": bar.timestamp,
                        "o": bar.open,
                        "h": bar.high,
                        "l": bar.low,
                        "c": bar.close,
                        "v": bar.volume,
                        "n": bar.trade_count,
                        "vw": bar.vwap,
                    },
                )
                for bar in bars
            ]
        )

    def append(self, bar: Bar):
        """Keeps the last 15 bars in memory"""
        if bar.symbol not in self.data:
            self.data[bar.symbol] = []
        symbol_list = self.data[bar.symbol]
        symbol_list.append(bar)

    def to_dict(self, time_frame: str):
        all_bars = []
        for bars in self.data.values():
            all_bars += bars
        response = []
        for bar in all_bars:
            dict_bar = bar.dict()
            dict_bar["timeframe"] = time_frame
            response.append(dict_bar)
        return response


@dataclass
class Metric:
    symbol: str
    name: str
    value: Any
    calculated_at: datetime = field(default_factory=datetime.utcnow)


class NullPosition(Position):
    asset_id: UUID = uuid4()
    symbol: str
    exchange: AssetExchange = AssetExchange.NASDAQ
    asset_class: AssetClass = AssetClass.US_EQUITY
    asset_marginable: Optional[bool] = False
    avg_entry_price: str = "0"
    qty: str = "0"
    side: PositionSide = PositionSide.LONG
    market_value: str = "0"
    cost_basis: str = "0"
    unrealized_pl: str = "0"
    unrealized_plpc: str = "0"
    unrealized_intraday_pl: str = "0"
    unrealized_intraday_plpc: str = "0"
    current_price: str = "0"
    lastday_price: str = "0"
    change_today: str = "0"
    swap_rate: Optional[str] = None
    avg_entry_swap_rate: Optional[str] = None
    usd: Optional[USDPositionValues] = None
    qty_available: Optional[str] = "0"
