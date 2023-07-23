"""
Consts, Enums and Models
"""
from pydantic import BaseSettings

from .stocks import LlamaHistory, LlamaTrader


class Settings(BaseSettings):
    """Application Settings"""

    api_endpoint: str = ""
    api_key: str = ""
    secret_key: str = ""

settings = Settings()
TRADER_CLIENT = LlamaTrader.create(settings)
HISTORY_CLIENT = LlamaHistory.create(settings)

