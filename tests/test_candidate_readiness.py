from __future__ import annotations

import hashlib
import json
import sqlite3
import subprocess
import sys
from pathlib import Path

import pytest
import yaml
from alembic.config import Config

from alembic import command
from qi_crawler import candidate_data
from qi_crawler.db import CURRENT_SCHEMA_REVISION

ROOT = Path(__file__).parent.parent
SOURCE_SHA = "1" * 40
VERSION = "0.10.0"


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
    receipt = candidate_readiness.migrate_candidate_data(
        data_root,
        source_git_sha=SOURCE_SHA,
    )
    return candidate, data_root, receipt


def _write_build_identity(candidate: Path, *, source_sha: str = SOURCE_SHA) -> None:
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
    artifact = {
        "receipt_schema_version": "qi-crawler-release-artifact-v1",
        **{key: value for key, value in manifest.items() if key != "metadata_schema_version"},
        "installer_sha256": "2" * 64,
    }
    (control / "release_artifact_receipt.json").write_text(
        json.dumps(artifact, indent=2) + "\n", encoding="utf-8"
    )


def _acceptance_args(candidate: Path, data_root: Path, migration: dict[str, object]):
    return {
        "candidate_root": candidate,
        "data_root": data_root,
        "expected_frozen_source_sha": SOURCE_SHA,
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
    assert candidate_readiness.validate_migration_receipt(data_root) == receipt


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
        candidate_readiness.migrate_candidate_data(data_root, source_git_sha=SOURCE_SHA)


def test_migration_rejects_working_data_root(tmp_path: Path) -> None:
    from qi_crawler import candidate_readiness

    data_root = tmp_path / "candidate" / "data-root"
    candidate_data.prepare_candidate_data(_migratable_source(tmp_path), data_root)

    with pytest.raises(Exception, match="CANDIDATE_ROOT_OVERLAPS_WORKING_ROOT"):
        candidate_readiness.migrate_candidate_data(
            data_root,
            source_git_sha=SOURCE_SHA,
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
        candidate_readiness.migrate_candidate_data(data_root, source_git_sha=SOURCE_SHA)


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
        "upgrade_database",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("migration failed")),
    )

    with pytest.raises(Exception, match="migration failed"):
        candidate_readiness.migrate_candidate_data(data_root, source_git_sha=SOURCE_SHA)

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
    assert acceptance["source_git_sha"] == SOURCE_SHA
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
        _write_build_identity(candidate, source_sha="3" * 40)
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
    else:
        migration_path.unlink()

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
