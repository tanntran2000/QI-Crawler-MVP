"""Windows standalone runtime paths and first-run preparation."""

from __future__ import annotations

import json
import logging
import os
import shutil
import sys
from collections.abc import MutableMapping
from dataclasses import dataclass
from pathlib import Path

import yaml
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

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
    if is_frozen():
        sidecar_root = Path(sys.executable).resolve().parent / "runtime"
        if sidecar_root.is_dir():
            return sidecar_root
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
        documents_dir=data_dir / "documents",
        config_path=root / "config.yaml",
        database_path=data_dir / "database" / "egp.db",
        browser_dir=resource_path("browsers"),
    )


def candidate_database_url(paths: StandalonePaths) -> str:
    """Return the one canonical database URL for an isolated candidate root."""
    return f"sqlite:///{paths.database_path.resolve(strict=False).as_posix()}"


def bind_candidate_runtime_environment(
    paths: StandalonePaths,
    environment: MutableMapping[str, str] | None = None,
) -> None:
    """Override every storage authority used by candidate configuration loading."""
    target = os.environ if environment is None else environment
    target["QI_CRAWLER_DATA_DIR"] = str(paths.user_root.resolve(strict=False))
    target["QI_CRAWLER_CONFIG_PATH"] = str(paths.config_path.resolve(strict=False))
    target["QI_CRAWLER_DATABASE_URL"] = candidate_database_url(paths)


def validate_candidate_database_target(
    database_url: str,
    paths: StandalonePaths,
) -> Path:
    """Reject an effective database target outside the authorized isolated root."""
    try:
        parsed = make_url(database_url)
        database = parsed.database
        if (
            parsed.get_backend_name() != "sqlite"
            or not database
            or database == ":memory:"
            or parsed.username is not None
            or parsed.password is not None
            or parsed.host is not None
            or parsed.port is not None
            or parsed.query
        ):
            raise ValueError("unsupported candidate database URL")
        actual = Path(database).expanduser().resolve(strict=False)
    except (ArgumentError, TypeError, ValueError) as exc:
        raise StandaloneResourceError("CANDIDATE_EFFECTIVE_DATABASE_ESCAPE") from exc
    expected = paths.database_path.resolve(strict=False)
    root = paths.user_root.resolve(strict=False)
    if actual != expected or not actual.is_relative_to(root):
        raise StandaloneResourceError("CANDIDATE_EFFECTIVE_DATABASE_ESCAPE")
    return actual


def _governed_candidate_root(executable: Path) -> Path | None:
    bundle = executable.parent
    if bundle.name != "QI-Crawler" or bundle.parent.name != "app":
        return None
    return bundle.parent.parent.resolve(strict=False)


def _candidate_release_manifest(executable: Path) -> dict[str, object] | None:
    manifest_path = executable.parent / "release_manifest.json"
    candidate_root = _governed_candidate_root(executable)
    if not manifest_path.is_file():
        if candidate_root is not None:
            raise StandaloneResourceError("CANDIDATE_RELEASE_MANIFEST_REQUIRED")
        return None
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise StandaloneResourceError("CANDIDATE_RELEASE_MANIFEST_INVALID") from exc
    if not isinstance(manifest, dict):
        raise StandaloneResourceError("CANDIDATE_RELEASE_MANIFEST_INVALID")
    return manifest


def _authorize_isolated_candidate_smoke(
    candidate_root: Path | None,
) -> None:
    raw_root = os.environ.get("QI_CRAWLER_DATA_DIR")
    if not raw_root:
        raise StandaloneResourceError("CANDIDATE_SMOKE_DATA_ROOT_REQUIRED")
    isolated = Path(raw_root).expanduser().resolve(strict=False)
    forbidden = [Path(r"D:\QI-Crawler").resolve(strict=False)]
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        forbidden.append((Path(local_app_data) / "QI-Crawler").resolve(strict=False))
    if candidate_root is not None:
        forbidden.append(candidate_root)
    for root in forbidden:
        if (
            isolated == root
            or isolated.is_relative_to(root)
            or root.is_relative_to(isolated)
        ):
            raise StandaloneResourceError("CANDIDATE_ROOT_OVERLAPS_WORKING_ROOT")
    bind_candidate_runtime_environment(standalone_paths(isolated))


def authorize_frozen_runtime(arguments: list[str]) -> str:
    """Authorize candidate storage before any standalone path is prepared."""
    if not is_frozen():
        return "NOT_FROZEN"
    executable = Path(sys.executable).resolve(strict=True)
    manifest = _candidate_release_manifest(executable)
    candidate_root = _governed_candidate_root(executable)
    if manifest is None:
        return "NON_CANDIDATE"
    if manifest.get("release_channel") != "INTERNAL_CANDIDATE":
        if candidate_root is not None:
            raise StandaloneResourceError("CANDIDATE_RELEASE_CHANNEL_INVALID")
        return "NON_CANDIDATE"
    smoke = any(
        option in arguments
        for option in ("--smoke-test", "--smoke-test-network", "--smoke-test-documents")
    )
    if smoke:
        _authorize_isolated_candidate_smoke(candidate_root)
        return "ISOLATED_CANDIDATE_SMOKE"
    if candidate_root is None:
        raise StandaloneResourceError("CANDIDATE_LAYOUT_INVALID")
    from .candidate_readiness import validate_existing_acceptance

    acceptance = validate_existing_acceptance(candidate_root)
    data_root = Path(str(acceptance["candidate_data_root"])).resolve(strict=True)
    config_path = Path(str(acceptance["candidate_config_path"])).resolve(strict=True)
    paths = standalone_paths(data_root)
    if paths.config_path.resolve(strict=True) != config_path:
        raise StandaloneResourceError("ACCEPTANCE_CONFIG_PATH_MISMATCH")
    bind_candidate_runtime_environment(paths)
    return "ACCEPTED_CANDIDATE"


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
            "database_url": candidate_database_url(paths),
            "document_dir": str(paths.documents_dir),
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


def _rebase_isolated_storage(paths: StandalonePaths) -> None:
    """Keep persisted managed storage paths inside an explicit data override."""
    raw = yaml.safe_load(paths.config_path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise StandaloneResourceError("Cau hinh QI-Crawler khong hop le cho che do co lap.")
    storage = raw.setdefault("storage", {})
    if not isinstance(storage, dict):
        raise StandaloneResourceError("Cau hinh storage khong hop le cho che do co lap.")
    configured_database = storage.get("database_url")
    if configured_database and not str(configured_database).lower().startswith("sqlite:"):
        raise StandaloneResourceError(
            "Khong the co lap database khong phai SQLite vao QI_CRAWLER_DATA_DIR."
        )
    desired = {
        "database_url": candidate_database_url(paths),
        "document_dir": str(paths.documents_dir),
        "download_dir": str(paths.data_dir / "downloads"),
        "discovery_dir": str(paths.data_dir / "discovery"),
        "raw_dir": str(paths.data_dir / "raw"),
        "rejects_dir": str(paths.data_dir / "rejects"),
        "report_dir": str(paths.reports_dir),
    }
    if any(storage.get(key) != value for key, value in desired.items()):
        storage.update(desired)
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
    if os.getenv("QI_CRAWLER_DATA_DIR"):
        _rebase_isolated_storage(paths)
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
