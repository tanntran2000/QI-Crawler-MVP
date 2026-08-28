from __future__ import annotations

from pathlib import Path

from qi_crawler.config import AppConfig
from qi_crawler.db import Database
from qi_crawler.gui_services import (
    run_tender_workspace_add_path,
    run_tender_workspace_export,
    run_tender_workspace_manifest,
    run_tender_workspace_open_or_create,
)
from qi_crawler.tender_case import AuthorityClass
from qi_crawler.tender_workspace import TeamBidZone, TenderWorkspaceService


def test_gui_service_adapters_delegate_workspace_manifest_and_export(tmp_path: Path) -> None:
    config = AppConfig()
    config.storage.database_url = f"sqlite:///{tmp_path / 'gui-workspace.db'}"
    config.storage.document_dir = tmp_path / "managed"
    database = Database(config.storage.database_url)
    service = TenderWorkspaceService(database, config.storage.document_dir)
    service.create_case("case-gui")
    release = service.add_release("case-gui", "IB2600000200-00")
    source = tmp_path / "hsmt.pdf"
    source.write_bytes(b"gui workspace source")
    service.add_path_to_zone(
        "case-gui",
        release.release_id,
        source,
        zone=TeamBidZone.SOURCE_E_HSMT,
        authority=AuthorityClass.SOURCE_E_HSMT,
        evidence="Team Bid source",
    )

    manifest = run_tender_workspace_manifest(config, "case-gui")
    assert len(manifest.for_zone(TeamBidZone.SOURCE_E_HSMT)) == 1
    result = run_tender_workspace_export(config, "case-gui", tmp_path / "out")
    assert result.entry_count == 1


def test_gui_service_adapters_open_create_and_assign_explicit_zone(tmp_path: Path) -> None:
    config = AppConfig()
    config.storage.database_url = f"sqlite:///{tmp_path / 'gui-open.db'}"
    config.storage.document_dir = tmp_path / "managed"
    source = tmp_path / "requirements.docx"
    source.write_bytes(b"requirements")

    release_id = run_tender_workspace_open_or_create(
        config,
        "case-open",
        "IB2600000201-00",
    )
    entries = run_tender_workspace_add_path(
        config,
        "case-open",
        release_id,
        source,
        TeamBidZone.REQUIREMENT_REGISTER,
        AuthorityClass.DERIVED_REQUIREMENT,
        "Team Bid requirement register",
    )

    reopened_release_id = run_tender_workspace_open_or_create(
        config,
        "case-open",
        "IB2600000201-00",
    )
    assert reopened_release_id == release_id
    assert entries[0].zone is TeamBidZone.REQUIREMENT_REGISTER
