from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest
from openpyxl import Workbook
from sqlalchemy import func, select

from qi_crawler.db import Database
from qi_crawler.market_intelligence.candidate_review import (
    CandidateReviewError,
    CandidateReviewService,
    HumanReviewDecision,
    candidate_identity,
    serialize_package_snapshot,
)
from qi_crawler.market_intelligence.khmt_contract import (
    OBSERVED_KHMT_HEADERS,
    load_sanitized_khmt_fixture,
)
from qi_crawler.market_intelligence.khmt_importer import import_khmt_workbook
from qi_crawler.market_intelligence.search import TargetedSearchRequest, search_packages
from qi_crawler.models import CandidateReviewEvent

FIXTURE = Path(__file__).parent / "fixtures" / "khmt" / "khmt_sanitized_golden.json"


def _packages():
    packages = load_sanitized_khmt_fixture(FIXTURE)[1]
    return tuple(
        replace(
            package,
            provenance={
                **package.provenance,
                "source_filename": package.plan.import_batch.source_filename,
                "source_sha256": package.plan.import_batch.source_sha256,
                "sheet": package.plan.import_batch.sheet,
                "source_row": package.source_row,
            },
        )
        for package in packages
    )


def _service(tmp_path: Path) -> tuple[Database, CandidateReviewService]:
    database = Database(f"sqlite:///{tmp_path / 'candidate-review.db'}")
    return database, CandidateReviewService(database)


def _with_batch(package, **changes):
    batch = replace(package.plan.import_batch, **changes)
    plan = replace(package.plan, import_batch=batch)
    provenance = dict(package.provenance)
    if "source_filename" in changes:
        provenance["source_filename"] = changes["source_filename"]
    if "source_sha256" in changes:
        provenance["source_sha256"] = changes["source_sha256"]
    return replace(package, plan=plan, provenance=provenance)


def test_unreviewed_has_no_fake_persisted_event(tmp_path: Path) -> None:
    database, service = _service(tmp_path)
    package = _packages()[0]

    assert service.current_event(package) is None
    with database.session() as session:
        assert session.scalar(select(func.count(CandidateReviewEvent.id))) == 0


def test_explicit_decisions_are_append_only_and_latest_id_is_current(tmp_path: Path) -> None:
    _, service = _service(tmp_path)
    package = _packages()[0]

    first = service.record_decision(
        package, decision=HumanReviewDecision.CONFIRMED, reviewer="Team Bid"
    )
    second = service.record_decision(
        package, decision=HumanReviewDecision.REJECTED, reviewer="Team Bid"
    )
    third = service.record_decision(
        package, decision=HumanReviewDecision.CONFIRMED, reviewer="Team Bid"
    )

    history = service.list_history(package)
    assert [event.id for event in history] == [first.id, second.id, third.id]
    assert service.current_event(package).id == third.id


def test_current_confirmed_uses_latest_decision_not_historical_confirmation(
    tmp_path: Path,
) -> None:
    _, service = _service(tmp_path)
    confirmed_then_rejected, rejected_then_confirmed = _packages()[:2]
    service.record_decision(
        confirmed_then_rejected,
        decision="CONFIRMED",
        reviewer="Reviewer",
    )
    service.record_decision(
        confirmed_then_rejected,
        decision="REJECTED",
        reviewer="Reviewer",
    )
    service.record_decision(
        rejected_then_confirmed,
        decision="REJECTED",
        reviewer="Reviewer",
    )
    service.record_decision(
        rejected_then_confirmed,
        decision="CONFIRMED",
        reviewer="Reviewer",
    )

    current = service.current_confirmed((confirmed_then_rejected, rejected_then_confirmed))

    assert [item.package.source_row for item in current] == [rejected_then_confirmed.source_row]


def test_same_sha_different_filename_reattaches_after_restart(tmp_path: Path) -> None:
    database, service = _service(tmp_path)
    package = _packages()[0]
    event = service.record_decision(
        package, decision="CONFIRMED", reviewer="Reviewer", note="Đã kiểm tra"
    )
    renamed = _with_batch(package, source_filename="renamed-copy.xlsx")

    reopened = CandidateReviewService(Database(database.url))

    assert candidate_identity(renamed).candidate_key == candidate_identity(package).candidate_key
    assert reopened.current_event(renamed).id == event.id
    assert [item.event.id for item in reopened.current_confirmed((renamed,))] == [event.id]


def test_changed_sha_is_new_unreviewed_candidate(tmp_path: Path) -> None:
    _, service = _service(tmp_path)
    package = _packages()[0]
    service.record_decision(package, decision="CONFIRMED", reviewer="Reviewer")
    changed = _with_batch(package, source_sha256="b" * 64)

    assert candidate_identity(changed).candidate_key != candidate_identity(package).candidate_key
    assert service.current_event(changed) is None


def test_revision_and_source_rows_have_independent_decisions(tmp_path: Path) -> None:
    _, service = _service(tmp_path)
    revision_00_row_8, revision_00_row_9, revision_01 = _packages()[:3]
    service.record_decision(revision_00_row_8, decision="CONFIRMED", reviewer="Reviewer")

    assert service.current_event(revision_00_row_9) is None
    assert service.current_event(revision_01) is None


def test_same_source_row_different_plan_revision_is_independent(tmp_path: Path) -> None:
    _, service = _service(tmp_path)
    revision_00 = _packages()[0]
    revision_01_plan = replace(
        revision_00.plan,
        plan_id_raw=f"{revision_00.plan.plan_base_id}-01",
        plan_revision="01",
    )
    revision_01 = replace(revision_00, plan=revision_01_plan)
    service.record_decision(revision_00, decision="CONFIRMED", reviewer="Reviewer")

    assert service.current_event(revision_01) is None


def test_search_match_does_not_create_human_review_event(tmp_path: Path) -> None:
    database, service = _service(tmp_path)
    packages = _packages()[:3]

    result = search_packages(packages, TargetedSearchRequest())

    assert result.matched_count == 3
    assert all(service.current_event(package) is None for package in packages)
    with database.session() as session:
        assert session.scalar(select(func.count(CandidateReviewEvent.id))) == 0


def test_importer_does_not_create_human_review_event(tmp_path: Path) -> None:
    database, _ = _service(tmp_path)
    workbook_path = tmp_path / "synthetic-khmt.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "KHMT"
    sheet.append(list(OBSERVED_KHMT_HEADERS))
    values = dict.fromkeys(OBSERVED_KHMT_HEADERS)
    values["SỐ KẾ HOẠCH"] = "PL1234567890-00"
    values["TÊN GÓI THẦU"] = "Synthetic package"
    sheet.append([values[header] for header in OBSERVED_KHMT_HEADERS])
    workbook.save(workbook_path)

    result = import_khmt_workbook(workbook_path)

    assert len(result.packages) == 1
    with database.session() as session:
        assert session.scalar(select(func.count(CandidateReviewEvent.id))) == 0


def test_snapshot_is_deterministic_versioned_and_preserves_unicode(tmp_path: Path) -> None:
    _, service = _service(tmp_path)
    package = replace(_packages()[0], package_name="Thiết bị mạng tổng hợp")

    first = serialize_package_snapshot(package)
    second = serialize_package_snapshot(package)
    event = service.record_decision(package, decision="NEEDS_REVIEW", reviewer="Người kiểm tra")

    assert first == second == event.package_snapshot_json
    payload = json.loads(first)
    assert payload["schema_version"] == "mi-3-v1"
    assert payload["package"]["name"] == "Thiết bị mạng tổng hợp"
    assert payload["source"]["sha256"] == package.plan.import_batch.source_sha256


def test_conflicting_provenance_fails_closed(tmp_path: Path) -> None:
    _, service = _service(tmp_path)
    package = _packages()[0]
    conflicting = replace(
        package,
        provenance={**package.provenance, "source_row": package.source_row + 1},
    )

    with pytest.raises(CandidateReviewError, match="source_row"):
        service.record_decision(conflicting, decision="CONFIRMED", reviewer="Reviewer")


def test_synthetic_three_candidate_golden_keeps_human_states_separate(
    tmp_path: Path,
) -> None:
    _, service = _service(tmp_path)
    confirmed, rejected, needs_review = _packages()[:3]
    service.record_decision(confirmed, decision="CONFIRMED", reviewer="Reviewer")
    service.record_decision(rejected, decision="REJECTED", reviewer="Reviewer")
    service.record_decision(needs_review, decision="NEEDS_REVIEW", reviewer="Reviewer")

    current = service.current_confirmed((confirmed, rejected, needs_review, confirmed))

    assert [(item.package.source_row, item.event.decision) for item in current] == [
        (confirmed.source_row, "CONFIRMED")
    ]


def test_synthetic_golden_survives_restart_exact_reimport_and_rejection(
    tmp_path: Path,
) -> None:
    workbook_path = tmp_path / "synthetic-mi3-golden.xlsx"
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "KHMT"
    sheet.append(list(OBSERVED_KHMT_HEADERS))
    for index in range(3):
        values = dict.fromkeys(OBSERVED_KHMT_HEADERS)
        values["SỐ KẾ HOẠCH"] = f"PL900000000{index}-00"
        values["TÊN GÓI THẦU"] = f"Synthetic candidate {index + 1}"
        sheet.append([values[header] for header in OBSERVED_KHMT_HEADERS])
    workbook.save(workbook_path)

    database = Database(f"sqlite:///{tmp_path / 'synthetic-golden.db'}")
    service = CandidateReviewService(database)
    first_import = import_khmt_workbook(workbook_path)
    for package in first_import.packages:
        service.record_decision(package, decision="CONFIRMED", reviewer="Team Bid")
    assert len(service.current_confirmed(first_import.packages)) == 3

    reopened = CandidateReviewService(Database(database.url))
    second_import = import_khmt_workbook(workbook_path)
    assert len(reopened.current_confirmed(second_import.packages)) == 3

    rejected = second_import.packages[0]
    reopened.record_decision(rejected, decision="REJECTED", reviewer="Team Bid")
    assert [event.decision for event in reopened.list_history(rejected)] == [
        "CONFIRMED",
        "REJECTED",
    ]
    assert len(reopened.current_confirmed(second_import.packages)) == 2
