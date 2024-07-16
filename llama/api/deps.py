"""
API dependencies
"""

from functools import lru_cache

from trekkers.config import get_async_sessionmaker

from ..backtester import BackTester
from ..settings import get_settings, get_sync_sessionm
from ..stocks.history import History
from ..stocks.trader import Trader


@lru_cache
def get_history():
    """Get global history object"""
    return History.create(get_settings())


@lru_cache
def get_trader():
    """Get global trader object"""
    return Trader.create(get_settings())


def get_backtester():
    """get an instance of a backtester"""
    return BackTester.create()


async def get_async_session():
    """Return an async session to connect to postgres"""
    async with get_async_sessionmaker(get_settings().db_settings).begin() as session:
        yield session


def get_sync_session():
    """get a sync session too connect to postgres"""
    with get_sync_sessionm().begin() as session:
        yield session
