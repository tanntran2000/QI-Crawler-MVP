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
import re
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


_IDENTITY_BINDING_FIELDS = frozenset(
    {"pid", "start_time_utc", "role", "executable_sha256", "identity_source"}
)
_IDENTITY_BINDING_ROLES = frozenset(
    {ProcessClass.SANDBOX_LEGACY, ProcessClass.SANDBOX_STUB}
)
_IDENTITY_BINDING_SOURCES = frozenset({"PROCESS_HANDLE", "LAUNCH_RECEIPT"})
_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def _parse_utc_timestamp(value: object) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        parsed = datetime.fromisoformat(value.strip())
    except ValueError:
        return None
    if parsed.tzinfo is None or parsed.utcoffset() is None or parsed.year < 1970:
        return None
    return parsed.astimezone(UTC)


def _normalize_sha256(value: object) -> str | None:
    if not isinstance(value, str) or not _SHA256_RE.fullmatch(value.strip()):
        return None
    return value.strip().lower()


@dataclass(frozen=True)
class ProcessIdentityBinding:
    """Immutable process-lifetime authority for a role-sensitive executable."""

    pid: int
    start_time_utc: str
    role: ProcessClass | str
    executable_sha256: str
    identity_source: str

    def __post_init__(self) -> None:
        if isinstance(self.pid, bool) or not isinstance(self.pid, int):
            raise TypeError("PROCESS_IDENTITY_BINDING: pid")
        pid = self.pid
        if pid <= 0:
            raise ValueError("PROCESS_IDENTITY_BINDING: pid")

        parsed = _parse_utc_timestamp(self.start_time_utc)
        if parsed is None:
            raise ValueError("PROCESS_IDENTITY_BINDING: start_time_utc")

        try:
            role = (
                self.role
                if isinstance(self.role, ProcessClass)
                else ProcessClass(str(self.role))
            )
        except ValueError as exc:
            raise ValueError("PROCESS_IDENTITY_BINDING: role") from exc
        if role not in _IDENTITY_BINDING_ROLES:
            raise ValueError("PROCESS_IDENTITY_BINDING: role")

        digest = _normalize_sha256(self.executable_sha256)
        if digest is None:
            raise ValueError("PROCESS_IDENTITY_BINDING: executable_sha256")

        if (
            not isinstance(self.identity_source, str)
            or self.identity_source not in _IDENTITY_BINDING_SOURCES
        ):
            raise ValueError("PROCESS_IDENTITY_BINDING: identity_source")

        object.__setattr__(self, "pid", pid)
        object.__setattr__(self, "start_time_utc", parsed.isoformat())
        object.__setattr__(self, "role", role)
        object.__setattr__(self, "executable_sha256", digest)

    @classmethod
    def from_mapping(cls, raw: Mapping[str, object]) -> ProcessIdentityBinding:
        if not isinstance(raw, Mapping) or set(raw) != _IDENTITY_BINDING_FIELDS:
            raise ValueError("PROCESS_IDENTITY_BINDING: fields")
        return cls(
            pid=raw["pid"],
            start_time_utc=raw["start_time_utc"],
            role=raw["role"],
            executable_sha256=raw["executable_sha256"],
            identity_source=raw["identity_source"],
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "pid": self.pid,
            "start_time_utc": self.start_time_utc,
            "role": self.role.value,
            "executable_sha256": self.executable_sha256,
            "identity_source": self.identity_source,
        }


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
    authoritative_process_identities: tuple[ProcessIdentityBinding | Mapping[str, object], ...] = ()

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

        try:
            raw_bindings = tuple(self.authoritative_process_identities)
        except TypeError as exc:
            raise TypeError("PROCESS_IDENTITY_BINDING: collection") from exc
        bindings: list[ProcessIdentityBinding] = []
        seen_pids: set[int] = set()
        for raw_binding in raw_bindings:
            if isinstance(raw_binding, ProcessIdentityBinding):
                binding = raw_binding
            elif isinstance(raw_binding, Mapping):
                binding = ProcessIdentityBinding.from_mapping(raw_binding)
            else:
                raise TypeError("PROCESS_IDENTITY_BINDING: object")
            if binding.pid in seen_pids:
                raise ValueError("PROCESS_IDENTITY_BINDING: duplicate")
            seen_pids.add(binding.pid)
            bindings.append(binding)
        object.__setattr__(self, "authoritative_process_identities", tuple(bindings))


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

    def _binding_for_pid(self, pid: int | None) -> ProcessIdentityBinding | None:
        if pid is None:
            return None
        return next(
            (binding for binding in self.config.authoritative_process_identities if binding.pid == pid),
            None,
        )

    def _resolve_binding(
        self,
        binding: ProcessIdentityBinding,
        *,
        image_path: str | None,
        in_sandbox: bool,
        record_start_time: object,
    ) -> ProcessClass | None:
        if not in_sandbox or image_path is None:
            return None
        record_created = _parse_utc_timestamp(record_start_time)
        binding_created = _parse_utc_timestamp(binding.start_time_utc)
        if record_created is None or binding_created is None or record_created != binding_created:
            return None
        expected_sha = {
            ProcessClass.SANDBOX_LEGACY: self.config.legacy_sha256,
            ProcessClass.SANDBOX_STUB: self.config.stub_sha256,
        }[binding.role]
        if _normalize_sha256(expected_sha) != binding.executable_sha256:
            return None
        role_paths = {
            ProcessClass.SANDBOX_LEGACY: self.config.legacy_paths,
            ProcessClass.SANDBOX_STUB: self.config.stub_paths,
        }[binding.role]
        if not any(_same_path(image_path, candidate) for candidate in role_paths):
            return None
        return binding.role

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
        binding = self._binding_for_pid(pid)
        if not readable and (known_pid or explicitly_relevant):
            classification = ProcessClass.UNRESOLVED_RELEVANT
        elif pid in self.config.controller_pids:
            classification = ProcessClass.SANDBOX_CONTROLLER
        elif pid in self.config.route_pids:
            classification = ProcessClass.SANDBOX_OTHER
        elif binding is not None:
            classification = self._resolve_binding(
                binding,
                image_path=image_path,
                in_sandbox=in_sandbox,
                record_start_time=raw.get("start_time_utc"),
            ) or ProcessClass.UNRESOLVED_RELEVANT
        elif in_sandbox:
            legacy_path = any(_same_path(image_path, candidate) for candidate in self.config.legacy_paths)
            stub_path = any(_same_path(image_path, candidate) for candidate in self.config.stub_paths)
            if legacy_path and stub_path:
                classification = ProcessClass.UNRESOLVED_RELEVANT
            elif legacy_path or (
                self.config.legacy_sha256 and digest == self.config.legacy_sha256.lower()
            ):
                classification = ProcessClass.SANDBOX_LEGACY
            elif any(_same_path(image_path, candidate) for candidate in self.config.controller_paths) or (
                self.config.controller_sha256 and digest == self.config.controller_sha256.lower()
            ):
                classification = ProcessClass.SANDBOX_CONTROLLER
            elif stub_path or (
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
    if not isinstance(raw, dict):
        raise TypeError("OBSERVER_CONFIG_INVALID")
    if raw.get("production_paths"):
        raise ValueError("OBSERVER_SCOPE_VIOLATION: production_paths")
    raw_bindings = raw.get("authoritative_process_identities", [])
    if not isinstance(raw_bindings, list):
        raise TypeError("PROCESS_IDENTITY_BINDING: collection")
    bindings = tuple(ProcessIdentityBinding.from_mapping(item) for item in raw_bindings)
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
        authoritative_process_identities=bindings,
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
