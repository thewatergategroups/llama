from functools import lru_cache

from trekkers.config import get_async_sessionmaker
from yumi import JwtClient

from ..backtester import BackTester
from ..settings import get_settings, get_sync_sessionm
from ..stocks.history import History
from ..stocks.trader import Trader


@lru_cache
def get_history():
    """Get history wrapper"""
    return History.create(get_settings())


@lru_cache
def get_trader():
    """Get trader wrapper"""
    return Trader.create(get_settings())


def get_backtester():
    return BackTester.create()


async def get_async_session():
    async with get_async_sessionmaker(get_settings().db_settings).begin() as session:
        yield session


@lru_cache
def get_jwt_client():
    return JwtClient(get_settings().jwt_config)


def get_sync_session():
    with get_sync_sessionm().begin() as session:
        yield session
