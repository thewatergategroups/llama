from functools import lru_cache

from ..stocks.history import History
from ..stocks.trader import Trader
from ..backtester import BackTester
from trekkers.config import get_async_sessionmaker
from ..settings import get_sync_sessionm, get_settings
from yumi import JwtClient


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
