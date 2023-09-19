from ..base import Strategy, get_base_conditions
from .conditions import get_vwap_conditions


class Vwap(Strategy):
    DEFAULT_CONDITIONS = get_vwap_conditions() + get_base_conditions()
    NAME = "Volume Weighted Average Price"
    ALIAS = "vwap"
    ACTIVE = True
