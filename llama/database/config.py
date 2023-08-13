from pydantic import BaseSettings, BaseModel
import pathlib
import json
from typing import Callable
from ..tools import custom_json_encoder
from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy import text
from alembic.config import Config
from alembic import command
import logging


class DbSettings(BaseSettings):
    pgdatabase: str = ""
    pghost: str = ""
    pgpassword: str = ""
    pguser: str = ""
    schema: str = "llama"
    alembic_config_file_path: str = (
        f"{pathlib.Path(__file__).parent.resolve()}/alembic.ini"
    )

    @property
    def url(self):
        return f"postgresql+psycopg2://{self.pguser}:{self.pgpassword}@{self.pghost}:5432/{self.pgdatabase}"


class ConnectionArgs(BaseModel):
    keepalives: int = 1
    keepalives_idle: int = 30
    keepalives_interval: int = 10
    keepalives_count: int = 5


def json_serialize(data: dict):
    return json.dumps(data, default=custom_json_encoder)


class DbConfig(BaseSettings):
    pool_size: int = 60
    pool_pre_ping: bool = True  # checks connection for liveness on checkout
    max_overflow: int = 30  # max overflow connections above pool size
    echo: bool = False  # will logg statements and their params
    echo_pool: bool = False  # connection pool logging
    json_serializer: Callable = json_serialize
    json_deserializer: Callable = json.loads
    isolation_level: str = "AUTOCOMMIT"
    connect_args: dict = ConnectionArgs().dict()
    url: str = ""


_DB_CONFIG: DbConfig | None = None
_ASYNC_ENGINE: AsyncEngine | None = None
_ASYNC_SESSION: async_sessionmaker[AsyncSession] | None = None
_SYNC_ENGINE: Engine | None = None
_SYNC_SESSION: sessionmaker[Session] | None = None


def set_db_config(config: DbConfig):
    global _DB_CONFIG
    _DB_CONFIG = config


def get_db_config():
    global _DB_CONFIG
    if _DB_CONFIG is None:
        raise ValueError("config has not yet been set")
    return _DB_CONFIG


def get_sync_engine(config: DbConfig | None = None):
    global _SYNC_ENGINE
    if _SYNC_ENGINE is None:
        config = config or get_db_config()
        _SYNC_ENGINE = create_engine(**config.dict())
    return _SYNC_ENGINE


def get_sync_sessionmaker(config: DbConfig | None = None):
    global _SYNC_SESSION
    if _SYNC_SESSION is None:
        config = config or get_db_config()
        engine = get_sync_engine(config)
        _SYNC_SESSION = sessionmaker(bind=engine)
    return _SYNC_SESSION


def get_async_engine(config: DbConfig | None = None):
    global _ASYNC_ENGINE
    if _ASYNC_ENGINE is None:
        config = config or get_db_config()
        _ASYNC_ENGINE = create_async_engine(**config.dict())
    return _ASYNC_ENGINE


def get_async_sessionmaker(config: DbConfig | None = None):
    global _ASYNC_SESSION
    if _ASYNC_SESSION is None:
        config = config or get_db_config()
        engine = get_async_engine(config)
        _ASYNC_SESSION = async_sessionmaker(bind=engine)
    return _ASYNC_SESSION


def create_database(config: DbConfig, settings: DbSettings):
    engine = get_sync_engine(config)
    with engine.connect() as session:
        session.execute(
            text(f'CREATE DATABASE "{settings.pgdatabase}" owner {settings.pguser}')
        )
        session.execute(text(f"CREATE SCHEMA IF NOT EXISTS {settings.schema}"))


def setup_alembic(settings: DbSettings):
    config = Config(file_=settings.alembic_config_file_path)
    config.set_main_option("sqlalchemy.url", settings.url)
    migration_options = config.get_section("options")
    if not migration_options:
        logging.error("options to prevent unsafe migrations missing!!!")
        raise KeyError
    return config


def run_upgrade(config: DbConfig, settings: DbSettings, revision: str = "head"):
    alembic_config = setup_alembic(settings)
    create_database(config, settings)
    command.upgrade(alembic_config, revision)


def run_downgrade(settings: DbSettings, revision: str = "head"):
    alembic_config = setup_alembic(settings)
    command.downgrade(alembic_config, revision)
