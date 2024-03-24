"""
Required by alembic - runs the database migrations
"""

from logging.config import fileConfig

from alembic import context
from trekkers.config import run_migrations_online

from llama.database.models import BaseSql

run_migrations_online(BaseSql.metadata, context.config)
