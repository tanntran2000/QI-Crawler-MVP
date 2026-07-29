from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session, sessionmaker

from .models import Base


# Additive compatibility migration for the MVP. Production deployments should use Alembic.
_ADDITIVE_COLUMNS: dict[str, dict[str, str]] = {
    "notices": {
        "content_hash": "VARCHAR(64)",
        "source_kind": "VARCHAR(32) NOT NULL DEFAULT 'web'",
        "data_quality_status": "VARCHAR(32) NOT NULL DEFAULT 'valid'",
    },
    "attachments": {
        "download_status": "VARCHAR(32) NOT NULL DEFAULT 'pending'",
        "download_method": "VARCHAR(32)",
        "download_attempts": "INTEGER NOT NULL DEFAULT 0",
        "download_error": "TEXT",
        "last_attempt_at": "TIMESTAMP",
    },
    "crawl_runs": {
        "source_name": "VARCHAR(255)",
        "records_found": "INTEGER NOT NULL DEFAULT 0",
        "records_inserted": "INTEGER NOT NULL DEFAULT 0",
        "records_updated": "INTEGER NOT NULL DEFAULT 0",
        "records_failed": "INTEGER NOT NULL DEFAULT 0",
        "error_message": "TEXT",
    },
}


class Database:
    def __init__(self, url: str):
        connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
        self.engine = create_engine(url, future=True, pool_pre_ping=True, connect_args=connect_args)
        self._session_factory = sessionmaker(bind=self.engine, expire_on_commit=False, class_=Session)

    def create_all(self) -> None:
        Base.metadata.create_all(self.engine)
        self._apply_additive_migrations()

    def _apply_additive_migrations(self) -> None:
        inspector = inspect(self.engine)
        existing_tables = set(inspector.get_table_names())
        with self.engine.begin() as connection:
            for table_name, columns in _ADDITIVE_COLUMNS.items():
                if table_name not in existing_tables:
                    continue
                existing_columns = {item["name"] for item in inspector.get_columns(table_name)}
                for column_name, ddl in columns.items():
                    if column_name in existing_columns:
                        continue
                    connection.exec_driver_sql(
                        f'ALTER TABLE "{table_name}" ADD COLUMN "{column_name}" {ddl}'
                    )

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
