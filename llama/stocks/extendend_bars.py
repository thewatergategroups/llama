from alpaca.common.types import RawData
from typing import Optional
from alpaca.data.mappings import BAR_MAPPING
from alpaca.data.models import Bar


class ExtedndedBar(Bar):
    def __init__(self, symbol: str, raw_data: RawData) -> None:
        """Instantiates a bar

        Args:
            raw_data (RawData): Raw unparsed bar data from API, contains ohlc and other fields.
        """
        mapped_bar = {}
        extedndedBarMapping = [
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
                extedndedBarMapping[key]: val
                for key, val in raw_data.items()
                if key in extedndedBarMapping
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
