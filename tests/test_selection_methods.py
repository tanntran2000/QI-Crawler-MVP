from __future__ import annotations

import importlib

import pytest


def _selection_module():
    try:
        return importlib.import_module("qi_crawler.market_intelligence.selection_methods")
    except ModuleNotFoundError:
        pytest.fail("shared selection-method contract is not implemented")


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        ("Chỉ định thầu", "CHI_DINH_THAU"),
        ("Chỉ định thầu rút gọn", "CHI_DINH_THAU_RUT_GON"),
        ("Chào hàng cạnh tranh", "CHAO_HANG_CANH_TRANH"),
        ("Đấu thầu rộng rãi", "DAU_THAU_RONG_RAI"),
        (
            "Chào giá trực tuyến theo quy trình rút gọn",
            "CHAO_GIA_TRUC_TUYEN_THEO_QUY_TRINH_RUT_GON",
        ),
        ("Chào giá trực tuyến", "CHAO_GIA_TRUC_TUYEN"),
        ("Đấu thầu hạn chế", "DAU_THAU_HAN_CHE"),
        ("Khác", "KHAC"),
        ("Tự thực hiện", "TU_THUC_HIEN"),
        ("Mua sắm trực tiếp", "MUA_SAM_TRUC_TIEP"),
    ],
)
def test_selection_method_contract_maps_supported_source_labels(
    label: str, expected: str
) -> None:
    module = _selection_module()

    assert module.normalize_selection_method(label) == expected


def test_selection_method_contract_is_conservative_for_unknown_source_labels() -> None:
    module = _selection_module()

    assert module.normalize_selection_method("Phương thức chưa được xác định") is None


def test_selection_method_filter_accepts_labels_and_canonical_codes() -> None:
    module = _selection_module()

    assert module.normalize_selection_method_filters(
        ("Đấu thầu rộng rãi", "CHAO_GIA_TRUC_TUYEN")
    ) == frozenset({"DAU_THAU_RONG_RAI", "CHAO_GIA_TRUC_TUYEN"})


def test_selection_method_filter_rejects_unknown_nonblank_input() -> None:
    module = _selection_module()

    with pytest.raises(ValueError, match="selection method"):
        module.normalize_selection_method_filters(("Phương thức tự do",))
