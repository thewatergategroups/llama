"""
Consts, Enums and Models
"""
from pydantic import BaseSettings
from trekkers.config import DbSettings
import pathlib

TOP_LEVEL_PATH = pathlib.Path(__file__).parent.resolve()


class Settings(BaseSettings):
    """Application Settings"""

    api_endpoint: str = ""
    api_key: str = ""
    secret_key: str = ""
    news_url: str = "https://data.alpaca.markets/v1beta1/news"
    paper: bool = True
    log_level: str = "INFO"
    db_settings: DbSettings = DbSettings(
        env_script_location=f"{TOP_LEVEL_PATH}/database/alembic"
    )
    force_get_all_assets: bool = False


_SETTINGS = None


def get_settings():
    """Get history wrapper"""
    global _SETTINGS
    if _SETTINGS is None:
        _SETTINGS = Settings()
    return _SETTINGS
