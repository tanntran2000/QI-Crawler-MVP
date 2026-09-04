"""Session-only identity and comparison for a Bid Radar working source."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .source_detection import SourceType


@dataclass(frozen=True, slots=True)
class SourceSessionIdentity:
    """Exact source observation governing one in-memory Bid Radar session."""

    path: Path
    source_filename: str
    source_sha256: str
    source_type: SourceType

    def __post_init__(self) -> None:
        path = Path(self.path).resolve()
        source_type = SourceType(self.source_type)
        if not self.source_filename or not self.source_filename.strip():
            raise ValueError("source session requires a filename")
        if not self.source_sha256 or not self.source_sha256.strip():
            raise ValueError("source session requires a SHA-256")
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "source_type", source_type)

    def matches(self, other: SourceSessionIdentity | None) -> bool:
        """Return whether two source observations are exactly the same."""

        return (
            other is not None
            and self.path == other.path
            and self.source_filename == other.source_filename
            and self.source_sha256.casefold() == other.source_sha256.casefold()
            and self.source_type is other.source_type
        )


def source_session_matches(
    left: SourceSessionIdentity | None,
    right: SourceSessionIdentity | None,
) -> bool:
    """Compare optional source identities without treating missing as equal."""

    return left is not None and left.matches(right)


__all__ = ["SourceSessionIdentity", "source_session_matches"]
