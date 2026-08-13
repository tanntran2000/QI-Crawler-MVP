from __future__ import annotations

from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    create_engine,
    inspect,
    text,
)

from alembic import command
from qi_crawler.db import Database, SchemaNotReady
from qi_crawler.migrations import upgrade_database
from qi_crawler.models import Base, Document

ROOT = Path(__file__).parent.parent
CORE_TABLES = {
    "alembic_version",
    "crawl_runs",
    "crawl_tasks",
    "notices",
    "attachments",
    "documents",
    "tender_items",
    "inventory_items",
    "company_evidence",
    "bid_requirements",
    "compliance_assessments",
    "bid_predictions",
    "selection_plans",
    "bid_results",
    "bid_openings",
    "contractors",
    "investor_profiles",
}


def _alembic_config(database: Path) -> Config:
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database}")
    return config


def test_blank_database_upgrade_creates_complete_core_schema(tmp_path: Path) -> None:
    database = tmp_path / "blank.db"

    command.upgrade(_alembic_config(database), "head")

    engine = create_engine(f"sqlite:///{database}")
    inspector = inspect(engine)
    assert CORE_TABLES.issubset(inspector.get_table_names())
    assert set(Base.metadata.tables).issubset(inspector.get_table_names())
    for table_name, table in Base.metadata.tables.items():
        actual_columns = {column["name"] for column in inspector.get_columns(table_name)}
        assert {column.name for column in table.columns}.issubset(actual_columns)
    notice_columns = {column["name"] for column in inspector.get_columns("notices")}
    assert {"source_name", "source_notice_id"}.issubset(notice_columns)
    notice_indexes = {index["name"] for index in inspector.get_indexes("notices")}
    assert {"ix_notices_source_name", "ix_notices_source_notice_id"}.issubset(notice_indexes)
    attachment_constraints = {
        tuple(constraint["column_names"])
        for constraint in inspector.get_unique_constraints("attachments")
    }
    assert ("notice_id", "source_url") in attachment_constraints
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == (
            "0006_add_document_taxonomy"
        )


def test_upgrade_preserves_legacy_notice_data(tmp_path: Path) -> None:
    database = tmp_path / "legacy.db"
    engine = create_engine(f"sqlite:///{database}")
    metadata = MetaData()
    Table(
        "crawl_runs",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("started_at", DateTime, nullable=False),
        Column("finished_at", DateTime),
        Column("status", String(32), nullable=False),
        Column("pages_ok", Integer, nullable=False),
        Column("pages_failed", Integer, nullable=False),
        Column("notes", Text),
    )
    Table(
        "notices",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("source_url", Text, nullable=False),
        Column("url_hash", String(64), nullable=False, unique=True),
        Column("title", Text),
        Column("first_seen_at", DateTime, nullable=False),
        Column("last_seen_at", DateTime, nullable=False),
    )
    metadata.create_all(engine)
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO notices (source_url, url_hash, title, first_seen_at, last_seen_at)
                VALUES (:source_url, :url_hash, :title, :first_seen_at, :last_seen_at)
                """
            ),
            {
                "source_url": "https://example.test/a",
                "url_hash": "a" * 64,
                "title": "Existing notice",
                "first_seen_at": "2026-08-12 00:00:00",
                "last_seen_at": "2026-08-12 00:00:00",
            },
        )

    command.upgrade(_alembic_config(database), "head")

    inspector = inspect(engine)
    assert CORE_TABLES.issubset(inspector.get_table_names())
    notice_columns = {column["name"] for column in inspector.get_columns("notices")}
    assert {"source_name", "source_notice_id", "package_description"}.issubset(notice_columns)
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT title FROM notices")) == "Existing notice"


def test_taxonomy_migration_preserves_wp1_document_and_file_format(
    tmp_path: Path,
) -> None:
    database = tmp_path / "wp1-documents.db"
    config = _alembic_config(database)
    command.upgrade(config, "0005_add_documents")
    engine = create_engine(f"sqlite:///{database}")
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO documents (
                    document_source, document_type, original_filename, stored_path,
                    mime_type, file_size, sha256, version, uploaded_at, status,
                    created_at, updated_at
                ) VALUES (
                    'manual_upload', 'PDF', 'legacy.pdf', 'legacy/path.pdf',
                    'application/pdf', 6, :sha256, 1, :timestamp, 'UNLINKED',
                    :timestamp, :timestamp
                )
                """
            ),
            {"sha256": "c" * 64, "timestamp": "2026-08-13 00:00:00"},
        )
    engine.dispose()

    command.upgrade(config, "head")

    upgraded = create_engine(f"sqlite:///{database}")
    with upgraded.connect() as connection:
        row = connection.execute(
            text(
                """
                SELECT document_type, file_format, classification_status,
                       original_filename, sha256
                FROM documents
                """
            )
        ).one()
        assert tuple(row) == ("OTHER", "PDF", "UNKNOWN", "legacy.pdf", "c" * 64)
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == (
            "0006_add_document_taxonomy"
        )
    upgraded.dispose()


def test_adopt_pre_alembic_database_with_existing_crawl_tasks(tmp_path: Path) -> None:
    """A database created by the former runtime must adopt, not recreate 0001."""
    database = tmp_path / "pre_alembic.db"
    engine = create_engine(f"sqlite:///{database}")
    Base.metadata.create_all(engine)
    # Simulate the schema that existed before the Document model/migration.
    Document.__table__.drop(engine)
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO notices (
                    source_url, url_hash, source_kind, notice_type, crawl_status,
                    review_status, data_quality_status, title, first_seen_at, last_seen_at
                ) VALUES (
                    :source_url, :url_hash, :source_kind, :notice_type, :crawl_status,
                    :review_status, :data_quality_status, :title, :first_seen_at, :last_seen_at
                )
                """
            ),
            {
                "source_url": "https://example.test/pre-alembic",
                "url_hash": "b" * 64,
                "source_kind": "web",
                "notice_type": "tender",
                "crawl_status": "completed",
                "review_status": "pending",
                "data_quality_status": "unknown",
                "title": "Notice created before Alembic",
                "first_seen_at": "2026-08-12 00:00:00",
                "last_seen_at": "2026-08-12 00:00:00",
            },
        )
    engine.dispose()

    before_adoption = create_engine(f"sqlite:///{database}")
    inspector = inspect(before_adoption)
    assert "crawl_tasks" in inspector.get_table_names()
    assert "alembic_version" not in inspector.get_table_names()
    before_adoption.dispose()

    result = upgrade_database(
        f"sqlite:///{database}", backup_dir=tmp_path / "backups"
    )

    assert result.adopted_legacy_database is True
    assert result.revision == "0006_add_document_taxonomy"
    assert result.backup_path is not None
    assert result.backup_path.exists()
    upgraded_engine = create_engine(f"sqlite:///{database}")
    upgraded_inspector = inspect(upgraded_engine)
    assert CORE_TABLES.issubset(upgraded_inspector.get_table_names())
    assert {"source_name", "source_notice_id"}.issubset(
        column["name"] for column in upgraded_inspector.get_columns("notices")
    )
    with upgraded_engine.connect() as connection:
        assert connection.scalar(text("SELECT title FROM notices")) == (
            "Notice created before Alembic"
        )
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == (
            "0006_add_document_taxonomy"
        )
    upgraded_engine.dispose()


def test_runtime_requires_explicit_alembic_upgrade(tmp_path: Path, monkeypatch) -> None:
    """Production services never invoke create_all or additive DDL automatically."""
    monkeypatch.undo()
    database_path = tmp_path / "runtime.db"
    database = Database(f"sqlite:///{database_path}")
    with pytest.raises(SchemaNotReady, match="QI-Crawler db-upgrade"):
        database.require_current_schema()

    upgrade_database(database.url, backup_dir=tmp_path / "backups")
    database.require_current_schema()
