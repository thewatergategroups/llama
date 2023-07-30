from alpaca.data.models.base import TimeSeriesMixin, BaseDataSet
from alpaca.data.models import Bar
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

    def append(self, bar: Bar):
        """Keeps the last 15 bars in memory"""
        symbol_list = self.data[bar.symbol]
        symbol_list.append(bar)
        if (len_list := len(symbol_list)) > 15:
            symbol_list = symbol_list[len_list - 15 :]


@dataclass
class Metric:
    symbol: str
    name: str
    value: Any
    calculated_at: datetime = field(default_factory=datetime.utcnow)
