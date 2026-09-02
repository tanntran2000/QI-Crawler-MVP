from __future__ import annotations

import hashlib
import sqlite3
from pathlib import Path
from types import SimpleNamespace

import conftest as test_setup
import pytest
from sqlalchemy import create_engine, inspect, text

from qi_crawler.db import CURRENT_SCHEMA_REVISION, Database, SchemaNotReady
from qi_crawler.migrations import upgrade_database


def test_session_template_is_migrated_once_and_available(_alembic_template) -> None:
    assert _alembic_template.upgrade_count == 1
    assert _alembic_template.path.is_file()


def test_fresh_database_uses_an_independent_template_clone(tmp_path: Path) -> None:
    template = tmp_path / "template.db"
    target = tmp_path / "target.db"
    template.write_bytes(b"template")

    assert test_setup._is_fresh_sqlite_target(target) is True


def _prepare(
    database,
    template_path: Path,
    prepared_paths: set[Path],
    backup_dir: Path,
    calls: list[str],
) -> None:
    test_setup._prepare_database(
        database,
        template_path=template_path,
        prepared_paths=prepared_paths,
        backup_dir=backup_dir,
        require_current_schema=lambda _database: calls.append("require"),
    )


def test_fresh_clone_has_current_revision_and_calls_original_require(
    tmp_path: Path, _alembic_template
) -> None:
    target = tmp_path / "fresh.db"
    database = Database(f"sqlite:///{target}")
    calls: list[str] = []

    _prepare(database, _alembic_template.path, set(), tmp_path / "backups", calls)

    assert calls == ["require"]
    engine = create_engine(f"sqlite:///{target}")
    with engine.connect() as connection:
        assert connection.scalar(text("SELECT version_num FROM alembic_version")) == (
            CURRENT_SCHEMA_REVISION
        )
    engine.dispose()


def test_same_database_path_reuses_prepared_copy_without_migration(
    tmp_path: Path, _alembic_template, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "shared.db"
    prepared_paths: set[Path] = set()
    calls: list[str] = []
    upgrade_calls: list[str] = []

    def record_upgrade(database_url: str, *, backup_dir: Path):
        upgrade_calls.append(database_url)

    monkeypatch.setattr(test_setup, "upgrade_database", record_upgrade)
    _prepare(Database(f"sqlite:///{target}"), _alembic_template.path, prepared_paths, tmp_path, calls)
    _prepare(Database(f"sqlite:///{target}"), _alembic_template.path, prepared_paths, tmp_path, calls)

    assert upgrade_calls == []
    assert calls == ["require", "require"]


def test_database_copies_are_isolated_and_template_fingerprint_is_stable(
    tmp_path: Path, _alembic_template
) -> None:
    template_before = hashlib.sha256(_alembic_template.path.read_bytes()).digest()
    prepared_paths: set[Path] = set()
    calls: list[str] = []
    target_a = tmp_path / "a.db"
    target_b = tmp_path / "b.db"

    _prepare(Database(f"sqlite:///{target_a}"), _alembic_template.path, prepared_paths, tmp_path, calls)
    _prepare(Database(f"sqlite:///{target_b}"), _alembic_template.path, prepared_paths, tmp_path, calls)
    with sqlite3.connect(target_a) as connection:
        connection.execute("CREATE TABLE test_isolation (value TEXT)")
        connection.execute("INSERT INTO test_isolation VALUES ('a')")
        connection.commit()

    with sqlite3.connect(target_b) as connection:
        assert connection.execute(
            "SELECT name FROM sqlite_master WHERE name = 'test_isolation'"
        ).fetchone() is None
    assert hashlib.sha256(_alembic_template.path.read_bytes()).digest() == template_before


def test_existing_database_is_never_overwritten_and_uses_real_upgrade(
    tmp_path: Path, _alembic_template, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "existing.db"
    target.write_bytes(b"existing-bytes")
    before = target.read_bytes()
    upgrade_calls: list[str] = []

    def record_upgrade(database_url: str, *, backup_dir: Path):
        upgrade_calls.append(database_url)

    monkeypatch.setattr(test_setup, "upgrade_database", record_upgrade)
    _prepare(Database(f"sqlite:///{target}"), _alembic_template.path, set(), tmp_path, [])

    assert target.read_bytes() == before
    assert upgrade_calls == [f"sqlite:///{target}"]


def test_zero_byte_existing_database_is_not_treated_as_fresh(
    tmp_path: Path, _alembic_template, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "zero-byte.db"
    target.touch()
    upgrade_calls: list[str] = []
    monkeypatch.setattr(
        test_setup,
        "upgrade_database",
        lambda database_url, *, backup_dir: upgrade_calls.append(database_url),
    )

    _prepare(Database(f"sqlite:///{target}"), _alembic_template.path, set(), tmp_path, [])

    assert target.stat().st_size == 0
    assert upgrade_calls == [f"sqlite:///{target}"]


def test_wal_or_shm_sidecar_disables_template_fast_path(
    tmp_path: Path, _alembic_template, monkeypatch: pytest.MonkeyPatch
) -> None:
    target = tmp_path / "sidecar.db"
    Path(f"{target}-wal").write_bytes(b"wal")
    upgrade_calls: list[str] = []
    monkeypatch.setattr(
        test_setup,
        "upgrade_database",
        lambda database_url, *, backup_dir: upgrade_calls.append(database_url),
    )

    _prepare(Database(f"sqlite:///{target}"), _alembic_template.path, set(), tmp_path, [])

    assert not target.exists()
    assert Path(f"{target}-wal").read_bytes() == b"wal"
    assert upgrade_calls == [f"sqlite:///{target}"]


@pytest.mark.parametrize("database_url", ["sqlite:///:memory:", "postgresql://example/db"])
def test_non_file_database_uses_fallback_without_copy(
    database_url: str,
    tmp_path: Path,
    _alembic_template,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    upgrade_calls: list[str] = []
    monkeypatch.setattr(
        test_setup,
        "upgrade_database",
        lambda url, *, backup_dir: upgrade_calls.append(url),
    )
    database = SimpleNamespace(url=database_url, engine=SimpleNamespace(dispose=lambda: None))

    _prepare(database, _alembic_template.path, set(), tmp_path, [])

    assert upgrade_calls == [database_url]


def test_sqlite_urls_with_query_or_uri_are_not_copy_targets() -> None:
    assert test_setup._sqlite_file_path("sqlite:///:memory:") is None
    assert test_setup._sqlite_file_path("sqlite:///file:shared.db?mode=ro") is None
    assert test_setup._sqlite_file_path("postgresql://example/db") is None


def test_migration_specific_lane_still_runs_real_alembic(tmp_path: Path) -> None:
    database_path = tmp_path / "intentional-migration.db"
    result = upgrade_database(f"sqlite:///{database_path}", backup_dir=tmp_path / "backups")
    engine = create_engine(f"sqlite:///{database_path}")

    assert result.revision == CURRENT_SCHEMA_REVISION
    assert "alembic_version" in inspect(engine).get_table_names()
    engine.dispose()


def test_production_require_current_schema_remains_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.undo()
    database = Database(f"sqlite:///{tmp_path / 'unready.db'}")

    with pytest.raises(SchemaNotReady, match="QI-Crawler db-upgrade"):
        database.require_current_schema()
