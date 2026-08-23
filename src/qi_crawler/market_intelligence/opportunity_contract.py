"""Source-neutral, import-free contract for market-intelligence opportunities.

This module deliberately contains no workbook, database, GUI, or review
logic. It preserves the source namespace (KHMT/PL or TBMT/IB) and provenance
so later adapters cannot silently convert one opportunity type into another.
"""

from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from types import MappingProxyType
from typing import Any


class OpportunityContractError(ValueError):
    """Raised when an opportunity violates a source or provenance invariant."""


class OpportunitySourceType(StrEnum):
    KHMT = "KHMT"
    TBMT = "TBMT"


class OpportunityIdentityNamespace(StrEnum):
    PL = "PL"
    IB = "IB"


_IDENTITY_RE = re.compile(
    r"^(?P<namespace>PL|IB)(?P<number>\d{8,14})"
    r"(?:\s*-\s*(?P<revision>\d{2}))?$",
    re.IGNORECASE,
)
_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
_EXPECTED_NAMESPACE = {
    OpportunitySourceType.KHMT: OpportunityIdentityNamespace.PL,
    OpportunitySourceType.TBMT: OpportunityIdentityNamespace.IB,
}


@dataclass(frozen=True, slots=True)
class OpportunityIdentity:
    """A source identity with raw and parsed values kept separately.

    ``base_id`` identifies the procurement-notice lineage, while ``revision``
    is part of the exact source identity. Different revisions therefore remain
    distinct ``OpportunityIdentity`` values even when they share a lineage.
    ``raw_id`` preserves the exact source identity segment as supplied by the
    source.
    """

    raw_id: str
    base_id: str
    revision: str | None
    namespace: OpportunityIdentityNamespace

    def __post_init__(self) -> None:
        namespace = OpportunityIdentityNamespace(self.namespace)
        if not isinstance(self.raw_id, str) or not self.raw_id.strip():
            raise OpportunityContractError("identity raw_id must be non-empty")
        match = _IDENTITY_RE.fullmatch(self.raw_id.strip())
        if match is None:
            raise OpportunityContractError("identity raw_id has an unsupported format")
        parsed_namespace = OpportunityIdentityNamespace(match.group("namespace").upper())
        parsed_base = f"{parsed_namespace.value}{match.group('number')}"
        parsed_revision = match.group("revision")
        if namespace is not parsed_namespace:
            raise OpportunityContractError("identity namespace does not match raw_id")
        if self.base_id != parsed_base or self.revision != parsed_revision:
            raise OpportunityContractError("identity base_id/revision do not match raw_id")
        object.__setattr__(self, "namespace", namespace)

    @classmethod
    def from_raw(cls, raw_id: str) -> OpportunityIdentity:
        """Parse an identity without rewriting its raw source value."""

        match = _IDENTITY_RE.fullmatch(raw_id.strip()) if isinstance(raw_id, str) else None
        if match is None:
            raise OpportunityContractError("identity raw_id has an unsupported format")
        namespace = OpportunityIdentityNamespace(match.group("namespace").upper())
        return cls(
            raw_id=raw_id,
            base_id=f"{namespace.value}{match.group('number')}",
            revision=match.group("revision"),
            namespace=namespace,
        )


@dataclass(frozen=True, slots=True)
class OpportunityImportBatch:
    """Provenance for one source workbook import batch."""

    source_filename: str
    source_sha256: str
    sheet: str
    imported_at: datetime
    schema_version: str
    source_type: OpportunitySourceType

    def __post_init__(self) -> None:
        source_type = OpportunitySourceType(self.source_type)
        if not isinstance(self.source_filename, str) or not self.source_filename.strip():
            raise OpportunityContractError("source_filename must be non-empty")
        if not isinstance(self.source_sha256, str) or not _SHA256_RE.fullmatch(self.source_sha256):
            raise OpportunityContractError("source_sha256 must be a valid SHA-256 digest")
        if not isinstance(self.sheet, str) or not self.sheet.strip():
            raise OpportunityContractError("sheet must be non-empty")
        if not isinstance(self.imported_at, datetime):
            raise OpportunityContractError("imported_at must be a datetime")
        if not isinstance(self.schema_version, str) or not self.schema_version.strip():
            raise OpportunityContractError("schema_version must be non-empty")
        object.__setattr__(self, "source_type", source_type)


@dataclass(frozen=True, slots=True)
class OpportunityCandidate:
    """One exact source row, independent of review and export authorities."""

    identity: OpportunityIdentity
    import_batch: OpportunityImportBatch
    source_row: int
    package_name: str
    project: str | None = None
    package_price_raw: str | None = None
    package_price: Decimal | None = None
    funding_source: str | None = None
    location_detail_raw: str | None = None
    raw_fields: Mapping[str, Any] = field(default_factory=dict)
    provenance: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not isinstance(self.identity, OpportunityIdentity):
            raise OpportunityContractError("identity must be an OpportunityIdentity")
        if not isinstance(self.import_batch, OpportunityImportBatch):
            raise OpportunityContractError("import_batch must be an OpportunityImportBatch")
        if not isinstance(self.source_row, int) or isinstance(self.source_row, bool) or self.source_row < 1:
            raise OpportunityContractError("source_row must be a positive integer")
        if not isinstance(self.package_name, str):
            raise OpportunityContractError("package_name must be text")
        expected = _EXPECTED_NAMESPACE[self.import_batch.source_type]
        if self.identity.namespace is not expected:
            raise OpportunityContractError(
                "source namespace mismatch: "
                f"{self.import_batch.source_type.value} requires {expected.value}"
            )
        if not isinstance(self.raw_fields, Mapping):
            raise OpportunityContractError("raw_fields must be a mapping")
        if not isinstance(self.provenance, Mapping) or not self.provenance:
            raise OpportunityContractError("provenance must retain source traceability")
        trace_keys = {
            "source_filename",
            "source_sha256",
            "sheet",
            "source_row",
            "source_locator",
        }
        if not trace_keys.intersection(self.provenance):
            raise OpportunityContractError("provenance must include a source locator")
        required_coordinates = {"source_sha256", "sheet", "source_row"}
        if not required_coordinates.issubset(self.provenance):
            raise OpportunityContractError(
                "provenance must include authoritative source_sha256, sheet, and source_row"
            )
        provenance_sha256 = self.provenance["source_sha256"]
        if (
            not isinstance(provenance_sha256, str)
            or provenance_sha256.casefold() != self.import_batch.source_sha256.casefold()
        ):
            raise OpportunityContractError("provenance source_sha256 does not match import batch")
        if self.provenance["sheet"] != self.import_batch.sheet:
            raise OpportunityContractError("provenance sheet does not match import batch")
        if self.provenance["source_row"] != self.source_row:
            raise OpportunityContractError("provenance source_row does not match candidate")
        object.__setattr__(self, "raw_fields", MappingProxyType(dict(self.raw_fields)))
        object.__setattr__(self, "provenance", MappingProxyType(dict(self.provenance)))
