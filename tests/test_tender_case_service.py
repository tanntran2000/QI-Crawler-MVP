from __future__ import annotations

import hashlib
import zipfile
from pathlib import Path

import pytest

from qi_crawler.db import Database
from qi_crawler.market_intelligence.opportunity_contract import OpportunityIdentity
from qi_crawler.tender_case import AuthorityClass, PlanContext, TenderRelease
from qi_crawler.tender_case_service import (
    ManagedDocumentMissing,
    ManagedDocumentShaMismatch,
    TenderCaseService,
    TenderCaseServiceError,
)


@pytest.fixture
def service(tmp_path: Path) -> TenderCaseService:
    database = Database(f"sqlite:///{tmp_path / 'service.db'}")
    return TenderCaseService(database, tmp_path / "managed")


def test_service_creates_pl_context_and_preserves_revisions(service: TenderCaseService) -> None:
    service.create_case(
        "case-1",
        plan_context=PlanContext(OpportunityIdentity.from_raw("PL2600000001-00")),
    )
    first = service.add_release("case-1", "IB2600000001-00")
    second = service.add_release("case-1", "IB2600000001-01")

    opened = service.open_case("case-1")
    assert opened.plan_context is not None
    assert [release.identity.raw_id for release in opened.releases] == [
        "IB2600000001-00",
        "IB2600000001-01",
    ]
    assert first.release_id != second.release_id


def test_service_rejects_pl_release_and_inexact_ib(service: TenderCaseService) -> None:
    service.create_case("case-1")
    with pytest.raises(TenderCaseServiceError, match="IB"):
        service.add_release("case-1", "PL2600000001-00")
    with pytest.raises(TenderCaseServiceError, match="revision"):
        service.add_release("case-1", "IB2600000001")


def test_add_document_reuses_document_intake_and_separates_membership(
    service: TenderCaseService, tmp_path: Path
) -> None:
    service.create_case("case-1")
    release = service.add_release("case-1", TenderRelease(OpportunityIdentity.from_raw("IB2600000002-00")))
    source = tmp_path / "hsmt.pdf"
    source.write_bytes(b"synthetic managed source")

    membership = service.add_document(
        "case-1",
        release.release_id,
        source,
        authority=AuthorityClass.SOURCE_E_HSMT,
        evidence="Team Bid explicit source declaration",
    )

    assert membership.document_id > 0
    manifest = service.get_release_manifest("case-1", release.release_id)
    assert len(manifest.memberships) == 1
    assert manifest.memberships[0].document_id == membership.document_id
    assert service.database.session


def test_source_membership_requires_evidence_when_content_has_no_identity(
    service: TenderCaseService, tmp_path: Path
) -> None:
    service.create_case("case-1")
    release = service.add_release("case-1", "IB2600000003-00")
    source = tmp_path / "hsmt.pdf"
    source.write_bytes(b"no embedded identity")

    with pytest.raises(TenderCaseServiceError, match="evidence"):
        service.add_document(
            "case-1",
            release.release_id,
            source,
            authority=AuthorityClass.SOURCE_E_HSMT,
            evidence="",
        )


def test_reference_and_working_authorities_are_explicitly_non_source(
    service: TenderCaseService, tmp_path: Path
) -> None:
    service.create_case("case-1")
    release = service.add_release("case-1", "IB2600000004-00")
    reference = tmp_path / "reference.pdf"
    reference.write_bytes(b"foreign specimen")
    working = tmp_path / "working.docx"
    working.write_bytes(b"working draft")

    ref_membership = service.add_document(
        "case-1",
        release.release_id,
        reference,
        authority=AuthorityClass.REFERENCE_ONLY,
        evidence="Team Bid explicit reference specimen",
    )
    working_membership = service.add_document(
        "case-1",
        release.release_id,
        working,
        authority=AuthorityClass.WORKING_E_HSDT,
        evidence="Team Bid working draft",
    )
    assert ref_membership.authority_class == AuthorityClass.REFERENCE_ONLY.value
    assert working_membership.authority_class == AuthorityClass.WORKING_E_HSDT.value


def test_matching_embedded_ib_identity_can_become_source_membership(
    service: TenderCaseService, tmp_path: Path
) -> None:
    service.create_case("case-1")
    release = service.add_release("case-1", "IB2600000006-00")
    source = tmp_path / "hsmt.docx"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr(
            "word/document.xml",
            "<document><p>HSMT IB2600000006-00</p></document>",
        )

    membership = service.add_document(
        "case-1", release.release_id, source,
        authority=AuthorityClass.SOURCE_E_HSMT,
        evidence="document content identity",
    )
    assert membership.authority_class == AuthorityClass.SOURCE_E_HSMT.value


def test_foreign_embedded_ib_identity_cannot_be_source_membership(
    service: TenderCaseService, tmp_path: Path
) -> None:
    service.create_case("case-1")
    release = service.add_release("case-1", "IB2600000007-00")
    source = tmp_path / "foreign.docx"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr(
            "word/document.xml",
            "<document><p>HSMT IB2699999999-00</p></document>",
        )

    with pytest.raises(TenderCaseServiceError, match="does not match"):
        service.add_document(
            "case-1", release.release_id, source,
            authority=AuthorityClass.SOURCE_E_HSMT,
            evidence="foreign document",
        )


def test_release_from_another_case_cannot_receive_membership(
    service: TenderCaseService, tmp_path: Path
) -> None:
    service.create_case("case-a")
    service.create_case("case-b")
    release = service.add_release("case-a", "IB2600000008-00")
    source = tmp_path / "cross-case.pdf"
    source.write_bytes(b"cross case")

    with pytest.raises(TenderCaseServiceError, match="does not belong"):
        service.add_document(
            "case-b", release.release_id, source,
            authority=AuthorityClass.REFERENCE_ONLY,
            evidence="explicit reference",
        )


def test_retrieve_managed_original_reopens_and_detects_tamper(
    service: TenderCaseService, tmp_path: Path
) -> None:
    service.create_case("case-1")
    release = service.add_release("case-1", "IB2600000005-00")
    source = tmp_path / "source.xlsx"
    source.write_bytes(b"immutable source bytes")
    membership = service.add_document(
        "case-1",
        release.release_id,
        source,
        authority=AuthorityClass.SOURCE_E_HSMT,
        evidence="explicit source evidence",
    )
    destination = tmp_path / "retrieved.xlsx"
    result = service.retrieve_managed_original(membership.id, destination)
    assert result == destination
    assert destination.read_bytes() == b"immutable source bytes"
    assert hashlib.sha256(destination.read_bytes()).hexdigest() != ""

    managed_path = service.managed_path(membership.document_id)
    managed_path.write_bytes(b"tampered")
    with pytest.raises(ManagedDocumentShaMismatch, match="SHA"):
        service.retrieve_managed_original(membership.id, tmp_path / "tampered.xlsx")


def test_missing_membership_or_managed_file_fails_closed(
    service: TenderCaseService, tmp_path: Path
) -> None:
    with pytest.raises(TenderCaseServiceError, match="membership"):
        service.retrieve_managed_original(999, tmp_path / "missing.pdf")
