from __future__ import annotations

from pathlib import Path

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, inspect, select, text

from alembic import command
from qi_crawler.db import Database
from qi_crawler.market_intelligence.opportunity_contract import OpportunityIdentity
from qi_crawler.models import (
    Document,
    TenderCaseRecord,
    TenderDocumentMembershipRecord,
    TenderReleaseRecord,
)
from qi_crawler.tender_case import AuthorityClass, TenderRelease, TenderReleaseError
from qi_crawler.tender_case_persistence import TenderCasePersistence

ROOT = Path(__file__).parent.parent


def _config(database: Path) -> Config:
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database}")
    return config


@pytest.fixture
def database(tmp_path: Path) -> Database:
    database = Database(f"sqlite:///{tmp_path / 'warehouse.db'}")
    return database


def test_0016_creates_dedicated_tender_tables(tmp_path: Path) -> None:
    database = tmp_path / "schema.db"
    command.upgrade(_config(database), "head")
    engine = create_engine(f"sqlite:///{database}")
    try:
        tables = set(inspect(engine).get_table_names())
        assert {
            "tender_cases",
            "tender_releases",
            "tender_document_memberships",
        }.issubset(tables)
        with engine.connect() as connection:
            assert connection.scalar(text("SELECT version_num FROM alembic_version")) == (
                "0018_add_tender_workspace_transitions"
            )
    finally:
        engine.dispose()


def test_migration_0015_to_0016_preserves_existing_notice_and_document(tmp_path: Path) -> None:
    database = tmp_path / "preserve.db"
    command.upgrade(_config(database), "0015_add_opportunity_review_events")
    engine = Database(f"sqlite:///{database}").engine
    with engine.begin() as connection:
        connection.execute(
            text(
                """
                INSERT INTO notices (source_url, url_hash, notice_code, source_name, title,
                                     first_seen_at, last_seen_at)
                VALUES ('https://example.test/ib', :url_hash, 'IB2600000001-00', 'egp',
                        'Existing notice', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
            ),
            {"url_hash": "a" * 64},
        )
        notice_id = connection.scalar(text("SELECT id FROM notices"))
        connection.execute(
            text(
                """
                INSERT INTO documents (
                    tender_id, document_source, document_type, original_filename,
                    stored_path, mime_type, file_size, sha256, version, status,
                    uploaded_at, created_at, updated_at
                ) VALUES (:tender_id, 'manual_upload', 'PDF', 'legacy.pdf',
                          'legacy/path.pdf', 'application/pdf', 5, :sha256, 7, 'STORED',
                          CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                """
            ),
            {"tender_id": notice_id, "sha256": "b" * 64},
        )
    command.upgrade(_config(database), "head")
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT title FROM notices")) == "Existing notice"
        assert connection.scalar(text("SELECT version FROM documents")) == 7
        assert connection.scalar(text("SELECT COUNT(*) FROM tender_cases")) == 0
    engine.dispose()


def test_persistence_keeps_exact_revisions_and_rejects_duplicate(database: Database) -> None:
    persistence = TenderCasePersistence(database)
    persistence.create_case("case-1")
    first = persistence.add_release("case-1", TenderRelease(OpportunityIdentity.from_raw("IB2600000001-00")))
    second = persistence.add_release("case-1", TenderRelease(OpportunityIdentity.from_raw("IB2600000001-01")))
    assert (first.revision, second.revision) == ("00", "01")
    with pytest.raises(TenderReleaseError, match="duplicate"):
        persistence.add_release("case-1", TenderRelease(OpportunityIdentity.from_raw("IB2600000001-00")))
    with database.session() as session:
        assert session.scalar(select(TenderCaseRecord).where(TenderCaseRecord.case_key == "case-1"))
        assert session.scalar(select(TenderReleaseRecord.id).where(TenderReleaseRecord.case_id == 1)) == 1
        assert session.scalar(select(TenderReleaseRecord.revision).where(TenderReleaseRecord.case_id == 1).order_by(TenderReleaseRecord.id.desc())) == "01"


def test_membership_is_separate_and_document_version_is_not_release_revision(database: Database) -> None:
    persistence = TenderCasePersistence(database)
    persistence.create_case("case-1")
    release = persistence.add_release("case-1", TenderRelease(OpportunityIdentity.from_raw("IB2600000002-01")))
    with database.session() as session:
        document = Document(
            document_source="manual_upload",
            document_type="PDF",
            original_filename="hsmt.pdf",
            stored_path="managed/hsmt.pdf",
            mime_type="application/pdf",
            file_size=1,
            sha256="c" * 64,
            version=9,
            status="STORED",
        )
        session.add(document)
        session.flush()
        document_id = document.id
    membership = persistence.add_membership(
        release.release_id,
        document_id,
        AuthorityClass.SOURCE_E_HSMT,
        "content:page:1",
    )
    assert membership.document_id == document_id
    assert membership.authority_class == AuthorityClass.SOURCE_E_HSMT.value
    with database.session() as session:
        assert session.get(Document, document_id).version == 9
    with database.session() as session:
        assert session.scalar(select(TenderDocumentMembershipRecord.id)) == membership.id
