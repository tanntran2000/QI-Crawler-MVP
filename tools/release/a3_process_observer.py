"""Fail-closed process census primitives for the A3 release safety prototype.

The observer is intentionally dependency-free.  Windows collection is performed by
the bounded PowerShell probe; this module owns identity, classification and the
zero-proof decision so the same rules are exercised by tests and the probe.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from pathlib import Path
from typing import Any


class ProcessClass(StrEnum):
    SANDBOX_LEGACY = "SANDBOX_LEGACY"
    SANDBOX_CONTROLLER = "SANDBOX_CONTROLLER"
    SANDBOX_STUB = "SANDBOX_STUB"
    SANDBOX_OTHER = "SANDBOX_OTHER"
    OBSERVER_SCOPE_VIOLATION = "OBSERVER_SCOPE_VIOLATION"
    UNRESOLVED_RELEVANT = "UNRESOLVED_RELEVANT"
    IRRELEVANT = "IRRELEVANT"


@dataclass(frozen=True)
class ObserverConfig:
    trial_root: Path | None = None
    legacy_paths: frozenset[Path] = frozenset()
    controller_paths: frozenset[Path] = frozenset()
    stub_paths: frozenset[Path] = frozenset()
    controller_pids: frozenset[int] = frozenset()
    route_pids: frozenset[int] = frozenset()
    legacy_sha256: str | None = None
    controller_sha256: str | None = None
    stub_sha256: str | None = None

    def __post_init__(self) -> None:
        if self.trial_root is None:
            raise ValueError("OBSERVER_SCOPE_VIOLATION: missing sandbox root")
        object.__setattr__(self, "trial_root", _norm(self.trial_root))
        for field_name in (
            "legacy_paths",
            "controller_paths",
            "stub_paths",
        ):
            paths = frozenset(_norm(path) for path in getattr(self, field_name))
            if any(not _is_under(path, self.trial_root) for path in paths):
                raise ValueError(f"OBSERVER_SCOPE_VIOLATION: {field_name}")
            object.__setattr__(
                self,
                field_name,
                paths,
            )


@dataclass(frozen=True)
class ProcessEvidence:
    pid: int | None
    parent_pid: int | None
    image_path: str | None
    image_sha256: str | None
    start_time_utc: str | None
    command_line: str | None
    access_status: str
    classification: ProcessClass
    evidence_source: str

    def to_dict(self) -> dict[str, Any]:
        result = {
            "pid": self.pid,
            "parent_pid": self.parent_pid,
            "image_path": self.image_path,
            "image_sha256": self.image_sha256,
            "start_time_utc": self.start_time_utc,
            "command_line": self.command_line,
            "access_status": self.access_status,
            "classification": self.classification.value,
            "evidence_source": self.evidence_source,
        }
        return result


@dataclass(frozen=True)
class CensusSnapshot:
    event_name: str
    timestamp_utc: str
    records: tuple[ProcessEvidence, ...]
    legacy_count: int
    unresolved_relevant_count: int
    legacy_zero_proven: bool

    def to_dict(self) -> dict[str, Any]:
        return {
            "event_name": self.event_name,
            "timestamp_utc": self.timestamp_utc,
            "records": [record.to_dict() for record in self.records],
            "legacy_count": self.legacy_count,
            "unresolved_relevant_count": self.unresolved_relevant_count,
            "legacy_zero_proven": self.legacy_zero_proven,
        }


F5_CANONICAL_REQUIRED_GATES = frozenset({
    "observer_self_test", "legacy_zero_P1", "legacy_zero_P2", "legacy_zero_P3",
    "unresolved_relevant_zero_P1_P2_P3", "controller_alive_at_P2", "job_created",
    "controller_assigned_to_job", "job_active_at_P2", "job_descendants_contained",
    "writer_revalidation", "canonical_stub_verified", "job_active_before_kill",
    "job_active_after_kill", "outer_orchestrator_alive", "exclusive_trial_lock_retained",
    "barrier_sequence", "controller_tree_dead_at_P3", "process_tree_positive_control",
    "process_tree_fail_closed_test", "route_contract", "sqlite_writer_quiescence",
    "db_generation_unchanged", "recovery_verified", "final_schema_expected",
    "final_logical_digest_unchanged", "final_stub_identity", "evidence_receipts_complete",
    "evidence_manifest_complete",
})


def aggregate_mandatory_gates(
    gates: Mapping[str, Any], *, contract: str | None = None
) -> tuple[str, bool]:
    """Return a fail-closed aggregate verdict for a probe gate mapping."""

    if not gates:
        return "HOLD", False
    if contract is not None and (
        contract != "F5_CANONICAL_V1" or set(gates) != F5_CANONICAL_REQUIRED_GATES
    ):
        return "HOLD", False
    passed = all(value is True for value in gates.values())
    return ("PASS", True) if passed else ("HOLD", False)


def _norm(path: Path | str) -> Path:
    # Lexical normalization never probes an outside path supplied by a process
    # record. Filesystem dereferencing belongs to the sandbox-only probe gate.
    return Path(os.path.abspath(os.path.normpath(str(path))))


def _same_path(left: str | Path | None, right: Path) -> bool:
    return left is not None and _norm(str(left)) == right


class A3ProcessObserver:
    def __init__(self, config: ObserverConfig, *, known_pids: frozenset[int] = frozenset()) -> None:
        self.config = config
        self.known_pids = known_pids

    def classify_record(self, raw: Mapping[str, Any]) -> ProcessEvidence:
        pid = _int_or_none(raw.get("pid"))
        parent_pid = _int_or_none(raw.get("parent_pid"))
        image_path_value = raw.get("image_path")
        image_path = str(image_path_value) if image_path_value not in (None, "") else None
        digest = _lower(raw.get("image_sha256"))
        access_status = str(raw.get("access_status") or "UNKNOWN")
        source = str(raw.get("evidence_source") or "unknown")
        readable = image_path is not None and access_status.upper() == "PASS"
        known_pid = pid in self.known_pids if pid is not None else False
        explicitly_relevant = bool(raw.get("relevant") or raw.get("child_of_known_pid"))

        in_sandbox = bool(image_path is not None and _is_under(_norm(image_path), self.config.trial_root))
        if not readable and (known_pid or explicitly_relevant):
            classification = ProcessClass.UNRESOLVED_RELEVANT
        elif pid in self.config.controller_pids:
            classification = ProcessClass.SANDBOX_CONTROLLER
        elif pid in self.config.route_pids:
            classification = ProcessClass.SANDBOX_OTHER
        elif in_sandbox:
            if any(_same_path(image_path, candidate) for candidate in self.config.legacy_paths) or (
                self.config.legacy_sha256 and digest == self.config.legacy_sha256.lower()
            ):
                classification = ProcessClass.SANDBOX_LEGACY
            elif any(_same_path(image_path, candidate) for candidate in self.config.controller_paths) or (
                self.config.controller_sha256 and digest == self.config.controller_sha256.lower()
            ):
                classification = ProcessClass.SANDBOX_CONTROLLER
            elif any(_same_path(image_path, candidate) for candidate in self.config.stub_paths) or (
                self.config.stub_sha256 and digest == self.config.stub_sha256.lower()
            ):
                classification = ProcessClass.SANDBOX_STUB
            else:
                classification = ProcessClass.SANDBOX_OTHER
        elif known_pid or explicitly_relevant:
            classification = ProcessClass.OBSERVER_SCOPE_VIOLATION
        else:
            classification = ProcessClass.IRRELEVANT

        return ProcessEvidence(
            pid=pid,
            parent_pid=parent_pid,
            image_path=image_path,
            image_sha256=digest,
            start_time_utc=_string_or_none(raw.get("start_time_utc")),
            command_line=_string_or_none(raw.get("command_line")),
            access_status=access_status,
            classification=classification,
            evidence_source=source,
        )

    def classify_records(self, records: Iterable[Mapping[str, Any]]) -> tuple[ProcessEvidence, ...]:
        return tuple(self.classify_record(record) for record in records)

    def census(
        self,
        records: Iterable[Mapping[str, Any]],
        *,
        event_name: str,
        positive_control_passed: bool,
        known_legacy_roots_absent: bool,
        timestamp_utc: str | None = None,
    ) -> CensusSnapshot:
        evidence = self.classify_records(records)
        legacy_count = sum(record.classification == ProcessClass.SANDBOX_LEGACY for record in evidence)
        unresolved_count = sum(
            record.classification in (ProcessClass.UNRESOLVED_RELEVANT, ProcessClass.OBSERVER_SCOPE_VIOLATION)
            for record in evidence
        )
        zero_proven = bool(
            positive_control_passed
            and known_legacy_roots_absent
            and legacy_count == 0
            and unresolved_count == 0
        )
        return CensusSnapshot(
            event_name=event_name,
            timestamp_utc=timestamp_utc or datetime.now(UTC).isoformat(),
            records=evidence,
            legacy_count=legacy_count,
            unresolved_relevant_count=unresolved_count,
            legacy_zero_proven=zero_proven,
        )


def _is_under(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _lower(value: Any) -> str | None:
    return str(value).lower() if value not in (None, "") else None


def _string_or_none(value: Any) -> str | None:
    return str(value) if value not in (None, "") else None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _cli() -> int:
    parser = argparse.ArgumentParser(description="Classify a bounded Windows process census")
    parser.add_argument("--aggregate-gates-json", type=Path)
    parser.add_argument("--records-json", type=Path)
    parser.add_argument("--config-json", type=Path)
    parser.add_argument("--event")
    parser.add_argument("--positive-control", action="store_true")
    parser.add_argument("--roots-absent", action="store_true")
    args = parser.parse_args()
    if args.aggregate_gates_json:
        raw_gates = json.loads(args.aggregate_gates_json.read_text(encoding="utf-8"))
        gates = raw_gates.get("mandatory_gates", raw_gates) if isinstance(raw_gates, dict) else {}
        contract = raw_gates.get("gate_contract") if isinstance(raw_gates, dict) else None
        verdict, passed = aggregate_mandatory_gates(gates, contract=contract)
        print(json.dumps({"final_probe_result": verdict, "all_mandatory_gates_pass": passed}, sort_keys=True))
        return 0 if passed else 2
    if not args.records_json or not args.config_json or not args.event:
        parser.error("--records-json, --config-json and --event are required unless --aggregate-gates-json is used")
    records = json.loads(args.records_json.read_text(encoding="utf-8"))
    raw = json.loads(args.config_json.read_text(encoding="utf-8"))
    if raw.get("production_paths"):
        raise ValueError("OBSERVER_SCOPE_VIOLATION: production_paths")
    config = ObserverConfig(
        trial_root=Path(raw["trial_root"]) if raw.get("trial_root") else None,
        legacy_paths=frozenset(Path(item) for item in raw.get("legacy_paths", [])),
        controller_paths=frozenset(Path(item) for item in raw.get("controller_paths", [])),
        stub_paths=frozenset(Path(item) for item in raw.get("stub_paths", [])),
        controller_pids=frozenset(int(item) for item in raw.get("controller_pids", [])),
        route_pids=frozenset(int(item) for item in raw.get("route_pids", [])),
        legacy_sha256=raw.get("legacy_sha256"),
        controller_sha256=raw.get("controller_sha256"),
        stub_sha256=raw.get("stub_sha256"),
    )
    observer = A3ProcessObserver(config, known_pids=frozenset(int(item) for item in raw.get("known_pids", [])))
    snapshot = observer.census(
        records,
        event_name=args.event,
        positive_control_passed=args.positive_control,
        known_legacy_roots_absent=args.roots_absent,
    )
    print(json.dumps(snapshot.to_dict(), ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":  # pragma: no cover - exercised by the Windows probe
    raise SystemExit(_cli())
