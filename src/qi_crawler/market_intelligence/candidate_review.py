"""Explicit, append-only human review overlay for KHMT candidates."""

from __future__ import annotations

import hashlib
import json
import math
import re
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from enum import Enum, StrEnum
from typing import Any

from sqlalchemy import func, select

from qi_crawler.db import Database
from qi_crawler.models import CandidateReviewEvent

from .khmt_contract import PlanPackage

SNAPSHOT_SCHEMA_VERSION = "mi-3-v1"
_SHA256_PATTERN = re.compile(r"^[0-9a-fA-F]{64}$")


class HumanReviewDecision(StrEnum):
    CONFIRMED = "CONFIRMED"
    REJECTED = "REJECTED"
    NEEDS_REVIEW = "NEEDS_REVIEW"


class CandidateReviewError(ValueError):
    """The requested review lacks an exact source identity or human authority."""


@dataclass(frozen=True, slots=True)
class CandidateIdentity:
    candidate_key: str
    source_sha256: str
    sheet: str
    source_row: int
    plan_id_raw: str
    plan_base_id: str
    plan_revision: str | None


@dataclass(frozen=True, slots=True)
class ReviewedCandidate:
    package: PlanPackage
    event: CandidateReviewEvent


def candidate_identity(package: PlanPackage) -> CandidateIdentity:
    """Build the exact source-backed identity; filename is deliberately excluded."""

    batch = package.plan.import_batch
    sha256 = batch.source_sha256.strip().lower()
    sheet = batch.sheet.strip()
    plan_id_raw = package.plan.plan_id_raw.strip()
    expected_plan_id = package.plan.plan_base_id + (
        f"-{package.plan.plan_revision}" if package.plan.plan_revision else ""
    )
    if not _SHA256_PATTERN.fullmatch(sha256):
        raise CandidateReviewError("source_sha256 must be a 64-character hexadecimal digest.")
    if not sheet or package.source_row <= 0 or not plan_id_raw:
        raise CandidateReviewError("Candidate source identity is incomplete.")
    if plan_id_raw != expected_plan_id:
        raise CandidateReviewError("Raw plan identity conflicts with base/revision fields.")

    expected_provenance = {
        "source_sha256": sha256,
        "sheet": sheet,
        "source_row": package.source_row,
    }
    for field, expected in expected_provenance.items():
        observed = package.provenance.get(field)
        if field == "source_sha256" and isinstance(observed, str):
            observed = observed.lower()
        if observed != expected:
            raise CandidateReviewError(f"Candidate provenance conflicts with {field}.")

    key_payload = {
        "plan_id_raw": plan_id_raw,
        "sheet": sheet,
        "source_row": package.source_row,
        "source_sha256": sha256,
    }
    encoded = json.dumps(
        key_payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return CandidateIdentity(
        candidate_key=hashlib.sha256(encoded).hexdigest(),
        source_sha256=sha256,
        sheet=sheet,
        source_row=package.source_row,
        plan_id_raw=plan_id_raw,
        plan_base_id=package.plan.plan_base_id,
        plan_revision=package.plan.plan_revision,
    )


class CandidateReviewService:
    """The sole MI-3 write authority for explicit human candidate decisions."""

    def __init__(self, database: Database) -> None:
        self.database = database
        self.database.require_current_schema()

    def record_decision(
        self,
        package: PlanPackage,
        *,
        decision: HumanReviewDecision | str,
        reviewer: str,
        note: str | None = None,
    ) -> CandidateReviewEvent:
        identity = candidate_identity(package)
        normalized_decision = _decision(decision)
        normalized_reviewer = _required_text("reviewer", reviewer)
        normalized_note = note.strip() if note and note.strip() else None
        snapshot = serialize_package_snapshot(package)

        with self.database.session() as session:
            latest = session.scalar(
                select(CandidateReviewEvent)
                .where(CandidateReviewEvent.candidate_key == identity.candidate_key)
                .order_by(CandidateReviewEvent.id.desc())
                .limit(1)
            )
            if latest is not None and (
                latest.decision,
                latest.reviewer,
                latest.note,
            ) == (
                normalized_decision.value,
                normalized_reviewer,
                normalized_note,
            ):
                return latest
            event = CandidateReviewEvent(
                candidate_key=identity.candidate_key,
                source_sha256=identity.source_sha256,
                source_sheet=identity.sheet,
                source_row=identity.source_row,
                plan_id_raw=identity.plan_id_raw,
                plan_base_id=identity.plan_base_id,
                plan_revision=identity.plan_revision,
                decision=normalized_decision.value,
                reviewer=normalized_reviewer,
                note=normalized_note,
                package_snapshot_json=snapshot,
                snapshot_schema_version=SNAPSHOT_SCHEMA_VERSION,
            )
            session.add(event)
            session.flush()
            return event

    def list_history(self, package: PlanPackage) -> tuple[CandidateReviewEvent, ...]:
        identity = candidate_identity(package)
        with self.database.session() as session:
            return tuple(
                session.scalars(
                    select(CandidateReviewEvent)
                    .where(CandidateReviewEvent.candidate_key == identity.candidate_key)
                    .order_by(CandidateReviewEvent.id.asc())
                )
            )

    def current_event(self, package: PlanPackage) -> CandidateReviewEvent | None:
        identity = candidate_identity(package)
        with self.database.session() as session:
            return session.scalar(
                select(CandidateReviewEvent)
                .where(CandidateReviewEvent.candidate_key == identity.candidate_key)
                .order_by(CandidateReviewEvent.id.desc())
                .limit(1)
            )

    def current_confirmed(
        self, packages: Iterable[PlanPackage]
    ) -> tuple[ReviewedCandidate, ...]:
        universe = tuple(packages)
        identities = tuple(candidate_identity(package) for package in universe)
        if not identities:
            return ()
        keys = tuple(dict.fromkeys(identity.candidate_key for identity in identities))
        latest = (
            select(
                CandidateReviewEvent.candidate_key.label("candidate_key"),
                func.max(CandidateReviewEvent.id).label("latest_id"),
            )
            .where(CandidateReviewEvent.candidate_key.in_(keys))
            .group_by(CandidateReviewEvent.candidate_key)
            .subquery()
        )
        with self.database.session() as session:
            events = session.scalars(
                select(CandidateReviewEvent).join(
                    latest,
                    CandidateReviewEvent.id == latest.c.latest_id,
                )
            ).all()
        by_key = {event.candidate_key: event for event in events}
        confirmed: list[ReviewedCandidate] = []
        seen: set[str] = set()
        for package, identity in zip(universe, identities, strict=True):
            if identity.candidate_key in seen:
                continue
            seen.add(identity.candidate_key)
            event = by_key.get(identity.candidate_key)
            if event is not None and event.decision == HumanReviewDecision.CONFIRMED.value:
                confirmed.append(ReviewedCandidate(package=package, event=event))
        return tuple(confirmed)


def serialize_package_snapshot(package: PlanPackage) -> str:
    """Serialize a bounded, deterministic and human-readable source snapshot."""

    batch = package.plan.import_batch
    payload = {
        "schema_version": SNAPSHOT_SCHEMA_VERSION,
        "source": {
            "filename": batch.source_filename,
            "sha256": batch.source_sha256,
            "sheet": batch.sheet,
            "source_row": package.source_row,
        },
        "plan": {
            "id_raw": package.plan.plan_id_raw,
            "base_id": package.plan.plan_base_id,
            "revision": package.plan.plan_revision,
        },
        "package": {
            "name": package.package_name,
            "investor": package.investor,
            "project": package.project,
            "package_price_raw": package.package_price_raw,
            "package_price": package.package_price,
            "total_investment_raw": package.total_investment_raw,
            "approval_content_raw": package.approval_content_raw,
            "funding_source": package.funding_source,
            "selection_method_raw": package.selection_method_raw,
            "selection_method": package.selection_method,
            "selection_schedule_raw": package.selection_schedule_raw,
            "contract_type_raw": package.contract_type_raw,
            "execution_duration_raw": package.execution_duration_raw,
            "location_detail_raw": package.location_detail_raw,
            "province_city_code": package.province_city_code,
            "province_city_name": package.province_city_name,
            "province_city_status": package.province_city_status,
            "province_city_evidence": package.province_city_evidence,
            "source_notice_id": package.source_notice_id,
        },
        "raw_fields": package.raw_fields,
        "provenance": package.provenance,
    }
    return json.dumps(
        _json_safe(payload),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise CandidateReviewError("Package snapshot contains a non-finite number.")
        return value
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Enum):
        return _json_safe(value.value)
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in sorted(value.items(), key=lambda pair: str(pair[0]))}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    raise CandidateReviewError(f"Unsupported package snapshot value: {type(value).__name__}.")


def _decision(value: HumanReviewDecision | str) -> HumanReviewDecision:
    try:
        return HumanReviewDecision(str(value).strip().upper())
    except ValueError as exc:
        raise CandidateReviewError("Invalid human review decision.") from exc


def _required_text(name: str, value: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise CandidateReviewError(f"{name} is required.")
    return normalized
