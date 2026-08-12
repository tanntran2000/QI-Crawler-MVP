"""Safe, explicit Alembic upgrades for databases created before Alembic.

Production runtime verifies schema readiness and directs operators to
``QI-Crawler db-upgrade``; it never creates or alters tables implicitly.
"""

from __future__ import annotations

import shutil
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from alembic.config import Config
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.engine import make_url

from alembic import command

from .standalone import resource_root

PROJECT_ROOT = resource_root()
ALEMBIC_CONFIG = PROJECT_ROOT / "alembic.ini"
LEGACY_CHECKPOINT_REVISION = "0001_add_crawl_tasks"


@dataclass(frozen=True)
class DatabaseUpgradeResult:
    revision: str
    backup_path: Path | None
    adopted_legacy_database: bool


def _sqlite_database_path(database_url: str) -> Path | None:
    url = make_url(database_url)
    if not url.drivername.startswith("sqlite") or not url.database or url.database == ":memory:":
        return None
    return Path(url.database)


def _alembic_config(database_url: str) -> Config:
    config = Config(str(ALEMBIC_CONFIG))
    config.set_main_option("script_location", str(PROJECT_ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def _backup_sqlite_database(path: Path, backup_dir: Path) -> Path:
    backup_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    destination = backup_dir / (
        f"{path.stem}_before_alembic_{timestamp}_{uuid4().hex[:8]}{path.suffix}"
    )
    shutil.copy2(path, destination)
    return destination


def backup_database(database_url: str, backup_dir: Path = Path("data/backups")) -> Path | None:
    """Create a local backup before an explicit maintenance operation."""
    sqlite_path = _sqlite_database_path(database_url)
    if sqlite_path is None or not sqlite_path.exists():
        return None
    return _backup_sqlite_database(sqlite_path, backup_dir)


def _legacy_database_needs_adoption(database_url: str) -> bool:
    engine = create_engine(database_url)
    try:
        tables = set(inspect(engine).get_table_names())
        if "alembic_version" in tables:
            return False
        if "crawl_tasks" not in tables:
            return False
        required = {"crawl_runs", "notices"}
        if not required.issubset(tables):
            raise ValueError(
                "Database co crawl_tasks nhung khong du crawl_runs/notices; "
                "tu choi stamp de tranh ghi nhan sai lich su migration."
            )
        return True
    finally:
        engine.dispose()


def upgrade_database(database_url: str, backup_dir: Path = Path("data/backups")) -> DatabaseUpgradeResult:
    """Backup, adopt a recognised pre-Alembic SQLite DB, then upgrade to head."""
    backup_path = backup_database(database_url, backup_dir)

    config = _alembic_config(database_url)
    adopted = _legacy_database_needs_adoption(database_url)
    if adopted:
        command.stamp(config, LEGACY_CHECKPOINT_REVISION)
    command.upgrade(config, "head")

    engine = create_engine(database_url)
    try:
        with engine.connect() as connection:
            revision = connection.scalar(text("SELECT version_num FROM alembic_version"))
    finally:
        engine.dispose()
    if not revision:
        raise RuntimeError("Alembic upgrade khong ghi nhan duoc revision hien tai")
    return DatabaseUpgradeResult(
        revision=revision,
        backup_path=backup_path,
        adopted_legacy_database=adopted,
    )
