from ..settings import Settings
from ..stocks.history import History

_HISTORY = None


def get_history():
    """Get history wrapper"""
    global _HISTORY
    if _HISTORY is None:
        _HISTORY = History(Settings())
    return _HISTORY
