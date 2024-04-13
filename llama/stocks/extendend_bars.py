from typing import Optional, List, Dict
from alpaca.common.types import RawData
from alpaca.data.mappings import BAR_MAPPING
from alpaca.data.models import Bar, BarSet


class ExtendedBar(Bar):
    def __init__(self, symbol: str, raw_data: RawData) -> None:
        """Instantiates a bar

        Args:
            raw_data (RawData): Raw unparsed bar data from API, contains ohlc and other fields.
        """
        mapped_bar = {}
        ExtendedBarMapping = [
            "garman_klass_vol",
            "rsi",
            "bb_low",
            "bb_mid",
            "bb_high",
            "stochastic_osci",
            "sma_short",
            "sma_log",
            *BAR_MAPPING,
        ]

        if raw_data is not None:
            mapped_bar = {
                ExtendedBarMapping[key]: val
                for key, val in raw_data.items()
                if key in ExtendedBarMapping
            }

        super().__init__(symbol=symbol, **mapped_bar)

    garman_klass_vol: Optional[float]
    rsi: Optional[float]
    bb_low: Optional[float]
    bb_mid: Optional[float]
    bb_high: Optional[float]
    stochastic_osci: Optional[float]
    sma_short: Optional[float]
    sma_log: Optional[float]


# class ExtendedBarSet(BaseDataSet, TimeSeriesMixin):
class ExtendedBarSet(BarSet):
    """A collection of ExtendedBar.

    Attributes:
        data (Dict[str, List[Bar]]): The collection of ExtendedBar-s keyed by symbol.
    """

    data: Dict[str, List[ExtendedBar]] = {}

    def __init__(
        self,
        raw_data: RawData,
    ) -> None:
        """A collection of Bars.

        Args:
            raw_data (RawData): The collection of raw bar data from API keyed by Symbol.
        """

        parsed_bars = {}

        raw_bars = raw_data

        if raw_bars is not None:
            for symbol, bars in raw_bars.items():
                parsed_bars[symbol] = [
                    ExtendedBar(symbol, bar) for bar in bars if bar is not None
                ]
        super().__init__(data=parsed_bars)
