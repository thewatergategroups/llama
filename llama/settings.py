"""
Consts, Enums and Models
"""
from pydantic import BaseSettings
import logging


class Settings(BaseSettings):
    """Application Settings"""

    api_endpoint: str = ""
    api_key: str = ""
    secret_key: str = ""
    news_url: str = "https://data.alpaca.markets/v1beta1/news"
    paper: bool = True
    log_level: str = "INFO"
