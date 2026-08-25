"""Source-file integrity guards for derived Opportunity Intelligence output."""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from pathlib import Path


class OpportunitySourceIntegrityError(ValueError):
    """Raised when a derived operation cannot prove its source is unchanged."""


@dataclass(frozen=True, slots=True)
class SourceIntegrityProof:
    """The expected and observed digest for one source path."""

    source_path: Path
    expected_sha256: str
    actual_sha256: str


_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")


def verify_source_integrity(
    source_path: str | Path,
    expected_sha256: str,
) -> SourceIntegrityProof:
    """Verify a source file against the digest captured at import time."""

    path = Path(source_path).resolve()
    if not isinstance(expected_sha256, str) or _SHA256_RE.fullmatch(expected_sha256) is None:
        raise OpportunitySourceIntegrityError("expected source SHA-256 is invalid")
    if not path.is_file():
        raise OpportunitySourceIntegrityError(f"source file is unavailable: {path.name}")
    digest = hashlib.sha256()
    try:
        with path.open("rb") as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise OpportunitySourceIntegrityError(
            f"source file cannot be read: {path.name}"
        ) from exc
    actual_sha256 = digest.hexdigest()
    if actual_sha256.casefold() != expected_sha256.casefold():
        raise OpportunitySourceIntegrityError(
            f"source file changed since import: {path.name}"
        )
    return SourceIntegrityProof(path, expected_sha256, actual_sha256)


__all__ = [
    "OpportunitySourceIntegrityError",
    "SourceIntegrityProof",
    "verify_source_integrity",
]
