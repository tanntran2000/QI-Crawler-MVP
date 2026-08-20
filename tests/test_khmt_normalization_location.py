from __future__ import annotations

from decimal import Decimal

import pytest

from qi_crawler.market_intelligence.khmt_contract import ProvinceCityStatus
from qi_crawler.market_intelligence.khmt_normalization import (
    normalize_selection_method,
    parse_package_price,
    parse_plan_identity,
)
from qi_crawler.market_intelligence.location_resolver import resolve_province_city


@pytest.mark.parametrize(
    ("raw", "base", "revision"),
    [
        ("PL2600265077-00", "PL2600265077", "00"),
        ("PL2600245672-02", "PL2600245672", "02"),
        ("PL2600245672", "PL2600245672", None),
    ],
)
def test_plan_identity_preserves_raw_base_and_revision(
    raw: str, base: str, revision: str | None
) -> None:
    parsed = parse_plan_identity(raw)

    assert parsed.raw == raw
    assert parsed.base_id == base
    assert parsed.revision == revision
    assert not parsed.base_id.startswith("IB")


@pytest.mark.parametrize("raw", ["IB2600265077-00", "PL123-00", "not-a-plan", ""])
def test_malformed_plan_identity_does_not_fabricate_pl(raw: str) -> None:
    assert parse_plan_identity(raw) is None


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (477850000, Decimal(477850000)),
        ("477,850,000", Decimal(477850000)),
        ("477.850.000", Decimal(477850000)),
        ("477 850 000", Decimal(477850000)),
        (0, Decimal(0)),
        ("0", Decimal(0)),
        (None, None),
        ("", None),
        ("12,34", None),
        ("unknown", None),
    ],
)
def test_package_price_parsing_is_conservative(raw: object, expected: Decimal | None) -> None:
    assert parse_package_price(raw) == expected


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        (
            "Chỉ định thầu, Không qua mạng, Không sơ tuyển, Một giai đoạn một túi hồ sơ",
            "CHI_DINH_THAU",
        ),
        (
            "Chỉ định thầu rút gọn, Không qua mạng, Không sơ tuyển, Một giai đoạn một túi hồ sơ",
            "CHI_DINH_THAU_RUT_GON",
        ),
        (
            "Chào hàng cạnh tranh, Qua mạng, Không sơ tuyển, Một giai đoạn một túi hồ sơ",
            "CHAO_HANG_CANH_TRANH",
        ),
        (
            "Đấu thầu rộng rãi, Qua mạng, Không sơ tuyển, Một giai đoạn một túi hồ sơ",
            "DAU_THAU_RONG_RAI",
        ),
        ("Unknown future method", None),
        ("Unknown future method, Qua mạng", None),
        (None, None),
    ],
)
def test_selection_method_normalizes_only_bounded_values(
    raw: str | None, expected: str | None
) -> None:
    assert normalize_selection_method(raw) == expected


@pytest.mark.parametrize(
    "alias",
    ["Thành phố Hồ Chí Minh", "TP. Hồ Chí Minh", "TP.HCM", "TP HCM"],
)
def test_explicit_hcm_alias_is_confirmed_with_source_evidence(alias: str) -> None:
    resolution = resolve_province_city({"TÊN CHỦ ĐẦU TƯ": f"Synthetic unit, {alias}"})

    assert resolution.code == "HCM"
    assert resolution.name == "Thành phố Hồ Chí Minh"
    assert resolution.status is ProvinceCityStatus.CONFIRMED
    assert resolution.evidence == f"TÊN CHỦ ĐẦU TƯ: Synthetic unit, {alias}"


@pytest.mark.parametrize("subunit", ["xã Châu Đức", "xã Phú Giáo", "phường Thới An"])
def test_approved_hcm_subunit_is_inferred_with_versioned_source_evidence(
    subunit: str,
) -> None:
    raw = f"Synthetic project at {subunit}"

    resolution = resolve_province_city({"TÊN DỰ ÁN": raw})

    assert resolution.code == "HCM"
    assert resolution.name == "Thành phố Hồ Chí Minh"
    assert resolution.status is ProvinceCityStatus.INFERRED
    assert f"TÊN DỰ ÁN: {raw}" in resolution.evidence
    assert "mapping=" in resolution.evidence


@pytest.mark.parametrize("unknown", ["xã", "phường", "Tân Phú", "xã Chưa Xác Định"])
def test_generic_or_unknown_subunit_remains_needs_review(unknown: str) -> None:
    resolution = resolve_province_city({"TÊN DỰ ÁN": f"Synthetic project {unknown}"})

    assert resolution.code is None
    assert resolution.status is ProvinceCityStatus.NEEDS_REVIEW


def test_unknown_or_missing_geography_needs_review_without_guessing() -> None:
    unknown = resolve_province_city({"TÊN DỰ ÁN": "Synthetic project at Unknown Locality"})
    missing = resolve_province_city({"TÊN DỰ ÁN": None})

    assert unknown.status is ProvinceCityStatus.NEEDS_REVIEW
    assert unknown.code is None
    assert missing.status is ProvinceCityStatus.NEEDS_REVIEW
    assert missing.code is None


def test_conflicting_explicit_cities_need_review_and_retain_evidence() -> None:
    resolution = resolve_province_city(
        {
            "TÊN CHỦ ĐẦU TƯ": "Synthetic unit TP.HCM",
            "NỘI DUNG PHÊ DUYỆT": "Synthetic activity at Hà Nội",
        }
    )

    assert resolution.status is ProvinceCityStatus.NEEDS_REVIEW
    assert resolution.code is None
    assert "TÊN CHỦ ĐẦU TƯ" in resolution.evidence
    assert "NỘI DUNG PHÊ DUYỆT" in resolution.evidence
