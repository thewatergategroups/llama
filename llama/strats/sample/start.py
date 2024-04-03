"""
SEIR = So Easy It's Ridiculous trading system implementation
https://www.babypips.com/learn/forex/the_so_easy-its-ridiculous-system
"""

from ..base import Strategy, get_base_conditions

# from .conditions import get_vwap_conditions


class SEIR(Strategy):
    """Volume weighted average proce strategy class"""

    DEFAULT_CONDITIONS = get_base_conditions()
    # DEFAULT_CONDITIONS = get_vwap_conditions() + get_base_conditions()
    NAME = "So Easy It's Ridiculous"
    ALIAS = "seir"
    ACTIVE = True
