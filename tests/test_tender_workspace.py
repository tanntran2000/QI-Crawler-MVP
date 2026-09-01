from __future__ import annotations

import json
from pathlib import Path

import pytest

from qi_crawler.db import Database
from qi_crawler.tender_case import AuthorityClass
from qi_crawler.tender_workspace import (
    TEAM_BID_ZONES,
    TeamBidZone,
    TenderWorkspaceError,
    TenderWorkspaceService,
)
from qi_crawler.workspace_candidate_intake import ConfirmedWorkspaceCandidate


@pytest.fixture
def workspace(tmp_path: Path) -> TenderWorkspaceService:
    database = Database(f"sqlite:///{tmp_path / 'workspace.db'}")
    return TenderWorkspaceService(database, tmp_path / "managed")


def _release(workspace: TenderWorkspaceService, case_id: str = "case-1"):
    workspace.create_case(case_id)
    return workspace.add_release(case_id, "IB2600000100-00")


def test_team_bid_zones_are_exactly_seven_logical_names() -> None:
    assert tuple(zone.value for zone in TEAM_BID_ZONES) == (
        "01_Source_E-HSMT",
        "02_Requirement_Register",
        "03_Legal_Capability",
        "04_Technical_Vendor",
        "05_Commercial_Price",
        "06_Submission_FINAL",
        "07_Evidence_Archive",
    )
    assert TeamBidZone.SOURCE_E_HSMT.value != AuthorityClass.SOURCE_E_HSMT.value


def test_folder_intake_assigns_explicit_zones_and_reopens(workspace, tmp_path: Path) -> None:
    release = _release(workspace)
    folder = tmp_path / "incoming"
    folder.mkdir()
    first = folder / "source.pdf"
    second = folder / "requirements.docx"
    first.write_bytes(b"source bytes")
    second.write_bytes(b"working requirements")

    candidates = workspace.scan_folder(folder)
    entries = workspace.add_confirmed_candidates(
        "case-1",
        release.release_id,
        (
            ConfirmedWorkspaceCandidate(
                candidate=candidates[0],
                role="C3",
                zone=TeamBidZone.SOURCE_E_HSMT,
                authority=AuthorityClass.SOURCE_E_HSMT,
                evidence="Team Bid confirmed source document",
                uploaded_by="Team Bid",
            ),
            ConfirmedWorkspaceCandidate(
                candidate=candidates[1],
                role="OTH",
                zone=TeamBidZone.REQUIREMENT_REGISTER,
                authority=AuthorityClass.DERIVED_REQUIREMENT,
                evidence="Team Bid confirmed requirement document",
                uploaded_by="Team Bid",
            ),
        ),
    )
    assert len(entries) == 2
    manifest = workspace.manifest("case-1")
    assert len(manifest.for_zone(TeamBidZone.SOURCE_E_HSMT)) == 1
    assert len(manifest.for_zone(TeamBidZone.REQUIREMENT_REGISTER)) == 1

    reopened_database = Database(f"sqlite:///{tmp_path / 'workspace.db'}")
    reopened = TenderWorkspaceService(reopened_database, tmp_path / "managed")
    assert len(reopened.manifest("case-1").for_zone(TeamBidZone.SOURCE_E_HSMT)) == 1


def test_controlled_export_is_zone_layout_with_manifest_and_no_source_mutation(
    workspace, tmp_path: Path
) -> None:
    release = _release(workspace)
    source = tmp_path / "hsmt.pdf"
    source.write_bytes(b"immutable source")
    original = source.read_bytes()
    workspace.add_path_to_zone(
        "case-1",
        release.release_id,
        source,
        zone=TeamBidZone.SOURCE_E_HSMT,
        authority=AuthorityClass.SOURCE_E_HSMT,
        evidence="explicit source declaration",
    )

    output = tmp_path / "exported-workspace"
    result = workspace.export("case-1", output)
    assert result.entry_count == 1
    exported = output / TeamBidZone.SOURCE_E_HSMT.value / source.name
    assert exported.read_bytes() == original
    payload = json.loads((output / "WORKSPACE_MANIFEST.json").read_text(encoding="utf-8"))
    assert payload["case_id"] == "case-1"
    assert payload["entries"][0]["zone"] == TeamBidZone.SOURCE_E_HSMT.value
    assert payload["entries"][0]["release_raw_id"] == "IB2600000100-00"
    assert payload["entries"][0]["release_base_id"] == "IB2600000100"
    assert payload["entries"][0]["release_revision"] == "00"
    assert source.read_bytes() == original


def test_export_materializes_all_team_bid_zone_directories_when_only_source_populated(
    workspace, tmp_path: Path
) -> None:
    release = _release(workspace)
    source = tmp_path / "hsmt.pdf"
    source.write_bytes(b"source only")
    workspace.add_path_to_zone(
        "case-1",
        release.release_id,
        source,
        zone=TeamBidZone.SOURCE_E_HSMT,
        authority=AuthorityClass.SOURCE_E_HSMT,
        evidence="explicit source declaration",
    )

    output = tmp_path / "all-zones"
    workspace.export("case-1", output)

    assert tuple(
        zone.value for zone in TEAM_BID_ZONES if (output / zone.value).is_dir()
    ) == tuple(zone.value for zone in TEAM_BID_ZONES)


def test_export_does_not_overwrite_existing_destination(workspace, tmp_path: Path) -> None:
    release = _release(workspace)
    source = tmp_path / "hsmt.pdf"
    source.write_bytes(b"immutable source")
    workspace.add_path_to_zone(
        "case-1",
        release.release_id,
        source,
        zone=TeamBidZone.SOURCE_E_HSMT,
        authority=AuthorityClass.SOURCE_E_HSMT,
        evidence="explicit source declaration",
    )
    output = tmp_path / "existing"
    output.mkdir()
    with pytest.raises(TenderWorkspaceError, match="already exists"):
        workspace.export("case-1", output)


def test_zip_is_supported_as_one_explicit_workspace_entry(workspace, tmp_path: Path) -> None:
    import zipfile

    release = _release(workspace)
    source = tmp_path / "bundle.zip"
    with zipfile.ZipFile(source, "w") as archive:
        archive.writestr("HSMT.pdf", b"inside bundle")
    entries = workspace.add_path_to_zone(
        "case-1",
        release.release_id,
        source,
        zone=TeamBidZone.EVIDENCE_ARCHIVE,
        authority=AuthorityClass.REFERENCE_ONLY,
        evidence="explicit reference bundle",
    )
    assert len(entries) == 1
    assert workspace.manifest("case-1").for_zone(TeamBidZone.EVIDENCE_ARCHIVE)[0].filename == "bundle.zip"
