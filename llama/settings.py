"""
Consts, Enums and Models
"""

import pathlib
from functools import lru_cache

from pydantic import BaseSettings
from trekkers.config import DbSettings, get_sync_sessionmaker
from yumi import JwtConfig, LogConfig

TOP_LEVEL_PATH = pathlib.Path(__file__).parent.resolve()


class Settings(BaseSettings):
    """Application Settings"""

    api_endpoint: str = ""
    api_key: str = ""
    secret_key: str = ""
    news_url: str = "https://data.alpaca.markets/v1beta1/news"
    paper: bool = True
    force_get_all_assets: bool = False
    db_settings: DbSettings = DbSettings(
        env_script_location=f"{TOP_LEVEL_PATH}/database/alembic"
    )
    log_config: LogConfig = LogConfig()
    jwt_config: JwtConfig = JwtConfig(jwks_server_url="http://authapi:8000")
    dev_mode: bool = False


@lru_cache
def get_settings():
    """Get global db settings"""
    return Settings()


def get_sync_sessionm():
    """Get syncronous Postgres DB session"""
    return get_sync_sessionmaker(get_settings().db_settings)
