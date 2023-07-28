from alpaca.data.models.base import TimeSeriesMixin, BaseDataSet
from alpaca.data.models import Quote, Bar, Trade
from collections import defaultdict


class CustomBarSet(BaseDataSet, TimeSeriesMixin):
    data: dict[str, list[Bar]]

    def __init__(
        self,
        bars: list[Bar],
    ):
        parsed_bars = defaultdict(lambda: [])
        for item in bars:
            parsed_bars[item.symbol].append(item)

        super().__init__(data=dict(parsed_bars))
