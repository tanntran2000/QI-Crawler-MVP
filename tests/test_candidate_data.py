from __future__ import annotations

import hashlib
import importlib
import json
import os
import sqlite3
import subprocess
import threading
from pathlib import Path

import pytest
import yaml


def _module():
    return importlib.import_module("qi_crawler.candidate_data")


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _source_root(
    tmp_path: Path,
    documents: list[tuple[int, str, bytes]] | None = None,
    *,
    create_document_root: bool = True,
) -> Path:
    source = tmp_path / "working"
    docs = source / "data" / "documents"
    db_path = source / "data" / "database" / "egp.db"
    if create_document_root:
        docs.mkdir(parents=True)
    db_path.parent.mkdir(parents=True)
    rows = (
        documents
        if documents is not None
        else [(1, "manual/a.pdf", b"alpha"), (2, "other/b.docx", b"beta")]
    )
    with sqlite3.connect(db_path) as connection:
        connection.execute("CREATE TABLE alembic_version (version_num TEXT NOT NULL)")
        connection.execute(
            "INSERT INTO alembic_version(version_num) VALUES "
            "('0020_add_tender_operational_revision_events')"
        )
        connection.execute(
            "CREATE TABLE documents ("
            "id INTEGER PRIMARY KEY, stored_path TEXT NOT NULL, sha256 TEXT NOT NULL)"
        )
        for document_id, relative, payload in rows:
            path = docs / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(payload)
            connection.execute(
                "INSERT INTO documents(id, stored_path, sha256) VALUES (?, ?, ?)",
                (document_id, str(path.resolve()), _sha(payload)),
            )
    config = {
        "storage": {
            "database_url": f"sqlite:///{db_path.resolve().as_posix()}",
            "document_dir": str(docs.resolve()),
            "download_dir": str((source / "data" / "downloads").resolve()),
            "discovery_dir": str((source / "data" / "discovery").resolve()),
            "raw_dir": str((source / "data" / "raw").resolve()),
            "rejects_dir": str((source / "data" / "rejects").resolve()),
            "report_dir": str((source / "data" / "reports").resolve()),
        }
    }
    (source / "config.yaml").write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    (source / "keyword-groups.yaml").write_text("groups: []\n", encoding="utf-8")
    return source


def _prepare(source: Path, destination: Path):
    return _module().prepare_candidate_data(source, destination)


def _enable_wal(source_db: Path) -> sqlite3.Connection:
    keeper = sqlite3.connect(source_db, isolation_level=None)
    assert keeper.execute("PRAGMA journal_mode = WAL").fetchone()[0].lower() == "wal"
    keeper.execute("PRAGMA wal_autocheckpoint = 0")
    keeper.execute("CREATE TABLE capture_writes (value TEXT NOT NULL)")
    keeper.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    return keeper


def _start_wal_writer(
    source_db: Path, trigger: threading.Event, committed: threading.Event
) -> threading.Thread:
    def write() -> None:
        assert trigger.wait(5), "capture hook did not release WAL writer"
        with sqlite3.connect(source_db, isolation_level=None) as connection:
            connection.execute("INSERT INTO capture_writes(value) VALUES ('external-commit')")
        committed.set()

    writer = threading.Thread(target=write, daemon=True)
    writer.start()
    return writer


@pytest.mark.parametrize("relationship", ["same", "destination_inside", "source_inside"])
def test_clone_rejects_overlapping_source_and_destination(
    tmp_path: Path, relationship: str
) -> None:
    source = _source_root(tmp_path)
    if relationship == "same":
        destination = source
    elif relationship == "destination_inside":
        destination = source / "candidate"
    else:
        destination = tmp_path / "outer"
        source = _source_root(destination)

    with pytest.raises(Exception, match="PATH_OVERLAP"):
        _prepare(source, destination)


def test_clone_rejects_populated_destination(tmp_path: Path) -> None:
    source = _source_root(tmp_path)
    destination = tmp_path / "candidate"
    destination.mkdir()
    (destination / "unknown.txt").write_text("keep", encoding="utf-8")

    with pytest.raises(Exception, match="DESTINATION_NOT_EMPTY"):
        _prepare(source, destination)
    assert (destination / "unknown.txt").read_text(encoding="utf-8") == "keep"


def test_clone_rejects_symlink_alias_or_escape(tmp_path: Path) -> None:
    source = _source_root(tmp_path)
    alias = tmp_path / "alias"
    try:
        alias.symlink_to(source, target_is_directory=True)
    except OSError:
        if os.name != "nt":
            pytest.skip("Directory symlink creation is unavailable on this host")
        junction = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(alias), str(source)],
            capture_output=True,
            text=True,
            check=False,
        )
        if junction.returncode != 0:
            pytest.skip("Directory symlink/junction creation is unavailable on this host")

    with pytest.raises(Exception, match="REPARSE_OR_SYMLINK"):
        _prepare(source, alias)


def test_clone_uses_sqlite_snapshot_and_rebases_exact_managed_documents(tmp_path: Path) -> None:
    source = _source_root(tmp_path)
    destination = tmp_path / "candidate"
    source_db = source / "data" / "database" / "egp.db"
    source_hash_before = _sha(source_db.read_bytes())

    receipt = _prepare(source, destination)

    assert receipt["status"] == "COMPLETE"
    assert receipt["source_schema"] == "0020_add_tender_operational_revision_events"
    assert receipt["document_count"] == 2
    assert receipt["rebase_count"] == 2
    assert receipt["receipt_schema_version"] == "qi-crawler-candidate-clone-v1"
    assert receipt["managed_document_mapping_digest"]
    assert receipt["candidate_config_path"] == str((destination / "config.yaml").resolve())
    assert receipt["source_document_root"] == str(
        (source / "data" / "documents").resolve()
    )
    assert receipt["source_document_root_basis"] == "CONFIG_EXPLICIT"
    assert receipt["source_document_dir_declared"] is True
    candidate_db = destination / "data" / "database" / "egp.db"
    with sqlite3.connect(candidate_db) as connection:
        paths = [
            Path(row[0]).resolve()
            for row in connection.execute("SELECT stored_path FROM documents ORDER BY id")
        ]
    assert all(path.is_relative_to(destination.resolve()) for path in paths)
    assert all(path.read_bytes() in {b"alpha", b"beta"} for path in paths)
    assert _sha(source_db.read_bytes()) == source_hash_before
    assert (
        json.loads((destination / "candidate_data_receipt.json").read_text(encoding="utf-8"))[
            "status"
        ]
        == "COMPLETE"
    )
    assert _module().validate_candidate_receipt(destination) == receipt


def test_clone_supports_legacy_source_config_without_document_dir(tmp_path: Path) -> None:
    source = _source_root(tmp_path, documents=[(1, "manual/a.pdf", b"alpha")])
    config_path = source / "config.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    del config["storage"]["document_dir"]
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    config_bytes_before = config_path.read_bytes()
    destination = tmp_path / "candidate"

    receipt = _prepare(source, destination)

    assert receipt["status"] == "COMPLETE"
    assert receipt["document_count"] == 1
    assert receipt["source_document_root"] == str(
        (source / "data" / "documents").resolve()
    )
    assert receipt["source_document_root_basis"] == "LEGACY_STANDALONE_DEFAULT"
    assert receipt["source_document_dir_declared"] is False
    assert config_path.read_bytes() == config_bytes_before


def test_clone_resolves_explicit_relative_document_dir_from_source_root(
    tmp_path: Path,
) -> None:
    source = _source_root(tmp_path, documents=[(1, "manual/a.pdf", b"alpha")])
    config_path = source / "config.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config["storage"]["document_dir"] = "./data/documents"
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")

    receipt = _prepare(source, tmp_path / "candidate")

    assert receipt["status"] == "COMPLETE"
    assert receipt["source_document_root"] == str(
        (source / "data" / "documents").resolve()
    )
    assert receipt["source_document_root_basis"] == "CONFIG_EXPLICIT"
    assert receipt["source_document_dir_declared"] is True


def test_clone_rejects_explicit_external_document_root(tmp_path: Path) -> None:
    source = _source_root(tmp_path)
    foreign = tmp_path / "foreign" / "documents"
    foreign.mkdir(parents=True)
    config_path = source / "config.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config["storage"]["document_dir"] = str(foreign.resolve())
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")

    with pytest.raises(Exception, match="SOURCE_CONFIG_ESCAPE"):
        _prepare(source, tmp_path / "candidate")


def test_legacy_document_root_does_not_authorize_stored_path_escape(tmp_path: Path) -> None:
    source = _source_root(tmp_path)
    config_path = source / "config.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    del config["storage"]["document_dir"]
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    outside = tmp_path / "foreign" / "a.pdf"
    outside.parent.mkdir()
    outside.write_bytes(b"alpha")
    with sqlite3.connect(source / "data" / "database" / "egp.db") as connection:
        connection.execute(
            "UPDATE documents SET stored_path = ? WHERE id = 1",
            (str(outside.resolve()),),
        )

    with pytest.raises(Exception, match="MANAGED_SOURCE_ESCAPE"):
        _prepare(source, tmp_path / "candidate")


@pytest.mark.parametrize("document_dir", ["", None, {"unexpected": "mapping"}])
def test_clone_rejects_invalid_explicit_document_dir(
    tmp_path: Path,
    document_dir: object,
) -> None:
    source = _source_root(tmp_path)
    config_path = source / "config.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config["storage"]["document_dir"] = document_dir
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")

    with pytest.raises(Exception, match="SOURCE_DOCUMENT_DIR_INVALID"):
        _prepare(source, tmp_path / "candidate")


def test_zero_document_legacy_clone_does_not_create_source_document_root(
    tmp_path: Path,
) -> None:
    source = _source_root(tmp_path, documents=[], create_document_root=False)
    config_path = source / "config.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    del config["storage"]["document_dir"]
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    source_documents = source / "data" / "documents"
    assert not source_documents.exists()

    receipt = _prepare(source, tmp_path / "candidate")

    assert receipt["status"] == "COMPLETE"
    assert receipt["document_count"] == 0
    assert receipt["source_document_root"] == str(source_documents.resolve())
    assert receipt["source_document_root_basis"] == "LEGACY_STANDALONE_DEFAULT"
    assert receipt["source_document_dir_declared"] is False
    assert not source_documents.exists()


def test_legacy_document_root_rejects_reparse_alias_when_available(tmp_path: Path) -> None:
    source = _source_root(tmp_path, documents=[], create_document_root=False)
    config_path = source / "config.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    del config["storage"]["document_dir"]
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    foreign = tmp_path / "foreign-documents"
    foreign.mkdir()
    alias = source / "data" / "documents"
    try:
        alias.symlink_to(foreign, target_is_directory=True)
    except OSError:
        if os.name != "nt":
            pytest.skip("Directory symlink creation is unavailable on this host")
        junction = subprocess.run(
            ["cmd", "/c", "mklink", "/J", str(alias), str(foreign)],
            capture_output=True,
            text=True,
            check=False,
        )
        if junction.returncode != 0:
            pytest.skip("Directory symlink/junction creation is unavailable on this host")

    with pytest.raises(Exception, match="REPARSE_OR_SYMLINK"):
        _prepare(source, tmp_path / "candidate")


def test_clone_receipt_validation_rejects_pre_migration_db_tamper(tmp_path: Path) -> None:
    source = _source_root(tmp_path)
    destination = tmp_path / "candidate"
    _prepare(source, destination)
    candidate_db = destination / "data" / "database" / "egp.db"

    with sqlite3.connect(candidate_db) as connection:
        connection.execute("CREATE TABLE post_clone_tamper (value TEXT)")

    with pytest.raises(Exception, match="CANDIDATE_DB_IDENTITY_MISMATCH"):
        _module().validate_candidate_receipt(destination)


def test_clone_receipt_validation_rejects_managed_document_tamper(tmp_path: Path) -> None:
    source = _source_root(tmp_path)
    destination = tmp_path / "candidate"
    _prepare(source, destination)
    (destination / "data" / "documents" / "manual" / "a.pdf").write_bytes(b"tampered")

    with pytest.raises(Exception, match="MANAGED_DOCUMENT_SHA_MISMATCH"):
        _module().validate_candidate_receipt(destination)


def test_mapping_digest_is_id_path_sensitive_with_reused_content_hash(tmp_path: Path) -> None:
    source = _source_root(
        tmp_path,
        documents=[(1, "one/shared.pdf", b"same"), (2, "two/shared.pdf", b"same")],
    )
    destination = tmp_path / "candidate"
    receipt = _prepare(source, destination)
    candidate_db = destination / "data" / "database" / "egp.db"
    second = destination / "data" / "documents" / "two" / "shared.pdf"

    with sqlite3.connect(candidate_db) as connection:
        connection.execute("UPDATE documents SET stored_path = ? WHERE id = 1", (str(second),))

    with pytest.raises(
        Exception,
        match="MANAGED_DOCUMENT_(?:PATH_COLLISION|MAPPING_MISMATCH)",
    ):
        _module().validate_candidate_receipt(
            destination,
            require_pre_migration_db_identity=False,
        )
    assert receipt["document_count"] == 2


def test_clone_receipt_validation_rejects_config_root_escape(tmp_path: Path) -> None:
    source = _source_root(tmp_path)
    destination = tmp_path / "candidate"
    _prepare(source, destination)
    config_path = destination / "config.yaml"
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    config["storage"]["report_dir"] = str((tmp_path / "working-reports").resolve())
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")

    with pytest.raises(Exception, match="CANDIDATE_CONFIG_ESCAPE"):
        _module().validate_candidate_receipt(destination)


def test_clone_captures_static_committed_wal_state_without_checkpoint(tmp_path: Path) -> None:
    source = _source_root(tmp_path)
    source_db = source / "data" / "database" / "egp.db"
    source_documents = source / "data" / "documents"
    keeper = _enable_wal(source_db)
    try:
        main_hash_before = _sha(source_db.read_bytes())
        third = source_documents / "wal" / "c.pdf"
        third.parent.mkdir(parents=True)
        third.write_bytes(b"committed-in-wal")
        keeper.execute(
            "INSERT INTO documents(id, stored_path, sha256) VALUES (?, ?, ?)",
            (3, str(third.resolve()), _sha(third.read_bytes())),
        )
        wal = Path(f"{source_db}-wal")
        assert wal.is_file() and wal.stat().st_size > 0
        assert _sha(source_db.read_bytes()) == main_hash_before

        receipt = _prepare(source, tmp_path / "candidate")

        assert receipt["status"] == "COMPLETE"
        assert receipt["document_count"] == 3
        assert receipt["source_sqlite_observation"]["journal_mode"] == "wal"
        assert receipt["source_sqlite_observation"]["data_version_start"] == receipt[
            "source_sqlite_observation"
        ]["data_version_end"]
        with sqlite3.connect(tmp_path / "candidate" / "data" / "database" / "egp.db") as candidate:
            assert candidate.execute("SELECT count(*) FROM documents").fetchone()[0] == 3
        assert _sha(source_db.read_bytes()) == main_hash_before
    finally:
        keeper.close()


@pytest.mark.parametrize(
    ("phase", "destination_name"),
    [
        ("AFTER_SOURCE_METADATA_READ", "candidate-before-backup"),
        ("AFTER_SQLITE_BACKUP", "candidate-after-backup"),
    ],
)
def test_clone_rejects_wal_commit_across_capture_boundary(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    phase: str,
    destination_name: str,
) -> None:
    source = _source_root(tmp_path)
    source_db = source / "data" / "database" / "egp.db"
    keeper = _enable_wal(source_db)
    trigger = threading.Event()
    committed = threading.Event()
    writer = _start_wal_writer(source_db, trigger, committed)
    module = _module()

    def capture_hook(observed_phase: str) -> None:
        if observed_phase == phase:
            trigger.set()
            assert committed.wait(5), "external WAL commit did not complete"

    monkeypatch.setattr(module, "_capture_hook", capture_hook)
    main_hash_before = _sha(source_db.read_bytes())
    destination = tmp_path / destination_name
    try:
        with pytest.raises(Exception, match="SOURCE_DB_CHANGED_DURING_CAPTURE"):
            module.prepare_candidate_data(source, destination)
        assert _sha(source_db.read_bytes()) == main_hash_before
        receipt = json.loads((destination / "candidate_data_receipt.json").read_text(encoding="utf-8"))
        assert receipt["status"] == "INCOMPLETE"
    finally:
        trigger.set()
        writer.join(5)
        keeper.close()
    assert not writer.is_alive()


def test_clone_backup_deadline_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = _source_root(tmp_path)
    module = _module()
    ticks = iter((0.0, 31.0, 31.0))
    monkeypatch.setattr(module, "_monotonic", lambda: next(ticks))
    monkeypatch.setattr(module, "MAX_BACKUP_SECONDS", 30.0)
    destination = tmp_path / "candidate-timeout"

    with pytest.raises(Exception, match="SOURCE_BACKUP_TIMEOUT"):
        module.prepare_candidate_data(source, destination)

    receipt = json.loads((destination / "candidate_data_receipt.json").read_text(encoding="utf-8"))
    assert receipt["status"] == "INCOMPLETE"


def test_clone_config_explicitly_isolates_every_candidate_root(tmp_path: Path) -> None:
    source = _source_root(tmp_path)
    destination = tmp_path / "candidate"

    receipt = _prepare(source, destination)

    config = yaml.safe_load((destination / "config.yaml").read_text(encoding="utf-8"))
    encoded = json.dumps(config, sort_keys=True)
    assert str(source.resolve()) not in encoded
    for key in (
        "candidate_database_root",
        "candidate_document_root",
        "candidate_download_root",
        "candidate_discovery_root",
        "candidate_raw_root",
        "candidate_reject_root",
        "candidate_report_root",
        "candidate_log_root",
        "candidate_session_root",
        "candidate_backup_root",
        "candidate_config_root",
    ):
        assert Path(receipt[key]).resolve().is_relative_to(destination.resolve())


@pytest.mark.parametrize("failure", ["missing", "sha_mismatch", "outside_root"])
def test_clone_rejects_invalid_managed_source_and_leaves_incomplete_receipt(
    tmp_path: Path, failure: str
) -> None:
    source = _source_root(tmp_path)
    db_path = source / "data" / "database" / "egp.db"
    managed = source / "data" / "documents" / "manual" / "a.pdf"
    if failure == "missing":
        managed.unlink()
        expected = "MANAGED_SOURCE_MISSING"
    elif failure == "sha_mismatch":
        managed.write_bytes(b"wrong")
        expected = "MANAGED_SOURCE_SHA_MISMATCH"
    else:
        outside = tmp_path / "outside.pdf"
        outside.write_bytes(b"alpha")
        with sqlite3.connect(db_path) as connection:
            connection.execute("UPDATE documents SET stored_path = ? WHERE id = 1", (str(outside),))
        expected = "MANAGED_SOURCE_ESCAPE"

    destination = tmp_path / "candidate"
    with pytest.raises(Exception, match=expected):
        _prepare(source, destination)
    receipt = json.loads((destination / "candidate_data_receipt.json").read_text(encoding="utf-8"))
    assert receipt["status"] == "INCOMPLETE"


def test_clone_rejects_destination_collision(tmp_path: Path) -> None:
    source = _source_root(
        tmp_path,
        documents=[(1, "shared.pdf", b"same"), (2, "shared.pdf", b"same")],
    )
    with pytest.raises(Exception, match="DESTINATION_COLLISION"):
        _prepare(source, tmp_path / "candidate")


def test_clone_detects_source_database_drift(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _source_root(tmp_path)
    source_db = source / "data" / "database" / "egp.db"
    with sqlite3.connect(source_db, isolation_level=None) as wal_connection:
        assert wal_connection.execute("PRAGMA journal_mode = WAL").fetchone()[0].lower() == "wal"
    module = _module()
    original = module._snapshot_sqlite

    def snapshot_then_drift(source_connection: sqlite3.Connection, candidate_db: Path) -> None:
        original(source_connection, candidate_db)
        with sqlite3.connect(source_db) as connection:
            connection.execute("CREATE TABLE drift_marker (value TEXT)")

    monkeypatch.setattr(module, "_snapshot_sqlite", snapshot_then_drift)
    with pytest.raises(Exception, match="SOURCE_DB_CHANGED_DURING_CAPTURE"):
        module.prepare_candidate_data(source, tmp_path / "candidate")


def test_clone_detects_managed_file_drift(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    source = _source_root(tmp_path)
    module = _module()
    original = module._copy_verified_document
    changed = False

    def copy_then_drift(*args, **kwargs):
        nonlocal changed
        result = original(*args, **kwargs)
        if not changed:
            changed = True
            Path(args[0]).write_bytes(b"changed-after-copy")
        return result

    monkeypatch.setattr(module, "_copy_verified_document", copy_then_drift)
    with pytest.raises(Exception, match="SOURCE_DOCUMENT_CHANGED_DURING_CAPTURE"):
        module.prepare_candidate_data(source, tmp_path / "candidate")


def test_interrupted_clone_never_emits_complete_receipt(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _source_root(tmp_path)
    module = _module()

    def interrupted(*_args, **_kwargs):
        raise OSError("simulated interruption")

    monkeypatch.setattr(module, "_copy_verified_document", interrupted)
    destination = tmp_path / "candidate"
    with pytest.raises(OSError, match="simulated interruption"):
        module.prepare_candidate_data(source, destination)
    receipt = json.loads((destination / "candidate_data_receipt.json").read_text(encoding="utf-8"))
    assert receipt["status"] == "INCOMPLETE"
    with pytest.raises(Exception, match="CANDIDATE_RECEIPT_INCOMPLETE"):
        module.validate_candidate_receipt(destination)


def test_clone_rejects_wrong_document_identity_before_rebase(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _source_root(tmp_path)
    module = _module()
    original = module._snapshot_sqlite

    def snapshot_with_wrong_identity(
        source_connection: sqlite3.Connection, candidate_db: Path
    ) -> None:
        original(source_connection, candidate_db)
        with sqlite3.connect(candidate_db) as connection:
            connection.execute("UPDATE documents SET sha256 = ? WHERE id = 1", ("0" * 64,))

    monkeypatch.setattr(module, "_snapshot_sqlite", snapshot_with_wrong_identity)
    with pytest.raises(Exception, match="DOCUMENT_IDENTITY_MISMATCH"):
        module.prepare_candidate_data(source, tmp_path / "candidate")


def test_clone_rejects_candidate_schema_mismatch_before_rebase(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = _source_root(tmp_path)
    module = _module()
    original = module._snapshot_sqlite

    def snapshot_with_wrong_schema(
        source_connection: sqlite3.Connection, candidate_db: Path
    ) -> None:
        original(source_connection, candidate_db)
        with sqlite3.connect(candidate_db) as connection:
            connection.execute("UPDATE alembic_version SET version_num = 'wrong_revision'")

    monkeypatch.setattr(module, "_snapshot_sqlite", snapshot_with_wrong_schema)
    with pytest.raises(Exception, match="FAIL_CANDIDATE_SCHEMA_MISMATCH"):
        module.prepare_candidate_data(source, tmp_path / "candidate")


def test_clone_rejects_hard_link_alias_when_detectable(tmp_path: Path) -> None:
    source = _source_root(tmp_path)
    destination = tmp_path / "candidate"
    destination.mkdir()
    linked = destination / "config.yaml"
    try:
        os.link(source / "config.yaml", linked)
    except OSError:
        pytest.skip("Hard-link creation is unavailable on this host")

    with pytest.raises(Exception, match="DESTINATION_NOT_EMPTY|SAME_FILE_ALIAS"):
        _prepare(source, destination)
