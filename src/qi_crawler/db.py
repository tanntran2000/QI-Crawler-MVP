from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager

import click
from sqlalchemy import create_engine, event, inspect, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from .keywords import normalize_keyword
from .models import Base

CURRENT_SCHEMA_REVISION = "0015_add_opportunity_review_events"


class SchemaNotReady(click.ClickException):
    """Raised when an operator must run the explicit database migration."""


def _register_sqlite_functions(dbapi_connection, _connection_record) -> None:
    dbapi_connection.create_function("qi_normalize", 1, lambda value: normalize_keyword(value or ""))


class Database:
    def __init__(self, url: str):
        self.url = url
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        self.engine = create_engine(url, future=True, pool_pre_ping=True, connect_args=connect_args)
        if url.startswith("sqlite"):
            event.listen(self.engine, "connect", _register_sqlite_functions)
        self._session_factory = sessionmaker(bind=self.engine, expire_on_commit=False, class_=Session)

    def require_current_schema(self) -> None:
        """Fail closed instead of creating or altering production tables at startup."""
        inspector = inspect(self.engine)
        tables = set(inspector.get_table_names())
        if "alembic_version" not in tables:
            raise SchemaNotReady(
                "Hay chay QI-Crawler db-upgrade"
            )
        missing = set(Base.metadata.tables) - tables
        if missing:
            raise SchemaNotReady(
                "Hay chay QI-Crawler db-upgrade"
            )
        with self.engine.connect() as connection:
            revision = connection.scalar(text("SELECT version_num FROM alembic_version"))
        if revision != CURRENT_SCHEMA_REVISION:
            raise SchemaNotReady(
                "Hay chay QI-Crawler db-upgrade"
            )

    def fts5_available(self) -> bool:
        if self.engine.dialect.name != "sqlite":
            return False
        try:
            with self.engine.connect() as connection:
                return bool(
                    connection.scalar(text("SELECT sqlite_compileoption_used('ENABLE_FTS5')"))
                )
        except SQLAlchemyError:  # pragma: no cover - defensive for unusual SQLite builds
            return False

    @contextmanager
    def session(self) -> Iterator[Session]:
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
