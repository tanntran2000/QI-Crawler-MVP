"""Rollback-first recovery prototype for the bounded AO-04 sandbox.

This module never runs an Alembic migration and only opens the supplied SQLite
database in read-only mode.  Production activation remains outside this prototype.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import time
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any, Protocol

from tools.release.a3_process_observer import CensusSnapshot, sha256_file


class RecoveryStatus(StrEnum):
    LEGACY_READY = "LEGACY_READY"
    RECOVERY_REQUIRED = "RECOVERY_REQUIRED"
    MAINTENANCE_RECOVERY_REQUIRED = "MAINTENANCE_RECOVERY_REQUIRED"


class SimulatedRecoveryCrash(RuntimeError):
    """Test/probe failpoint representing a hard stop at a journal boundary."""


class MaterialWriteBoundExceeded(RuntimeError):
    """A recovery artifact would exceed its declared finite persistence bound."""


class ObserverLike(Protocol):
    def snapshot(self) -> CensusSnapshot: ...


@dataclass(frozen=True)
class WriterProbeResult:
    success: bool
    schema: str | None
    message: str


@dataclass(frozen=True)
class RecoveryResult:
    status: RecoveryStatus
    mutated: bool
    reason: str
    db_generation_unchanged: bool
    journal_phase: str | None


def _sha(path: Path) -> str:
    return sha256_file(path)


def _inventory(root: Path) -> tuple[tuple[str, int, str], ...]:
    if not root.exists():
        return ()
    entries: list[tuple[str, int, str]] = []
    for path in sorted(root.glob("egp.db*"), key=lambda item: item.name):
        if path.is_file():
            entries.append((path.name, path.stat().st_size, _sha(path)))
    return tuple(entries)


def _read_schema(db_path: Path) -> str | None:
    if not db_path.is_file():
        return None
    uri = f"file:{db_path.resolve().as_posix()}?mode=ro"
    try:
        with sqlite3.connect(uri, uri=True, timeout=0) as connection:
            row = connection.execute(
                "SELECT version_num FROM alembic_version ORDER BY version_num LIMIT 1"
            ).fetchone()
            return str(row[0]) if row else None
    except sqlite3.Error:
        return None


def sqlite_writer_quiescence_probe(db_path: Path) -> WriterProbeResult:
    """Prove a zero-timeout immediate lock can be opened and rolled back read-only."""

    schema = _read_schema(db_path)
    if schema is None:
        return WriterProbeResult(False, None, "schema unavailable")
    uri = f"file:{db_path.resolve().as_posix()}?mode=ro"
    try:
        with sqlite3.connect(uri, uri=True, timeout=0, isolation_level=None) as connection:
            connection.execute("BEGIN IMMEDIATE")
            connection.execute("ROLLBACK")
    except sqlite3.Error as exc:
        return WriterProbeResult(False, schema, f"writer lock unavailable: {exc}")
    return WriterProbeResult(True, schema, "BEGIN IMMEDIATE / ROLLBACK succeeded")


class RecoveryController:
    def __init__(
        self,
        *,
        canonical_path: Path,
        recovery_path: Path,
        transaction_root: Path,
        db_root: Path,
        expected_legacy_sha256: str,
        expected_schema: str,
        observer: ObserverLike,
        barrier_confirmed: bool = False,
        failpoint: str | None = None,
        pause_file: Path | None = None,
        max_journal_bytes: int = 1_048_576,
        max_pause_marker_bytes: int = 64,
    ) -> None:
        self.canonical_path = Path(canonical_path)
        self.recovery_path = Path(recovery_path)
        self.transaction_root = Path(transaction_root)
        self.db_root = Path(db_root)
        self.expected_legacy_sha256 = expected_legacy_sha256.lower()
        self.expected_schema = expected_schema
        self.observer = observer
        self.barrier_confirmed = barrier_confirmed
        self.failpoint = failpoint
        self.pause_file = Path(pause_file) if pause_file else None
        self.max_journal_bytes = max_journal_bytes
        self.max_pause_marker_bytes = max_pause_marker_bytes
        self.journal_path = self.transaction_root / "recovery_journal.json"

    def _load_journal(self) -> dict[str, Any] | None:
        if not self.journal_path.is_file():
            return None
        try:
            value = json.loads(self.journal_path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {"phase": "UNKNOWN"}
        return value if isinstance(value, dict) else {"phase": "UNKNOWN"}

    def _write_journal(self, phase: str, db_generation: tuple[tuple[str, int, str], ...]) -> None:
        self.transaction_root.mkdir(parents=True, exist_ok=True)
        payload = {
            "phase": phase,
            "canonical": str(self.canonical_path),
            "recovery": str(self.recovery_path),
            "legacy_sha256": self.expected_legacy_sha256,
            "db_generation": [list(entry) for entry in db_generation],
            "barrier_confirmed": self.barrier_confirmed,
        }
        temporary = self.journal_path.with_suffix(".tmp")
        raw = json.dumps(payload, sort_keys=True).encode("utf-8")
        if len(raw) > self.max_journal_bytes:
            raise MaterialWriteBoundExceeded(
                "MATERIAL_WRITE_BOUND_EXCEEDED: RECOVERY journal"
            )
        try:
            with temporary.open("xb") as stream:
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.journal_path)
        except Exception:
            temporary.unlink(missing_ok=True)
            raise

    def _crash_if_requested(self, phase: str) -> None:
        if self.failpoint == phase:
            if self.pause_file:
                self.pause_file.parent.mkdir(parents=True, exist_ok=True)
                raw = phase.encode("utf-8")
                if len(raw) > self.max_pause_marker_bytes:
                    raise MaterialWriteBoundExceeded(
                        "MATERIAL_WRITE_BOUND_EXCEEDED: RECOVERY pause marker"
                    )
                self.pause_file.write_bytes(raw)
                while self.pause_file.exists():
                    time.sleep(0.05)
            raise SimulatedRecoveryCrash(f"simulated crash at {phase}")

    def _result(
        self,
        status: RecoveryStatus,
        *,
        mutated: bool,
        reason: str,
        before: tuple[tuple[str, int, str], ...],
        phase: str | None,
    ) -> RecoveryResult:
        return RecoveryResult(
            status=status,
            mutated=mutated,
            reason=reason,
            db_generation_unchanged=before == _inventory(self.db_root),
            journal_phase=phase,
        )

    def recover(self) -> RecoveryResult:
        before = _inventory(self.db_root)
        journal = self._load_journal()
        phase = str(journal.get("phase")) if journal else None
        if self.barrier_confirmed or phase == "BARRIER_CONFIRMED":
            return self._result(
                RecoveryStatus.MAINTENANCE_RECOVERY_REQUIRED,
                mutated=False,
                reason="barrier confirmed; automatic legacy restore forbidden",
                before=before,
                phase=phase,
            )

        snapshot = self.observer.snapshot()
        if not snapshot.legacy_zero_proven or snapshot.unresolved_relevant_count:
            return self._result(
                RecoveryStatus.RECOVERY_REQUIRED,
                mutated=False,
                reason="legacy zero is not proven",
                before=before,
                phase=phase,
            )

        if _read_schema(self.db_root / "egp.db") != self.expected_schema:
            return self._result(
                RecoveryStatus.RECOVERY_REQUIRED,
                mutated=False,
                reason="database schema is not the expected pre-barrier revision",
                before=before,
                phase=phase,
            )

        if not self.recovery_path.is_file() or _sha(self.recovery_path) != self.expected_legacy_sha256:
            return self._result(
                RecoveryStatus.RECOVERY_REQUIRED,
                mutated=False,
                reason="recovery executable identity is not exact",
                before=before,
                phase=phase,
            )

        if self.canonical_path.is_dir() or self.transaction_root.is_file():
            return self._result(
                RecoveryStatus.RECOVERY_REQUIRED,
                mutated=False,
                reason="canonical or transaction path has an unexpected type",
                before=before,
                phase=phase,
            )

        if self.canonical_path.is_file() and _sha(self.canonical_path) == self.expected_legacy_sha256:
            self._write_journal("LEGACY_READY", before)
            return self._result(
                RecoveryStatus.LEGACY_READY,
                mutated=False,
                reason="canonical legacy identity already restored",
                before=before,
                phase="LEGACY_READY",
            )

        self._write_journal("RECOVERY_INTENT", before)
        self._crash_if_requested("R0")

        self.transaction_root.mkdir(parents=True, exist_ok=True)
        staged = self.transaction_root / "legacy.exe.stage"
        if not staged.is_file() or _sha(staged) != self.expected_legacy_sha256:
            shutil.copyfile(self.recovery_path, staged)
        if _sha(staged) != self.expected_legacy_sha256:
            return self._result(
                RecoveryStatus.RECOVERY_REQUIRED,
                mutated=False,
                reason="staged recovery identity failed verification",
                before=before,
                phase="RECOVERY_INTENT",
            )
        self._write_journal("STAGED_VERIFIED", before)
        self._crash_if_requested("R1")

        self.canonical_path.parent.mkdir(parents=True, exist_ok=True)
        os.replace(staged, self.canonical_path)
        self._write_journal("CANONICAL_REPLACED", before)
        self._crash_if_requested("R2")

        if _sha(self.canonical_path) != self.expected_legacy_sha256:
            return self._result(
                RecoveryStatus.RECOVERY_REQUIRED,
                mutated=True,
                reason="canonical identity failed after replacement",
                before=before,
                phase="CANONICAL_REPLACED",
            )
        self._write_journal("CANONICAL_VERIFIED", before)
        self._crash_if_requested("R3")

        after = _inventory(self.db_root)
        if after != before:
            return self._result(
                RecoveryStatus.RECOVERY_REQUIRED,
                mutated=True,
                reason="database generation changed during recovery",
                before=before,
                phase="CANONICAL_VERIFIED",
            )
        self._write_journal("LEGACY_READY", before)
        return RecoveryResult(
            status=RecoveryStatus.LEGACY_READY,
            mutated=True,
            reason="legacy executable restored and verified",
            db_generation_unchanged=True,
            journal_phase="LEGACY_READY",
        )


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Run bounded rollback-first recovery")
    parser.add_argument("--writer-probe", type=Path)
    parser.add_argument("--canonical", type=Path)
    parser.add_argument("--recovery", type=Path)
    parser.add_argument("--transaction-root", type=Path)
    parser.add_argument("--db-root", type=Path)
    parser.add_argument("--legacy-sha256")
    parser.add_argument("--expected-schema")
    parser.add_argument("--observer-json", type=Path)
    parser.add_argument("--barrier-confirmed", action="store_true")
    parser.add_argument("--failpoint")
    parser.add_argument("--pause-file", type=Path)
    args = parser.parse_args()
    if args.writer_probe:
        result = sqlite_writer_quiescence_probe(args.writer_probe)
        print(json.dumps({"success": result.success, "schema": result.schema, "message": result.message}))
        return 0 if result.success else 2
    required = {
        "canonical": args.canonical,
        "recovery": args.recovery,
        "transaction_root": args.transaction_root,
        "db_root": args.db_root,
        "legacy_sha256": args.legacy_sha256,
        "expected_schema": args.expected_schema,
        "observer_json": args.observer_json,
    }
    missing = [name for name, value in required.items() if value is None]
    if missing:
        parser.error("missing recovery arguments: " + ", ".join(missing))
    raw = json.loads(args.observer_json.read_text(encoding="utf-8"))

    class _CliObserver:
        def snapshot(self) -> CensusSnapshot:
            return CensusSnapshot(
                event_name=str(raw.get("event_name", "cli")),
                timestamp_utc=str(raw.get("timestamp_utc", "")),
                records=(),
                legacy_count=int(raw.get("legacy_count", 0)),
                unresolved_relevant_count=int(raw.get("unresolved_relevant_count", 0)),
                legacy_zero_proven=bool(raw.get("legacy_zero_proven", False)),
            )

    result = RecoveryController(
        canonical_path=args.canonical,
        recovery_path=args.recovery,
        transaction_root=args.transaction_root,
        db_root=args.db_root,
        expected_legacy_sha256=args.legacy_sha256,
        expected_schema=args.expected_schema,
        observer=_CliObserver(),
        barrier_confirmed=args.barrier_confirmed,
        failpoint=args.failpoint,
        pause_file=args.pause_file,
    ).recover()
    print(json.dumps({"status": result.status.value, "mutated": result.mutated, "reason": result.reason}))
    return 0 if result.status == RecoveryStatus.LEGACY_READY else 2


if __name__ == "__main__":  # pragma: no cover - exercised by the Windows probe
    raise SystemExit(_cli())
