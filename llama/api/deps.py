from ..settings import get_settings
from ..stocks.history import History
from ..stocks.trader import Trader
from ..backtester import BackTester
from trekkers.config import get_async_sessionmaker

_HISTORY = None
_TRADER = None
_BACKTESTER = None


def get_history():
    """Get history wrapper"""
    global _HISTORY
    if _HISTORY is None:
        _HISTORY = History.create(get_settings())
    return _HISTORY


def get_trader():
    """Get trader wrapper"""
    global _TRADER
    if _TRADER is None:
        _TRADER = Trader.create(get_settings())
    return _TRADER


def get_backtester():
    global _BACKTESTER
    if _BACKTESTER is None:
        _BACKTESTER = BackTester.create()
    return _BACKTESTER


async def get_async_session():
    async with get_async_sessionmaker(get_settings().db_settings).begin() as session:
        yield session
