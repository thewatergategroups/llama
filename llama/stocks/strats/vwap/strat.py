from ..base import Strategy
from .conditions import get_conditions


class Vwap(Strategy):
    CONDITIONS = get_conditions()
    NAME = "Volume Weighted Average Price"
    ALIAS = "WVAP"
