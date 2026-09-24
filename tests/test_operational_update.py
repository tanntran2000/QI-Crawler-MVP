from __future__ import annotations

import hashlib
import json
import os
import sqlite3
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


def test_observation_is_read_only_and_preserves_tree_identity(tmp_path: Path) -> None:
    paths, journal = _fixture(tmp_path, phase="BACKUP_REQUIRED")
    _install_backup(paths, journal)
    wal = Path(f"{paths.database_path}-wal")
    shm = Path(f"{paths.database_path}-shm")
    wal.write_bytes(b"pre-existing wal evidence")
    shm.write_bytes(b"pre-existing shm evidence")

    before = _tree_identity(paths.root)
    result = _classify(paths)
    after = _tree_identity(paths.root)

    assert result.classification == "BACKUP_VALID"
    assert after == before


def test_observation_reads_committed_wal_state_without_mutating_sidecars(tmp_path: Path) -> None:
    paths, journal = _fixture(tmp_path, phase="DB_COMMITTED")
    _install_backup(paths, journal)
    _install_new_identity(paths)

    with closing(sqlite3.connect(paths.database_path)) as writer:
        assert writer.execute("PRAGMA journal_mode = WAL").fetchone() == ("wal",)
        writer.execute("PRAGMA wal_autocheckpoint = 0")
        writer.executemany(
            "UPDATE documents SET stored_path = ? WHERE id = ?",
            [(value, int(key)) for key, value in NEW_PATHS.items()],
        )
        writer.commit()

        before = _tree_identity(paths.root)
        result = _classify(paths)
        after = _tree_identity(paths.root)

        assert result.classification == "DB_COMMITTED_JOURNAL_LAG"
        identities = {item.name: item.value for item in result.evidence_identities}
        assert identities["database_state"] == "NEW"
        assert after == before


def test_wal_snapshot_generation_coherence(
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
        assert writer.execute("PRAGMA journal_mode = WAL").fetchone() == ("wal",)
        writer.execute("PRAGMA wal_autocheckpoint = 0")
        writer.execute(
            "UPDATE documents SET stored_path = ? WHERE id = 1",
            (generation_one["1"],),
        )
        writer.commit()
        wal_path = Path(f"{database}-wal")
        assert wal_path.is_file() and wal_path.stat().st_size > 32
        assert read_main_only(database) == initial
        assert writer.execute(
            "SELECT id, stored_path FROM documents WHERE id IN (1, 3000) ORDER BY id"
        ).fetchall() == [(1, generation_one["1"]), (3000, initial["3000"])]

        source_before_capture = source_sqlite_files()
        interleavings: list[tuple[int, tuple[int, ...]]] = []
        source_after_interleaving: list[tuple[tuple[str, bytes | None], ...]] = []
        source_states: list[tuple[str, tuple[tuple[str, bytes | None], ...]]] = []

        def record_source_state(label: str) -> None:
            source_states.append((label, source_sqlite_files()))

        source_uri = database.resolve(strict=False).as_uri() + "?mode=ro"
        original_connect = sqlite3.connect

        class InterleavingConnection:
            def __init__(self, connection: sqlite3.Connection) -> None:
                self.connection = connection

            def __getattr__(self, name: str):
                return getattr(self.connection, name)

            def execute(self, sql: str, *args, **kwargs):
                result = self.connection.execute(sql, *args, **kwargs)
                normalized_sql = sql.casefold().replace(" ", "")
                if normalized_sql == "pragmaquery_only=on":
                    record_source_state("query_only")
                elif normalized_sql == "pragmabusy_timeout=1000":
                    record_source_state("busy_timeout")
                elif normalized_sql == "pragmadata_version":
                    label = (
                        "data_version_start"
                        if not any(name == "data_version_start" for name, _ in source_states)
                        else "data_version_end"
                    )
                    record_source_state(label)
                return result

            def backup(self, destination: sqlite3.Connection, **kwargs: object) -> None:
                original_progress = kwargs["progress"]
                record_source_state("backup_start")

                def checkpoint_between_backup_pages(
                    status: int, remaining: int, total: int
                ) -> None:
                    if remaining > 0 and not interleavings:
                        checkpoint = writer.execute(
                            "PRAGMA wal_checkpoint(PASSIVE)"
                        ).fetchone()
                        writer.execute(
                            "UPDATE documents SET stored_path = ? WHERE id = 3000",
                            (generation_two["3000"],),
                        )
                        writer.commit()
                        interleavings.append((remaining, checkpoint))
                        source_after_interleaving.append(source_sqlite_files())
                        source_states.append(("post_writer", source_after_interleaving[-1]))
                    if original_progress is not None:
                        original_progress(status, remaining, total)

                self.connection.backup(
                    destination,
                    **{**kwargs, "progress": checkpoint_between_backup_pages},
                )
                record_source_state("backup_end")

            def close(self) -> None:
                self.connection.close()
                record_source_state("source_close")

        def connect_with_interleaving(database_name, *args, **kwargs):
            connection = original_connect(database_name, *args, **kwargs)
            if str(database_name) == source_uri:
                wrapped = InterleavingConnection(connection)
                record_source_state("source_open")
                return wrapped
            return connection

        monkeypatch.setattr(sqlite3, "connect", connect_with_interleaving)
        rows, error = _database_paths(database, active_wal=True)
        source_after_capture = source_sqlite_files()
        source_states.append(("helper_return", source_after_capture))

    assert interleavings and interleavings[0][0] > 0
    assert interleavings[0][1][0] == 0
    assert interleavings[0][1][2] > 0
    assert source_before_capture != source_after_interleaving[0]
    if error is not None:
        logical_result_valid = rows is None and error in {
            "DATABASE_UNREADABLE",
            "DATABASE_CHANGED_DURING_SNAPSHOT",
            "DATABASE_SNAPSHOT_TIMEOUT",
        }
        logical_outcome = f"explicit_error:{error}"
    else:
        logical_result_valid = rows in (generation_one, generation_two)
        logical_outcome = (
            "generation_one"
            if rows == generation_one
            else "generation_two"
            if rows == generation_two
            else "mixed_or_unknown_generation"
        )
    post_writer_index = next(
        index for index, (label, _state) in enumerate(source_states) if label == "post_writer"
    )
    post_writer_state = source_states[post_writer_index][1]
    source_state_changes = {
        label: tuple(
            suffix
            for (suffix, data), (_baseline_suffix, baseline_data) in zip(state, post_writer_state)
            if data != baseline_data
        )
        for label, state in source_states[post_writer_index + 1 :]
        if state != post_writer_state
    }
    source_state_digests = {
        label: {
            suffix: None if data is None else hashlib.sha256(data).hexdigest()
            for suffix, data in state
        }
        for label, state in source_states
    }
    source_bytes_unchanged = source_after_capture == post_writer_state
    assert logical_result_valid and source_bytes_unchanged, (
        f"logical_outcome={logical_outcome}; error={error!r}; "
        f"source_bytes_unchanged={source_bytes_unchanged}; "
        f"source_state_changes_after_post_writer={source_state_changes!r}; "
        f"source_state_digests={source_state_digests!r}"
    )


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


def test_active_wal_exclusive_lock_returns_unreadable_within_finite_timeout(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    paths, _ = _fixture(tmp_path)
    database = paths.database_path
    wal_path = Path(f"{database}-wal")
    shm_path = Path(f"{database}-shm")
    helper_calls: list[tuple[Path, bool]] = []
    original_database_paths = _database_paths

    def observe_helper(path: Path, *, active_wal: bool):
        helper_calls.append((path, active_wal))
        return original_database_paths(path, active_wal=active_wal)

    monkeypatch.setattr(operational_update, "_database_paths", observe_helper)
    def source_sqlite_files() -> tuple[tuple[str, bytes | None], ...]:
        return tuple(
            (suffix, path.read_bytes() if path.exists() else None)
            for suffix in ("", "-wal", "-shm")
            for path in (Path(f"{database}{suffix}"),)
        )

    with closing(sqlite3.connect(database, timeout=0.1)) as blocker:
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
        blocker.execute("SELECT id FROM documents LIMIT 1").fetchone()
        assert wal_path.is_file() and wal_path.stat().st_size > 32
        assert not shm_path.exists()
        source_before_probe = source_sqlite_files()
        uri = database.as_uri() + "?mode=ro"
        probe_error: sqlite3.OperationalError | None = None
        try:
            with closing(sqlite3.connect(uri, uri=True, timeout=0)) as probe:
                probe.execute("SELECT id FROM documents LIMIT 1").fetchone()
        except sqlite3.OperationalError as exc:
            probe_error = exc
        assert probe_error is not None, "zero-time read probe unexpectedly acquired the database"
        assert "locked" in str(probe_error).lower() or "busy" in str(probe_error).lower()
        source_before_helper = source_sqlite_files()

        started = time.monotonic()
        rows, error = operational_update._database_paths(database, active_wal=True)
        elapsed = time.monotonic() - started
        source_after_read = source_sqlite_files()

    assert helper_calls == [(database, True)]
    assert source_after_read == source_before_helper
    assert rows is None
    assert error in {"DATABASE_UNREADABLE", "DATABASE_SNAPSHOT_TIMEOUT"}
    assert elapsed < 10.0


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
