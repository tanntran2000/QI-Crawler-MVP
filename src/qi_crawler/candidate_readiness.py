"""Three-stage evidence and controlled first-start gate for release candidates."""

from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import subprocess
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from alembic.config import Config
from alembic.script import ScriptDirectory

from alembic import command

from .candidate_data import managed_document_mapping_identity, validate_candidate_receipt
from .db import CURRENT_SCHEMA_REVISION
from .migrations import DatabaseUpgradeResult, backup_database


class CandidateReadinessError(RuntimeError):
    """A candidate evidence or first-start invariant failed closed."""


MIGRATION_RECEIPT_SCHEMA_VERSION = "qi-crawler-candidate-migration-v1"
ACCEPTANCE_SCHEMA_VERSION = "qi-crawler-pre-first-business-startup-v1"
MIGRATION_RECEIPT_NAME = "candidate_migration_receipt.json"
ACCEPTANCE_RECEIPT_NAME = "pre_start_acceptance.json"
V010_EXPECTED_SOURCE_REVISION = "0020_add_tender_operational_revision_events"
_SHA40 = re.compile(r"[0-9a-fA-F]{40}")
_SHA64 = re.compile(r"[0-9a-fA-F]{64}")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _read_json(path: Path, error: str) -> dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CandidateReadinessError(error) from exc
    if not isinstance(value, dict):
        raise CandidateReadinessError(error)
    return value


def _write_json_once(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8", newline="\n") as stream:
            json.dump(payload, stream, ensure_ascii=False, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError as exc:
        raise CandidateReadinessError(f"EVIDENCE_ALREADY_EXISTS: {path.name}") from exc


def _database_path(clone_receipt: dict[str, Any]) -> Path:
    try:
        return Path(str(clone_receipt["candidate_db_identity"]["path"])).resolve(strict=True)
    except (KeyError, OSError, TypeError) as exc:
        raise CandidateReadinessError("CLONE_RECEIPT_DATABASE_INVALID") from exc


def _schema_revision(database: Path) -> str:
    try:
        uri = database.as_uri() + "?mode=ro"
        with sqlite3.connect(uri, uri=True) as connection:
            connection.execute("PRAGMA query_only = ON")
            row = connection.execute("SELECT version_num FROM alembic_version").fetchone()
    except sqlite3.Error as exc:
        raise CandidateReadinessError("MIGRATED_SCHEMA_NOT_VERIFIED") from exc
    if row is None or not row[0]:
        raise CandidateReadinessError("MIGRATED_SCHEMA_NOT_VERIFIED")
    return str(row[0])


def _guard_candidate_boundary(
    candidate: Path,
    forbidden_roots: tuple[Path | str, ...],
) -> None:
    system_forbidden = [Path(r"D:\QI-Crawler").resolve(strict=False)]
    local_app_data = os.environ.get("LOCALAPPDATA")
    if local_app_data:
        system_forbidden.append(
            (Path(local_app_data) / "QI-Crawler").resolve(strict=False)
        )
    for raw_root in (*system_forbidden, *forbidden_roots):
        forbidden = Path(raw_root).resolve(strict=False)
        if (
            candidate == forbidden
            or candidate.is_relative_to(forbidden)
            or forbidden.is_relative_to(candidate)
        ):
            raise CandidateReadinessError("CANDIDATE_ROOT_OVERLAPS_WORKING_ROOT")


def _git(
    repo_root: Path,
    *args: str,
    binary: bool = False,
) -> str | bytes:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=repo_root,
            capture_output=True,
            text=not binary,
            check=False,
        )
    except OSError as exc:
        raise CandidateReadinessError("FROZEN_SOURCE_GIT_UNAVAILABLE") from exc
    if result.returncode != 0:
        stderr = result.stderr
        if isinstance(stderr, bytes):
            stderr = stderr.decode("utf-8", errors="replace")
        raise CandidateReadinessError(
            f"FROZEN_SOURCE_GIT_COMMAND_FAILED: {' '.join(args)}: {stderr.strip()}"
        )
    return result.stdout


def verify_frozen_source_checkout(
    repo_root: Path | str,
    expected_frozen_source_sha: str,
) -> dict[str, Any]:
    """Bind migration execution to one clean checkout at an exact Git commit."""
    if _SHA40.fullmatch(expected_frozen_source_sha) is None:
        raise CandidateReadinessError("EXPECTED_FROZEN_SOURCE_SHA_INVALID")
    supplied = Path(repo_root).resolve(strict=True)
    try:
        top_level = Path(
            str(_git(supplied, "rev-parse", "--show-toplevel")).strip()
        ).resolve(strict=True)
    except CandidateReadinessError as exc:
        raise CandidateReadinessError("FROZEN_SOURCE_NOT_GIT_WORKTREE") from exc
    if top_level != supplied:
        raise CandidateReadinessError("FROZEN_SOURCE_REPO_ROOT_MISMATCH")
    try:
        _git(supplied, "cat-file", "-e", f"{expected_frozen_source_sha}^{{commit}}")
    except CandidateReadinessError as exc:
        raise CandidateReadinessError("FROZEN_SOURCE_COMMIT_NOT_FOUND") from exc
    head = str(_git(supplied, "rev-parse", "HEAD")).strip().lower()
    if head != expected_frozen_source_sha.lower():
        raise CandidateReadinessError("FROZEN_SOURCE_HEAD_MISMATCH")
    tracked_status = str(
        _git(supplied, "status", "--porcelain", "--untracked-files=no")
    ).strip()
    if tracked_status:
        raise CandidateReadinessError("FROZEN_SOURCE_TRACKED_TREE_DIRTY")
    return {
        "source_repository_root": str(supplied),
        "source_git_sha": head,
        "tracked_tree_clean": True,
    }


def _frozen_alembic_config(repo_root: Path, database_url: str) -> Config:
    config_path = (repo_root / "alembic.ini").resolve(strict=True)
    script_root = (repo_root / "alembic").resolve(strict=True)
    config = Config(str(config_path))
    config.set_main_option("script_location", str(script_root))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def _migration_source_identity(
    *,
    repo_root: Path | str,
    from_revision: str,
    to_revision: str,
    source_git_sha: str,
) -> dict[str, Any]:
    if _SHA40.fullmatch(source_git_sha) is None:
        raise CandidateReadinessError("MIGRATION_SOURCE_SHA_INVALID")
    root = Path(repo_root).resolve(strict=True)
    scripts = ScriptDirectory.from_config(_frozen_alembic_config(root, "sqlite://"))
    try:
        revisions = list(scripts.iterate_revisions(to_revision, from_revision))
    except Exception as exc:
        raise CandidateReadinessError("MIGRATION_CHAIN_INVALID") from exc
    chain: list[dict[str, str]] = []
    for revision in reversed(revisions):
        path = Path(revision.path).resolve(strict=True)
        try:
            relative = path.relative_to(root).as_posix()
        except ValueError as exc:
            raise CandidateReadinessError("MIGRATION_SCRIPT_PATH_ESCAPE") from exc
        filesystem_bytes = path.read_bytes()
        try:
            git_bytes = _git(root, "show", f"{source_git_sha}:{relative}", binary=True)
            git_blob = str(
                _git(root, "rev-parse", f"{source_git_sha}:{relative}")
            ).strip()
        except CandidateReadinessError as exc:
            raise CandidateReadinessError("MIGRATION_SCRIPT_GIT_OBJECT_MISSING") from exc
        if git_bytes != filesystem_bytes:
            raise CandidateReadinessError("MIGRATION_SCRIPT_GIT_OBJECT_MISMATCH")
        down_revision = revision.down_revision
        if not isinstance(down_revision, str):
            raise CandidateReadinessError("MIGRATION_CHAIN_NOT_LINEAR")
        chain.append(
            {
                "revision": str(revision.revision),
                "down_revision": down_revision,
                "script_sha256": _sha256(path),
                "repo_relative_path": relative,
                "git_blob_identity": git_blob,
            }
        )
    expected_parent = from_revision
    for item in chain:
        if item["down_revision"] != expected_parent:
            raise CandidateReadinessError("MIGRATION_CHAIN_NOT_LINEAR")
        expected_parent = item["revision"]
    if expected_parent != to_revision:
        raise CandidateReadinessError("MIGRATION_CHAIN_INCOMPLETE")
    serialized = json.dumps(chain, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return {
        "source_git_sha": source_git_sha.lower(),
        "source_repository_root": str(root),
        "from_revision": from_revision,
        "to_revision": to_revision,
        "chain": chain,
        "chain_sha256": hashlib.sha256(serialized).hexdigest(),
    }


def _upgrade_from_frozen_source(
    database_url: str,
    *,
    repo_root: Path,
    backup_dir: Path,
) -> DatabaseUpgradeResult:
    backup_path = backup_database(database_url, backup_dir)
    command.upgrade(_frozen_alembic_config(repo_root, database_url), "head")
    revision = _schema_revision(Path(database_url.removeprefix("sqlite:///")))
    return DatabaseUpgradeResult(
        revision=revision,
        backup_path=backup_path,
        adopted_legacy_database=False,
    )


def migrate_candidate_data(
    destination_root: Path | str,
    *,
    source_repository_root: Path | str,
    expected_frozen_source_sha: str,
    expected_revision: str = CURRENT_SCHEMA_REVISION,
    forbidden_roots: tuple[Path | str, ...] = (),
) -> dict[str, Any]:
    """Migrate one validated isolated clone and emit immutable Stage-2 evidence."""
    destination = Path(destination_root).resolve(strict=True)
    _guard_candidate_boundary(destination, forbidden_roots)
    receipt_path = destination / MIGRATION_RECEIPT_NAME
    if receipt_path.exists():
        raise CandidateReadinessError("MIGRATION_RECEIPT_ALREADY_EXISTS")
    clone_path = destination / "candidate_data_receipt.json"
    clone_receipt = validate_candidate_receipt(destination)
    database = _database_path(clone_receipt)
    if not database.is_relative_to(destination):
        raise CandidateReadinessError("CANDIDATE_DB_PATH_ESCAPE")
    input_db_sha = _sha256(database)
    from_revision = _schema_revision(database)
    if from_revision != V010_EXPECTED_SOURCE_REVISION:
        raise CandidateReadinessError("MIGRATION_INPUT_SCHEMA_UNEXPECTED")
    database_url = f"sqlite:///{database.as_posix()}"
    source_checkout = verify_frozen_source_checkout(
        source_repository_root,
        expected_frozen_source_sha,
    )
    source_root = Path(source_checkout["source_repository_root"])
    source_identity = _migration_source_identity(
        repo_root=source_root,
        from_revision=from_revision,
        to_revision=expected_revision,
        source_git_sha=expected_frozen_source_sha,
    )
    common: dict[str, Any] = {
        "receipt_schema_version": MIGRATION_RECEIPT_SCHEMA_VERSION,
        "input_clone_receipt_sha256": _sha256(clone_path),
        "input_db_sha256": input_db_sha,
        "from_revision": from_revision,
        "to_revision": expected_revision,
        "migration_source_identity": source_identity,
        "managed_document_mapping_digest": clone_receipt[
            "managed_document_mapping_digest"
        ],
        "document_count": clone_receipt["document_count"],
        "created_at": datetime.now(UTC).isoformat(),
    }
    try:
        result = _upgrade_from_frozen_source(
            database_url,
            repo_root=source_root,
            backup_dir=Path(str(clone_receipt["candidate_backup_root"])),
        )
        actual_revision = _schema_revision(database)
        if result.revision != expected_revision or actual_revision != expected_revision:
            raise CandidateReadinessError("MIGRATED_SCHEMA_MISMATCH")
        current_mapping = managed_document_mapping_identity(destination, database)
        if current_mapping != {
            "document_count": common["document_count"],
            "managed_document_mapping_digest": common[
                "managed_document_mapping_digest"
            ],
        }:
            raise CandidateReadinessError("MANAGED_DOCUMENT_MAPPING_CHANGED_BY_MIGRATION")
        receipt = {
            **common,
            "migration_result": "PASS",
            "output_db_sha256": _sha256(database),
            "actual_output_revision": actual_revision,
            "backup_path": str(result.backup_path.resolve()) if result.backup_path else None,
        }
        _write_json_once(receipt_path, receipt)
        return receipt
    except Exception as exc:
        failed = {
            **common,
            "migration_result": "FAIL",
            "error": str(exc),
            "output_db_sha256": _sha256(database) if database.is_file() else None,
        }
        _write_json_once(receipt_path, failed)
        raise


def validate_migration_receipt(
    destination_root: Path | str,
    *,
    expected_receipt_sha256: str | None = None,
    expected_source_git_sha: str | None = None,
) -> dict[str, Any]:
    destination = Path(destination_root).resolve(strict=True)
    receipt_path = destination / MIGRATION_RECEIPT_NAME
    if expected_receipt_sha256 is not None and (
        not receipt_path.is_file()
        or _sha256(receipt_path) != expected_receipt_sha256.lower()
    ):
        raise CandidateReadinessError("MIGRATION_RECEIPT_IDENTITY_MISMATCH")
    receipt = _read_json(receipt_path, "MIGRATION_RECEIPT_INVALID")
    if receipt.get("receipt_schema_version") != MIGRATION_RECEIPT_SCHEMA_VERSION:
        raise CandidateReadinessError("MIGRATION_RECEIPT_SCHEMA_UNSUPPORTED")
    if receipt.get("migration_result") != "PASS":
        raise CandidateReadinessError("MIGRATION_RECEIPT_NOT_PASS")
    source_identity = receipt.get("migration_source_identity") or {}
    if expected_source_git_sha is not None and (
        str(source_identity.get("source_git_sha", "")).lower()
        != expected_source_git_sha.lower()
    ):
        raise CandidateReadinessError("MIGRATION_SOURCE_SHA_MISMATCH")
    clone_path = destination / "candidate_data_receipt.json"
    if not clone_path.is_file():
        raise CandidateReadinessError("CLONE_RECEIPT_INVALID")
    if _sha256(clone_path) != receipt.get("input_clone_receipt_sha256"):
        raise CandidateReadinessError("CLONE_RECEIPT_LINEAGE_MISMATCH")
    clone_receipt = validate_candidate_receipt(
        destination,
        require_pre_migration_db_identity=False,
    )
    if receipt.get("input_db_sha256") != (
        clone_receipt.get("candidate_db_identity") or {}
    ).get("sha256"):
        raise CandidateReadinessError("MIGRATION_INPUT_DB_LINEAGE_MISMATCH")
    if receipt.get("from_revision") != clone_receipt.get("source_schema"):
        raise CandidateReadinessError("MIGRATION_INPUT_SCHEMA_LINEAGE_MISMATCH")
    if receipt.get("to_revision") != CURRENT_SCHEMA_REVISION:
        raise CandidateReadinessError("MIGRATED_SCHEMA_MISMATCH")
    database = _database_path(clone_receipt)
    if _sha256(database) != receipt.get("output_db_sha256"):
        raise CandidateReadinessError("MIGRATED_DB_IDENTITY_MISMATCH")
    actual_revision = _schema_revision(database)
    if (
        actual_revision != receipt.get("to_revision")
        or receipt.get("actual_output_revision") != receipt.get("to_revision")
    ):
        raise CandidateReadinessError("MIGRATED_SCHEMA_MISMATCH")
    current_mapping = managed_document_mapping_identity(destination, database)
    expected_mapping = {
        "document_count": receipt.get("document_count"),
        "managed_document_mapping_digest": receipt.get(
            "managed_document_mapping_digest"
        ),
    }
    if current_mapping != expected_mapping:
        raise CandidateReadinessError("MANAGED_DOCUMENT_MAPPING_MISMATCH")
    if expected_mapping != {
        "document_count": clone_receipt.get("document_count"),
        "managed_document_mapping_digest": clone_receipt.get(
            "managed_document_mapping_digest"
        ),
    }:
        raise CandidateReadinessError("MIGRATION_MAPPING_LINEAGE_MISMATCH")
    expected_source_identity = _migration_source_identity(
        repo_root=str(source_identity.get("source_repository_root", "")),
        from_revision=str(receipt.get("from_revision", "")),
        to_revision=str(receipt.get("to_revision", "")),
        source_git_sha=str(source_identity.get("source_git_sha", "")),
    )
    if source_identity != expected_source_identity:
        raise CandidateReadinessError("MIGRATION_SOURCE_IDENTITY_MISMATCH")
    return receipt


def _parse_build_info(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as exc:
        raise CandidateReadinessError("BUILD_INFO_INVALID") from exc
    fields: dict[str, str] = {}
    for line in lines:
        if not line or "=" not in line:
            raise CandidateReadinessError("BUILD_INFO_INVALID")
        key, value = line.split("=", 1)
        if not key or not value or key in fields:
            raise CandidateReadinessError("BUILD_INFO_INVALID")
        fields[key] = value
    return fields


def _validate_build_identity(
    candidate: Path,
    *,
    expected_frozen_source_sha: str,
    expected_version: str,
) -> dict[str, Any]:
    if _SHA40.fullmatch(expected_frozen_source_sha) is None:
        raise CandidateReadinessError("EXPECTED_FROZEN_SOURCE_SHA_INVALID")
    bundle = candidate / "app" / "QI-Crawler"
    manifest = _read_json(bundle / "release_manifest.json", "RELEASE_MANIFEST_INVALID")
    artifact = _read_json(
        candidate / "control" / "release_artifact_receipt.json",
        "ARTIFACT_RECEIPT_INVALID",
    )
    build_info = _parse_build_info(bundle / "BUILD_INFO.txt")
    required_manifest = {
        "metadata_schema_version",
        "product",
        "version",
        "source_git_sha",
        "source_branch",
        "build_timestamp_utc",
        "alembic_head",
        "release_channel",
        "portable_exe_sha256",
    }
    if set(manifest) != required_manifest or set(build_info) != required_manifest:
        raise CandidateReadinessError("BUILD_IDENTITY_FIELDS_INVALID")
    if manifest.get("metadata_schema_version") != "qi-crawler-installed-release-v1":
        raise CandidateReadinessError("BUILD_IDENTITY_SCHEMA_UNSUPPORTED")
    if artifact.get("receipt_schema_version") != "qi-crawler-release-artifact-v1":
        raise CandidateReadinessError("ARTIFACT_RECEIPT_SCHEMA_UNSUPPORTED")
    if manifest.get("product") != "QI-Crawler" or manifest.get("version") != expected_version:
        raise CandidateReadinessError("BUILD_PRODUCT_VERSION_MISMATCH")
    for key in required_manifest:
        if str(build_info.get(key, "")) != str(manifest.get(key, "")):
            raise CandidateReadinessError("BUILD_INFO_MANIFEST_MISMATCH")
    shared_artifact_fields = required_manifest - {"metadata_schema_version", "release_channel"}
    for key in shared_artifact_fields:
        if str(artifact.get(key, "")) != str(manifest.get(key, "")):
            raise CandidateReadinessError("MANIFEST_ARTIFACT_MISMATCH")
    source_values = {
        str(manifest.get("source_git_sha", "")).lower(),
        str(build_info.get("source_git_sha", "")).lower(),
        str(artifact.get("source_git_sha", "")).lower(),
    }
    if source_values != {expected_frozen_source_sha.lower()}:
        raise CandidateReadinessError("FROZEN_SOURCE_SHA_MISMATCH")
    if not str(manifest.get("source_branch", "")).strip():
        raise CandidateReadinessError("BUILD_SOURCE_BRANCH_INVALID")
    if manifest.get("alembic_head") != CURRENT_SCHEMA_REVISION:
        raise CandidateReadinessError("BUILD_SCHEMA_IDENTITY_MISMATCH")
    expected_exe_hash = str(manifest.get("portable_exe_sha256", ""))
    executable = bundle / "QI-Crawler.exe"
    if _SHA64.fullmatch(expected_exe_hash) is None or not executable.is_file():
        raise CandidateReadinessError("PORTABLE_EXE_IDENTITY_INVALID")
    if _sha256(executable).upper() != expected_exe_hash.upper():
        raise CandidateReadinessError("PORTABLE_EXE_SHA_MISMATCH")
    return {
        "bundle_root": str(bundle.resolve()),
        "executable": str(executable.resolve()),
        "source_git_sha": expected_frozen_source_sha.lower(),
        "source_branch": str(manifest["source_branch"]),
        "version": expected_version,
        "portable_exe_sha256": expected_exe_hash.lower(),
        "release_manifest_sha256": _sha256(bundle / "release_manifest.json"),
        "artifact_receipt_sha256": _sha256(
            candidate / "control" / "release_artifact_receipt.json"
        ),
    }


def accept_pre_first_business_startup(
    candidate_root: Path | str,
    data_root: Path | str,
    *,
    expected_frozen_source_sha: str,
    expected_migration_receipt_sha256: str,
    expected_version: str,
    forbidden_roots: tuple[Path | str, ...] = (),
) -> dict[str, Any]:
    """Create Stage-3 evidence only after every first-business-start invariant passes."""
    candidate = Path(candidate_root).resolve(strict=True)
    data = Path(data_root).resolve(strict=True)
    _guard_candidate_boundary(candidate, forbidden_roots)
    if data != (candidate / "data-root").resolve(strict=True):
        raise CandidateReadinessError("CANDIDATE_DATA_ROOT_MISMATCH")
    build = _validate_build_identity(
        candidate,
        expected_frozen_source_sha=expected_frozen_source_sha,
        expected_version=expected_version,
    )
    migration = validate_migration_receipt(
        data,
        expected_receipt_sha256=expected_migration_receipt_sha256,
        expected_source_git_sha=expected_frozen_source_sha,
    )
    migration_source = migration.get("migration_source_identity") or {}
    if (
        str(migration_source.get("source_git_sha", "")).lower()
        != expected_frozen_source_sha.lower()
    ):
        raise CandidateReadinessError("MIGRATION_SOURCE_SHA_MISMATCH")
    database = _database_path(
        validate_candidate_receipt(data, require_pre_migration_db_identity=False)
    )
    if migration.get("to_revision") != CURRENT_SCHEMA_REVISION:
        raise CandidateReadinessError("MIGRATED_SCHEMA_MISMATCH")
    acceptance = {
        "acceptance_schema_version": ACCEPTANCE_SCHEMA_VERSION,
        "status": "ACCEPTED",
        "candidate_root": str(candidate),
        "candidate_data_root": str(data),
        "candidate_config_path": str((data / "config.yaml").resolve(strict=True)),
        **build,
        "clone_receipt_sha256": str(migration["input_clone_receipt_sha256"]),
        "migration_receipt_sha256": expected_migration_receipt_sha256.lower(),
        "database_sha256": _sha256(database),
        "schema_revision": _schema_revision(database),
        "managed_document_mapping_digest": migration[
            "managed_document_mapping_digest"
        ],
        "document_count": migration["document_count"],
        "created_at": datetime.now(UTC).isoformat(),
    }
    _write_json_once(candidate / "control" / ACCEPTANCE_RECEIPT_NAME, acceptance)
    return acceptance


def launch_candidate_after_acceptance(
    candidate_root: Path | str,
    data_root: Path | str,
    *,
    expected_frozen_source_sha: str,
    expected_migration_receipt_sha256: str,
    expected_version: str,
    forbidden_roots: tuple[Path | str, ...] = (),
    launcher: Callable[..., Any] = subprocess.Popen,
) -> Any:
    """Run the candidate's one-time controlled first start after Stage 3 passes."""
    acceptance = accept_pre_first_business_startup(
        candidate_root,
        data_root,
        expected_frozen_source_sha=expected_frozen_source_sha,
        expected_migration_receipt_sha256=expected_migration_receipt_sha256,
        expected_version=expected_version,
        forbidden_roots=forbidden_roots,
    )
    environment = os.environ.copy()
    environment["QI_CRAWLER_DATA_DIR"] = str(Path(data_root).resolve(strict=True))
    environment["QI_CRAWLER_CONFIG_PATH"] = str(
        (Path(data_root) / "config.yaml").resolve(strict=True)
    )
    executable = Path(str(acceptance["executable"]))
    return launcher([str(executable)], cwd=str(executable.parent), env=environment)
