from trekkers import BaseSql, on_conflict_update
from pydantic import BaseModel
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.dialects.postgresql import insert


def upsert(seshmaker: sessionmaker[Session], data: list[dict] | dict, model: BaseSql):
    with seshmaker.begin() as session:
        stmt = insert(model).values(data)
        session.execute(on_conflict_update(stmt, model))
