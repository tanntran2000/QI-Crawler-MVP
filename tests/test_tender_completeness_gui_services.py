from __future__ import annotations

from pathlib import Path

from qi_crawler.config import AppConfig
from qi_crawler.db import Database
from qi_crawler.gui_services import (
    run_tender_completeness_retrieve,
    run_tender_completeness_view,
    run_tender_core_confirmation,
    run_tender_publication_expectation,
    run_tender_publication_item,
    run_tender_publication_reconcile,
)
from qi_crawler.tender_case import AuthorityClass
from qi_crawler.tender_case_service import TenderCaseService
from qi_crawler.tender_completeness import (
    CoreCoverageState,
    CoreRole,
    PublicationExpectationBasis,
    PublicationPackageState,
)


def test_completeness_gui_adapters_expose_domain_projection_and_exact_retrieval(
    tmp_path: Path,
) -> None:
    config = AppConfig()
    config.storage.database_url = f"sqlite:///{tmp_path / 'completeness-gui.db'}"
    config.storage.document_dir = tmp_path / "managed"
    database = Database(config.storage.database_url)
    documents = TenderCaseService(database, config.storage.document_dir)
    documents.create_case("case-gui-completeness")
    release = documents.add_release("case-gui-completeness", "IB2600502358-00")
    source = tmp_path / "chapter-v.pdf"
    source.write_bytes(b"technical source")
    membership = documents.add_document(
        "case-gui-completeness",
        release.release_id,
        source,
        authority=AuthorityClass.SOURCE_E_HSMT,
        evidence="Team Bid source",
    )

    initial = run_tender_completeness_view(config, release.release_id)
    assert initial.core_readiness.full_research_ready is False
    assert initial.publication_summary.state is PublicationPackageState.UNKNOWN
    assert initial.role_labels[1] == ("TECHNICAL_REQUIREMENTS", "Yêu cầu kỹ thuật và giải pháp", "UNKNOWN")

    run_tender_core_confirmation(
        config,
        release.release_id,
        membership.id,
        CoreRole.TECHNICAL_REQUIREMENTS,
        CoreCoverageState.CONFIRMED,
        "pages:1-2",
        "Human checked technical requirements",
        "bid-reviewer",
    )
    expectation_id = run_tender_publication_expectation(
        config,
        release.release_id,
        PublicationExpectationBasis.COMPLETE_LIST,
        "official-manifest",
        "Human checked publication list",
        "bid-reviewer",
    )
    run_tender_publication_item(config, expectation_id, "chapter-v", "Chapter V")
    summary = run_tender_publication_reconcile(
        config,
        release.release_id,
        expectation_id,
        {"chapter-v": membership.id},
    )
    assert summary.state is PublicationPackageState.COMPLETE

    destination = tmp_path / "retrieved.pdf"
    run_tender_completeness_retrieve(
        config,
        "case-gui-completeness",
        release.release_id,
        membership.id,
        destination,
    )
    assert destination.read_bytes() == b"technical source"
