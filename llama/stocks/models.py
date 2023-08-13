from alpaca.data.models.base import TimeSeriesMixin, BaseDataSet
from alpaca.data.models import Bar, BarSet
from collections import defaultdict
from datetime import datetime
from dataclasses import dataclass, field
from typing import Any


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
