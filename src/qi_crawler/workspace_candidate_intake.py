"""Read-only folder discovery and explicit candidate confirmation models."""

from __future__ import annotations

import hashlib
import re
import unicodedata
from collections.abc import Collection
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .document_intake import SUPPORTED_EXTENSIONS, extract_document_identity
from .tender_case import AuthorityClass

ROLE_CODES = frozenset({"C3", "C5", "PL", "REF", "OTH"})


class WorkspaceCandidateError(ValueError):
    """The candidate scan could not be completed safely."""


@dataclass(frozen=True, slots=True)
class WorkspaceCandidate:
    """Immutable read-only observation of one supported source file."""

    source_path: Path
    relative_path: Path
    original_filename: str
    extension: str
    file_size: int
    last_modified: datetime
    sha256: str
    detected_raw_id: str | None
    detected_base_id: str | None
    detected_revision: str | None
    identity_status: str
    suggested_role: str
    duplicate_status: str

    @property
    def short_sha256(self) -> str:
        return self.sha256[:8]


@dataclass(frozen=True, slots=True)
class ConfirmedWorkspaceCandidate:
    """Human confirmation binding a scanned file to one workspace role."""

    candidate: WorkspaceCandidate
    role: str
    zone: str
    authority: AuthorityClass | str
    evidence: str
    uploaded_by: str | None = None


def scan_folder(
    folder: Path,
    *,
    duplicate_shas: Collection[str] = (),
) -> tuple[WorkspaceCandidate, ...]:
    """Recursively discover supported files without any Warehouse writes."""

    root = Path(folder).expanduser().resolve()
    if not root.is_dir():
        raise WorkspaceCandidateError("candidate scan requires a directory")
    known = {str(value).casefold() for value in duplicate_shas}
    candidates: list[WorkspaceCandidate] = []
    for path in sorted(
        (item for item in root.rglob("*") if item.is_file()),
        key=lambda item: item.relative_to(root).as_posix().casefold(),
    ):
        extension = path.suffix.lower()
        if extension not in SUPPORTED_EXTENSIONS:
            continue
        try:
            stat = path.stat()
            digest = _hash_file(path)
        except OSError as exc:
            raise WorkspaceCandidateError("candidate file cannot be read") from exc
        identity = extract_document_identity(path)
        candidates.append(
            WorkspaceCandidate(
                source_path=path,
                relative_path=path.relative_to(root),
                original_filename=path.name,
                extension=extension,
                file_size=stat.st_size,
                last_modified=datetime.fromtimestamp(stat.st_mtime, tz=UTC),
                sha256=digest,
                detected_raw_id=identity.raw_notice_id,
                detected_base_id=identity.base_notice_id,
                detected_revision=identity.revision,
                identity_status=identity.status or "UNRESOLVED",
                suggested_role=suggest_role(path.name),
                duplicate_status="DUPLICATE" if digest.casefold() in known else "NEW",
            )
        )
    return tuple(candidates)


def suggest_role(filename: str) -> str:
    """Return an advisory role only; the Human must confirm the role."""

    normalized = _fold(filename)
    if re.search(r"\bchuong\s*iii\b|\bchapter\s*iii\b", normalized):
        return "C3"
    if re.search(r"\bchuong\s*v\b|\bchapter\s*v\b", normalized):
        return "C5"
    if re.search(r"\bphu\s*luc\b|\bappendix\b", normalized):
        return "PL"
    return "OTH"


def _fold(value: str) -> str:
    return " ".join(
        unicodedata.normalize("NFKD", value)
        .encode("ascii", "ignore")
        .decode("ascii")
        .casefold()
        .split()
    )


def _hash_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


__all__ = [
    "ROLE_CODES",
    "ConfirmedWorkspaceCandidate",
    "WorkspaceCandidate",
    "WorkspaceCandidateError",
    "scan_folder",
    "suggest_role",
]
