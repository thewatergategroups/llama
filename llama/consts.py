"""
Consts, Enums and Models
"""
from pydantic import BaseSettings

class Settings(BaseSettings):
    """Application Settings"""
    api_endpoint:str = ""
    api_key:str = ""
    secret_key:str = ""
 
