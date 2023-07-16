"""
Consts, Enums and Models
"""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application Settings"""
    alpaca_url:str = ""
    alpaca_secret_key:str = ""
    alpaca_api_key:str = ""

GLOBAL_SETTINGS = Settings()
