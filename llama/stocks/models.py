"""
Helper Stock models
"""

import logging

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from uuid import UUID, uuid4
import pandas as pd

# from alpaca.data.models import ExtendedBar, ExtendedBarSet
from alpaca.data.models.base import BaseDataSet, TimeSeriesMixin
from alpaca.trading import (
    AssetClass,
    AssetExchange,
    Position,
    PositionSide,
    USDPositionValues,
)

from ..database.models import Bars

from .extendend_bars import ExtendedBar, ExtendedBarSet


class CustomBarSet(BaseDataSet, TimeSeriesMixin):
    """
    The same as the Alpaca defined barset, but with extra functionality
    """

    data: dict[str, list[ExtendedBar]]

    def __init__(
        self,
        bars: list[ExtendedBar] | None = None,
    ):
        """_summary_

        Args:
            bars (list[ExtendedBar] | None, optional): _description_. Defaults to None.
        """
        bars = bars or list()
        parsed_bars = defaultdict(lambda: [])
        for item in bars:
            logging.info(item)
            logging.info(type(item))
            parsed_bars[item.symbol].append(item)

        super().__init__(data=dict(parsed_bars))

    @classmethod
    def from_barset(cls, barset: ExtendedBarSet):
        """From barset to custom barset"""
        bars = []
        for bset in barset.data.values():
            bars += bset
        return cls(bars)

    @classmethod
    def from_dataframe(cls, barset_df: pd.DataFrame):
        """From Pandas DataFrame to custom barset"""
        bars_from_df = list(barset_df.T.to_dict().values())
        return cls(bars_from_df)

    @classmethod
    def from_postgres_bars(cls, bars: list[Bars]):
        """From postgres data to ExtendedBar and dataframes"""
        return cls(
            [
                ExtendedBar(
                    bar_.symbol,
                    {
                        "t": bar_.timestamp,
                        "o": bar_.open,
                        "h": bar_.high,
                        "l": bar_.low,
                        "c": bar_.close,
                        "v": bar_.volume,
                        "n": bar_.trade_count,
                        "vw": bar_.vwap,
                        "gkv": bar_.garman_klass_vol,
                        "rsi": bar_.rsi,
                        "bb_low": bar_.bb_low,
                        "bb_mid": bar_.bb_mid,
                        "bb_high": bar_.bb_high,
                        "stochastic_osci": bar_.stochastic_osci,
                        "sma_short": bar_.sma_short,
                        "sma_long": bar_.sma_long,
                    },
                )
                for bar_ in bars
            ]
        )

    def append(self, bar_: ExtendedBar):
        """Keeps the last 15 bars in memory"""
        if bar_.symbol not in self.data:
            self.data[bar_.symbol] = []
        symbol_list = self.data[bar_.symbol]
        symbol_list.append(bar_)

    def to_dict(self, time_frame: str):
        """Transforms a ExtendedBarSet into a dictionary"""
        all_bars: list[ExtendedBar] = list()
        for bars in self.data.values():
            all_bars += bars
        response = []
        for bar_ in all_bars:
            dict_bar = bar_.model_dump()
            dict_bar["timeframe"] = time_frame
            response.append(dict_bar)
        return response


@dataclass
class Metric:
    """Metric definition"""

    symbol: str
    name: str
    value: Any
    calculated_at: datetime = field(default_factory=datetime.utcnow)


class NullPosition(Position):
    """
    A stand-in Position class where there are no positions
    """

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
