from typing import Optional
from alpaca.common.types import RawData
from alpaca.data.models import Bar, BarSet


class ExtendedBar(Bar):
    # def __init__(self, symbol: str, raw_data: RawData) -> None:
    #     """Instantiates a bar

    #     Args:
    #         raw_data (RawData): Raw unparsed bar data from API, contains ohlc and other fields.
    #     """
    #     mapped_bar = {}
    #     ExtendedBarMapping = [
    #         "garman_klass_vol",
    #         "rsi",
    #         "bb_low",
    #         "bb_mid",
    #         "bb_high",
    #         "stochastic_osci",
    #         "sma_short",
    #         "sma_log",
    #         *BAR_MAPPING,
    #     ]

    #     if raw_data is not None:
    #         mapped_bar = {
    #             ExtendedBarMapping[key]: val
    #             for key, val in raw_data.items()
    #             if key in ExtendedBarMapping
    #         }

    #     super().__init__(symbol=symbol, **mapped_bar)

    # garman_klass_vol: Optional[float]
    # rsi: Optional[float]
    # bb_low: Optional[float]
    # bb_mid: Optional[float]
    # bb_high: Optional[float]
    # stochastic_osci: Optional[float]
    # sma_short: Optional[float]
    # sma_log: Optional[float]
    """Extended version of the Bar class with additional technical analysis metrics.

    Attributes:
        garman_klass_vol (Optional[float]): Estimate of volatility using Garman-Klass method.
        rsi (Optional[float]): Relative Strength Index.
        bb_low (Optional[float]): Lower band of Bollinger Bands.
        bb_mid (Optional[float]): Middle band of Bollinger Bands.
        bb_high (Optional[float]): Upper band of Bollinger Bands.
        stochastic_osci (Optional[float]): Stochastic oscillator value.
        sma_short (Optional[float]): Short-term simple moving average.
        sma_long (Optional[float]): Long-term simple moving average.
    """

    def __init__(self, symbol: str, raw_data: RawData, **kwargs):
        super().__init__(symbol=symbol, raw_data=raw_data)
        self.garman_klass_vol: Optional[float] = None
        self.rsi: Optional[float] = None
        self.bb_low: Optional[float] = None
        self.bb_mid: Optional[float] = None
        self.bb_high: Optional[float] = None
        self.stochastic_osci: Optional[float] = None
        self.sma_short: Optional[float] = None
        self.sma_long: Optional[float] = None

        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)


class ExtendedBarSet(BarSet):
    """An extended collection of Bars with additional functionality or metrics.


    Attributes:
        data (Dict[str, List[Bar]]): The collection of Bars keyed by symbol.
    """

    def __init__(self, raw_data: RawData):
        """Initializes an ExtendedBarSet.

        Args:
            raw_data (RawData): The collection of raw bar data from API keyed by Symbol.
        """
        super().__init__(raw_data=raw_data)
