from __future__ import annotations

from hashlib import sha256
from pathlib import Path

import pytest
from pypdf import PdfWriter
from pypdf.generic import DecodedStreamObject, DictionaryObject, NameObject
from sqlalchemy import func, select

from qi_crawler.db import Database
from qi_crawler.document_intake import (
    BundleMembershipClaim,
    DocumentIdentityMismatch,
    DocumentIntakeService,
)
from qi_crawler.manual_tender import ManualTenderWorkspaceService
from qi_crawler.models import Document, Notice
from qi_crawler.native_extraction import NativeHSMTExtractionService


@pytest.fixture
def intake(tmp_path: Path) -> DocumentIntakeService:
    database = Database(f"sqlite:///{tmp_path / 'bundle.db'}")
    ManualTenderWorkspaceService(database).create_workspace("IB2500585490")
    return DocumentIntakeService(database, tmp_path / "documents")


def _pdf(path: Path, text: str = "") -> Path:
    writer = PdfWriter()
    page = writer.add_blank_page(width=144, height=144)
    if text:
        font = DictionaryObject(
            {
                NameObject("/Type"): NameObject("/Font"),
                NameObject("/Subtype"): NameObject("/Type1"),
                NameObject("/BaseFont"): NameObject("/Helvetica"),
            }
        )
        font_ref = writer._add_object(font)
        page[NameObject("/Resources")] = DictionaryObject(
            {NameObject("/Font"): DictionaryObject({NameObject("/F1"): font_ref})}
        )
        contents = DecodedStreamObject()
        contents.set_data(f"BT /F1 12 Tf 12 72 Td ({text}) Tj ET".encode("latin-1"))
        page[NameObject("/Contents")] = writer._add_object(contents)
    with path.open("wb") as stream:
        writer.write(stream)
    return path


def test_content_identity_uses_exact_same_revision_bundle(
    intake: DocumentIntakeService, tmp_path: Path
) -> None:
    result = intake.intake_file(
        _pdf(tmp_path / "primary.pdf", "IB2500585490-00"),
        tender_reference="IB2500585490",
    )

    assert result.bundle_base_notice_id == "IB2500585490"
    assert result.bundle_revision == "00"
    assert result.bundle_membership_status == "EXACT_BUNDLE"
    assert result.identity_status == "DOCUMENT_VERIFIED"


def test_same_tender_different_revisions_remain_separate_bundles(
    intake: DocumentIntakeService, tmp_path: Path
) -> None:
    first = intake.intake_file(
        _pdf(tmp_path / "revision-00.pdf", "IB2500585490-00"),
        tender_reference="IB2500585490",
    )
    second = intake.intake_file(
        _pdf(tmp_path / "revision-01.pdf", "IB2500585490-01"),
        tender_reference="IB2500585490",
    )

    assert (first.bundle_base_notice_id, first.bundle_revision) == ("IB2500585490", "00")
    assert (second.bundle_base_notice_id, second.bundle_revision) == ("IB2500585490", "01")
    assert second.identity_match_status == "SAME_TENDER_DIFFERENT_REVISION"


def test_content_identity_from_another_tender_is_blocked(
    intake: DocumentIntakeService, tmp_path: Path
) -> None:
    with pytest.raises(DocumentIdentityMismatch, match="CRITICAL_MISMATCH"):
        intake.intake_file(
            _pdf(tmp_path / "other.pdf", "IB2500999999-00"),
            tender_reference="IB2500585490",
        )


def test_no_identity_can_link_to_primary_hsmt_by_explicit_reference(
    intake: DocumentIntakeService, tmp_path: Path
) -> None:
    primary = intake.intake_file(
        _pdf(tmp_path / "primary.pdf", "IB2500585490-00"),
        tender_reference="IB2500585490",
        document_name="Hồ sơ mời thầu qua mạng",
    )

    linked = intake.intake_file(
        _pdf(tmp_path / "appendix.pdf"),
        tender_reference="IB2500585490",
        bundle_claim=BundleMembershipClaim(
            "REFERENCE_LINKED",
            "primary-document:page:1",
            reference_document_id=primary.document_id,
        ),
    )

    assert linked.identity_match_status == "NO_CONTENT_ID"
    assert linked.bundle_membership_status == "REFERENCE_LINKED"
    assert (linked.bundle_base_notice_id, linked.bundle_revision) == ("IB2500585490", "00")


def test_no_identity_can_link_to_official_download_batch(tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'web-bundle.db'}")
    database.require_current_schema()
    tender_url = "https://official.example.test/tender/IB2500585490-00"
    with database.session() as session:
        session.add(
            Notice(
                source_url=tender_url,
                url_hash=sha256(tender_url.encode()).hexdigest(),
                notice_code="IB2500585490-00",
                source_name="egp",
                title="Tender from official source",
            )
        )
    service = DocumentIntakeService(database, tmp_path / "documents")
    result = service.intake_file(
        _pdf(tmp_path / "attachment.pdf"),
        tender_reference="IB2500585490-00",
        document_source="web",
        source_url="https://official.example.test/download/attachment.pdf",
        bundle_claim=BundleMembershipClaim(
            "PROVENANCE_LINKED",
            "official-download-batch:2026-08-17T00:00:00Z",
            base_notice_id="IB2500585490",
            revision="00",
        ),
    )

    assert result.bundle_membership_status == "PROVENANCE_LINKED"
    assert result.bundle_membership_source == "OFFICIAL_DOWNLOAD_BATCH"


def test_no_identity_can_link_only_after_explicit_team_bid_confirmation(
    intake: DocumentIntakeService, tmp_path: Path
) -> None:
    result = intake.intake_file(
        _pdf(tmp_path / "team-bid.pdf"),
        tender_reference="IB2500585490",
        bundle_claim=BundleMembershipClaim(
            "HUMAN_LINKED",
            "team-bid-confirmation:2026-08-17",
            base_notice_id="IB2500585490",
            revision="00",
            confirmed_by="Team Bid A",
        ),
    )

    assert result.bundle_membership_status == "HUMAN_LINKED"
    assert result.bundle_membership_source == "TEAM_BID_CONFIRMATION"


def test_no_identity_without_explicit_membership_is_held_for_review(
    intake: DocumentIntakeService, tmp_path: Path
) -> None:
    result = intake.intake_file(
        _pdf(tmp_path / "unknown.pdf"), tender_reference="IB2500585490"
    )

    assert result.bundle_membership_status == "NEEDS_REVIEW"
    assert result.identity_status == "HUMAN_DECLARED"


def test_same_sha_in_one_bundle_reuses_one_logical_document(
    intake: DocumentIntakeService, tmp_path: Path
) -> None:
    source = _pdf(tmp_path / "duplicate.pdf", "IB2500585490-00")
    first = intake.intake_file(source, tender_reference="IB2500585490")
    duplicate = intake.intake_file(source, tender_reference="IB2500585490")

    assert duplicate.outcome == "DUPLICATE"
    assert duplicate.document_id == first.document_id
    with intake.database.session() as session:
        assert session.scalar(select(func.count(Document.id))) == 1


def test_managed_storage_remains_independent_when_external_source_is_deleted(
    intake: DocumentIntakeService, tmp_path: Path
) -> None:
    external_dir = tmp_path / "downloads"
    external_dir.mkdir(parents=True, exist_ok=True)
    external_file = _pdf(external_dir / "external_hsmt.pdf", "IB2500585490-00")
    original_bytes = external_file.read_bytes()
    expected_sha = sha256(original_bytes).hexdigest()

    result = intake.intake_file(
        external_file,
        tender_reference="IB2500585490",
        document_name="Hồ sơ mời thầu chính",
    )

    assert result.outcome == "IMPORTED"
    assert result.sha256 == expected_sha
    assert result.stored_path.exists()
    assert result.stored_path.resolve() != external_file.resolve()

    # Destructive action: External original is deleted
    external_file.unlink()
    assert not external_file.exists()

    # The crawler-managed copy must remain intact, readable, byte-identical, and match the SHA-256
    assert result.stored_path.is_file()
    assert result.stored_path.read_bytes() == original_bytes
    assert sha256(result.stored_path.read_bytes()).hexdigest() == expected_sha

    # Downstream extraction on the crawler-managed copy succeeds without external file
    with intake.database.session() as session:
        document = session.get(Document, result.document_id)
        assert document is not None
        assert Path(document.stored_path).is_file()
        assert Path(document.stored_path).read_bytes() == original_bytes

    extraction = NativeHSMTExtractionService(intake.database).extract_document(result.document_id)
    assert extraction.document_id == result.document_id
    assert extraction.status in {"NATIVE_OK", "NEEDS_REVIEW"}
