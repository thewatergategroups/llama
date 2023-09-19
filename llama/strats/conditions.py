from .base import get_base_conditions
from .vwap import get_vwap_conditions


def get_all_conditions():
    conditions = get_base_conditions() + get_vwap_conditions()
    return {cond.name: cond for cond in conditions}
