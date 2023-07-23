from fastapi import FastAPI

from .endpoints import router


def create_app() -> FastAPI:
    """
    create and return fastapi app
    """
    app = FastAPI(
        title="llama trading bot",
        description="trading bot using alpaca API",
        version="1.0",
    )
    app.include_router(router)
    return app
