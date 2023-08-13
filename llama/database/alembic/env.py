from logging.config import fileConfig

from llama.database.models import BaseSql
from llama.database.config import run_migrations_online
from alembic import context


run_migrations_online(BaseSql.metadata, context.config)
