from __future__ import annotations

import hashlib
import json
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest
import yaml
from alembic.config import Config

from alembic import command
from qi_crawler import candidate_data
from qi_crawler.db import CURRENT_SCHEMA_REVISION

ROOT = Path(__file__).parent.parent
SOURCE_SHA = "1" * 40
VERSION = "0.10.0"


def _git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=repo,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    return result.stdout.strip()


def _frozen_source_repo(
    tmp_path: Path, *, full_package: bool = False
) -> tuple[Path, str]:
    repo = tmp_path / "frozen-source"
    repo.mkdir()
    shutil.copytree(ROOT / "alembic", repo / "alembic")
    shutil.copy2(ROOT / "alembic.ini", repo / "alembic.ini")
    if full_package:
        shutil.copytree(
            ROOT / "src" / "qi_crawler",
            repo / "src" / "qi_crawler",
            ignore=shutil.ignore_patterns("__pycache__", "*.pyc"),
        )
    else:
        for relative in (
            Path("src/qi_crawler/candidate_readiness.py"),
            Path("src/qi_crawler/candidate_data.py"),
            Path("src/qi_crawler/migrations.py"),
            Path("src/qi_crawler/db.py"),
        ):
            target = repo / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(ROOT / relative, target)
    _git(repo, "init")
    _git(repo, "config", "core.autocrlf", "false")
    _git(repo, "config", "user.email", "candidate-readiness@example.invalid")
    _git(repo, "config", "user.name", "Candidate Readiness Test")
    _git(repo, "add", ".")
    _git(repo, "commit", "-m", "frozen source")
    return repo, _git(repo, "rev-parse", "HEAD")


def _loaded_modules_from(repo: Path) -> dict[str, object]:
    return {
        name: SimpleNamespace(__file__=repo / relative)
        for name, relative in {
            "candidate_readiness": "src/qi_crawler/candidate_readiness.py",
            "candidate_data": "src/qi_crawler/candidate_data.py",
            "migrations": "src/qi_crawler/migrations.py",
            "db": "src/qi_crawler/db.py",
        }.items()
    }


def test_frozen_execution_code_rejects_foreign_loaded_checkout(tmp_path: Path) -> None:
    from qi_crawler import candidate_readiness

    repo, head = _frozen_source_repo(tmp_path)

    with pytest.raises(Exception, match="FROZEN_EXECUTION_MODULE_PATH_MISMATCH"):
        candidate_readiness.verify_frozen_execution_code(repo, head)


def test_frozen_execution_code_rejects_same_path_wrong_bytes(tmp_path: Path) -> None:
    from qi_crawler import candidate_readiness

    repo, head = _frozen_source_repo(tmp_path)
    target = repo / "src" / "qi_crawler" / "candidate_readiness.py"
    target.write_text(target.read_text(encoding="utf-8") + "\n# mismatch\n", encoding="utf-8")

    with mock.patch.object(
        candidate_readiness,
        "_loaded_execution_modules",
        return_value=_loaded_modules_from(repo),
    ), pytest.raises(
        Exception, match="FROZEN_EXECUTION_MODULE_GIT_OBJECT_MISMATCH"
    ):
        candidate_readiness.verify_frozen_execution_code(repo, head)


def test_frozen_execution_code_rejects_alembic_config_mismatch(tmp_path: Path) -> None:
    from qi_crawler import candidate_readiness

    repo, head = _frozen_source_repo(tmp_path)
    target = repo / "alembic" / "env.py"
    target.write_text(target.read_text(encoding="utf-8") + "\n# mismatch\n", encoding="utf-8")

    with mock.patch.object(
        candidate_readiness,
        "_loaded_execution_modules",
        return_value=_loaded_modules_from(repo),
    ), pytest.raises(Exception, match="FROZEN_ALEMBIC_CONFIG_GIT_OBJECT_MISMATCH"):
        candidate_readiness.verify_frozen_execution_code(repo, head)


def test_frozen_execution_code_accepts_exact_loaded_checkout(tmp_path: Path) -> None:
    repo, head = _frozen_source_repo(tmp_path, full_package=True)
    script = (
        "import json; "
        "from qi_crawler import candidate_readiness as c; "
        f"print(json.dumps(c.verify_frozen_execution_code({str(repo)!r}, {head!r})))"
    )
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(repo / "src")

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=repo,
        env=environment,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    identity = json.loads(result.stdout)
    assert set(identity) == {
        "candidate_readiness",
        "candidate_data",
        "migrations",
        "db",
        "alembic_ini",
        "alembic_env",
    }
    assert all(item["git_blob_identity"] for item in identity.values())


def test_frozen_execution_code_rejects_replaced_callable_origin(tmp_path: Path) -> None:
    from qi_crawler import candidate_readiness

    repo, head = _frozen_source_repo(tmp_path)
    with (
        mock.patch.object(
            candidate_readiness,
            "_loaded_execution_modules",
            return_value=_loaded_modules_from(repo),
        ),
        mock.patch.object(candidate_readiness, "backup_database", lambda: None),
        pytest.raises(Exception, match="FROZEN_EXECUTION_CALLABLE_ORIGIN_MISMATCH"),
    ):
        candidate_readiness.verify_frozen_execution_code(repo, head)


def test_frozen_source_checkout_verifies_exact_clean_head_and_allows_untracked(
    tmp_path: Path,
) -> None:
    from qi_crawler import candidate_readiness

    repo, head = _frozen_source_repo(tmp_path)
    (repo / "dist").mkdir()
    (repo / "dist" / "QI-Crawler.exe").write_bytes(b"untracked build output")

    result = candidate_readiness.verify_frozen_source_checkout(repo, head)

    assert result["source_git_sha"] == head
    assert result["tracked_tree_clean"] is True


def test_frozen_source_checkout_rejects_wrong_head(tmp_path: Path) -> None:
    from qi_crawler import candidate_readiness

    repo, old_head = _frozen_source_repo(tmp_path)
    (repo / "tracked.txt").write_text("next\n", encoding="utf-8")
    _git(repo, "add", "tracked.txt")
    _git(repo, "commit", "-m", "next")

    with pytest.raises(Exception, match="FROZEN_SOURCE_HEAD_MISMATCH"):
        candidate_readiness.verify_frozen_source_checkout(repo, old_head)


@pytest.mark.parametrize(
    "relative",
    [
        "alembic/versions/0021_add_tender_completeness.py",
        "src/qi_crawler/candidate_readiness.py",
    ],
)
def test_frozen_source_checkout_rejects_dirty_tracked_source(
    tmp_path: Path, relative: str
) -> None:
    from qi_crawler import candidate_readiness

    repo, head = _frozen_source_repo(tmp_path)
    path = repo / relative
    path.write_text(path.read_text(encoding="utf-8") + "\n# dirty\n", encoding="utf-8")

    with pytest.raises(Exception, match="FROZEN_SOURCE_TRACKED_TREE_DIRTY"):
        candidate_readiness.verify_frozen_source_checkout(repo, head)


def test_frozen_source_checkout_rejects_non_git_and_wrong_root(tmp_path: Path) -> None:
    from qi_crawler import candidate_readiness

    non_git = tmp_path / "non-git"
    non_git.mkdir()
    (non_git / ".git").write_text("gitdir: missing\n", encoding="utf-8")
    with pytest.raises(Exception, match="FROZEN_SOURCE_NOT_GIT_WORKTREE"):
        candidate_readiness.verify_frozen_source_checkout(non_git, "1" * 40)

    repo, head = _frozen_source_repo(tmp_path)
    with pytest.raises(Exception, match="FROZEN_SOURCE_REPO_ROOT_MISMATCH"):
        candidate_readiness.verify_frozen_source_checkout(repo / "src", head)


def test_migration_source_identity_binds_filesystem_bytes_to_git_blobs(
    tmp_path: Path,
) -> None:
    from qi_crawler import candidate_readiness

    repo, head = _frozen_source_repo(tmp_path)
    identity = candidate_readiness._migration_source_identity(
        repo_root=repo,
        from_revision="0020_add_tender_operational_revision_events",
        to_revision=CURRENT_SCHEMA_REVISION,
        source_git_sha=head,
    )

    assert [item["revision"] for item in identity["chain"]] == [
        "0021_add_tender_completeness",
        "0022_add_tender_recovery_events",
    ]
    assert all(item["git_blob_identity"] for item in identity["chain"])
    target = repo / identity["chain"][0]["repo_relative_path"]
    target.write_text(target.read_text(encoding="utf-8") + "\n# mismatch\n", encoding="utf-8")
    with pytest.raises(Exception, match="MIGRATION_SCRIPT_GIT_OBJECT_MISMATCH"):
        candidate_readiness._migration_source_identity(
            repo_root=repo,
            from_revision="0020_add_tender_operational_revision_events",
            to_revision=CURRENT_SCHEMA_REVISION,
            source_git_sha=head,
        )


def test_candidate_readiness_cli_exposes_three_bounded_stages() -> None:
    result = subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "candidate_readiness.py"), "--help"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "migrate" in result.stdout
    assert "accept" in result.stdout
    assert "launch" in result.stdout


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _migratable_source(tmp_path: Path) -> Path:
    source = tmp_path / "working"
    documents = source / "data" / "documents"
    database = source / "data" / "database" / "egp.db"
    documents.mkdir(parents=True)
    database.parent.mkdir(parents=True)
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database.as_posix()}")
    command.upgrade(config, "0020_add_tender_operational_revision_events")
    payload = b"managed-document"
    managed = documents / "manual" / "source.pdf"
    managed.parent.mkdir(parents=True)
    managed.write_bytes(payload)
    with sqlite3.connect(database) as connection:
        connection.execute(
            "INSERT INTO documents("
            "id, tender_id, document_source, document_type, display_name, original_filename, "
            "stored_path, mime_type, file_size, sha256, version, source_url, uploaded_by, "
            "uploaded_at, status, zip_supported_entries, created_at, updated_at"
            ") VALUES (?, NULL, ?, ?, ?, ?, ?, ?, ?, ?, ?, NULL, ?, ?, ?, NULL, ?, ?)",
            (
                1,
                "manual",
                "HSMT",
                "Source",
                managed.name,
                str(managed.resolve()),
                "application/pdf",
                len(payload),
                hashlib.sha256(payload).hexdigest(),
                1,
                "test",
                "2026-09-18T00:00:00Z",
                "VERIFIED",
                "2026-09-18T00:00:00Z",
                "2026-09-18T00:00:00Z",
            ),
        )
    storage = {
        "database_url": f"sqlite:///{database.resolve().as_posix()}",
        "document_dir": str(documents.resolve()),
        "download_dir": str((source / "data" / "downloads").resolve()),
        "discovery_dir": str((source / "data" / "discovery").resolve()),
        "raw_dir": str((source / "data" / "raw").resolve()),
        "rejects_dir": str((source / "data" / "rejects").resolve()),
        "report_dir": str((source / "data" / "reports").resolve()),
    }
    (source / "config.yaml").write_text(
        yaml.safe_dump({"storage": storage}, sort_keys=False), encoding="utf-8"
    )
    return source


def _prepare_and_migrate(tmp_path: Path):
    from qi_crawler import candidate_readiness

    candidate = tmp_path / "candidate"
    data_root = candidate / "data-root"
    candidate_data.prepare_candidate_data(_migratable_source(tmp_path), data_root)
    source_repo, source_head = _frozen_source_repo(tmp_path)
    with mock.patch.object(
        candidate_readiness,
        "_loaded_execution_modules",
        return_value=_loaded_modules_from(source_repo),
    ):
        receipt = candidate_readiness.migrate_candidate_data(
            data_root,
            source_repository_root=source_repo,
            expected_frozen_source_sha=source_head,
        )
    return candidate, data_root, receipt


def test_migration_rejects_foreign_execution_before_database_mutation(
    tmp_path: Path,
) -> None:
    from qi_crawler import candidate_readiness

    data_root = tmp_path / "candidate" / "data-root"
    candidate_data.prepare_candidate_data(_migratable_source(tmp_path), data_root)
    database = data_root / "data" / "database" / "egp.db"
    database_sha = _sha256(database)
    source_repo, source_head = _frozen_source_repo(tmp_path)

    with pytest.raises(Exception, match="FROZEN_EXECUTION_MODULE_PATH_MISMATCH"):
        candidate_readiness.migrate_candidate_data(
            data_root,
            source_repository_root=source_repo,
            expected_frozen_source_sha=source_head,
        )

    assert _sha256(database) == database_sha
    assert not (data_root / "candidate_migration_receipt.json").exists()


def _write_build_identity(candidate: Path, *, source_sha: str | None = None) -> None:
    from qi_crawler import candidate_readiness

    if source_sha is None:
        migration = json.loads(
            (candidate / "data-root" / "candidate_migration_receipt.json").read_text(
                encoding="utf-8"
            )
        )
        source_sha = migration["migration_source_identity"]["source_git_sha"]
    bundle = candidate / "app" / "QI-Crawler"
    control = candidate / "control"
    bundle.mkdir(parents=True, exist_ok=True)
    control.mkdir(parents=True, exist_ok=True)
    executable = bundle / "QI-Crawler.exe"
    executable.write_bytes(b"portable-executable")
    portable_hash = _sha256(executable).upper()
    manifest = {
        "metadata_schema_version": "qi-crawler-installed-release-v1",
        "product": "QI-Crawler",
        "version": VERSION,
        "source_git_sha": source_sha,
        "source_branch": "main",
        "build_timestamp_utc": "2026-09-18T00:00:00Z",
        "alembic_head": CURRENT_SCHEMA_REVISION,
        "release_channel": "INTERNAL_CANDIDATE",
        "portable_exe_sha256": portable_hash,
    }
    (bundle / "release_manifest.json").write_text(
        json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
    )
    (bundle / "BUILD_INFO.txt").write_text(
        "\n".join(f"{key}={value}" for key, value in manifest.items()) + "\n",
        encoding="utf-8",
    )
    candidate_readiness.create_portable_artifact_receipt(
        candidate,
        expected_frozen_source_sha=source_sha,
        expected_version=VERSION,
    )


def test_portable_artifact_receipt_is_produced_from_actual_bundle(
    tmp_path: Path,
) -> None:
    candidate, _, migration = _prepare_and_migrate(tmp_path)

    _write_build_identity(candidate)

    receipt_path = candidate / "control" / "portable_artifact_receipt.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    assert receipt["receipt_schema_version"] == "qi-crawler-portable-artifact-v1"
    assert receipt["artifact_kind"] == "PORTABLE"
    assert "installer_sha256" not in receipt
    assert receipt["portable_exe_sha256"] == _sha256(
        candidate / "app" / "QI-Crawler" / "QI-Crawler.exe"
    )
    assert receipt["source_git_sha"] == migration["migration_source_identity"][
        "source_git_sha"
    ]


@pytest.mark.parametrize(
    ("target", "expected"),
    [
        ("exe", "PORTABLE_EXE_SHA_MISMATCH"),
        ("manifest", "BUILD_PRODUCT_VERSION_MISMATCH"),
        ("build_info", "BUILD_INFO_MANIFEST_MISMATCH"),
    ],
)
def test_portable_artifact_producer_rejects_bundle_tamper(
    tmp_path: Path, target: str, expected: str
) -> None:
    from qi_crawler import candidate_readiness

    candidate, _, migration = _prepare_and_migrate(tmp_path)
    source_sha = migration["migration_source_identity"]["source_git_sha"]
    bundle = candidate / "app" / "QI-Crawler"
    _write_build_identity(candidate)
    (candidate / "control" / "portable_artifact_receipt.json").unlink()
    if target == "exe":
        (bundle / "QI-Crawler.exe").write_bytes(b"tamper")
    elif target == "manifest":
        manifest = json.loads(
            (bundle / "release_manifest.json").read_text(encoding="utf-8")
        )
        manifest["version"] = "9.9.9"
        (bundle / "release_manifest.json").write_text(
            json.dumps(manifest) + "\n", encoding="utf-8"
        )
    else:
        build_info = bundle / "BUILD_INFO.txt"
        build_info.write_text(
            build_info.read_text(encoding="utf-8").replace(
                "version=0.10.0", "version=9.9.9"
            ),
            encoding="utf-8",
        )
    with pytest.raises(Exception, match=expected):
        candidate_readiness.create_portable_artifact_receipt(
            candidate,
            expected_frozen_source_sha=source_sha,
            expected_version=VERSION,
        )


def test_portable_artifact_producer_rejects_expected_source_mismatch(
    tmp_path: Path,
) -> None:
    from qi_crawler import candidate_readiness

    candidate, _, _ = _prepare_and_migrate(tmp_path)
    _write_build_identity(candidate)
    (candidate / "control" / "portable_artifact_receipt.json").unlink()
    with pytest.raises(Exception, match="FROZEN_SOURCE_SHA_MISMATCH"):
        candidate_readiness.create_portable_artifact_receipt(
            candidate,
            expected_frozen_source_sha="3" * 40,
            expected_version=VERSION,
        )


def _acceptance_args(candidate: Path, data_root: Path, migration: dict[str, object]):
    return {
        "candidate_root": candidate,
        "data_root": data_root,
        "expected_frozen_source_sha": migration["migration_source_identity"][
            "source_git_sha"
        ],
        "expected_migration_receipt_sha256": _sha256(
            data_root / "candidate_migration_receipt.json"
        ),
        "expected_version": VERSION,
    }


def test_migration_receipt_binds_real_0020_to_current_chain(tmp_path: Path) -> None:
    from qi_crawler import candidate_readiness

    _, data_root, receipt = _prepare_and_migrate(tmp_path)

    assert receipt["migration_result"] == "PASS"
    assert receipt["from_revision"] == "0020_add_tender_operational_revision_events"
    assert receipt["to_revision"] == CURRENT_SCHEMA_REVISION
    assert [item["revision"] for item in receipt["migration_source_identity"]["chain"]] == [
        "0021_add_tender_completeness",
        "0022_add_tender_recovery_events",
    ]
    assert receipt["input_db_sha256"] != receipt["output_db_sha256"]
    assert set(receipt["migration_source_identity"]["execution_code"]) == {
        "candidate_readiness",
        "candidate_data",
        "migrations",
        "db",
        "alembic_ini",
        "alembic_env",
    }
    assert candidate_readiness.validate_migration_receipt(data_root) == receipt


def test_migration_receipt_rejects_execution_code_identity_tamper(
    tmp_path: Path,
) -> None:
    from qi_crawler import candidate_readiness

    _, data_root, receipt = _prepare_and_migrate(tmp_path)
    receipt["migration_source_identity"]["execution_code"]["db"][
        "git_blob_identity"
    ] = "0" * 40
    receipt_path = data_root / "candidate_migration_receipt.json"
    receipt_path.write_text(json.dumps(receipt) + "\n", encoding="utf-8")

    with pytest.raises(Exception, match="MIGRATION_SOURCE_IDENTITY_MISMATCH"):
        candidate_readiness.validate_migration_receipt(data_root)


@pytest.mark.parametrize(
    ("field", "value", "expected"),
    [
        ("input_db_sha256", "0" * 64, "MIGRATION_INPUT_DB_LINEAGE_MISMATCH"),
        (
            "from_revision",
            "0019_unrelated",
            "MIGRATION_INPUT_SCHEMA_LINEAGE_MISMATCH",
        ),
    ],
)
def test_migration_receipt_rejects_input_lineage_tamper(
    tmp_path: Path, field: str, value: str, expected: str
) -> None:
    from qi_crawler import candidate_readiness

    _, data_root, receipt = _prepare_and_migrate(tmp_path)
    receipt[field] = value
    receipt_path = data_root / "candidate_migration_receipt.json"
    receipt_path.write_text(json.dumps(receipt) + "\n", encoding="utf-8")

    with pytest.raises(Exception, match=expected):
        candidate_readiness.validate_migration_receipt(data_root)


def test_migration_rejects_candidate_db_tamper_before_upgrade(tmp_path: Path) -> None:
    from qi_crawler import candidate_readiness

    data_root = tmp_path / "candidate" / "data-root"
    candidate_data.prepare_candidate_data(_migratable_source(tmp_path), data_root)
    database = data_root / "data" / "database" / "egp.db"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE tamper_before_migration (value TEXT)")

    with pytest.raises(Exception, match="CANDIDATE_DB_IDENTITY_MISMATCH"):
        source_repo, source_head = _frozen_source_repo(tmp_path)
        candidate_readiness.migrate_candidate_data(
            data_root,
            source_repository_root=source_repo,
            expected_frozen_source_sha=source_head,
        )


def test_migration_rejects_working_data_root(tmp_path: Path) -> None:
    from qi_crawler import candidate_readiness

    data_root = tmp_path / "candidate" / "data-root"
    candidate_data.prepare_candidate_data(_migratable_source(tmp_path), data_root)

    with pytest.raises(Exception, match="CANDIDATE_ROOT_OVERLAPS_WORKING_ROOT"):
        source_repo, source_head = _frozen_source_repo(tmp_path)
        candidate_readiness.migrate_candidate_data(
            data_root,
            source_repository_root=source_repo,
            expected_frozen_source_sha=source_head,
            forbidden_roots=(data_root,),
        )


def test_migration_rejects_unexpected_source_revision(tmp_path: Path) -> None:
    from qi_crawler import candidate_readiness

    source = _migratable_source(tmp_path)
    database = source / "data" / "database" / "egp.db"
    config = Config(str(ROOT / "alembic.ini"))
    config.set_main_option("script_location", str(ROOT / "alembic"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database.as_posix()}")
    command.upgrade(config, "0021_add_tender_completeness")
    data_root = tmp_path / "candidate" / "data-root"
    candidate_data.prepare_candidate_data(source, data_root)

    with pytest.raises(Exception, match="MIGRATION_INPUT_SCHEMA_UNEXPECTED"):
        source_repo, source_head = _frozen_source_repo(tmp_path)
        candidate_readiness.migrate_candidate_data(
            data_root,
            source_repository_root=source_repo,
            expected_frozen_source_sha=source_head,
        )


def test_migration_failure_emits_failed_evidence_and_no_acceptance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from qi_crawler import candidate_readiness

    data_root = tmp_path / "candidate" / "data-root"
    source = _migratable_source(tmp_path)
    source_db = source / "data" / "database" / "egp.db"
    source_document = source / "data" / "documents" / "manual" / "source.pdf"
    source_identity_before = (_sha256(source_db), _sha256(source_document))
    candidate_data.prepare_candidate_data(source, data_root)
    monkeypatch.setattr(
        candidate_readiness,
        "_upgrade_from_frozen_source",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("migration failed")),
    )

    with pytest.raises(Exception, match="migration failed"):
        source_repo, source_head = _frozen_source_repo(tmp_path)
        with mock.patch.object(
            candidate_readiness,
            "_loaded_execution_modules",
            return_value=_loaded_modules_from(source_repo),
        ):
            candidate_readiness.migrate_candidate_data(
                data_root,
                source_repository_root=source_repo,
                expected_frozen_source_sha=source_head,
            )

    receipt = json.loads(
        (data_root / "candidate_migration_receipt.json").read_text(encoding="utf-8")
    )
    assert receipt["migration_result"] == "FAIL"
    assert not (tmp_path / "candidate" / "control" / "pre_start_acceptance.json").exists()
    assert (_sha256(source_db), _sha256(source_document)) == source_identity_before


def test_pre_first_start_acceptance_binds_build_data_config_and_lineage(tmp_path: Path) -> None:
    from qi_crawler import candidate_readiness

    candidate, data_root, migration = _prepare_and_migrate(tmp_path)
    _write_build_identity(candidate)

    acceptance = candidate_readiness.accept_pre_first_business_startup(
        **_acceptance_args(candidate, data_root, migration)
    )

    assert acceptance["status"] == "ACCEPTED"
    assert acceptance["source_git_sha"] == migration["migration_source_identity"][
        "source_git_sha"
    ]
    assert acceptance["database_sha256"] == migration["output_db_sha256"]
    assert acceptance["schema_revision"] == CURRENT_SCHEMA_REVISION
    assert acceptance["managed_document_mapping_digest"] == migration[
        "managed_document_mapping_digest"
    ]


@pytest.mark.parametrize(
    ("tamper", "expected"),
    [
        ("clone_receipt", "CLONE_RECEIPT_LINEAGE_MISMATCH"),
        ("migration_receipt", "MIGRATION_RECEIPT_IDENTITY_MISMATCH"),
        ("database", "MIGRATED_DB_IDENTITY_MISMATCH"),
        ("document", "MANAGED_DOCUMENT_SHA_MISMATCH"),
        ("config_escape", "CANDIDATE_CONFIG_ESCAPE"),
        ("build_sha", "FROZEN_SOURCE_SHA_MISMATCH"),
        ("migration_source_sha", "MIGRATION_SOURCE_SHA_MISMATCH"),
        ("executable", "PORTABLE_EXE_SHA_MISMATCH"),
        ("schema", "MIGRATED_SCHEMA_MISMATCH"),
        ("missing_clone", "CLONE_RECEIPT_INVALID"),
        ("missing_migration", "MIGRATION_RECEIPT_IDENTITY_MISMATCH"),
        ("missing_portable", "PORTABLE_ARTIFACT_RECEIPT_INVALID"),
        ("installer_only", "PORTABLE_ARTIFACT_RECEIPT_INVALID"),
        ("portable_extra", "PORTABLE_ARTIFACT_RECEIPT_FIELDS_INVALID"),
    ],
)
def test_pre_first_start_rejects_tamper(
    tmp_path: Path, tamper: str, expected: str
) -> None:
    from qi_crawler import candidate_readiness

    candidate, data_root, migration = _prepare_and_migrate(tmp_path)
    _write_build_identity(candidate)
    args = _acceptance_args(candidate, data_root, migration)
    clone_path = data_root / "candidate_data_receipt.json"
    migration_path = data_root / "candidate_migration_receipt.json"
    database = data_root / "data" / "database" / "egp.db"
    if tamper == "clone_receipt":
        clone = json.loads(clone_path.read_text(encoding="utf-8"))
        clone["created_at"] = "tampered"
        clone_path.write_text(json.dumps(clone), encoding="utf-8")
    elif tamper == "migration_receipt":
        migration_path.write_text(migration_path.read_text(encoding="utf-8") + " ", encoding="utf-8")
    elif tamper == "database":
        with sqlite3.connect(database) as connection:
            connection.execute("CREATE TABLE post_migration_tamper (value TEXT)")
    elif tamper == "document":
        (data_root / "data" / "documents" / "manual" / "source.pdf").write_bytes(b"tamper")
    elif tamper == "config_escape":
        config_path = data_root / "config.yaml"
        config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
        config["storage"]["report_dir"] = str((tmp_path / "working" / "reports").resolve())
        config_path.write_text(yaml.safe_dump(config), encoding="utf-8")
    elif tamper == "build_sha":
        bundle = candidate / "app" / "QI-Crawler"
        manifest_path = bundle / "release_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["source_git_sha"] = "3" * 40
        manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")
        build_info = bundle / "BUILD_INFO.txt"
        build_info.write_text(
            build_info.read_text(encoding="utf-8").replace(
                f"source_git_sha={args['expected_frozen_source_sha']}",
                f"source_git_sha={'3' * 40}",
            ),
            encoding="utf-8",
        )
    elif tamper == "migration_source_sha":
        migration["migration_source_identity"]["source_git_sha"] = "3" * 40
        migration_path.write_text(json.dumps(migration) + "\n", encoding="utf-8")
        args["expected_migration_receipt_sha256"] = _sha256(migration_path)
    elif tamper == "executable":
        (candidate / "app" / "QI-Crawler" / "QI-Crawler.exe").write_bytes(b"tamper")
    elif tamper == "schema":
        with sqlite3.connect(database) as connection:
            connection.execute("UPDATE alembic_version SET version_num = 'wrong_revision'")
        migration["output_db_sha256"] = _sha256(database)
        migration_path.write_text(json.dumps(migration, sort_keys=True) + "\n", encoding="utf-8")
        args["expected_migration_receipt_sha256"] = _sha256(migration_path)
    elif tamper == "missing_clone":
        clone_path.unlink()
    elif tamper == "missing_migration":
        migration_path.unlink()
    elif tamper == "missing_portable":
        (candidate / "control" / "portable_artifact_receipt.json").unlink()
    elif tamper == "installer_only":
        control = candidate / "control"
        (control / "portable_artifact_receipt.json").unlink()
        (control / "release_artifact_receipt.json").write_text(
            json.dumps(
                {
                    "receipt_schema_version": "qi-crawler-release-artifact-v1",
                    "installer_sha256": "2" * 64,
                }
            ),
            encoding="utf-8",
        )
    else:
        receipt_path = candidate / "control" / "portable_artifact_receipt.json"
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        receipt["unsupported"] = True
        receipt_path.write_text(json.dumps(receipt) + "\n", encoding="utf-8")

    with pytest.raises(Exception, match=expected):
        candidate_readiness.accept_pre_first_business_startup(**args)


def test_invalid_acceptance_never_launches_or_falls_back_to_working_data(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from qi_crawler import candidate_readiness

    candidate, data_root, migration = _prepare_and_migrate(tmp_path)
    _write_build_identity(candidate)
    working = tmp_path / "working-user-data"
    working.mkdir()
    working_db = working / "egp.db"
    working_db.write_bytes(b"working-data")
    before = _sha256(working_db)
    monkeypatch.setenv("QI_CRAWLER_DATA_DIR", str(working))
    monkeypatch.setenv("QI_CRAWLER_CONFIG_PATH", str(working / "config.yaml"))
    (candidate / "app" / "QI-Crawler" / "QI-Crawler.exe").write_bytes(b"tampered")
    launches: list[object] = []

    with pytest.raises(Exception, match="PORTABLE_EXE_SHA_MISMATCH"):
        candidate_readiness.launch_candidate_after_acceptance(
            **_acceptance_args(candidate, data_root, migration),
            launcher=lambda *args, **kwargs: launches.append((args, kwargs)),
        )

    assert launches == []
    assert _sha256(working_db) == before


def test_candidate_root_cannot_be_the_working_data_root(tmp_path: Path) -> None:
    from qi_crawler import candidate_readiness

    candidate, data_root, migration = _prepare_and_migrate(tmp_path)
    _write_build_identity(candidate)

    with pytest.raises(Exception, match="CANDIDATE_ROOT_OVERLAPS_WORKING_ROOT"):
        candidate_readiness.accept_pre_first_business_startup(
            **_acceptance_args(candidate, data_root, migration),
            forbidden_roots=(candidate,),
        )


def test_successful_controlled_launch_overrides_inherited_working_roots(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from qi_crawler import candidate_readiness

    candidate, data_root, migration = _prepare_and_migrate(tmp_path)
    _write_build_identity(candidate)
    monkeypatch.setenv("QI_CRAWLER_DATA_DIR", str(tmp_path / "working"))
    monkeypatch.setenv("QI_CRAWLER_CONFIG_PATH", str(tmp_path / "working-config.yaml"))
    calls: list[tuple[tuple[object, ...], dict[str, object]]] = []

    candidate_readiness.launch_candidate_after_acceptance(
        **_acceptance_args(candidate, data_root, migration),
        launcher=lambda *args, **kwargs: calls.append((args, kwargs)),
    )

    assert len(calls) == 1
    environment = calls[0][1]["env"]
    assert environment["QI_CRAWLER_DATA_DIR"] == str(data_root.resolve())
    assert environment["QI_CRAWLER_CONFIG_PATH"] == str((data_root / "config.yaml").resolve())


def test_failed_process_launch_preserves_acceptance_and_retry_succeeds(
    tmp_path: Path,
) -> None:
    from qi_crawler import candidate_readiness

    candidate, data_root, migration = _prepare_and_migrate(tmp_path)
    _write_build_identity(candidate)
    args = _acceptance_args(candidate, data_root, migration)
    receipt_path = candidate / "control" / "pre_start_acceptance.json"

    with pytest.raises(OSError, match="simulated launch failure"):
        candidate_readiness.launch_candidate_after_acceptance(
            **args,
            launcher=lambda *_args, **_kwargs: (_ for _ in ()).throw(
                OSError("simulated launch failure")
            ),
        )
    receipt_before = receipt_path.read_bytes()
    calls: list[object] = []
    candidate_readiness.launch_candidate_after_acceptance(
        **args,
        launcher=lambda *launcher_args, **launcher_kwargs: calls.append(
            (launcher_args, launcher_kwargs)
        ),
    )

    assert receipt_path.read_bytes() == receipt_before
    assert len(calls) == 1


def test_existing_acceptance_allows_operational_database_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from qi_crawler import candidate_readiness, standalone

    candidate, data_root, migration = _prepare_and_migrate(tmp_path)
    _write_build_identity(candidate)
    acceptance = candidate_readiness.accept_pre_first_business_startup(
        **_acceptance_args(candidate, data_root, migration)
    )
    database = data_root / "data" / "database" / "egp.db"
    with sqlite3.connect(database) as connection:
        connection.execute("CREATE TABLE normal_runtime_write (value TEXT)")

    assert candidate_readiness.validate_existing_acceptance(candidate) == acceptance
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(
        sys,
        "executable",
        str(candidate / "app" / "QI-Crawler" / "QI-Crawler.exe"),
    )
    monkeypatch.setenv("QI_CRAWLER_DATA_DIR", str(tmp_path / "inherited-working"))
    monkeypatch.setenv(
        "QI_CRAWLER_CONFIG_PATH", str(tmp_path / "inherited-working" / "config.yaml")
    )
    assert standalone.authorize_frozen_runtime([]) == "ACCEPTED_CANDIDATE"


def test_frozen_candidate_direct_start_requires_acceptance_before_default_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from qi_crawler import standalone

    candidate, _, _ = _prepare_and_migrate(tmp_path)
    _write_build_identity(candidate)
    executable = candidate / "app" / "QI-Crawler" / "QI-Crawler.exe"
    working_root = tmp_path / "working-localappdata" / "QI-Crawler"
    working_root.mkdir(parents=True)
    marker = working_root / "keep.txt"
    marker.write_text("untouched", encoding="utf-8")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(executable))
    monkeypatch.setenv("LOCALAPPDATA", str(working_root.parent))
    monkeypatch.delenv("QI_CRAWLER_DATA_DIR", raising=False)
    monkeypatch.delenv("QI_CRAWLER_CONFIG_PATH", raising=False)

    with pytest.raises(Exception, match="CANDIDATE_ACCEPTANCE_REQUIRED"):
        standalone.authorize_frozen_runtime([])

    assert marker.read_text(encoding="utf-8") == "untouched"
    assert "QI_CRAWLER_DATA_DIR" not in os.environ


def test_frozen_candidate_direct_start_binds_accepted_candidate_data(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from qi_crawler import candidate_readiness, standalone

    candidate, data_root, migration = _prepare_and_migrate(tmp_path)
    _write_build_identity(candidate)
    candidate_readiness.accept_pre_first_business_startup(
        **_acceptance_args(candidate, data_root, migration)
    )
    executable = candidate / "app" / "QI-Crawler" / "QI-Crawler.exe"
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(executable))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "working-localappdata"))
    monkeypatch.setenv("QI_CRAWLER_DATA_DIR", str(tmp_path / "inherited-working"))
    monkeypatch.setenv(
        "QI_CRAWLER_CONFIG_PATH", str(tmp_path / "inherited-working" / "config.yaml")
    )

    result = standalone.authorize_frozen_runtime([])

    assert result == "ACCEPTED_CANDIDATE"
    assert os.environ["QI_CRAWLER_DATA_DIR"] == str(data_root.resolve())
    assert os.environ["QI_CRAWLER_CONFIG_PATH"] == str(
        (data_root / "config.yaml").resolve()
    )


def test_frozen_candidate_rejects_tampered_or_foreign_acceptance(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from qi_crawler import candidate_readiness, standalone

    candidate, data_root, migration = _prepare_and_migrate(tmp_path)
    _write_build_identity(candidate)
    candidate_readiness.accept_pre_first_business_startup(
        **_acceptance_args(candidate, data_root, migration)
    )
    receipt_path = candidate / "control" / "pre_start_acceptance.json"
    receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
    receipt["candidate_root"] = str((tmp_path / "foreign-candidate").resolve())
    receipt_path.write_text(json.dumps(receipt) + "\n", encoding="utf-8")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(
        sys,
        "executable",
        str(candidate / "app" / "QI-Crawler" / "QI-Crawler.exe"),
    )

    with pytest.raises(Exception, match="ACCEPTANCE_CANDIDATE_ROOT_MISMATCH"):
        standalone.authorize_frozen_runtime([])


def test_preacceptance_candidate_smoke_requires_explicit_isolated_root(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from qi_crawler import standalone

    candidate, _, _ = _prepare_and_migrate(tmp_path)
    _write_build_identity(candidate)
    executable = candidate / "app" / "QI-Crawler" / "QI-Crawler.exe"
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(executable))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "working-localappdata"))
    monkeypatch.delenv("QI_CRAWLER_DATA_DIR", raising=False)

    with pytest.raises(Exception, match="CANDIDATE_SMOKE_DATA_ROOT_REQUIRED"):
        standalone.authorize_frozen_runtime(["--smoke-test"])

    isolated = tmp_path / "isolated-smoke"
    monkeypatch.setenv("QI_CRAWLER_DATA_DIR", str(isolated))
    assert standalone.authorize_frozen_runtime(["--smoke-test"]) == (
        "ISOLATED_CANDIDATE_SMOKE"
    )
    working = Path(os.environ["LOCALAPPDATA"]) / "QI-Crawler"
    monkeypatch.setenv("QI_CRAWLER_DATA_DIR", str(working))
    with pytest.raises(Exception, match="CANDIDATE_ROOT_OVERLAPS_WORKING_ROOT"):
        standalone.authorize_frozen_runtime(["--smoke-test"])


@pytest.mark.parametrize(
    ("tamper", "expected"),
    [
        ("missing", "CANDIDATE_RELEASE_MANIFEST_REQUIRED"),
        ("channel", "CANDIDATE_RELEASE_CHANNEL_INVALID"),
    ],
)
def test_governed_candidate_layout_fails_closed_on_release_metadata_tamper(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    tamper: str,
    expected: str,
) -> None:
    from qi_crawler import standalone

    candidate, _, _ = _prepare_and_migrate(tmp_path)
    _write_build_identity(candidate)
    executable = candidate / "app" / "QI-Crawler" / "QI-Crawler.exe"
    manifest_path = executable.parent / "release_manifest.json"
    if tamper == "missing":
        manifest_path.unlink()
    else:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["release_channel"] = "INTERNAL_PILOT"
        manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    monkeypatch.setattr(sys, "executable", str(executable))

    with pytest.raises(Exception, match=expected):
        standalone.authorize_frozen_runtime([])


def test_gui_candidate_gate_runs_before_standalone_preparation(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from qi_crawler import gui

    events: list[str] = []
    monkeypatch.setattr(gui, "is_frozen", lambda: True)

    def reject(_arguments: list[str]) -> None:
        events.append("authorize")
        raise RuntimeError("candidate not accepted")

    monkeypatch.setattr(gui, "authorize_frozen_runtime", reject)
    monkeypatch.setattr(
        gui,
        "prepare_standalone_runtime",
        lambda: events.append("prepare"),
    )

    assert gui.main() == 1
    assert events == ["authorize"]
