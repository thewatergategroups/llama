from fastapi import FastAPI

from .endpoints.stocks import router as stock_router
from .endpoints.backtest import router as bt_router
from .endpoints.trading import router as tr_router
from fastapi.middleware.cors import CORSMiddleware
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
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(stock_router)
    app.include_router(bt_router)
    app.include_router(tr_router)

    return app
