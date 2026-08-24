"""Source-neutral application projection for opportunity intelligence.

This module bridges source observations into one immutable application shape.
It does not persist data, perform filtering, record review decisions, or create
Tender Package revisions.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Mapping
from dataclasses import dataclass, field
from decimal import Decimal
from types import MappingProxyType
from typing import Any

from .khmt_contract import PlanPackage, ProvinceCityStatus
from .opportunity_contract import (
    OpportunityCandidate,
    OpportunityIdentity,
    OpportunityIdentityNamespace,
    OpportunitySourceType,
)

_SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
_EXPECTED_NAMESPACE = {
    OpportunitySourceType.KHMT: OpportunityIdentityNamespace.PL,
    OpportunitySourceType.TBMT: OpportunityIdentityNamespace.IB,
}


class OpportunityRadarContractError(ValueError):
    """Raised when a source observation cannot form a safe radar item."""


def build_observation_key(
    *,
    source_type: OpportunitySourceType | str,
    identity: OpportunityIdentity,
    source_sha256: str,
    sheet: str,
    source_row: int,
) -> str:
    """Build a stable key for one exact source observation."""

    source_type = OpportunitySourceType(source_type)
    payload = {
        "source_type": source_type.value,
        "namespace": identity.namespace.value,
        "raw_id": identity.raw_id,
        "source_sha256": source_sha256.casefold(),
        "sheet": sheet,
        "source_row": source_row,
    }
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _text(value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, str):
        return value if value.strip() else None
    return str(value)


@dataclass(frozen=True, slots=True)
class OpportunityRadarItem:
    """Immutable source observation projected for later application use cases."""

    source_type: OpportunitySourceType
    identity: OpportunityIdentity
    observation_key: str
    source_filename: str
    source_sha256: str
    sheet: str
    source_row: int
    schema_version: str
    package_name: str
    project: str | None
    package_price_raw: str | None
    package_price: Decimal | None
    funding_source: str | None
    investor: str | None = None
    procuring_entity: str | None = None
    approval_content: str | None = None
    package_main_content: str | None = None
    selection_method: str | None = None
    procurement_method: str | None = None
    location_detail_raw: str | None = None
    province_city_code: str | None = None
    province_city_name: str | None = None
    province_city_status: ProvinceCityStatus | None = None
    province_city_evidence: str | None = None
    source_fields: Mapping[str, Any] = field(default_factory=dict)
    raw_fields: Mapping[str, Any] = field(default_factory=dict)
    provenance: Mapping[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        source_type = OpportunitySourceType(self.source_type)
        if not isinstance(self.identity, OpportunityIdentity):
            raise OpportunityRadarContractError("identity must be an OpportunityIdentity")
        if self.identity.namespace is not _EXPECTED_NAMESPACE[source_type]:
            raise OpportunityRadarContractError("source type and identity namespace do not match")
        for field_name in ("source_filename", "sheet", "schema_version"):
            value = getattr(self, field_name)
            if not isinstance(value, str) or not value.strip():
                raise OpportunityRadarContractError(f"{field_name} must be non-empty")
        if not isinstance(self.source_sha256, str) or not _SHA256_RE.fullmatch(self.source_sha256):
            raise OpportunityRadarContractError("source_sha256 must be a valid SHA-256 digest")
        if not isinstance(self.source_row, int) or isinstance(self.source_row, bool) or self.source_row < 1:
            raise OpportunityRadarContractError("source_row must be a positive integer")
        if not isinstance(self.package_name, str):
            raise OpportunityRadarContractError("package_name must be text")
        expected_key = build_observation_key(
            source_type=source_type,
            identity=self.identity,
            source_sha256=self.source_sha256,
            sheet=self.sheet,
            source_row=self.source_row,
        )
        if self.observation_key != expected_key:
            raise OpportunityRadarContractError("observation_key does not match source observation")
        if self.province_city_status is not None:
            object.__setattr__(
                self,
                "province_city_status",
                ProvinceCityStatus(self.province_city_status),
            )
        for field_name in ("source_fields", "raw_fields", "provenance"):
            value = getattr(self, field_name)
            if not isinstance(value, Mapping):
                raise OpportunityRadarContractError(f"{field_name} must be a mapping")
            object.__setattr__(self, field_name, MappingProxyType(dict(value)))
        object.__setattr__(self, "source_type", source_type)


def radar_item_from_plan_package(package: PlanPackage) -> OpportunityRadarItem:
    """Project one KHMT PlanPackage without deriving an IB relation."""

    batch = package.plan.import_batch
    identity = OpportunityIdentity.from_raw(package.plan.plan_id_raw)
    source_fields = {
        "investor": package.investor,
        "approval_content": package.approval_content_raw,
        "selection_method_raw": package.selection_method_raw,
        "selection_method": package.selection_method,
        "location_detail_raw": package.location_detail_raw,
        "province_city_code": package.province_city_code,
        "province_city_name": package.province_city_name,
        "province_city_status": package.province_city_status.value,
        "province_city_evidence": package.province_city_evidence,
    }
    return OpportunityRadarItem(
        source_type=OpportunitySourceType.KHMT,
        identity=identity,
        observation_key=build_observation_key(
            source_type=OpportunitySourceType.KHMT,
            identity=identity,
            source_sha256=batch.source_sha256,
            sheet=batch.sheet,
            source_row=package.source_row,
        ),
        source_filename=batch.source_filename,
        source_sha256=batch.source_sha256,
        sheet=batch.sheet,
        source_row=package.source_row,
        schema_version=batch.schema_version,
        package_name=package.package_name,
        project=package.project,
        package_price_raw=package.package_price_raw,
        package_price=package.package_price,
        funding_source=package.funding_source,
        investor=package.investor,
        approval_content=package.approval_content_raw,
        selection_method=package.selection_method,
        location_detail_raw=package.location_detail_raw,
        province_city_code=package.province_city_code,
        province_city_name=package.province_city_name,
        province_city_status=package.province_city_status,
        province_city_evidence=package.province_city_evidence,
        source_fields=source_fields,
        raw_fields=package.raw_fields,
        provenance=package.provenance,
    )


def radar_item_from_opportunity_candidate(
    candidate: OpportunityCandidate,
) -> OpportunityRadarItem:
    """Project one TBMT OpportunityCandidate without converting it to KHMT."""

    batch = candidate.import_batch
    fields = candidate.raw_fields
    identity = candidate.identity
    source_fields = {
        "procuring_entity": fields.get("BÊN MỜI THẦU"),
        "procuring_entity_address": fields.get("ĐỊA CHỈ BÊN MỜI THẦU"),
        "package_main_content": fields.get("NỘI DUNG CHÍNH CỦA GÓI THẦU"),
        "selection_method": fields.get("HÌNH THỨC LỰA CHỌN NHÀ THẦU"),
        "procurement_method": fields.get("PHƯƠNG THỨC LỰA CHỌN NHÀ THẦU"),
        "location_detail_raw": candidate.location_detail_raw,
    }
    return OpportunityRadarItem(
        source_type=OpportunitySourceType.TBMT,
        identity=identity,
        observation_key=build_observation_key(
            source_type=OpportunitySourceType.TBMT,
            identity=identity,
            source_sha256=batch.source_sha256,
            sheet=batch.sheet,
            source_row=candidate.source_row,
        ),
        source_filename=batch.source_filename,
        source_sha256=batch.source_sha256,
        sheet=batch.sheet,
        source_row=candidate.source_row,
        schema_version=batch.schema_version,
        package_name=candidate.package_name,
        project=candidate.project,
        package_price_raw=candidate.package_price_raw,
        package_price=candidate.package_price,
        funding_source=candidate.funding_source,
        procuring_entity=_text(fields.get("BÊN MỜI THẦU")),
        package_main_content=_text(fields.get("NỘI DUNG CHÍNH CỦA GÓI THẦU")),
        selection_method=_text(fields.get("HÌNH THỨC LỰA CHỌN NHÀ THẦU")),
        procurement_method=_text(fields.get("PHƯƠNG THỨC LỰA CHỌN NHÀ THẦU")),
        location_detail_raw=candidate.location_detail_raw,
        source_fields=source_fields,
        raw_fields=candidate.raw_fields,
        provenance=candidate.provenance,
    )


plan_package_to_radar_item = radar_item_from_plan_package
opportunity_candidate_to_radar_item = radar_item_from_opportunity_candidate


__all__ = [
    "OpportunityRadarContractError",
    "OpportunityRadarItem",
    "build_observation_key",
    "opportunity_candidate_to_radar_item",
    "plan_package_to_radar_item",
    "radar_item_from_opportunity_candidate",
    "radar_item_from_plan_package",
]
