from ..settings import Settings
from ..stocks.history import LlamaHistory

_HISTORY = None


def get_history():
    """Get history wrapper"""
    global _HISTORY
    if _HISTORY is None:
        _HISTORY = LlamaHistory(Settings())
    return _HISTORY
