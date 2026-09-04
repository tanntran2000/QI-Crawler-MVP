from __future__ import annotations

import dataclasses
import importlib
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from qi_crawler.market_intelligence.khmt_contract import (
    KHMTImportBatch,
    PlanPackage,
    ProcurementPlan,
    ProvinceCityStatus,
)
from qi_crawler.market_intelligence.opportunity_contract import (
    OpportunityCandidate,
    OpportunityIdentity,
    OpportunityImportBatch,
    OpportunitySourceType,
)


def _radar_module():
    try:
        return importlib.import_module("qi_crawler.market_intelligence.opportunity_radar")
    except ModuleNotFoundError:
        pytest.fail("source-neutral opportunity radar projection is not implemented")


def _khmt_package(
    *,
    plan_id: str = "PL2600265077-00",
    plan_base_id: str | None = None,
    plan_revision: str | None = None,
    source_sha256: str = "a" * 64,
    sheet: str = "KHMT",
    source_row: int = 7,
) -> PlanPackage:
    batch = KHMTImportBatch(
        source_filename="KHMT_synthetic.xlsx",
        source_sha256=source_sha256,
        sheet=sheet,
        imported_at=datetime(2026, 8, 24, tzinfo=UTC),
        schema_version="mi-1",
    )
    identity = OpportunityIdentity.from_raw(plan_id)
    plan = ProcurementPlan(
        plan_id_raw=identity.raw_id,
        plan_base_id=identity.base_id if plan_base_id is None else plan_base_id,
        plan_revision=identity.revision if plan_revision is None else plan_revision,
        import_batch=batch,
    )
    return PlanPackage(
        plan=plan,
        source_row=source_row,
        package_name="Gói KHMT tổng hợp",
        investor="Nhà đầu tư KHMT",
        project="Dự án KHMT",
        package_price_raw="123.450.000",
        package_price=Decimal(123450000),
        total_investment_raw="200.000.000",
        approval_content_raw="Phê duyệt phạm vi KHMT",
        funding_source="Ngân sách KHMT",
        selection_method_raw="Chào hàng cạnh tranh",
        selection_method="CHAO_HANG_CANH_TRANH",
        selection_schedule_raw="Q4/2026",
        contract_type_raw="Trọn gói",
        execution_duration_raw="45 ngày",
        location_detail_raw="Địa điểm KHMT",
        province_city_code="HCM",
        province_city_name="TP.HCM",
        province_city_status=ProvinceCityStatus.CONFIRMED,
        province_city_evidence="TÊN CHỦ ĐẦU TƯ",
        raw_fields={"TÊN GÓI THẦU": "Gói KHMT tổng hợp", "RAW": "giữ nguyên"},
        provenance={
            "source_filename": "KHMT_synthetic.xlsx",
            "source_sha256": source_sha256,
            "sheet": sheet,
            "source_row": source_row,
        },
    )


def _tbmt_candidate(
    *,
    raw_id: str = "IB2600463290-00",
    source_sha256: str = "b" * 64,
    sheet: str = "TBMT",
    source_row: int = 11,
) -> OpportunityCandidate:
    batch = OpportunityImportBatch(
        source_filename="TBMT_synthetic.xlsx",
        source_sha256=source_sha256,
        sheet=sheet,
        imported_at=datetime(2026, 8, 24, tzinfo=UTC),
        schema_version="mi-tbmt-1",
        source_type=OpportunitySourceType.TBMT,
    )
    return OpportunityCandidate(
        identity=OpportunityIdentity.from_raw(raw_id),
        import_batch=batch,
        source_row=source_row,
        package_name="Gói TBMT tổng hợp IB2600463290-00",
        project="Dự án TBMT",
        package_price_raw="456.000.000",
        package_price=Decimal(456000000),
        funding_source="Nguồn vốn TBMT",
        location_detail_raw=None,
        raw_fields={
            "GÓI THẦU": "Gói TBMT tổng hợp IB2600463290-00",
            "BÊN MỜI THẦU": "Bên mời thầu TBMT",
            "ĐỊA CHỈ BÊN MỜI THẦU": "Địa chỉ không phải địa điểm thực hiện",
            "DỰ ÁN": "Dự án TBMT",
            "NỘI DUNG CHÍNH CỦA GÓI THẦU": "Nội dung chính TBMT",
            "HÌNH THỨC LỰA CHỌN NHÀ THẦU": "Đấu thầu rộng rãi",
            "PHƯƠNG THỨC LỰA CHỌN NHÀ THẦU": "Một giai đoạn một túi hồ sơ",
        },
        provenance={
            "source_filename": "TBMT_synthetic.xlsx",
            "source_sha256": source_sha256,
            "sheet": sheet,
            "source_row": source_row,
        },
    )


def test_plan_package_projects_to_radar_item_with_pl_identity_and_khmt_semantics() -> None:
    module = _radar_module()
    item = module.radar_item_from_plan_package(_khmt_package())

    assert item.source_type is OpportunitySourceType.KHMT
    assert item.identity.namespace.value == "PL"
    assert item.identity.raw_id == "PL2600265077-00"
    assert item.identity.base_id == "PL2600265077"
    assert item.identity.revision == "00"
    assert item.investor == "Nhà đầu tư KHMT"
    assert item.selection_method == "CHAO_HANG_CANH_TRANH"
    assert item.province_city_code == "HCM"


def test_plan_package_rejects_conflicting_base_identity() -> None:
    module = _radar_module()

    with pytest.raises(module.OpportunityRadarContractError):
        module.radar_item_from_plan_package(
            _khmt_package(plan_base_id="PL9999999999")
        )


def test_plan_package_rejects_conflicting_revision_identity() -> None:
    module = _radar_module()

    with pytest.raises(module.OpportunityRadarContractError):
        module.radar_item_from_plan_package(_khmt_package(plan_revision="99"))


def test_tbmt_candidate_projects_to_radar_item_with_ib_identity_and_semantics() -> None:
    module = _radar_module()
    item = module.radar_item_from_opportunity_candidate(_tbmt_candidate())

    assert item.source_type is OpportunitySourceType.TBMT
    assert item.identity.namespace.value == "IB"
    assert item.identity.raw_id == "IB2600463290-00"
    assert item.identity.base_id == "IB2600463290"
    assert item.identity.revision == "00"
    assert item.procuring_entity == "Bên mời thầu TBMT"
    assert item.package_main_content == "Nội dung chính TBMT"
    assert item.selection_method_raw == "Đấu thầu rộng rãi"
    assert item.selection_method == "DAU_THAU_RONG_RAI"


def test_pl_and_ib_remain_distinct() -> None:
    module = _radar_module()
    khmt = module.radar_item_from_plan_package(_khmt_package())
    tbmt = module.radar_item_from_opportunity_candidate(_tbmt_candidate())

    assert khmt.identity.namespace != tbmt.identity.namespace
    assert khmt.identity != tbmt.identity
    assert khmt.observation_key != tbmt.observation_key


def test_investor_and_procuring_entity_remain_distinct() -> None:
    module = _radar_module()
    khmt = module.radar_item_from_plan_package(_khmt_package())
    tbmt = module.radar_item_from_opportunity_candidate(_tbmt_candidate())

    assert khmt.investor == "Nhà đầu tư KHMT"
    assert khmt.procuring_entity is None
    assert tbmt.procuring_entity == "Bên mời thầu TBMT"
    assert tbmt.investor is None


def test_selection_method_and_procurement_method_remain_distinct() -> None:
    module = _radar_module()
    item = module.radar_item_from_opportunity_candidate(_tbmt_candidate())

    assert item.selection_method == "DAU_THAU_RONG_RAI"
    assert item.selection_method_raw == "Đấu thầu rộng rãi"
    assert item.procurement_method == "Một giai đoạn một túi hồ sơ"
    assert item.selection_method != item.procurement_method


def test_observation_key_is_deterministic_for_identical_observation() -> None:
    module = _radar_module()
    first = module.radar_item_from_plan_package(_khmt_package())
    second = module.radar_item_from_plan_package(_khmt_package())

    assert first.observation_key == second.observation_key


@pytest.mark.parametrize(
    "changes",
    [
        {"source_sha256": "c" * 64},
        {"sheet": "Other"},
        {"source_row": 8},
        {"plan_id": "PL2600265077-01"},
    ],
)
def test_observation_key_changes_for_any_observation_coordinate(
    changes: dict[str, object],
) -> None:
    module = _radar_module()
    first = module.radar_item_from_plan_package(_khmt_package())
    second = module.radar_item_from_plan_package(_khmt_package(**changes))

    assert first.observation_key != second.observation_key


def test_source_and_raw_fields_are_preserved() -> None:
    module = _radar_module()
    package = _khmt_package()
    item = module.radar_item_from_plan_package(package)

    assert item.raw_fields == package.raw_fields
    assert item.source_fields["approval_content"] == package.approval_content_raw
    assert item.source_fields["selection_method_raw"] == package.selection_method_raw
    assert item.provenance == package.provenance


@pytest.mark.parametrize("missing", ["source_sha256", "sheet", "source_row"])
def test_radar_item_requires_authoritative_provenance_coordinates(missing: str) -> None:
    module = _radar_module()
    item = module.radar_item_from_plan_package(_khmt_package())
    provenance = dict(item.provenance)
    provenance.pop(missing)

    with pytest.raises(module.OpportunityRadarContractError):
        dataclasses.replace(item, provenance=provenance)


@pytest.mark.parametrize(
    ("coordinate", "value"),
    [
        ("source_sha256", "c" * 64),
        ("sheet", "Other"),
        ("source_row", 999),
    ],
)
def test_radar_item_rejects_mismatched_provenance_coordinates(
    coordinate: str,
    value: object,
) -> None:
    module = _radar_module()
    item = module.radar_item_from_plan_package(_khmt_package())
    provenance = dict(item.provenance)
    provenance[coordinate] = value

    with pytest.raises(module.OpportunityRadarContractError):
        dataclasses.replace(item, provenance=provenance)


def test_radar_fields_are_immutable() -> None:
    module = _radar_module()
    item = module.radar_item_from_plan_package(_khmt_package())

    with pytest.raises(TypeError):
        item.raw_fields["new"] = "value"
    with pytest.raises(TypeError):
        item.source_fields["new"] = "value"
    with pytest.raises(TypeError):
        item.provenance["new"] = "value"
    with pytest.raises(dataclasses.FrozenInstanceError):
        item.package_name = "changed"


def test_tbmt_procuring_entity_address_does_not_become_execution_location() -> None:
    module = _radar_module()
    item = module.radar_item_from_opportunity_candidate(_tbmt_candidate())

    assert item.location_detail_raw is None
    assert item.province_city_code is None
    assert item.province_city_name is None
    assert item.source_fields["procuring_entity_address"] == (
        "Địa chỉ không phải địa điểm thực hiện"
    )


def test_radar_item_contains_no_human_review_authority_state() -> None:
    module = _radar_module()
    field_names = {field.name for field in dataclasses.fields(module.OpportunityRadarItem)}

    assert field_names.isdisjoint(
        {
            "decision",
            "reviewer",
            "review_state",
            "ground_truth",
            "go_hold_no_go",
            "warehouse_shelf",
            "gui_state",
        }
    )


def test_different_revisions_remain_distinct_radar_observations() -> None:
    module = _radar_module()
    first = module.radar_item_from_opportunity_candidate(_tbmt_candidate())
    second = module.radar_item_from_opportunity_candidate(
        _tbmt_candidate(raw_id="IB2600463290-01", source_row=12)
    )

    assert first.identity.base_id == second.identity.base_id
    assert first.identity.revision != second.identity.revision
    assert first.identity != second.identity
    assert first.observation_key != second.observation_key
