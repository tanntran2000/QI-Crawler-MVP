from __future__ import annotations

from pathlib import Path

import evaluate_qi_crawler as evaluation
from qi_crawler.db import Database
from qi_crawler.models import Notice


def test_evaluation_database_uses_migrations_without_create_all(
    tmp_path: Path,
    monkeypatch,
) -> None:
    monkeypatch.delattr(Database, "create_all", raising=False)
    database_path = tmp_path / "evaluation.db"
    backup_dir = tmp_path / "backups"

    database = evaluation.prepare_evaluation_database(database_path, backup_dir)
    database.require_current_schema()
    with database.session() as session:
        session.add(
            Notice(
                source_url="https://example.test/evaluation/current-schema",
                url_hash="a" * 64,
                notice_code="EVALUATION-MIGRATION-001",
                title="Evaluation migration regression",
            )
        )

    reopened = evaluation.prepare_evaluation_database(database_path, backup_dir)
    reopened.require_current_schema()
    with reopened.session() as session:
        notice = (
            session.query(Notice)
            .filter(Notice.notice_code == "EVALUATION-MIGRATION-001")
            .one()
        )

    assert notice.title == "Evaluation migration regression"
