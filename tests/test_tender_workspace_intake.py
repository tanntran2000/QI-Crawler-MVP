from __future__ import annotations

import hashlib
from dataclasses import replace
from pathlib import Path

import pytest

from qi_crawler.db import Database
from qi_crawler.models import Document, TenderDocumentMembershipRecord, TenderWorkspaceEntryRecord
from qi_crawler.tender_case import AuthorityClass
from qi_crawler.tender_workspace import (
    TeamBidZone,
    TenderWorkspaceError,
    TenderWorkspaceService,
)
from qi_crawler.workspace_candidate_intake import ConfirmedWorkspaceCandidate


@pytest.fixture
def workspace(tmp_path: Path) -> TenderWorkspaceService:
    return TenderWorkspaceService(
        Database(f"sqlite:///{tmp_path / 'intake.db'}"), tmp_path / "managed"
    )


def _release(workspace: TenderWorkspaceService, case_id: str = "case-1", raw_id: str = "IB2600000100-00") -> int:
    workspace.create_case(case_id)
    return workspace.add_release(case_id, raw_id).release_id


def _counts(workspace: TenderWorkspaceService) -> tuple[int, int, int]:
    with workspace.database.session() as session:
        return (
            session.query(Document).count(),
            session.query(TenderDocumentMembershipRecord).count(),
            session.query(TenderWorkspaceEntryRecord).count(),
        )


def _confirmed(
    candidate,
    *,
    role: str = "C3",
    zone: TeamBidZone = TeamBidZone.TECHNICAL_VENDOR,
    authority: AuthorityClass = AuthorityClass.WORKING_E_HSDT,
) -> ConfirmedWorkspaceCandidate:
    return ConfirmedWorkspaceCandidate(
        candidate=candidate,
        role=role,
        zone=zone,
        authority=authority,
        evidence="Team Bid confirmed candidate",
        uploaded_by="Team Bid",
    )


def test_scan_folder_returns_candidates_without_warehouse_writes(workspace, tmp_path: Path) -> None:
    release_id = _release(workspace)
    folder = tmp_path / "incoming"
    folder.mkdir()
    (folder / "Chuong III.docx").write_bytes(b"chapter three")
    (folder / "notes.txt").write_bytes(b"ignored")
    before = _counts(workspace)

    candidates = workspace.scan_folder(folder)

    assert len(candidates) == 1
    assert candidates[0].original_filename == "Chuong III.docx"
    assert candidates[0].relative_path == Path("Chuong III.docx")
    assert candidates[0].suggested_role == "C3"
    assert _counts(workspace) == before
    assert release_id
    assert not (tmp_path / "managed").exists()


def test_rescan_discovers_new_supported_file_without_import(workspace, tmp_path: Path) -> None:
    _release(workspace)
    folder = tmp_path / "incoming"
    folder.mkdir()
    (folder / "first.pdf").write_bytes(b"first")
    assert len(workspace.scan_folder(folder)) == 1
    (folder / "second.xlsx").write_bytes(b"second")

    candidates = workspace.scan_folder(folder)

    assert [candidate.original_filename for candidate in candidates] == ["first.pdf", "second.xlsx"]
    assert _counts(workspace) == (0, 0, 0)


def test_direct_directory_add_path_is_rejected_without_writes(workspace, tmp_path: Path) -> None:
    release_id = _release(workspace)
    folder = tmp_path / "incoming"
    folder.mkdir()
    (folder / "candidate.pdf").write_bytes(b"candidate")
    before = _counts(workspace)

    with pytest.raises(
        TenderWorkspaceError,
        match="Folder intake requires scan and explicit candidate confirmation",
    ):
        workspace.add_path_to_zone(
            "case-1", release_id, folder,
            zone=TeamBidZone.EVIDENCE_ARCHIVE,
            authority=AuthorityClass.REFERENCE_ONLY,
            evidence="folder",
        )

    assert _counts(workspace) == before


def test_only_explicitly_confirmed_candidates_are_ingested(workspace, tmp_path: Path) -> None:
    release_id = _release(workspace)
    folder = tmp_path / "incoming"
    folder.mkdir()
    (folder / "one.docx").write_bytes(b"one")
    (folder / "two.docx").write_bytes(b"two")
    candidates = workspace.scan_folder(folder)

    entries = workspace.add_confirmed_candidates(
        "case-1", release_id, [_confirmed(candidates[0])]
    )

    assert len(entries) == 1
    assert _counts(workspace) == (1, 1, 1)
    assert entries[0].filename == "one.docx"


def test_unselected_candidate_creates_no_document_or_membership(workspace, tmp_path: Path) -> None:
    release_id = _release(workspace)
    folder = tmp_path / "incoming"
    folder.mkdir()
    (folder / "unselected.pdf").write_bytes(b"unselected")
    candidate = workspace.scan_folder(folder)[0]

    assert candidate
    assert _counts(workspace) == (0, 0, 0)
    assert release_id


def test_confirmation_rejects_candidate_changed_since_scan(workspace, tmp_path: Path) -> None:
    release_id = _release(workspace)
    folder = tmp_path / "incoming"
    folder.mkdir()
    source = folder / "changed.pdf"
    source.write_bytes(b"before")
    candidate = workspace.scan_folder(folder)[0]
    source.write_bytes(b"after")

    with pytest.raises(TenderWorkspaceError, match="CANDIDATE_CHANGED_SINCE_SCAN"):
        workspace.add_confirmed_candidates("case-1", release_id, [_confirmed(candidate)])

    assert _counts(workspace) == (0, 0, 0)


def test_foreign_package_source_candidate_is_rejected(workspace, tmp_path: Path) -> None:
    release_id = _release(workspace)
    source = tmp_path / "foreign.pdf"
    source.write_bytes(b"foreign")
    candidate = workspace.scan_folder(tmp_path)[0]
    candidate = replace(
        candidate,
        detected_raw_id="IB2600000999-00",
        detected_base_id="IB2600000999",
        detected_revision="00",
        identity_status="FOUND",
    )

    with pytest.raises(TenderWorkspaceError, match="PACKAGE_MISMATCH"):
        workspace.add_confirmed_candidates(
            "case-1", release_id,
            [_confirmed(candidate, zone=TeamBidZone.SOURCE_E_HSMT, authority=AuthorityClass.SOURCE_E_HSMT)],
        )
    assert _counts(workspace) == (0, 0, 0)


def test_same_base_different_revision_source_candidate_requires_revision_transition(workspace, tmp_path: Path) -> None:
    release_id = _release(workspace)
    source = tmp_path / "later.pdf"
    source.write_bytes(b"later")
    candidate = replace(
        workspace.scan_folder(tmp_path)[0],
        detected_raw_id="IB2600000100-01",
        detected_base_id="IB2600000100",
        detected_revision="01",
        identity_status="FOUND",
    )

    with pytest.raises(TenderWorkspaceError, match="REVISION_TRANSITION_REQUIRED"):
        workspace.add_confirmed_candidates(
            "case-1", release_id,
            [_confirmed(candidate, zone=TeamBidZone.SOURCE_E_HSMT, authority=AuthorityClass.SOURCE_E_HSMT)],
        )
    assert _counts(workspace) == (0, 0, 0)


def test_reference_only_foreign_candidate_remains_non_source(workspace, tmp_path: Path) -> None:
    release_id = _release(workspace)
    source = tmp_path / "reference.pdf"
    source.write_bytes(b"reference")
    candidate = replace(
        workspace.scan_folder(tmp_path)[0],
        detected_raw_id="IB2600000999-00",
        detected_base_id="IB2600000999",
        detected_revision="00",
        identity_status="FOUND",
    )

    entries = workspace.add_confirmed_candidates(
        "case-1", release_id,
        [_confirmed(candidate, role="REF", zone=TeamBidZone.EVIDENCE_ARCHIVE, authority=AuthorityClass.REFERENCE_ONLY)],
    )

    assert entries[0].authority is AuthorityClass.REFERENCE_ONLY
    assert entries[0].zone is TeamBidZone.EVIDENCE_ARCHIVE


def test_first_chapter_three_candidate_gets_c3_01(workspace, tmp_path: Path) -> None:
    release_id = _release(workspace)
    source = tmp_path / "first.docx"
    source.write_bytes(b"first")
    candidate = workspace.scan_folder(tmp_path)[0]
    entry = workspace.add_confirmed_candidates("case-1", release_id, [_confirmed(candidate)])[0]

    assert entry.slot_key == "pkg:IB2600000100-00|role:C3|seq:01"
    exported = workspace.export_release("case-1", release_id, tmp_path / "export")
    assert (exported.output / TeamBidZone.TECHNICAL_VENDOR.value / "C3_01.docx").is_file()


def test_second_chapter_three_candidate_gets_c3_02(workspace, tmp_path: Path) -> None:
    release_id = _release(workspace)
    first = tmp_path / "first.docx"
    second = tmp_path / "second.docx"
    first.write_bytes(b"first")
    second.write_bytes(b"second")
    candidates = workspace.scan_folder(tmp_path)
    entries = workspace.add_confirmed_candidates(
        "case-1", release_id, [_confirmed(candidates[0]), _confirmed(candidates[1])]
    )

    assert [entry.slot_key for entry in entries] == [
        "pkg:IB2600000100-00|role:C3|seq:01",
        "pkg:IB2600000100-00|role:C3|seq:02",
    ]


def test_same_role_in_another_release_starts_again_at_01(workspace, tmp_path: Path) -> None:
    workspace.create_case("case-1")
    first_release = workspace.add_release("case-1", "IB2600000100-00").release_id
    second_release = workspace.add_release("case-1", "IB2600000101-00").release_id
    source = tmp_path / "same.docx"
    source.write_bytes(b"same")
    candidate = workspace.scan_folder(tmp_path)[0]

    first = workspace.add_confirmed_candidates("case-1", first_release, [_confirmed(candidate)])[0]
    second = workspace.add_confirmed_candidates("case-1", second_release, [_confirmed(candidate)])[0]

    assert first.slot_key.endswith("|seq:01")
    assert second.slot_key.endswith("|seq:01")
    assert first.release_id != second.release_id


def test_original_filename_is_preserved(workspace, tmp_path: Path) -> None:
    release_id = _release(workspace)
    source = tmp_path / "Vendor Original Name.docx"
    source.write_bytes(b"bytes")
    entry = workspace.add_confirmed_candidates(
        "case-1", release_id, [_confirmed(workspace.scan_folder(tmp_path)[0])]
    )[0]

    assert entry.filename == "Vendor Original Name.docx"


def test_original_source_bytes_are_unchanged(workspace, tmp_path: Path) -> None:
    release_id = _release(workspace)
    source = tmp_path / "source.docx"
    original = b"immutable source"
    source.write_bytes(original)
    workspace.add_confirmed_candidates("case-1", release_id, [_confirmed(workspace.scan_folder(tmp_path)[0])])

    assert source.read_bytes() == original


def test_same_sha_in_different_releases_keeps_distinct_memberships(workspace, tmp_path: Path) -> None:
    workspace.create_case("case-1")
    first_release = workspace.add_release("case-1", "IB2600000100-00").release_id
    second_release = workspace.add_release("case-1", "IB2600000101-00").release_id
    source = tmp_path / "same.pdf"
    source.write_bytes(b"same bytes")
    candidate = workspace.scan_folder(tmp_path)[0]
    workspace.add_confirmed_candidates("case-1", first_release, [_confirmed(candidate)])
    workspace.add_confirmed_candidates("case-1", second_release, [_confirmed(candidate)])

    assert _counts(workspace) == (1, 2, 2)


def test_restart_reopen_preserves_managed_short_name(workspace, tmp_path: Path) -> None:
    release_id = _release(workspace)
    source = tmp_path / "restart.docx"
    source.write_bytes(b"restart")
    workspace.add_confirmed_candidates("case-1", release_id, [_confirmed(workspace.scan_folder(tmp_path)[0])])

    reopened = TenderWorkspaceService(workspace.database, tmp_path / "managed")

    assert reopened.release_manifest("case-1", release_id).entries[0].slot_key.endswith("|seq:01")
    output = reopened.export_release("case-1", release_id, tmp_path / "reopen-export")
    assert (output.output / TeamBidZone.TECHNICAL_VENDOR.value / "C3_01.docx").exists()


def test_short_name_is_not_database_identity(workspace, tmp_path: Path) -> None:
    release_id = _release(workspace)
    source = tmp_path / "database-name.docx"
    source.write_bytes(b"database-name")
    entry = workspace.add_confirmed_candidates(
        "case-1", release_id, [_confirmed(workspace.scan_folder(tmp_path)[0])]
    )[0]

    with workspace.database.session() as session:
        document = session.get(Document, entry.document_id)
        assert document is not None
        assert document.original_filename == "database-name.docx"
        assert document.sha256 == hashlib.sha256(b"database-name").hexdigest()
        assert entry.slot_key != document.original_filename
