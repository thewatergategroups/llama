from ..base import Strategy
from .conditions import get_conditions


class Vwap(Strategy):
    DEFAULT_CONDITIONS = get_conditions()
    NAME = "Volume Weighted Average Price"
    ALIAS = "vwap"
    ACTIVE = True
