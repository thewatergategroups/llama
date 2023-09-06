from fastapi import FastAPI

from .endpoints.stocks import router as stock_router
from .endpoints.backtest import router as bt_router
from ..tools import setup_logging
from ..settings import get_settings


def create_app() -> FastAPI:
    """
    create and return fastapi app
    """
    setup_logging(get_settings())
    app = FastAPI(
        title="llama trading bot",
        description="trading bot using alpaca API",
        version="1.0",
    )
    app.include_router(stock_router)
    app.include_router(bt_router)

    return app
