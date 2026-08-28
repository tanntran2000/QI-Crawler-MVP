from __future__ import annotations

import json
from pathlib import Path

import pytest

from qi_crawler.db import Database
from qi_crawler.market_intelligence.opportunity_contract import OpportunityIdentity
from qi_crawler.models import Document
from qi_crawler.tender_case import AuthorityClass, PlanContext
from qi_crawler.tender_workspace import (
    ManagedIntegrityState,
    TeamBidZone,
    TenderWorkspaceError,
    TenderWorkspaceService,
)


@pytest.fixture
def workspace(tmp_path: Path) -> TenderWorkspaceService:
    return TenderWorkspaceService(
        Database(f"sqlite:///{tmp_path / 'ops.db'}"), tmp_path / "managed"
    )


def _case_with_revisions(workspace: TenderWorkspaceService) -> tuple[int, int]:
    workspace.create_case(
        "case-ops",
        plan_context=PlanContext(OpportunityIdentity.from_raw("PL2600000001-00")),
    )
    first = workspace.add_release("case-ops", "IB2600000001-00")
    second = workspace.add_release("case-ops", "IB2600000001-01")
    return first.release_id, second.release_id


def _source(path: Path, content: bytes = b"source") -> Path:
    path.write_bytes(content)
    return path


def test_search_cases_preserves_exact_revisions_and_linked_plan(workspace) -> None:
    first, second = _case_with_revisions(workspace)

    results = workspace.search_cases("ib2600000001")

    assert [item.release_id for item in results] == [first, second]
    assert [item.release_raw_id for item in results] == [
        "IB2600000001-00",
        "IB2600000001-01",
    ]
    assert results[0].plan_raw_id == "PL2600000001-00"


def test_case_level_export_fails_closed_when_multiple_releases_exist(
    workspace, tmp_path: Path
) -> None:
    first, second = _case_with_revisions(workspace)
    assert first != second

    with pytest.raises(TenderWorkspaceError, match="exact release"):
        workspace.export("case-ops", tmp_path / "unsafe")


def test_exact_release_export_isolates_revision_and_materializes_active_view(
    workspace, tmp_path: Path
) -> None:
    first, second = _case_with_revisions(workspace)
    first_file = _source(tmp_path / "first.pdf", b"first")
    second_file = _source(tmp_path / "second.pdf", b"second")
    workspace.add_path_to_zone(
        "case-ops", first, first_file, zone=TeamBidZone.SOURCE_E_HSMT,
        authority=AuthorityClass.SOURCE_E_HSMT, evidence="source first",
    )
    workspace.add_path_to_zone(
        "case-ops", second, second_file, zone=TeamBidZone.SOURCE_E_HSMT,
        authority=AuthorityClass.SOURCE_E_HSMT, evidence="source second",
    )

    output = workspace.export_release("case-ops", first, tmp_path / "first-export")

    assert output.entry_count == 1
    manifest = json.loads((output.output / "WORKSPACE_MANIFEST.json").read_text())
    assert {entry["release_id"] for entry in manifest["entries"]} == {first}
    assert not (output.output / TeamBidZone.SOURCE_E_HSMT.value / second_file.name).exists()


def test_zone_authority_matrix_fails_closed(workspace, tmp_path: Path) -> None:
    release_id, _ = _case_with_revisions(workspace)
    source = _source(tmp_path / "wrong.pdf")

    with pytest.raises(TenderWorkspaceError, match="not compatible"):
        workspace.add_path_to_zone(
            "case-ops", release_id, source,
            zone=TeamBidZone.SOURCE_E_HSMT,
            authority=AuthorityClass.REFERENCE_ONLY,
            evidence="wrong authority",
        )


def test_replace_uses_explicit_slot_and_same_sha_is_idempotent(workspace, tmp_path: Path) -> None:
    release_id, _ = _case_with_revisions(workspace)
    source = _source(tmp_path / "working.docx", b"working")
    entry = workspace.add_path_to_zone(
        "case-ops", release_id, source,
        zone=TeamBidZone.TECHNICAL_VENDOR,
        authority=AuthorityClass.WORKING_E_HSDT,
        evidence="working draft",
    )[0]

    same = workspace.replace_entry(
        "case-ops", release_id, entry.id, source,
        evidence="same content", actor="Team Bid",
    )
    assert same.status == "NO_CHANGE_IDENTICAL_CONTENT"
    assert workspace.release_manifest("case-ops", release_id).entries[0].id == entry.id

    replacement = _source(tmp_path / "replacement.docx", b"replacement")
    result = workspace.replace_entry(
        "case-ops", release_id, entry.id, replacement,
        evidence="new working draft", actor="Team Bid",
    )
    assert result.status == "REPLACED"
    assert result.entry.slot_key == entry.slot_key
    manifest = workspace.release_manifest("case-ops", release_id)
    assert manifest.entries[0].operational_state == "SUPERSEDED"
    assert manifest.active_entries == (result.entry,)
    assert manifest.history[0].transition_type.value == "SUPERSEDE"
    exported = workspace.export_release("case-ops", release_id, tmp_path / "replacement-export")
    export_manifest = json.loads((exported.output / "WORKSPACE_MANIFEST.json").read_text())
    historical = next(item for item in export_manifest["entries"] if item["entry_id"] == entry.id)
    current = next(item for item in export_manifest["entries"] if item["entry_id"] == result.entry.id)
    assert historical["export_filename"] is None
    assert current["export_filename"] is not None
    assert len(export_manifest["transitions"]) == 1
    with pytest.raises(TenderWorkspaceError, match="not active"):
        workspace.replace_entry(
            "case-ops", release_id, entry.id, _source(tmp_path / "third.docx", b"third"),
            evidence="second replacement", actor="Team Bid",
        )


def test_transition_history_survives_service_restart(workspace, tmp_path: Path) -> None:
    release_id, _ = _case_with_revisions(workspace)
    original = _source(tmp_path / "restart-original.docx", b"original")
    entry = workspace.add_path_to_zone(
        "case-ops", release_id, original,
        zone=TeamBidZone.TECHNICAL_VENDOR,
        authority=AuthorityClass.WORKING_E_HSDT,
        evidence="restart original",
    )[0]
    replacement = _source(tmp_path / "restart-replacement.docx", b"replacement")
    workspace.replace_entry(
        "case-ops", release_id, entry.id, replacement,
        evidence="restart replacement", actor="Team Bid",
    )

    reopened = TenderWorkspaceService(workspace.database, workspace.case_service.intake.document_root)
    manifest = reopened.release_manifest("case-ops", release_id)

    assert len(manifest.history) == 1
    assert manifest.history[0].prior_entry_id == entry.id
    assert len(manifest.active_entries) == 1
    assert manifest.active_entries[0].filename == replacement.name


def test_assigning_a_second_active_entry_to_same_slot_is_forbidden(workspace, tmp_path: Path) -> None:
    release_id, _ = _case_with_revisions(workspace)
    first = _source(tmp_path / "first.docx", b"first")
    second = _source(tmp_path / "second.docx", b"second")
    entry = workspace.add_path_to_zone(
        "case-ops", release_id, first,
        zone=TeamBidZone.TECHNICAL_VENDOR,
        authority=AuthorityClass.WORKING_E_HSDT,
        evidence="first",
    )[0]
    membership = workspace.case_service.add_document(
        "case-ops", release_id, second,
        authority=AuthorityClass.WORKING_E_HSDT,
        evidence="second",
    )
    with pytest.raises(TenderWorkspaceError, match="semantic slot"):
        workspace.assign_membership(
            membership.id, TeamBidZone.TECHNICAL_VENDOR, slot_key=entry.slot_key
        )


def test_replace_rejects_embedded_identity_from_another_release(workspace, tmp_path: Path) -> None:
    from zipfile import ZipFile

    first, second = _case_with_revisions(workspace)
    source = _source(tmp_path / "working.docx", b"working")
    entry = workspace.add_path_to_zone(
        "case-ops", first, source,
        zone=TeamBidZone.TECHNICAL_VENDOR,
        authority=AuthorityClass.WORKING_E_HSDT,
        evidence="working draft",
    )[0]
    foreign = tmp_path / "foreign.docx"
    with ZipFile(foreign, "w") as archive:
        archive.writestr(
            "word/document.xml",
            "<document><p>IB2600000001-01</p></document>",
        )
    with pytest.raises(TenderWorkspaceError, match="release mismatch"):
        workspace.replace_entry(
            "case-ops", first, entry.id, foreign,
            evidence="foreign", actor="Team Bid",
        )
    assert workspace.release_manifest("case-ops", second).entries == ()


def test_generic_source_replace_is_forbidden_and_source_correction_is_explicit(
    workspace, tmp_path: Path
) -> None:
    release_id, _ = _case_with_revisions(workspace)
    source = _source(tmp_path / "source.pdf", b"source")
    entry = workspace.add_path_to_zone(
        "case-ops", release_id, source,
        zone=TeamBidZone.SOURCE_E_HSMT,
        authority=AuthorityClass.SOURCE_E_HSMT,
        evidence="source",
    )[0]

    with pytest.raises(TenderWorkspaceError, match="generic"):
        workspace.replace_entry(
            "case-ops", release_id, entry.id, _source(tmp_path / "other.pdf"),
            evidence="not allowed", actor="Team Bid",
        )
    with pytest.raises(TenderWorkspaceError, match="operator"):
        workspace.correct_source_entry(
            "case-ops", release_id, entry.id, operator="", reason="fix", evidence="evidence"
        )

    withdrawn = workspace.correct_source_entry(
        "case-ops", release_id, entry.id, operator="Team Bid", reason="wrong source",
        evidence="explicit correction",
    )
    assert withdrawn.status == "WITHDRAWN_BY_CORRECTION"
    manifest = workspace.release_manifest("case-ops", release_id)
    assert manifest.entries[0].operational_state == "WITHDRAWN_BY_CORRECTION"
    exported = workspace.export_release("case-ops", release_id, tmp_path / "withdrawn-export")
    assert exported.entry_count == 0
    assert not any(
        path.is_file()
        for path in exported.output.rglob("*")
        if path.name != "WORKSPACE_MANIFEST.json"
    )


def test_source_correction_rejects_new_official_revision(tmp_path: Path) -> None:
    from zipfile import ZipFile

    workspace = TenderWorkspaceService(
        Database(f"sqlite:///{tmp_path / 'revision.db'}"), tmp_path / "managed"
    )
    workspace.create_case("case-revision")
    release = workspace.add_release("case-revision", "IB2600000002-00")
    source = _source(tmp_path / "source.pdf", b"source")
    entry = workspace.add_path_to_zone(
        "case-revision", release.release_id, source,
        zone=TeamBidZone.SOURCE_E_HSMT,
        authority=AuthorityClass.SOURCE_E_HSMT,
        evidence="source",
    )[0]
    revised = tmp_path / "revised.docx"
    with ZipFile(revised, "w") as archive:
        archive.writestr(
            "word/document.xml",
            "<document><p>IB2600000002-01</p></document>",
        )

    with pytest.raises(TenderWorkspaceError, match="NEW_RELEASE_REQUIRED"):
        workspace.correct_source_entry(
            "case-revision", release.release_id, entry.id, revised,
            operator="Team Bid", reason="new publication", evidence="identity proof",
        )


def test_dashboard_integrity_is_not_checked_until_bytes_are_verified(workspace, tmp_path: Path) -> None:
    release_id, _ = _case_with_revisions(workspace)
    source = _source(tmp_path / "dashboard.pdf", b"dashboard")
    workspace.add_path_to_zone(
        "case-ops", release_id, source,
        zone=TeamBidZone.EVIDENCE_ARCHIVE,
        authority=AuthorityClass.REFERENCE_ONLY,
        evidence="reference",
    )

    dashboard = workspace.release_dashboard("case-ops", release_id)
    assert dashboard.zones[6].entries[0].integrity_state is ManagedIntegrityState.NOT_CHECKED
    verified = workspace.release_dashboard("case-ops", release_id, verify_integrity=True)
    assert verified.zones[6].entries[0].integrity_state is ManagedIntegrityState.VERIFIED

    managed = verified.zones[6].entries[0].stored_path
    managed.unlink()
    missing = workspace.release_dashboard("case-ops", release_id, verify_integrity=True)
    assert missing.zones[6].entries[0].integrity_state is ManagedIntegrityState.MISSING

    managed.parent.mkdir(parents=True, exist_ok=True)
    managed.write_bytes(b"tampered")
    mismatch = workspace.release_dashboard("case-ops", release_id, verify_integrity=True)
    assert mismatch.zones[6].entries[0].integrity_state is ManagedIntegrityState.MISMATCH


def test_export_disambiguates_windows_collisions_deterministically(workspace, tmp_path: Path) -> None:
    release_id, _ = _case_with_revisions(workspace)
    first = _source(tmp_path / "BaoGia.xlsx", b"one")
    second = _source(tmp_path / "BaoGia .xlsx", b"two")
    workspace.add_path_to_zone(
        "case-ops", release_id, first,
        zone=TeamBidZone.COMMERCIAL_PRICE,
        authority=AuthorityClass.WORKING_E_HSDT,
        evidence="first price",
    )
    workspace.add_path_to_zone(
        "case-ops", release_id, second,
        zone=TeamBidZone.COMMERCIAL_PRICE,
        authority=AuthorityClass.WORKING_E_HSDT,
        evidence="second price",
    )

    output = workspace.export_release("case-ops", release_id, tmp_path / "collision-export")
    names = sorted(path.name for path in (output.output / TeamBidZone.COMMERCIAL_PRICE.value).iterdir())
    assert len(names) == 2
    assert names[0] != names[1]
    manifest = json.loads((output.output / "WORKSPACE_MANIFEST.json").read_text())
    active = [entry for entry in manifest["entries"] if entry["export_filename"]]
    assert len({entry["export_filename"] for entry in active}) == 2


def test_add_is_logically_atomic_when_workspace_assignment_fails(workspace, tmp_path: Path, monkeypatch) -> None:
    release_id, _ = _case_with_revisions(workspace)
    source = _source(tmp_path / "atomic.pdf")

    def fail_assignment(*args, **kwargs):
        raise TenderWorkspaceError("injected assignment failure")

    monkeypatch.setattr(workspace, "assign_membership", fail_assignment)
    with pytest.raises(TenderWorkspaceError, match="injected"):
        workspace.add_path_to_zone(
            "case-ops", release_id, source,
            zone=TeamBidZone.SOURCE_E_HSMT,
            authority=AuthorityClass.SOURCE_E_HSMT,
            evidence="atomic test",
        )
    assert workspace.case_service.get_release_manifest("case-ops", release_id).memberships == ()
    with workspace.database.session() as session:
        assert session.query(Document).count() == 0


def test_add_cleans_document_when_membership_validation_fails_after_intake(
    workspace, tmp_path: Path, monkeypatch
) -> None:
    release_id, _ = _case_with_revisions(workspace)
    source = tmp_path / "wrong-source.pdf"
    source.write_bytes(b"source with wrong embedded identity")
    original = workspace.case_service.add_document

    def fail_after_intake(*args, **kwargs):
        original(*args, **kwargs)
        raise TenderWorkspaceError("injected membership validation failure")

    # The wrapper models a post-intake membership validation failure: the
    # Document has been committed, but no membership result reaches the caller.
    monkeypatch.setattr(workspace.case_service, "add_document", fail_after_intake)
    with pytest.raises(TenderWorkspaceError, match="injected"):
        workspace.add_path_to_zone(
            "case-ops",
            release_id,
            source,
            zone=TeamBidZone.SOURCE_E_HSMT,
            authority=AuthorityClass.SOURCE_E_HSMT,
            evidence="atomic post-intake test",
        )

    with workspace.database.session() as session:
        assert session.query(Document).count() == 0
