from __future__ import annotations

import shutil
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

import pytest
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

from qi_crawler.db import Database
from qi_crawler.migrations import upgrade_database

_ORIGINAL_REQUIRE_CURRENT_SCHEMA = Database.require_current_schema


@dataclass(frozen=True)
class _AlembicTemplate:
    path: Path
    upgrade_count: int


def _sqlite_file_path(database_url: str) -> Path | None:
    try:
        url = make_url(database_url)
    except ArgumentError:
        return None
    if (
        not url.drivername.startswith("sqlite")
        or not url.database
        or url.database == ":memory:"
        or url.query
    ):
        return None
    database = str(url.database)
    if database.startswith("file:"):
        return None
    return Path(database).expanduser()


def _sqlite_sidecar_exists(path: Path) -> bool:
    return Path(f"{path}-wal").exists() or Path(f"{path}-shm").exists()


def _is_fresh_sqlite_target(path: Path) -> bool:
    return not path.exists() and not _sqlite_sidecar_exists(path)


def _prepare_database(
    database: Database,
    *,
    template_path: Path,
    prepared_paths: set[Path],
    backup_dir: Path,
    require_current_schema: Callable[[Database], None],
) -> None:
    path = _sqlite_file_path(database.url)
    key = path.resolve(strict=False) if path is not None else None
    if key is not None and key in prepared_paths:
        require_current_schema(database)
        return

    database.engine.dispose()
    if path is not None and _is_fresh_sqlite_target(path):
        shutil.copy2(template_path, path)
    else:
        upgrade_database(database.url, backup_dir=backup_dir)

    require_current_schema(database)
    if key is not None:
        prepared_paths.add(key)


@pytest.fixture(scope="session")
def _alembic_template(tmp_path_factory: pytest.TempPathFactory) -> _AlembicTemplate:
    root = tmp_path_factory.mktemp("alembic-template")
    path = root / "template.db"
    upgrade_database(f"sqlite:///{path}", backup_dir=root / "backups")
    return _AlembicTemplate(path=path, upgrade_count=1)


@pytest.fixture(autouse=True)
def _prepare_database_for_tests(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    _alembic_template: _AlembicTemplate,
) -> None:
    """Keep test setup explicit while production only verifies Alembic state."""
    prepared_paths: set[Path] = set()

    def prepare(database: Database) -> None:
        _prepare_database(
            database,
            template_path=_alembic_template.path,
            prepared_paths=prepared_paths,
            backup_dir=tmp_path / "migration-backups",
            require_current_schema=_ORIGINAL_REQUIRE_CURRENT_SCHEMA,
        )

    monkeypatch.setattr(Database, "require_current_schema", prepare)
    # Older tests use this name as a fixture helper.  Production has no such method.
    monkeypatch.setattr(Database, "create_all", prepare, raising=False)
