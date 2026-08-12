from __future__ import annotations

from pathlib import Path

import pytest

from qi_crawler.db import Database
from qi_crawler.migrations import upgrade_database


@pytest.fixture(autouse=True)
def _prepare_database_for_tests(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Keep test setup explicit while production only verifies Alembic state."""
    require_current_schema = Database.require_current_schema

    def prepare(database: Database) -> None:
        upgrade_database(database.url, backup_dir=tmp_path / "migration-backups")
        require_current_schema(database)

    monkeypatch.setattr(Database, "require_current_schema", prepare)
    # Older tests use this name as a fixture helper.  Production has no such method.
    monkeypatch.setattr(Database, "create_all", prepare, raising=False)
