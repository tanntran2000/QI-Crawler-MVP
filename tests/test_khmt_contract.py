from __future__ import annotations

from pathlib import Path

from qi_crawler.market_intelligence.khmt_contract import (
    OBSERVED_KHMT_HEADERS,
    ProvinceCityStatus,
    load_sanitized_khmt_fixture,
)

FIXTURE = Path(__file__).parent / "fixtures" / "khmt" / "khmt_sanitized_golden.json"


def _load():
    return load_sanitized_khmt_fixture(FIXTURE)


def test_plan_base_and_revision_are_distinct_identities() -> None:
    _, packages = _load()

    identities = {(item.plan.plan_base_id, item.plan.plan_revision) for item in packages}

    assert ("PL-SYN-2026-001", "00") in identities
    assert ("PL-SYN-2026-001", "01") in identities
    assert len(identities) == 3


def test_raw_plan_suffix_is_preserved_separately_from_normalized_identity() -> None:
    _, packages = _load()
    original = packages[0].plan
    amended = packages[2].plan

    assert original.plan_id_raw == "PL-SYN-2026-001-00"
    assert original.plan_base_id == amended.plan_base_id == "PL-SYN-2026-001"
    assert original.plan_revision == "00"
    assert amended.plan_revision == "01"


def test_one_plan_can_have_multiple_plan_package_rows() -> None:
    _, packages = _load()

    rows = [item.source_row for item in packages if item.plan.plan_base_id == "PL-SYN-2026-001"
            and item.plan.plan_revision == "00"]

    assert rows == [8, 9]


def test_pl_never_derives_an_ib_notice_relation() -> None:
    _, packages = _load()

    assert all(item.source_notice_id is None for item in packages)
    assert all(not item.plan.plan_base_id.startswith("IB") for item in packages)


def test_raw_and_normalized_values_coexist_with_provenance() -> None:
    _, packages = _load()
    package = packages[0]

    assert package.package_price_raw == "125.000.000 VND"
    assert str(package.package_price) == "125000000"
    assert package.selection_method_raw == "Chao hang canh tranh"
    assert package.selection_method == "CHAO_HANG_CANH_TRANH"
    assert package.total_investment_raw == "500.000.000 VND"
    assert package.approval_content_raw.endswith("Tinh Mau A.")
    assert package.contract_type_raw == "Tron goi"
    assert package.execution_duration_raw == "45 ngay"
    assert package.raw_fields["GIÁ GÓI THẦU"] == package.package_price_raw
    assert package.provenance == {"sheet": "Ke hoach mua sam", "source_row": 8}


def test_all_observed_source_headers_are_retained_without_column_loss() -> None:
    _, packages = _load()

    for package in packages:
        assert tuple(package.raw_fields) == OBSERVED_KHMT_HEADERS


def test_location_evidence_uses_existing_source_text_not_a_dedicated_column() -> None:
    _, packages = _load()
    explicit_place = packages[0]
    unresolved = packages[-1]

    assert explicit_place.location_detail_raw is None
    assert explicit_place.province_city_status is ProvinceCityStatus.NEEDS_REVIEW
    assert explicit_place.province_city_evidence.startswith("NỘI DUNG PHÊ DUYỆT:")
    assert unresolved.province_city_status is ProvinceCityStatus.NEEDS_REVIEW


def test_unresolved_province_city_is_needs_review_not_guessed() -> None:
    _, packages = _load()
    unresolved = packages[-1]

    assert unresolved.province_city_status is ProvinceCityStatus.NEEDS_REVIEW
    assert unresolved.province_city_code is None
    assert unresolved.province_city_name is None
    assert unresolved.province_city_evidence == "No explicit province/city in source row"


def test_sanitized_fixture_loads_deterministically() -> None:
    first_batch, first_packages = _load()
    second_batch, second_packages = _load()

    assert first_batch == second_batch
    assert first_packages == second_packages
    assert first_batch.source_filename == "KHMT_sanitized_golden.xlsx"
    assert first_batch.schema_version == "mi-0"
