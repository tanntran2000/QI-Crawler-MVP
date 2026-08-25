from __future__ import annotations

import ast
import importlib.util
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

from qi_crawler.db import Database
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
from qi_crawler.market_intelligence.opportunity_review import (
    OpportunityReviewDecision,
    OpportunityReviewRecord,
    OpportunityReviewService,
    opportunity_review_identity,
)
from qi_crawler.migrations import upgrade_database
from qi_crawler.opportunity_review_persistence import SqlAlchemyOpportunityReviewRepository


class MemoryOpportunityReviewRepository:
    def __init__(self) -> None:
        self.records: list[OpportunityReviewRecord] = []

    def latest(self, observation_key: str) -> OpportunityReviewRecord | None:
        matches = [record for record in self.records if record.identity.observation_key == observation_key]
        return max(matches, key=lambda record: record.event_id, default=None)

    def history(self, observation_key: str) -> tuple[OpportunityReviewRecord, ...]:
        return tuple(
            record
            for record in self.records
            if record.identity.observation_key == observation_key
        )

    def append(self, write) -> OpportunityReviewRecord:
        record = OpportunityReviewRecord(
            event_id=len(self.records) + 1,
            identity=write.identity,
            decision=write.decision,
            reviewer=write.reviewer,
            note=write.note,
            opportunity_snapshot_json=write.opportunity_snapshot_json,
            snapshot_schema_version=write.snapshot_schema_version,
            created_at=datetime(2026, 1, 1, tzinfo=UTC),
        )
        self.records.append(record)
        return record

    def latest_for_keys(
        self, observation_keys: tuple[str, ...]
    ) -> dict[str, OpportunityReviewRecord]:
        return {
            key: record
            for key in observation_keys
            if (record := self.latest(key)) is not None
        }


def _item(
    *,
    revision: str = "00",
    source_sha256: str = "a" * 64,
    source_row: int = 7,
    source_filename: str = "TBMT-demo.xlsx",
) -> OpportunityRadarItem:
    identity = OpportunityIdentity(
        raw_id=f"IB2600463290-{revision}",
        base_id="IB2600463290",
        revision=revision,
        namespace=OpportunityIdentityNamespace.IB,
    )
    batch = OpportunityImportBatch(
        source_filename=source_filename,
        source_sha256=source_sha256,
        sheet="TBMT",
        imported_at=datetime(2026, 1, 1, tzinfo=UTC),
        schema_version="tbmt-v1",
        source_type=OpportunitySourceType.TBMT,
    )
    provenance = {
        "source_filename": source_filename,
        "source_sha256": source_sha256,
        "sheet": batch.sheet,
        "source_row": source_row,
        "source_locator": f"{batch.sheet}!A{source_row}",
    }
    return OpportunityRadarItem(
        source_type=OpportunitySourceType.TBMT,
        identity=identity,
        observation_key=build_observation_key(
            source_type=OpportunitySourceType.TBMT,
            identity=identity,
            source_sha256=source_sha256,
            sheet=batch.sheet,
            source_row=source_row,
        ),
        source_filename=source_filename,
        source_sha256=source_sha256,
        sheet=batch.sheet,
        source_row=source_row,
        schema_version=batch.schema_version,
        package_name="Gói TBMT thử nghiệm",
        project="Dự án nguồn",
        package_price_raw="1.234,50",
        package_price=Decimal("1234.50"),
        funding_source="Ngân sách",
        source_fields={"selection_method": "Đấu thầu rộng rãi"},
        raw_fields={"Tên gói": "Gói TBMT thử nghiệm"},
        provenance=provenance,
    )


def _service() -> tuple[MemoryOpportunityReviewRepository, OpportunityReviewService]:
    repository = MemoryOpportunityReviewRepository()
    return repository, OpportunityReviewService(repository)


def _sqlalchemy_service(
    tmp_path: Path,
) -> tuple[Database, OpportunityReviewService]:
    database = Database(f"sqlite:///{tmp_path / 'opportunity-review.db'}")
    upgrade_database(database.url, backup_dir=tmp_path / "backups")
    repository = SqlAlchemyOpportunityReviewRepository(database)
    return database, OpportunityReviewService(repository)


def _imported_modules(source: str) -> tuple[str, ...]:
    tree = ast.parse(source)
    imported: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            prefix = "." * node.level
            module = prefix + (node.module or "")
            if node.level:
                module = importlib.util.resolve_name(
                    module,
                    "qi_crawler.market_intelligence",
                )
            imported.append(module)
    return tuple(imported)


def test_backend_module_has_no_persistence_or_delivery_imports() -> None:
    import qi_crawler.market_intelligence.opportunity_review as backend

    tree = ast.parse(Path(backend.__file__).read_text(encoding="utf-8"))
    forbidden = (
        "sqlalchemy",
        "qi_crawler.db",
        "qi_crawler.models",
        "PySide",
        "PyQt",
        "qi_crawler.cli",
    )
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    assert not any(
        module == blocked or module.startswith(blocked + ".")
        for module in imported
        for blocked in forbidden
    )


def test_domain_contract_is_separate_from_application_backend() -> None:
    import qi_crawler.market_intelligence.opportunity_review as backend

    contract_path = Path(backend.__file__).with_name("opportunity_review_contract.py")
    assert contract_path.exists()
    tree = ast.parse(contract_path.read_text(encoding="utf-8"))
    defined = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert {
        "OpportunityReviewError",
        "OpportunityReviewDecision",
        "OpportunityReviewIdentity",
        "OpportunityReviewRecord",
        "OpportunityReviewWrite",
    }.issubset(defined)


def test_domain_contract_has_no_persistence_or_delivery_imports() -> None:
    import qi_crawler.market_intelligence.opportunity_review as backend

    contract_path = Path(backend.__file__).with_name("opportunity_review_contract.py")
    assert contract_path.exists()
    tree = ast.parse(contract_path.read_text(encoding="utf-8"))
    forbidden = (
        "sqlalchemy",
        "qi_crawler.db",
        "qi_crawler.models",
        "qi_crawler.opportunity_review_persistence",
        "PySide",
        "PyQt",
        "qi_crawler.cli",
    )
    imported = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported.append(node.module)
    assert not any(
        module == blocked or module.startswith(blocked + ".")
        for module in imported
        for blocked in forbidden
    )


def test_domain_contract_has_no_application_projection_imports() -> None:
    import qi_crawler.market_intelligence.opportunity_review as backend

    contract_path = Path(backend.__file__).with_name("opportunity_review_contract.py")
    imported = _imported_modules(contract_path.read_text(encoding="utf-8"))
    assert "qi_crawler.market_intelligence.opportunity_radar" not in imported


def test_import_inspection_normalizes_relative_and_absolute_projection_imports() -> None:
    relative = _imported_modules(
        "from .opportunity_radar import OpportunityRadarItem"
    )
    absolute = _imported_modules(
        "from qi_crawler.market_intelligence.opportunity_radar "
        "import OpportunityRadarItem"
    )

    expected = ("qi_crawler.market_intelligence.opportunity_radar",)
    assert relative == absolute == expected


def test_application_backend_does_not_define_domain_value_types() -> None:
    import qi_crawler.market_intelligence.opportunity_review as backend

    tree = ast.parse(Path(backend.__file__).read_text(encoding="utf-8"))
    defined = {
        node.name
        for node in ast.walk(tree)
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
    }
    assert not defined.intersection(
        {
            "OpportunityReviewError",
            "OpportunityReviewDecision",
            "OpportunityReviewIdentity",
            "OpportunityReviewRecord",
            "OpportunityReviewWrite",
        }
    )


def test_tbmt_review_preserves_ib_namespace_and_exact_revision() -> None:
    _, service = _service()
    record = service.record_decision(_item(), decision="CONFIRMED", reviewer="Team Bid")

    assert record.identity.source_type is OpportunitySourceType.TBMT
    assert record.identity.identity_namespace is OpportunityIdentityNamespace.IB
    assert record.identity.identity_raw == "IB2600463290-00"
    assert record.identity.identity_revision == "00"


def test_revision_00_confirmation_does_not_confirm_revision_01() -> None:
    _, service = _service()
    revision_00 = _item(revision="00")
    revision_01 = _item(revision="01")
    service.record_decision(revision_00, decision="CONFIRMED", reviewer="Team Bid")

    assert service.current_confirmed((revision_00, revision_01)) == (
        service.current_event(revision_00),
    )


def test_changed_source_sha_is_unreviewed() -> None:
    _, service = _service()
    original = _item()
    changed = _item(source_sha256="b" * 64)
    service.record_decision(original, decision="CONFIRMED", reviewer="Team Bid")

    assert service.current_event(changed) is None


def test_changed_source_row_is_unreviewed() -> None:
    _, service = _service()
    original = _item(source_row=7)
    changed = _item(source_row=8)
    service.record_decision(original, decision="CONFIRMED", reviewer="Team Bid")

    assert service.current_event(changed) is None


def test_same_observation_different_filename_reattaches_review() -> None:
    _, service = _service()
    original = _item(source_filename="first.xlsx")
    renamed = _item(source_filename="renamed-copy.xlsx")
    first = service.record_decision(original, decision="CONFIRMED", reviewer="Team Bid")

    assert service.current_event(renamed) == first


def test_exact_duplicate_decision_reviewer_note_is_idempotent() -> None:
    repository, service = _service()
    item = _item()
    first = service.record_decision(
        item, decision=" confirmed ", reviewer=" Team Bid ", note=" Đã xem "
    )
    duplicate = service.record_decision(
        item, decision=OpportunityReviewDecision.CONFIRMED, reviewer="Team Bid", note="Đã xem"
    )

    assert duplicate.event_id == first.event_id
    assert len(repository.history(item.observation_key)) == 1


def test_changed_note_appends_new_review_event() -> None:
    repository, service = _service()
    item = _item()
    first = service.record_decision(item, decision="CONFIRMED", reviewer="Team Bid", note="Một")
    changed = service.record_decision(item, decision="CONFIRMED", reviewer="Team Bid", note="Hai")

    assert changed.event_id != first.event_id
    assert len(repository.history(item.observation_key)) == 2


def test_changed_reviewer_appends_new_review_event() -> None:
    repository, service = _service()
    item = _item()
    first = service.record_decision(item, decision="CONFIRMED", reviewer="Maker")
    changed = service.record_decision(item, decision="CONFIRMED", reviewer="Checker")

    assert changed.event_id != first.event_id
    assert len(repository.history(item.observation_key)) == 2


def test_latest_event_is_current_authority() -> None:
    _, service = _service()
    item = _item()
    service.record_decision(item, decision="CONFIRMED", reviewer="Team Bid")
    latest = service.record_decision(item, decision="REJECTED", reviewer="Team Bid")

    assert service.current_event(item) == latest
    assert latest.decision is OpportunityReviewDecision.REJECTED


def test_current_confirmed_uses_latest_decision_only() -> None:
    _, service = _service()
    confirmed_then_rejected = _item(source_row=7)
    rejected_then_confirmed = _item(source_row=8)
    service.record_decision(confirmed_then_rejected, decision="CONFIRMED", reviewer="Team Bid")
    service.record_decision(confirmed_then_rejected, decision="REJECTED", reviewer="Team Bid")
    service.record_decision(rejected_then_confirmed, decision="REJECTED", reviewer="Team Bid")
    service.record_decision(rejected_then_confirmed, decision="CONFIRMED", reviewer="Team Bid")

    current = service.current_confirmed(
        (confirmed_then_rejected, rejected_then_confirmed, rejected_then_confirmed)
    )

    assert [record.identity.source_row for record in current] == [8]


def test_snapshot_is_deterministic_versioned_and_unicode_safe() -> None:
    _, service = _service()
    item = _item()
    first = service.record_decision(item, decision="NEEDS_REVIEW", reviewer="Người kiểm tra")
    second = service.record_decision(item, decision="NEEDS_REVIEW", reviewer="Người kiểm tra")

    assert first.opportunity_snapshot_json == second.opportunity_snapshot_json
    assert first.snapshot_schema_version == "mi-opportunity-review-v1"
    assert "Gói TBMT thử nghiệm" in first.opportunity_snapshot_json


def test_sqlalchemy_repository_persists_review_across_restart(tmp_path: Path) -> None:
    database, service = _sqlalchemy_service(tmp_path)
    item = _item()
    first = service.record_decision(item, decision="CONFIRMED", reviewer="Team Bid")

    reopened = OpportunityReviewService(
        SqlAlchemyOpportunityReviewRepository(Database(database.url))
    )

    assert reopened.current_event(item).event_id == first.event_id
    assert len(reopened.list_history(item)) == 1


def test_sqlalchemy_repository_round_trips_source_neutral_identity(tmp_path: Path) -> None:
    _, service = _sqlalchemy_service(tmp_path)
    item = _item(revision="01", source_row=11)
    record = service.record_decision(item, decision="NEEDS_REVIEW", reviewer="Team Bid")

    assert record.identity == opportunity_review_identity(item)


def test_sqlalchemy_repository_history_is_append_only(tmp_path: Path) -> None:
    _, service = _sqlalchemy_service(tmp_path)
    item = _item()
    service.record_decision(item, decision="CONFIRMED", reviewer="Team Bid")
    service.record_decision(item, decision="REJECTED", reviewer="Team Bid")

    assert [record.decision for record in service.list_history(item)] == [
        OpportunityReviewDecision.CONFIRMED,
        OpportunityReviewDecision.REJECTED,
    ]


def test_sqlalchemy_repository_bulk_latest_uses_latest_id(tmp_path: Path) -> None:
    _, service = _sqlalchemy_service(tmp_path)
    first = _item(source_row=7)
    second = _item(source_row=8)
    service.record_decision(first, decision="CONFIRMED", reviewer="Team Bid")
    service.record_decision(first, decision="REJECTED", reviewer="Team Bid")
    service.record_decision(second, decision="CONFIRMED", reviewer="Team Bid")

    current = service.current_confirmed((first, second))

    assert [record.identity.source_row for record in current] == [8]
