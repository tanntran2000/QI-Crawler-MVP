"""Domain values for managed tender-source integrity and recovery."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from .tender_workspace import ManagedIntegrityState


class RecoveryAction(StrEnum):
    INTEGRITY_SCAN = "INTEGRITY_SCAN"
    ORPHAN_SCAN = "ORPHAN_SCAN"
    RECOVER = "RECOVER"


@dataclass(frozen=True, slots=True)
class RecoveryInspection:
    membership_id: int | None
    document_id: int | None
    release_id: int | None
    expected_sha256: str | None
    observed_sha256: str | None
    path: Path
    state: ManagedIntegrityState


@dataclass(frozen=True, slots=True)
class RecoveryReport:
    case_id: str
    release_id: int
    entries: tuple[RecoveryInspection, ...]
    orphans: tuple[RecoveryInspection, ...] = ()


@dataclass(frozen=True, slots=True)
class RecoveryResult:
    state: ManagedIntegrityState
    membership_id: int
    document_id: int
    release_id: int
    expected_sha256: str
    verified_sha256: str
    managed_path: Path
    quarantine_path: Path | None = None


__all__ = [
    "ManagedIntegrityState",
    "RecoveryAction",
    "RecoveryInspection",
    "RecoveryReport",
    "RecoveryResult",
]
