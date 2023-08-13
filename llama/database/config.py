from pydantic import BaseSettings, BaseModel
import pathlib
import json
from typing import Callable
from ..tools import custom_json_encoder
from sqlalchemy import Engine, create_engine, MetaData, text, pool, engine_from_config
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from alembic.config import Config
from alembic import command, context
import logging


class DbSettings(BaseSettings):
    pgdatabase: str = ""
    pghost: str = ""
    pgpassword: str = ""
    pguser: str = ""
    db_schema: str = "llama"
    alembic_config_file_path: str = (
        f"{pathlib.Path(__file__).parent.resolve()}/alembic.ini"
    )

    @property
    def url(self):
        return f"postgresql+psycopg2://{self.pguser}:{self.pgpassword}@{self.pghost}:5432/{self.pgdatabase}"

    @property
    def db_config(self):
        try:
            return get_db_config()
        except ValueError:
            set_db_config(self)
        return get_db_config()


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


def set_db_config(settings: DbSettings, config: DbConfig | None = None):
    config = config or DbConfig()
    config.url = settings.url
    global _DB_CONFIG
    _DB_CONFIG = config


def get_db_config():
    global _DB_CONFIG
    if _DB_CONFIG is None:
        raise ValueError("config has not yet been set")
    return _DB_CONFIG


def get_sync_engine(settings: DbSettings):
    global _SYNC_ENGINE
    if _SYNC_ENGINE is None:
        config = settings.db_config
        _SYNC_ENGINE = create_engine(**config.dict())
    return _SYNC_ENGINE


def get_sync_sessionmaker(settings: DbSettings):
    global _SYNC_SESSION
    if _SYNC_SESSION is None:
        engine = get_sync_engine(settings)
        _SYNC_SESSION = sessionmaker(bind=engine)
    return _SYNC_SESSION


def get_async_engine(settings: DbSettings):
    global _ASYNC_ENGINE
    if _ASYNC_ENGINE is None:
        config = settings.db_config
        _ASYNC_ENGINE = create_async_engine(**config.dict())
    return _ASYNC_ENGINE


def get_async_sessionmaker(settings: DbSettings):
    global _ASYNC_SESSION
    if _ASYNC_SESSION is None:
        config = settings.db_config
        engine = get_async_engine(config)
        _ASYNC_SESSION = async_sessionmaker(bind=engine)
    return _ASYNC_SESSION


def create_schema(settings: DbSettings):
    engine = get_sync_engine(settings)
    with engine.connect() as session:
        session.execute(text(f"CREATE SCHEMA IF NOT EXISTS {settings.db_schema}"))


def setup_alembic(settings: DbSettings):
    config = Config(file_=settings.alembic_config_file_path)
    config.set_main_option("sqlalchemy.url", settings.url)
    migration_options = config.get_section("options")
    if not migration_options:
        logging.error("options to prevent unsafe migrations missing!!!")
        raise KeyError
    return config


def run_upgrade(settings: DbSettings, revision: str | None = None):
    revision = revision if revision is not None else "head"
    alembic_config = setup_alembic(settings)
    create_schema(settings)
    command.upgrade(alembic_config, revision)


def run_downgrade(settings: DbSettings, revision: str | None = None):
    revision = revision if revision is not None else "head"
    alembic_config = setup_alembic(settings)
    command.downgrade(alembic_config, revision)


def run_migrations_online(target_metadata: MetaData, config: Config):
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    migration_options = config.get_section("options")
    if not migration_options:
        logging.error("options to prevent unsafe migrations missing!!!")
        raise KeyError
    schema = migration_options["schema"]

    def include_object(object, name, type_, reflected, compare_to):
        if type_ == "table" and object.schema != schema:
            return False
        return True

    with connectable.connect() as connection:
        transaction = connection.begin()
        connection.execute(text(f"CREATE SCHEMA IF NOT EXISTS {schema}"))
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            version_table_schema=schema,
            version_table=migration_options["alembic_table"],
            include_schemas=True,
            include_object=include_object,
        )

        with context.begin_transaction():
            context.run_migrations()
        transaction.commit()
