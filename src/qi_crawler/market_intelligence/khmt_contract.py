"""Stable, import-free data contract for procurement-plan (KHMT) records.

This module deliberately models source facts only.  It does not derive tender
notices, import Excel workbooks, filter opportunities, or make bid decisions.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from pathlib import Path
from typing import Any


class ProvinceCityStatus(StrEnum):
    """Confidence of the source-provided province/city assignment."""

    CONFIRMED = "CONFIRMED"
    INFERRED = "INFERRED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


@dataclass(frozen=True)
class KHMTImportBatch:
    """Provenance of one future KHMT spreadsheet import."""

    source_filename: str
    source_sha256: str
    sheet: str
    imported_at: datetime
    schema_version: str


@dataclass(frozen=True)
class ProcurementPlan:
    """A procurement plan identity in the PL namespace only."""

    plan_base_id: str
    plan_revision: str | None
    import_batch: KHMTImportBatch


@dataclass(frozen=True)
class PlanPackage:
    """One source row/package within a procurement plan.

    ``source_notice_id`` is intentionally optional: an IB notice can be
    related only when an upstream source explicitly supplies that relation.
    It is never derived from a PL identifier.
    """

    plan: ProcurementPlan
    source_row: int
    package_name: str
    investor: str | None
    project: str | None
    package_price_raw: str | None
    package_price: Decimal | None
    funding_source: str | None
    selection_method_raw: str | None
    selection_method: str | None
    selection_schedule_raw: str | None
    location_detail_raw: str | None
    province_city_code: str | None
    province_city_name: str | None
    province_city_status: ProvinceCityStatus
    province_city_evidence: str | None
    raw_fields: Mapping[str, Any] = field(default_factory=dict)
    provenance: Mapping[str, Any] = field(default_factory=dict)
    source_notice_id: str | None = None


def load_sanitized_khmt_fixture(path: Path) -> tuple[KHMTImportBatch, tuple[PlanPackage, ...]]:
    """Load the deterministic MI-0 golden fixture for contract tests only.

    This is not a KHMT Excel importer and must not be used as production intake
    logic.  It exists so the contractual shape stays executable in CI.
    """

    payload = json.loads(path.read_text(encoding="utf-8"))
    batch_payload = payload["import_batch"]
    batch = KHMTImportBatch(
        source_filename=batch_payload["source_filename"],
        source_sha256=batch_payload["source_sha256"],
        sheet=batch_payload["sheet"],
        imported_at=datetime.fromisoformat(batch_payload["imported_at"]),
        schema_version=batch_payload["schema_version"],
    )
    plans: dict[tuple[str, str | None], ProcurementPlan] = {}
    packages: list[PlanPackage] = []
    for row in payload["plan_packages"]:
        key = (row["plan_base_id"], row.get("plan_revision"))
        plan = plans.setdefault(
            key,
            ProcurementPlan(
                plan_base_id=key[0],
                plan_revision=key[1],
                import_batch=batch,
            ),
        )
        price = row.get("package_price")
        packages.append(
            PlanPackage(
                plan=plan,
                source_row=row["source_row"],
                package_name=row["package_name"],
                investor=row.get("investor"),
                project=row.get("project"),
                package_price_raw=row.get("package_price_raw"),
                package_price=Decimal(price) if price is not None else None,
                funding_source=row.get("funding_source"),
                selection_method_raw=row.get("selection_method_raw"),
                selection_method=row.get("selection_method"),
                selection_schedule_raw=row.get("selection_schedule_raw"),
                location_detail_raw=row.get("location_detail_raw"),
                province_city_code=row.get("province_city_code"),
                province_city_name=row.get("province_city_name"),
                province_city_status=ProvinceCityStatus(row["province_city_status"]),
                province_city_evidence=row.get("province_city_evidence"),
                raw_fields=row.get("raw_fields", {}),
                provenance=row["provenance"],
                source_notice_id=row.get("source_notice_id"),
            )
        )
    return batch, tuple(packages)
