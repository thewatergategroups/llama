from sqlalchemy.dialects.postgresql import Insert
from .models import BaseSql


def on_conflict_update(stmt: Insert, model: BaseSql):
    return stmt.on_conflict_do_update(
        index_elements=model.__mapper__.primary_key,
        set_={
            column.name: getattr(stmt.excluded, column.name)
            for column in model.__mapper__.columns
            if not column.primary_key and not column.server_default
        },
    )
