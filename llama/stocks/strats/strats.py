from .vwap import Vwap
from .base import Strategy


def get_all_strats() -> dict[str, type[Strategy]]:
    return {Vwap.NAME: Vwap}
