from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from qi_crawler.config import AppConfig
from qi_crawler.db import Database
from qi_crawler.gui_services import (
    run_bid_radar_workspace_handoff,
    run_tender_workspace_add_path,
    run_tender_workspace_dashboard,
    run_tender_workspace_export,
    run_tender_workspace_manifest,
    run_tender_workspace_open_or_create,
    run_tender_workspace_search,
)
from qi_crawler.market_intelligence.opportunity_contract import (
    OpportunityIdentity,
    OpportunityIdentityNamespace,
    OpportunityImportBatch,
    OpportunitySourceType,
)
from qi_crawler.market_intelligence.opportunity_radar import (
    OpportunityRadarItem,
    build_observation_key,
)
from qi_crawler.market_intelligence.opportunity_review import OpportunityReviewService
from qi_crawler.migrations import upgrade_database
from qi_crawler.opportunity_review_persistence import SqlAlchemyOpportunityReviewRepository
from qi_crawler.tender_case import AuthorityClass
from qi_crawler.tender_workspace import TeamBidZone, TenderWorkspaceService


def _radar_item() -> OpportunityRadarItem:
    raw_id = "IB2600463290-00"
    source_sha256 = "a" * 64
    sheet = "TBMT"
    source_row = 7
    identity = OpportunityIdentity(
        raw_id=raw_id,
        base_id="IB2600463290",
        revision="00",
        namespace=OpportunityIdentityNamespace.IB,
    )
    filename = "TBMT-handoff.xlsx"
    batch = OpportunityImportBatch(
        source_filename=filename,
        source_sha256=source_sha256,
        sheet=sheet,
        imported_at=datetime(2026, 1, 1, tzinfo=UTC),
        schema_version="tbmt-v1",
        source_type=OpportunitySourceType.TBMT,
    )
    return OpportunityRadarItem(
        source_type=OpportunitySourceType.TBMT,
        identity=identity,
        observation_key=build_observation_key(
            source_type=OpportunitySourceType.TBMT,
            identity=identity,
            source_sha256=source_sha256,
            sheet=sheet,
            source_row=source_row,
        ),
        source_filename=batch.source_filename,
        source_sha256=source_sha256,
        sheet=sheet,
        source_row=source_row,
        schema_version=batch.schema_version,
        package_name="Gói adapter",
        project="Dự án adapter",
        package_price_raw="1000",
        package_price=Decimal(1000),
        funding_source="Ngân sách",
        source_fields={},
        raw_fields={},
        provenance={
            "source_filename": filename,
            "source_sha256": source_sha256,
            "sheet": sheet,
            "source_row": source_row,
            "source_locator": f"{sheet}!A{source_row}",
        },
    )


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


def test_gui_service_adapters_search_dashboard_and_exact_export(tmp_path: Path) -> None:
    config = AppConfig()
    config.storage.database_url = f"sqlite:///{tmp_path / 'gui-ops.db'}"
    config.storage.document_dir = tmp_path / "managed"
    database = Database(config.storage.database_url)
    service = TenderWorkspaceService(database, config.storage.document_dir)
    service.create_case("case-gui-ops")
    release = service.add_release("case-gui-ops", "IB2600000202-00")
    source = tmp_path / "evidence.pdf"
    source.write_bytes(b"gui ops")
    service.add_path_to_zone(
        "case-gui-ops", release.release_id, source,
        zone=TeamBidZone.EVIDENCE_ARCHIVE,
        authority=AuthorityClass.REFERENCE_ONLY,
        evidence="reference",
    )

    results = run_tender_workspace_search(config, "IB2600000202")
    dashboard = run_tender_workspace_dashboard(
        config, "case-gui-ops", release.release_id, True
    )
    exported = run_tender_workspace_export(
        config, "case-gui-ops", tmp_path / "exact-export", release.release_id
    )

    assert results[0].release_id == release.release_id
    assert dashboard.release_raw_id == "IB2600000202-00"
    assert dashboard.zones[6].entries[0].integrity_state.value == "VERIFIED"
    assert exported.entry_count == 1


def test_bid_radar_workspace_handoff_adapter_uses_persisted_review(tmp_path: Path) -> None:
    config = AppConfig()
    config.storage.database_url = f"sqlite:///{tmp_path / 'gui-handoff.db'}"
    config.storage.document_dir = tmp_path / "managed"
    database = Database(config.storage.database_url)
    upgrade_database(database.url, backup_dir=tmp_path / "backups")
    item = _radar_item()
    review = OpportunityReviewService(SqlAlchemyOpportunityReviewRepository(database))
    review.record_decision(item, decision="CONFIRMED", reviewer="Team Bid")

    result = run_bid_radar_workspace_handoff(config, item)

    assert result.case_id == "IB2600463290"
    assert result.release_raw_id == item.identity.raw_id
    assert result.release_id is not None


def test_bid_radar_workspace_handoff_adapter_rejects_newer_persisted_rejection(
    tmp_path: Path,
) -> None:
    config = AppConfig()
    config.storage.database_url = f"sqlite:///{tmp_path / 'gui-handoff-reject.db'}"
    config.storage.document_dir = tmp_path / "managed"
    database = Database(config.storage.database_url)
    upgrade_database(database.url, backup_dir=tmp_path / "backups")
    item = _radar_item()
    review = OpportunityReviewService(SqlAlchemyOpportunityReviewRepository(database))
    review.record_decision(item, decision="CONFIRMED", reviewer="Team Bid")
    review.record_decision(item, decision="REJECTED", reviewer="Checker")

    with pytest.raises(ValueError, match="latest persisted CONFIRMED"):
        run_bid_radar_workspace_handoff(config, item)
