"""Windows standalone runtime paths and first-run preparation."""

from __future__ import annotations

import logging
import os
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


class StandaloneResourceError(RuntimeError):
    """A required packaged resource is unavailable or damaged."""


@dataclass(frozen=True)
class StandalonePaths:
    resource_root: Path
    user_root: Path
    data_dir: Path
    database_dir: Path
    reports_dir: Path
    logs_dir: Path
    sessions_dir: Path
    documents_dir: Path
    config_path: Path
    database_path: Path
    browser_dir: Path


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def resource_root() -> Path:
    bundled_root = getattr(sys, "_MEIPASS", None)
    if bundled_root:
        return Path(bundled_root).resolve()
    return Path(__file__).resolve().parents[2]


def resource_path(*parts: str) -> Path:
    return resource_root().joinpath(*parts)


def default_user_root() -> Path:
    override = os.getenv("QI_CRAWLER_DATA_DIR")
    if override:
        return Path(override).expanduser().resolve()
    local_app_data = os.getenv("LOCALAPPDATA")
    if not local_app_data:
        raise StandaloneResourceError(
            "Khong xac dinh duoc thu muc LOCALAPPDATA cua Windows."
        )
    return (Path(local_app_data) / "QI-Crawler").resolve()


def standalone_paths(user_root: Path | None = None) -> StandalonePaths:
    root = (user_root or default_user_root()).resolve()
    data_dir = root / "data"
    return StandalonePaths(
        resource_root=resource_root(),
        user_root=root,
        data_dir=data_dir,
        database_dir=data_dir / "database",
        reports_dir=data_dir / "reports",
        logs_dir=root / "logs",
        sessions_dir=data_dir / "sessions",
        documents_dir=root / "documents",
        config_path=root / "config.yaml",
        database_path=data_dir / "database" / "egp.db",
        browser_dir=resource_path("browsers"),
    )


def _write_default_config(paths: StandalonePaths) -> None:
    source = resource_path("config.example.yaml")
    if not source.is_file():
        raise StandaloneResourceError(
            "Thieu config.example.yaml trong bo cai QI-Crawler. Hay cai dat lai ung dung."
        )
    raw = yaml.safe_load(source.read_text(encoding="utf-8")) or {}
    storage = raw.setdefault("storage", {})
    storage.update(
        {
            "database_url": f"sqlite:///{paths.database_path.as_posix()}",
            "download_dir": str(paths.data_dir / "downloads"),
            "discovery_dir": str(paths.data_dir / "discovery"),
            "raw_dir": str(paths.data_dir / "raw"),
            "rejects_dir": str(paths.data_dir / "rejects"),
            "report_dir": str(paths.reports_dir),
        }
    )
    paths.config_path.write_text(
        yaml.safe_dump(raw, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def _copy_mutable_default(name: str, destination: Path) -> None:
    if destination.exists():
        return
    source = resource_path(name)
    if not source.is_file():
        raise StandaloneResourceError(
            f"Thieu tai nguyen {name} trong bo cai QI-Crawler. Hay cai dat lai ung dung."
        )
    shutil.copy2(source, destination)


def prepare_standalone_runtime(
    user_root: Path | None = None,
    *,
    require_browser: bool = True,
) -> StandalonePaths:
    """Prepare durable user directories without overwriting existing user data."""
    paths = standalone_paths(user_root)
    for directory in (
        paths.user_root,
        paths.data_dir,
        paths.database_dir,
        paths.reports_dir,
        paths.logs_dir,
        paths.sessions_dir,
        paths.documents_dir,
        paths.data_dir / "downloads",
        paths.data_dir / "discovery",
        paths.data_dir / "raw",
        paths.data_dir / "rejects",
        paths.data_dir / "sources",
        paths.data_dir / "backups",
    ):
        directory.mkdir(parents=True, exist_ok=True)

    if not paths.config_path.exists():
        _write_default_config(paths)
    _copy_mutable_default("keyword-groups.yaml", paths.user_root / "keyword-groups.yaml")

    template = resource_path("templates", "TBMT_template_v1.xlsx")
    migrations = resource_path("alembic", "versions")
    if not template.is_file() or not migrations.is_dir():
        raise StandaloneResourceError(
            "Bo cai thieu template Excel hoac migration database. Hay cai dat lai QI-Crawler."
        )
    if require_browser and not paths.browser_dir.is_dir():
        raise StandaloneResourceError(
            "Khong tim thay Chromium cua QI-Crawler. Hay dung lai bo cai day du; "
            "ung dung se khong tu tai trinh duyet."
        )

    if paths.browser_dir.is_dir():
        os.environ["PLAYWRIGHT_BROWSERS_PATH"] = str(paths.browser_dir)
    os.environ["QI_CRAWLER_CONFIG_PATH"] = str(paths.config_path)
    os.chdir(paths.user_root)
    return paths


def configure_standalone_file_logging(log_file: Path, level: str = "INFO") -> None:
    log_file.parent.mkdir(parents=True, exist_ok=True)
    handler = logging.FileHandler(log_file, encoding="utf-8")
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s")
    )
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level.upper())
