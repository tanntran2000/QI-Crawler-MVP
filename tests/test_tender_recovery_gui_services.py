from __future__ import annotations

from pathlib import Path

from qi_crawler.config import AppConfig
from qi_crawler.db import Database
from qi_crawler.gui_services import run_tender_recovery_scan
from qi_crawler.tender_case import AuthorityClass
from qi_crawler.tender_workspace import TeamBidZone, TenderWorkspaceService


def test_recovery_gui_scan_exposes_human_readable_integrity_state(tmp_path: Path) -> None:
    config = AppConfig()
    config.storage.database_url = f"sqlite:///{tmp_path / 'recovery-gui.db'}"
    config.storage.document_dir = tmp_path / "managed"
    service = TenderWorkspaceService(Database(config.storage.database_url), config.storage.document_dir)
    service.create_case("case-recovery-gui")
    release = service.add_release("case-recovery-gui", "IB2600999200-00")
    source = tmp_path / "source.pdf"
    source.write_bytes(b"GUI state bytes")
    entry = service.add_path_to_zone(
        "case-recovery-gui",
        release.release_id,
        source,
        zone=TeamBidZone.SOURCE_E_HSMT,
        authority=AuthorityClass.SOURCE_E_HSMT,
        evidence="GUI scan fixture",
    )[0]
    Path(entry.stored_path).unlink()

    report = run_tender_recovery_scan(config, "case-recovery-gui", release.release_id)

    assert report.entries[0].state.value == "MISSING"
