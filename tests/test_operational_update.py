from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import subprocess
import sys
import time
from contextlib import closing
from pathlib import Path

import pytest

from qi_crawler import operational_update
from qi_crawler.operational_release import OperationalPaths, operational_paths
from qi_crawler.operational_update import (
    JOURNAL_SCHEMA,
    MARKER_SCHEMA,
    RECEIPT_SCHEMA,
    _database_paths,
    classify_operational_update_state,
)

UPDATE_ID = "update-01"
OLD_PATHS = {"1": "documents/old-a.pdf", "2": "documents/old-b.pdf"}
NEW_PATHS = {"1": "documents/new-a.pdf", "2": "documents/new-b.pdf"}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest().upper()


def _write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def _write_db(path: Path, stored_paths: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(path)) as connection:
        connection.execute("CREATE TABLE documents (id INTEGER PRIMARY KEY, stored_path TEXT)")
        connection.executemany(
            "INSERT INTO documents(id, stored_path) VALUES (?, ?)",
            [(int(key), value) for key, value in stored_paths.items()],
        )
        connection.commit()


def _replace_db(path: Path, stored_paths: dict[str, str]) -> None:
    path.unlink()
    _write_db(path, stored_paths)


def _fixture(tmp_path: Path, *, phase: str = "EARLY_ACTIVE") -> tuple[OperationalPaths, dict]:
    paths = operational_paths(tmp_path / "operational")
    paths.application_root.mkdir(parents=True)
    paths.executable.write_bytes(b"old application")
    paths.config_path.parent.mkdir(parents=True)
    paths.config_path.write_bytes(b"old config")
    _write_db(paths.database_path, OLD_PATHS)
    paths.control_root.mkdir(parents=True)

    marker = {
        "schema_version": MARKER_SCHEMA,
        "update_id": UPDATE_ID,
        "journal": "update_journal.json",
    }
    journal = {
        "schema_version": JOURNAL_SCHEMA,
        "update_id": UPDATE_ID,
        "phase": phase,
        "application": {
            "old_sha256": _sha(paths.executable),
            "new_sha256": hashlib.sha256(b"new application").hexdigest().upper(),
        },
        "config": {
            "old_sha256": _sha(paths.config_path),
            "new_sha256": hashlib.sha256(b"new config").hexdigest().upper(),
        },
        "database": {"old_paths": OLD_PATHS, "new_paths": NEW_PATHS},
        "backup": {
            "path": "backups/preupdate.db",
            "sha256": "",
            "baseline_paths": OLD_PATHS,
        },
    }
    _write_json(paths.control_root / "active_update.json", marker)
    _write_json(paths.control_root / "update_journal.json", journal)
    return paths, journal


def _write_journal(paths: OperationalPaths, journal: dict) -> None:
    _write_json(paths.control_root / "update_journal.json", journal)


def _install_backup(paths: OperationalPaths, journal: dict) -> Path:
    backup = paths.control_root / journal["backup"]["path"]
    _write_db(backup, OLD_PATHS)
    journal["backup"]["sha256"] = _sha(backup)
    _write_journal(paths, journal)
    return backup


def _install_new_identity(paths: OperationalPaths) -> None:
    paths.executable.write_bytes(b"new application")
    paths.config_path.write_bytes(b"new config")


def _write_receipt(paths: OperationalPaths, journal: dict, **overrides: object) -> None:
    receipt = {
        "schema_version": RECEIPT_SCHEMA,
        "update_id": UPDATE_ID,
        "application_sha256": journal["application"]["new_sha256"],
        "config_sha256": journal["config"]["new_sha256"],
        "database_state": "NEW",
    }
    receipt.update(overrides)
    _write_json(paths.control_root / "update_receipt.json", receipt)


def _classify(paths: OperationalPaths):
    before = _tree_identity(paths.root)
    result = classify_operational_update_state(paths)
    assert _tree_identity(paths.root) == before
    return result


def test_idle_absence_is_phase_valid_and_result_has_no_action_authority(tmp_path: Path) -> None:
    paths, _ = _fixture(tmp_path)
    (paths.control_root / "active_update.json").unlink()
    (paths.control_root / "update_journal.json").unlink()

    result = _classify(paths)

    assert result.classification == "NO_ACTIVE_UPDATE"
    assert result.observed_phase == "IDLE"
    assert result.input_stable is True
    assert result.artifact_states["marker"] == "PHASE_VALID_ABSENCE"
    assert not ({"action", "delete", "restore", "overwrite", "continue"} & set(result.__dataclass_fields__))


@pytest.mark.skipif(os.name != "nt", reason="positive active capture requires Windows exclusive file-sharing semantics")
@pytest.mark.parametrize(
    ("phase", "db_state", "receipt", "expected"),
    [
        ("EARLY_ACTIVE", "OLD", False, "EARLY_ACTIVE_PHASE"),
        ("BACKUP_REQUIRED", "OLD", False, "BACKUP_VALID"),
        ("PRECOMMIT", "OLD", False, "PRECOMMIT_OLD_DB"),
        ("DB_COMMIT_INTENT", "OLD", False, "PRECOMMIT_OLD_DB"),
        ("DB_COMMITTED", "NEW", False, "DB_COMMITTED_JOURNAL_LAG"),
        ("RECEIPT_WRITTEN", "NEW", True, "RECEIPT_PRESENT_VALID"),
        ("TERMINAL", "NEW", True, "TERMINAL_CONSISTENT"),
    ],
)
def test_positive_phase_matrix(
    tmp_path: Path, phase: str, db_state: str, receipt: bool, expected: str
) -> None:
    paths, journal = _fixture(tmp_path, phase=phase)
    if phase != "EARLY_ACTIVE":
        _install_backup(paths, journal)
    if db_state == "NEW":
        _replace_db(paths.database_path, NEW_PATHS)
        _install_new_identity(paths)
    if receipt:
        _write_receipt(paths, journal)

    result = _classify(paths)

    assert result.classification == expected
    assert result.observed_phase == phase
    assert result.input_stable is True


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        ("journal_missing", "JOURNAL_REQUIRED"),
        ("journal_corrupt", "JOURNAL_INVALID"),
        ("journal_id_mismatch", "UPDATE_ID_MISMATCH"),
        ("journal_schema", "JOURNAL_SCHEMA_UNSUPPORTED"),
        ("journal_phase", "PHASE_UNSUPPORTED"),
    ],
)
def test_marker_and_journal_ambiguity_fails_closed(
    tmp_path: Path, mutation: str, reason: str
) -> None:
    paths, journal = _fixture(tmp_path)
    journal_path = paths.control_root / "update_journal.json"
    if mutation == "journal_missing":
        journal_path.unlink()
    elif mutation == "journal_corrupt":
        journal_path.write_text("{", encoding="utf-8")
    elif mutation == "journal_id_mismatch":
        journal["update_id"] = "other"
        _write_journal(paths, journal)
    elif mutation == "journal_schema":
        journal["schema_version"] = "future"
        _write_journal(paths, journal)
    else:
        journal["phase"] = "FUTURE_PHASE"
        _write_journal(paths, journal)

    result = _classify(paths)

    assert result.classification == "RECOVERY_REQUIRED_AMBIGUOUS"
    assert reason in result.reasons


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        ("missing", "BACKUP_REQUIRED"),
        ("wrong_hash", "BACKUP_IDENTITY_MISMATCH"),
        ("wrong_baseline", "BACKUP_BASELINE_MISMATCH"),
    ],
)
def test_required_backup_is_validated(tmp_path: Path, mutation: str, reason: str) -> None:
    paths, journal = _fixture(tmp_path, phase="BACKUP_REQUIRED")
    if mutation == "missing":
        journal["backup"]["sha256"] = "0" * 64
        _write_journal(paths, journal)
    else:
        _install_backup(paths, journal)
        if mutation == "wrong_hash":
            journal["backup"]["sha256"] = "0" * 64
        else:
            journal["backup"]["baseline_paths"] = {"1": "wrong"}
        _write_journal(paths, journal)

    result = _classify(paths)

    assert result.classification == "RECOVERY_REQUIRED_AMBIGUOUS"
    assert reason in result.reasons


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        ("missing", "RECEIPT_REQUIRED"),
        ("corrupt", "RECEIPT_INVALID"),
        ("app_mismatch", "RECEIPT_APPLICATION_MISMATCH"),
    ],
)
def test_required_receipt_is_validated(tmp_path: Path, mutation: str, reason: str) -> None:
    paths, journal = _fixture(tmp_path, phase="RECEIPT_WRITTEN")
    _install_backup(paths, journal)
    _replace_db(paths.database_path, NEW_PATHS)
    _install_new_identity(paths)
    receipt_path = paths.control_root / "update_receipt.json"
    if mutation == "corrupt":
        receipt_path.write_text("{", encoding="utf-8")
    elif mutation == "app_mismatch":
        _write_receipt(paths, journal, application_sha256="0" * 64)

    result = _classify(paths)

    assert result.classification == "RECOVERY_REQUIRED_AMBIGUOUS"
    assert reason in result.reasons


@pytest.mark.parametrize(
    ("mutation", "reason"),
    [
        ("mixed_db", "DATABASE_STATE_MIXED_OR_UNKNOWN"),
        ("config", "CONFIG_IDENTITY_MISMATCH"),
        ("application", "APPLICATION_IDENTITY_MISMATCH"),
    ],
)
def test_identity_ambiguity_fails_closed(tmp_path: Path, mutation: str, reason: str) -> None:
    paths, journal = _fixture(tmp_path, phase="DB_COMMITTED")
    _install_backup(paths, journal)
    _replace_db(paths.database_path, NEW_PATHS)
    _install_new_identity(paths)
    if mutation == "mixed_db":
        _replace_db(paths.database_path, {"1": OLD_PATHS["1"], "2": NEW_PATHS["2"]})
    elif mutation == "config":
        paths.config_path.write_bytes(b"unknown config")
    else:
        paths.executable.write_bytes(b"unknown application")

    result = _classify(paths)

    assert result.classification == "RECOVERY_REQUIRED_AMBIGUOUS"
    assert reason in result.reasons


def test_backup_path_escape_fails_closed(tmp_path: Path) -> None:
    paths, journal = _fixture(tmp_path, phase="BACKUP_REQUIRED")
    journal["backup"]["path"] = "../../outside.db"
    journal["backup"]["sha256"] = "0" * 64
    _write_journal(paths, journal)

    result = _classify(paths)

    assert result.classification == "RECOVERY_REQUIRED_AMBIGUOUS"
    assert "BACKUP_PATH_UNSAFE" in result.reasons


def test_journal_read_error_fails_closed(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    paths, _ = _fixture(tmp_path)
    journal_path = paths.control_root / "update_journal.json"
    original = Path.read_bytes
    before = _tree_identity(paths.root)

    def denied(path: Path) -> bytes:
        if path == journal_path:
            raise PermissionError("synthetic access denial")
        return original(path)

    monkeypatch.setattr(Path, "read_bytes", denied)

    result = classify_operational_update_state(paths)
    monkeypatch.undo()

    assert result.classification == "RECOVERY_REQUIRED_AMBIGUOUS"
    assert "JOURNAL_INVALID" in result.reasons
    assert _tree_identity(paths.root) == before


@pytest.mark.skipif(not hasattr(os, "symlink"), reason="symlinks unavailable")
def test_reparse_or_symlink_artifact_fails_closed(tmp_path: Path) -> None:
    paths, journal = _fixture(tmp_path, phase="BACKUP_REQUIRED")
    outside = tmp_path / "outside.db"
    _write_db(outside, OLD_PATHS)
    backup = paths.control_root / journal["backup"]["path"]
    backup.parent.mkdir(parents=True)
    try:
        backup.symlink_to(outside)
    except OSError:
        pytest.skip("symlink creation unavailable")
    journal["backup"]["sha256"] = _sha(outside)
    _write_journal(paths, journal)

    result = _classify(paths)

    assert result.classification == "RECOVERY_REQUIRED_AMBIGUOUS"
    assert "BACKUP_PATH_UNSAFE" in result.reasons


def test_observation_rejects_ambiguous_sidecars_without_opening_source(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, journal = _fixture(tmp_path, phase="BACKUP_REQUIRED")
    _install_backup(paths, journal)
    wal = Path(f"{paths.database_path}-wal")
    shm = Path(f"{paths.database_path}-shm")
    wal.write_bytes(b"pre-existing wal evidence")
    shm.write_bytes(b"pre-existing shm evidence")

    source_uri = paths.database_path.resolve(strict=False).as_uri() + "?mode=ro"
    original_connect = sqlite3.connect
    source_opens: list[str] = []

    def reject_source_open(database_name, *args, **kwargs):
        if str(database_name) == source_uri:
            source_opens.append(str(database_name))
        return original_connect(database_name, *args, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", reject_source_open)
    before = _tree_identity(paths.root)
    result = _classify(paths)
    after = _tree_identity(paths.root)

    assert result.classification == "RECOVERY_REQUIRED_AMBIGUOUS"
    expected_reason = (
        "DATABASE_CAPTURE_UNSUPPORTED" if os.name != "nt" else "DATABASE_CAPTURE_UNPROVEN"
    )
    assert expected_reason in result.reasons
    assert source_opens == []
    assert after == before


@pytest.mark.skipif(os.name != "nt", reason="capture barrier requires Windows file-sharing semantics")
def test_stable_rollback_source_reads_only_hash_matched_private_copy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, _ = _fixture(tmp_path)
    database = paths.database_path
    before = (database.stat().st_size, _sha(database))
    assert database.read_bytes()[18:20] == b"\x01\x01"
    assert not Path(f"{database}-wal").exists()
    assert not Path(f"{database}-shm").exists()
    assert not Path(f"{database}-journal").exists()

    source_uri = database.resolve(strict=False).as_uri() + "?mode=ro"
    original_connect = sqlite3.connect
    source_opens: list[str] = []
    original_copy = operational_update._copy_database
    copy_states: list[tuple[int, str]] = []

    def track_source_open(database_name, *args, **kwargs):
        if str(database_name) == source_uri:
            source_opens.append(str(database_name))
        return original_connect(database_name, *args, **kwargs)

    def record_private_copy(source, destination, deadline, *args, **kwargs) -> None:
        original_copy(source, destination, deadline, *args, **kwargs)
        copy_states.append((destination.stat().st_size, _sha(destination)))

    monkeypatch.setattr(sqlite3, "connect", track_source_open)
    monkeypatch.setattr(operational_update, "_copy_database", record_private_copy)
    rows, error = _database_paths(database, active_wal=True)
    after = (database.stat().st_size, _sha(database))

    assert rows == OLD_PATHS
    assert error is None
    assert source_opens == []
    assert copy_states == [(before[0], before[1])]
    assert after == before
    assert not Path(f"{database}-wal").exists()
    assert not Path(f"{database}-shm").exists()
    assert not Path(f"{database}-journal").exists()


@pytest.mark.skipif(os.name != "nt", reason="requires Windows file-sharing semantics")
def test_valid_uncheckpointed_wal_without_capture_barrier_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, journal = _fixture(tmp_path, phase="DB_COMMITTED")
    _install_backup(paths, journal)
    _install_new_identity(paths)

    source_uri = paths.database_path.resolve(strict=False).as_uri() + "?mode=ro"
    original_connect = sqlite3.connect
    source_opens: list[str] = []

    def reject_source_open(database_name, *args, **kwargs):
        if str(database_name) == source_uri:
            source_opens.append(str(database_name))
        return original_connect(database_name, *args, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", reject_source_open)
    with closing(sqlite3.connect(paths.database_path)) as writer:
        assert writer.execute("PRAGMA journal_mode = WAL").fetchone() == ("wal",)
        writer.execute("PRAGMA wal_autocheckpoint = 0")
        writer.executemany(
            "UPDATE documents SET stored_path = ? WHERE id = ?",
            [(value, int(key)) for key, value in NEW_PATHS.items()],
        )
        writer.commit()

        wal = Path(f"{paths.database_path}-wal")
        shm = Path(f"{paths.database_path}-shm")
        assert wal.is_file() and wal.stat().st_size > 32
        assert shm.is_file()
        before = tuple(
            (suffix, path.read_bytes() if path.exists() else None)
            for suffix, path in (("", paths.database_path), ("-wal", wal), ("-shm", shm))
        )
        result = _classify(paths)
        after = tuple(
            (suffix, path.read_bytes() if path.exists() else None)
            for suffix, path in (("", paths.database_path), ("-wal", wal), ("-shm", shm))
        )

        assert result.classification == "RECOVERY_REQUIRED_AMBIGUOUS"
        assert "DATABASE_CAPTURE_BUSY" in result.reasons
        assert source_opens == []
        assert after == before


@pytest.mark.skipif(os.name != "nt", reason="requires Windows file-sharing semantics")
def test_wal_header_without_sidecars_is_not_eligible_for_capture(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, _ = _fixture(tmp_path)
    database = paths.database_path
    with closing(sqlite3.connect(database)) as writer:
        assert writer.execute("PRAGMA journal_mode = WAL").fetchone() == ("wal",)
        writer.execute("UPDATE documents SET stored_path = ? WHERE id = 1", (NEW_PATHS["1"],))
        writer.commit()
        assert writer.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()[0] == 0
    wal = Path(f"{database}-wal")
    shm = Path(f"{database}-shm")
    journal = Path(f"{database}-journal")
    assert not wal.exists()
    assert not shm.exists()
    assert not journal.exists()
    assert database.read_bytes()[18:20] == b"\x02\x02"
    before = tuple(
        (suffix, path.read_bytes() if path.exists() else None)
        for suffix, path in (("", database), ("-wal", wal), ("-shm", shm))
    )

    source_uri = database.resolve(strict=False).as_uri() + "?mode=ro"
    original_connect = sqlite3.connect
    source_opens: list[str] = []

    def track_source_open(database_name, *args, **kwargs):
        if str(database_name) == source_uri:
            source_opens.append(str(database_name))
        return original_connect(database_name, *args, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", track_source_open)
    rows, error = _database_paths(database, active_wal=True)
    after = tuple(
        (suffix, path.read_bytes() if path.exists() else None)
        for suffix, path in (("", database), ("-wal", wal), ("-shm", shm))
    )

    assert rows is None
    assert error == "DATABASE_CAPTURE_UNPROVEN"
    assert source_opens == []
    assert after == before


@pytest.mark.skipif(os.name != "nt", reason="requires Windows file-sharing semantics")
def test_open_sqlite_writer_prevents_capture_before_copy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, _ = _fixture(tmp_path)
    database = paths.database_path
    database.unlink()
    initial = {
        str(row_id): f"initial/{row_id:04d}/" + "x" * 500
        for row_id in range(1, 3001)
    }
    generation_one = {**initial, "1": "generation-1/first.pdf"}
    generation_two = {**generation_one, "3000": "generation-2/last.pdf"}

    with closing(sqlite3.connect(database)) as setup:
        setup.execute("CREATE TABLE documents (id INTEGER PRIMARY KEY, stored_path TEXT)")
        setup.executemany(
            "INSERT INTO documents(id, stored_path) VALUES (?, ?)",
            [(int(key), value) for key, value in initial.items()],
        )
        setup.commit()
        assert setup.execute("PRAGMA page_count").fetchone()[0] > 128

    def source_sqlite_files() -> tuple[tuple[str, bytes | None], ...]:
        return tuple(
            (suffix, path.read_bytes() if path.exists() else None)
            for suffix in ("", "-wal", "-shm")
            for path in (Path(f"{database}{suffix}"),)
        )

    def read_main_only(path: Path) -> dict[str, str]:
        uri = path.as_uri() + "?mode=ro&immutable=1"
        with closing(sqlite3.connect(uri, uri=True)) as connection:
            rows = connection.execute("SELECT id, stored_path FROM documents ORDER BY id")
            return {str(row[0]): str(row[1]) for row in rows.fetchall()}

    with closing(sqlite3.connect(database)) as writer:
        writer.execute(
            "UPDATE documents SET stored_path = ? WHERE id = 1",
            (generation_one["1"],),
        )
        writer.commit()
        assert not Path(f"{database}-wal").exists()
        assert not Path(f"{database}-shm").exists()
        assert not Path(f"{database}-journal").exists()
        assert read_main_only(database) == generation_one

        source_before_capture = source_sqlite_files()
        source_after_interleaving: list[tuple[tuple[str, bytes | None], ...]] = []
        copied_generations: list[tuple[str, str]] = []

        def copy_with_writer_interleaving(
            source: Path, destination: Path, deadline: float
        ) -> None:
            size = source.stat().st_size
            with source.open("rb") as input_stream, destination.open("wb") as output_stream:
                output_stream.write(input_stream.read(size // 2))
                output_stream.flush()
                writer.execute(
                    "UPDATE documents SET stored_path = ? WHERE id = 3000",
                    (generation_two["3000"],),
                )
                writer.commit()
                source_after_interleaving.append(source_sqlite_files())
                output_stream.write(input_stream.read())
            captured = read_main_only(destination)
            copied_generations.append((captured["1"], captured["3000"]))

        monkeypatch.setattr(
            operational_update, "_copy_database", copy_with_writer_interleaving
        )
        rows, error = _database_paths(database, active_wal=True)
        source_after_capture = source_sqlite_files()

    assert copied_generations == []
    assert source_after_interleaving == []
    assert source_before_capture == source_after_capture
    assert rows is None
    assert error == "DATABASE_CAPTURE_BUSY"


@pytest.mark.skipif(os.name != "nt", reason="requires Windows file-sharing semantics")
def test_copied_database_exclusive_lock_returns_unreadable_within_finite_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, _ = _fixture(tmp_path)
    database = paths.database_path
    locked_copied_databases: list[Path] = []
    original_reader = operational_update._read_database_paths

    def lock_backup_database(path: Path, **kwargs):
        if path.resolve() != database.resolve():
            blocker = sqlite3.connect(path, timeout=0.1)
            blocker.execute("BEGIN EXCLUSIVE")
            locked_copied_databases.append(path)
            try:
                return original_reader(path, **kwargs)
            finally:
                blocker.close()
        return original_reader(path, **kwargs)

    monkeypatch.setattr(operational_update, "_read_database_paths", lock_backup_database)

    started = time.monotonic()
    rows, error = _database_paths(database, active_wal=True)
    elapsed = time.monotonic() - started

    assert locked_copied_databases
    assert rows is None
    assert error == "DATABASE_UNREADABLE"
    assert elapsed < 10.0


@pytest.mark.skipif(os.name != "nt", reason="requires Windows file-sharing semantics")
def test_active_wal_without_capture_barrier_is_rejected_before_source_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, _ = _fixture(tmp_path)
    database = paths.database_path
    wal_path = Path(f"{database}-wal")
    shm_path = Path(f"{database}-shm")

    def source_sqlite_files() -> tuple[tuple[str, bytes | None], ...]:
        return tuple(
            (suffix, path.read_bytes() if path.exists() else None)
            for suffix, path in (
                ("", database),
                ("-wal", wal_path),
                ("-shm", shm_path),
            )
        )

    original_connect = sqlite3.connect
    source_uri = database.resolve(strict=False).as_uri() + "?mode=ro"
    source_opens: list[str] = []

    def reject_source_open(database_name, *args, **kwargs):
        if str(database_name) == source_uri:
            source_opens.append(str(database_name))
        return original_connect(database_name, *args, **kwargs)

    with closing(original_connect(database, timeout=0.1)) as blocker:
        assert blocker.execute("PRAGMA locking_mode=EXCLUSIVE").fetchone() == (
            "exclusive",
        )
        assert blocker.execute("PRAGMA journal_mode = WAL").fetchone() == ("wal",)
        blocker.execute("PRAGMA wal_autocheckpoint = 0")
        blocker.execute(
            "UPDATE documents SET stored_path = ? WHERE id = 1",
            (NEW_PATHS["1"],),
        )
        blocker.commit()
        assert wal_path.is_file() and wal_path.stat().st_size > 32
        assert not shm_path.exists()
        before = source_sqlite_files()
        monkeypatch.setattr(sqlite3, "connect", reject_source_open)

        started = time.monotonic()
        rows, error = _database_paths(database, active_wal=True)
        elapsed = time.monotonic() - started
        after = source_sqlite_files()

    assert source_opens == []
    assert after == before
    assert rows is None
    assert error == "DATABASE_CAPTURE_UNPROVEN"
    assert elapsed < 1.0


@pytest.mark.skipif(os.name != "nt", reason="requires Windows file-sharing semantics")
def test_existing_sqlite_reader_prevents_capture_barrier(
    tmp_path: Path,
) -> None:
    paths, _ = _fixture(tmp_path)
    database = paths.database_path
    sidecars = (Path(f"{database}-wal"), Path(f"{database}-shm"))

    def source_files() -> tuple[tuple[str, bytes | None], ...]:
        return tuple(
            (suffix, path.read_bytes() if path.exists() else None)
            for suffix, path in (("", database), ("-wal", sidecars[0]), ("-shm", sidecars[1]))
        )

    before = source_files()
    with closing(sqlite3.connect(database, timeout=0.1)) as reader:
        assert reader.execute("SELECT stored_path FROM documents ORDER BY id").fetchall()
        started = time.monotonic()
        rows, error = _database_paths(database, active_wal=True)
        elapsed = time.monotonic() - started

    after = source_files()
    assert after == before
    assert elapsed < 1.0
    assert rows is None
    assert error == "DATABASE_CAPTURE_BUSY"


@pytest.mark.skipif(os.name != "nt", reason="requires Windows file-sharing semantics")
def test_stable_uncheckpointed_wal_is_captured_without_source_sqlite_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, _ = _fixture(tmp_path)
    database = paths.database_path
    wal_path = Path(f"{database}-wal")
    shm_path = Path(f"{database}-shm")
    crash_writer = """
import os, sqlite3, sys
connection = sqlite3.connect(sys.argv[1], timeout=0.1)
connection.execute("PRAGMA journal_mode = WAL")
connection.execute("PRAGMA wal_autocheckpoint = 0")
connection.execute("UPDATE documents SET stored_path = ? WHERE id = 1", (sys.argv[2],))
connection.commit()
print("COMMITTED", flush=True)
os._exit(0)
"""
    setup = subprocess.run(
        [sys.executable, "-c", crash_writer, str(database), NEW_PATHS["1"]],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert setup.returncode == 0, setup.stderr
    assert setup.stdout.strip() == "COMMITTED"
    assert wal_path.is_file() and shm_path.is_file()

    def source_files() -> tuple[tuple[str, bytes | None], ...]:
        return tuple(
            (suffix, path.read_bytes() if path.exists() else None)
            for suffix, path in (("", database), ("-wal", wal_path), ("-shm", shm_path))
        )

    before = source_files()
    source_uri = database.resolve(strict=False).as_uri() + "?mode=ro"
    original_connect = sqlite3.connect
    source_opens: list[str] = []
    locked_source_attempts: list[tuple[int, str]] = []
    probe_source_handles = """
import sys
for name in sys.argv[1:]:
    try:
        with open(name, "rb") as source:
            source.read(1)
    except OSError as error:
        print("BLOCKED:" + str(error))
    else:
        print("OPENED")
"""
    original_copy = operational_update._copy_database

    def track_source_open(database_name, *args, **kwargs):
        if str(database_name) == source_uri:
            source_opens.append(str(database_name))
        return original_connect(database_name, *args, **kwargs)

    def copy_with_lock_probe(source, destination, deadline, *args, **kwargs) -> None:
        if source == database:
            probe = subprocess.run(
                [sys.executable, "-c", probe_source_handles, str(database), str(wal_path), str(shm_path)],
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
            locked_source_attempts.append((probe.returncode, probe.stdout.strip()))
        original_copy(source, destination, deadline, *args, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", track_source_open)
    monkeypatch.setattr(operational_update, "_copy_database", copy_with_lock_probe)
    rows, error = _database_paths(database, active_wal=True)
    after = source_files()

    assert after == before
    assert source_opens == []
    assert len(locked_source_attempts) == 1
    assert locked_source_attempts[0][0] == 0
    probe_lines = locked_source_attempts[0][1].splitlines()
    assert len(probe_lines) == 3
    assert all(line.startswith("BLOCKED:") for line in probe_lines)
    assert rows == {**OLD_PATHS, "1": NEW_PATHS["1"]}
    assert error is None


@pytest.mark.skipif(os.name != "nt", reason="requires Windows file-sharing semantics")
def test_sqlite_writer_started_during_capture_is_blocked_and_source_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, _ = _fixture(tmp_path)
    database = paths.database_path
    original_copy = operational_update._copy_database
    writer_attempts: list[tuple[int, str]] = []
    writer = """
import sqlite3, sys
try:
    connection = sqlite3.connect(sys.argv[1], timeout=0.2)
    connection.execute("UPDATE documents SET stored_path = ? WHERE id = 1", (sys.argv[2],))
    connection.commit()
    connection.close()
    print("WRITE_SUCCEEDED")
except sqlite3.Error as error:
    print("BLOCKED:" + str(error))
"""

    def source_files() -> tuple[tuple[str, bytes | None], ...]:
        return tuple(
            (suffix, path.read_bytes() if path.exists() else None)
            for suffix in ("", "-wal", "-shm")
            for path in (Path(f"{database}{suffix}"),)
        )

    def copy_with_writer_attempt(source, destination, deadline, *args, **kwargs) -> None:
        attempt = subprocess.run(
            [sys.executable, "-c", writer, str(database), NEW_PATHS["1"]],
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        writer_attempts.append((attempt.returncode, attempt.stdout.strip()))
        original_copy(source, destination, deadline, *args, **kwargs)

    before = source_files()
    monkeypatch.setattr(operational_update, "_copy_database", copy_with_writer_attempt)
    rows, error = _database_paths(database, active_wal=True)
    after = source_files()

    assert after == before, f"source changed while writer attempt ran: {writer_attempts}"
    assert writer_attempts and all(
        returncode == 0 and output.startswith("BLOCKED:")
        for returncode, output in writer_attempts
    )
    assert rows == OLD_PATHS
    assert error is None


@pytest.mark.skipif(os.name != "nt", reason="requires Windows file-sharing semantics")
def test_sidecar_added_during_copy_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, _ = _fixture(tmp_path)
    database = paths.database_path
    wal_path = Path(f"{database}-wal")
    original_copy = operational_update._copy_database
    injected_wal = b"persistent injected sidecar"
    copy_calls: list[Path] = []

    def copy_then_add_sidecar(source, destination, deadline, *args, **kwargs) -> None:
        original_copy(source, destination, deadline, *args, **kwargs)
        if source == database:
            copy_calls.append(source)
            wal_path.write_bytes(injected_wal)

    monkeypatch.setattr(operational_update, "_copy_database", copy_then_add_sidecar)
    rows, error = _database_paths(database, active_wal=True)

    assert copy_calls == [database]
    assert rows is None
    assert error == "DATABASE_CHANGED_DURING_SNAPSHOT"
    assert wal_path.read_bytes() == injected_wal


def _seed_uncheckpointed_wal(database: Path) -> tuple[Path, Path, bytes, bytes]:
    writer = """
import os, sqlite3, sys
connection = sqlite3.connect(sys.argv[1], timeout=0.1)
connection.execute("PRAGMA journal_mode = WAL")
connection.execute("PRAGMA wal_autocheckpoint = 0")
connection.execute("UPDATE documents SET stored_path = ? WHERE id = 1", (sys.argv[2],))
connection.commit()
print("COMMITTED", flush=True)
os._exit(0)
"""
    setup = subprocess.run(
        [sys.executable, "-c", writer, str(database), NEW_PATHS["1"]],
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert setup.returncode == 0, setup.stderr
    assert setup.stdout.strip() == "COMMITTED"

    wal_path = Path(f"{database}-wal")
    shm_path = Path(f"{database}-shm")
    assert wal_path.is_file() and shm_path.is_file()
    wal_bytes = wal_path.read_bytes()
    shm_bytes = shm_path.read_bytes()
    page_size = int.from_bytes(wal_bytes[8:12], "big")
    frame_size = 24 + page_size
    assert wal_bytes[:4] in (b"\x37\x7f\x06\x82", b"\x37\x7f\x06\x83")
    assert int.from_bytes(wal_bytes[4:8], "big") == 3007000
    assert page_size >= 512 and page_size <= 65536 and page_size & (page_size - 1) == 0
    database_page_size = int.from_bytes(database.read_bytes()[16:18], "big")
    assert page_size == (65536 if database_page_size == 1 else database_page_size)
    assert len(wal_bytes) >= 32 + frame_size
    assert (len(wal_bytes) - 32) % frame_size == 0
    assert len(shm_bytes) >= 32768 and len(shm_bytes) % 32768 == 0
    return wal_path, shm_path, wal_bytes, shm_bytes


def _assert_partial_sidecar_rejected_before_private_verification(
    database: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    source_paths = tuple(
        Path(f"{database}{suffix}") for suffix in ("", "-wal", "-shm")
    )

    def source_state() -> tuple[tuple[bool, bytes | None], ...]:
        return tuple(
            (path.is_file(), path.read_bytes() if path.is_file() else None)
            for path in source_paths
        )

    before = source_state()
    private_verification_paths: list[Path] = []
    original_read = operational_update._read_database_paths

    def observe_private_verification(path: Path, *args, **kwargs):
        if kwargs.get("immutable") is False:
            private_verification_paths.append(path)
        return original_read(path, *args, **kwargs)

    monkeypatch.setattr(operational_update, "_read_database_paths", observe_private_verification)
    rows, error = _database_paths(database, active_wal=True)
    after = source_state()

    assert after == before
    assert not private_verification_paths, (
        f"invalid source sidecar reached private SQLite: rows={rows!r}, error={error!r}"
    )
    assert rows is None
    assert error == "DATABASE_CAPTURE_UNPROVEN"


@pytest.mark.skipif(os.name != "nt", reason="requires Windows file-sharing semantics")
def test_capture_rejects_wal_header_without_complete_frame(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, _ = _fixture(tmp_path)
    wal_path, _shm_path, valid_wal, _valid_shm = _seed_uncheckpointed_wal(
        paths.database_path
    )
    wal_path.write_bytes(valid_wal[:32])

    _assert_partial_sidecar_rejected_before_private_verification(
        paths.database_path, monkeypatch
    )


@pytest.mark.skipif(os.name != "nt", reason="requires Windows file-sharing semantics")
def test_capture_rejects_misaligned_wal_frame_tail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, _ = _fixture(tmp_path)
    wal_path, _shm_path, valid_wal, _valid_shm = _seed_uncheckpointed_wal(
        paths.database_path
    )
    wal_path.write_bytes(valid_wal + b"\x00")

    _assert_partial_sidecar_rejected_before_private_verification(
        paths.database_path, monkeypatch
    )


@pytest.mark.skipif(os.name != "nt", reason="requires Windows file-sharing semantics")
@pytest.mark.parametrize(
    ("field_offset", "invalid_value"),
    [(8, 1000), (4, 0)],
    ids=("invalid-page-size", "unsupported-format-version"),
)
def test_capture_rejects_untrusted_wal_header_fields(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    field_offset: int,
    invalid_value: int,
) -> None:
    paths, _ = _fixture(tmp_path)
    wal_path, _shm_path, valid_wal, _valid_shm = _seed_uncheckpointed_wal(
        paths.database_path
    )
    invalid_wal = bytearray(valid_wal)
    invalid_wal[field_offset : field_offset + 4] = invalid_value.to_bytes(4, "big")
    wal_path.write_bytes(invalid_wal)

    _assert_partial_sidecar_rejected_before_private_verification(
        paths.database_path, monkeypatch
    )


@pytest.mark.skipif(os.name != "nt", reason="requires Windows file-sharing semantics")
def test_capture_rejects_shm_truncated_below_region(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, _ = _fixture(tmp_path)
    _wal_path, shm_path, _valid_wal, valid_shm = _seed_uncheckpointed_wal(
        paths.database_path
    )
    shm_path.write_bytes(valid_shm[: len(valid_shm) // 2])

    _assert_partial_sidecar_rejected_before_private_verification(
        paths.database_path, monkeypatch
    )


@pytest.mark.skipif(os.name != "nt", reason="requires Windows file-sharing semantics")
def test_capture_rejects_misaligned_shm_region(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, _ = _fixture(tmp_path)
    _wal_path, shm_path, _valid_wal, valid_shm = _seed_uncheckpointed_wal(
        paths.database_path
    )
    shm_path.write_bytes(valid_shm + b"\x00")

    _assert_partial_sidecar_rejected_before_private_verification(
        paths.database_path, monkeypatch
    )


@pytest.mark.skipif(os.name == "nt", reason="only verifies unsupported non-Windows behavior")
def test_active_capture_fails_closed_off_windows_without_source_sqlite_open(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, _ = _fixture(tmp_path)
    database = paths.database_path
    source_uri = database.resolve(strict=False).as_uri() + "?mode=ro"
    original_connect = sqlite3.connect
    source_opens: list[str] = []

    def track_source_open(database_name, *args, **kwargs):
        if str(database_name) == source_uri:
            source_opens.append(str(database_name))
        return original_connect(database_name, *args, **kwargs)

    before = database.read_bytes()
    monkeypatch.setattr(sqlite3, "connect", track_source_open)
    rows, error = _database_paths(database, active_wal=True)

    assert rows is None
    assert error == "DATABASE_CAPTURE_UNSUPPORTED"
    assert source_opens == []
    assert database.read_bytes() == before


def test_changed_input_during_observation_is_reported_unstable(tmp_path: Path) -> None:
    paths, _ = _fixture(tmp_path)

    def mutate_after_read(stage: str) -> None:
        if stage == "after_read":
            paths.config_path.write_bytes(b"external concurrent change")

    result = classify_operational_update_state(paths, observation_hook=mutate_after_read)

    assert result.classification == "OBSERVATION_UNSTABLE"
    assert result.input_stable is False
    assert "INPUT_CHANGED_DURING_OBSERVATION" in result.reasons


def _tree_identity(root: Path) -> tuple[tuple[str, str, int, str], ...]:
    rows = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            rows.append((relative, "link", 0, os.readlink(path)))
        elif path.is_dir():
            rows.append((relative, "directory", 0, ""))
        else:
            rows.append((relative, "file", path.stat().st_size, _sha(path)))
    return tuple(rows)
