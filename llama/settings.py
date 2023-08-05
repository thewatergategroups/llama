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


STOCKS_TO_TRADE = (
    "AAPL",
    "TSLA",
    "MSFT",
    "PFE",
    "XOM",
    "BAC",
    "INTC",
    "IBM",
    "CSCO",
    "HPQ",
    "JPM",
    "WML",
)

ETFS_TO_TRADE = (
    "SPY",
    "VOO",
    "IVV",
    "QQQ",
    "VTWO",
    "DIA",
    "VTI",
    "ONEQ",
    "QQQE",
    "QQQJ",
)