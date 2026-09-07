from __future__ import annotations

from dataclasses import replace
from decimal import Decimal

import pytest

from qi_crawler.market_intelligence import filter_engine, search
from qi_crawler.market_intelligence.khmt_contract import ProvinceCityStatus
from qi_crawler.market_intelligence.opportunity_contract import (
    OpportunityIdentity,
    OpportunitySourceType,
)
from qi_crawler.market_intelligence.opportunity_radar import (
    OpportunityRadarItem,
    build_observation_key,
)


def _item(
    *,
    source_type: OpportunitySourceType = OpportunitySourceType.KHMT,
    raw_id: str = "PL2600265077-00",
    source_row: int = 7,
    price: Decimal | str | None = Decimal(400000000),
    province_code: str | None = "HCM",
    province_status: ProvinceCityStatus | None = ProvinceCityStatus.CONFIRMED,
    selection_method: str | None = "CHAO_HANG_CANH_TRANH",
    procurement_method: str | None = "MOT_GIAI_DOAN",
    package_name: str = "Mua sắm máy chủ",
    project: str | None = "Dự án mạng",
    investor: str | None = "Nhà đầu tư hạ tầng",
    approval_content: str | None = "Phê duyệt thiết bị mạng",
    procuring_entity: str | None = "Bên mời thầu hạ tầng",
    package_main_content: str | None = "Cung cấp firewall và switch",
) -> OpportunityRadarItem:
    if source_type is OpportunitySourceType.TBMT and raw_id.startswith("PL"):
        raw_id = raw_id.replace("PL", "IB", 1)
    identity = OpportunityIdentity.from_raw(raw_id)
    sha256 = "a" * 64 if source_type is OpportunitySourceType.KHMT else "b" * 64
    sheet = source_type.value
    source_fields = {
        "investor": investor,
        "approval_content": approval_content,
        "procuring_entity": procuring_entity,
        "package_main_content": package_main_content,
        "procuring_entity_address": "TP.HCM",
    }
    return OpportunityRadarItem(
        source_type=source_type,
        identity=identity,
        observation_key=build_observation_key(
            source_type=source_type,
            identity=identity,
            source_sha256=sha256,
            sheet=sheet,
            source_row=source_row,
        ),
        source_filename=f"{source_type.value}_synthetic.xlsx",
        source_sha256=sha256,
        sheet=sheet,
        source_row=source_row,
        schema_version="02b-2-test",
        package_name=package_name,
        project=project,
        package_price_raw=str(price) if price is not None else None,
        package_price=price,
        funding_source="Ngân sách tổng hợp",
        investor=investor if source_type is OpportunitySourceType.KHMT else None,
        procuring_entity=(
            procuring_entity if source_type is OpportunitySourceType.TBMT else None
        ),
        approval_content=(
            approval_content if source_type is OpportunitySourceType.KHMT else None
        ),
        package_main_content=(
            package_main_content if source_type is OpportunitySourceType.TBMT else None
        ),
        selection_method=selection_method,
        procurement_method=procurement_method,
        location_detail_raw=None,
        province_city_code=province_code,
        province_city_name="TP.HCM" if province_code else None,
        province_city_status=province_status,
        province_city_evidence="synthetic source field",
        source_fields=source_fields,
        raw_fields={"synthetic": True},
        provenance={
            "source_filename": f"{source_type.value}_synthetic.xlsx",
            "source_sha256": sha256,
            "sheet": sheet,
            "source_row": source_row,
        },
    )


def _profile(**kwargs):
    return filter_engine.FilterProfile(**kwargs)


def test_khmt_radar_item_matches_all_active_criteria() -> None:
    evaluation = filter_engine.evaluate_opportunity(
        _item(),
        _profile(
            min_budget=Decimal(300000000),
            max_budget=Decimal(500000000),
            province_city_codes=frozenset({"HCM"}),
            include_keywords=("nhà đầu tư",),
            selection_methods=frozenset({"CHAO_HANG_CANH_TRANH"}),
        ),
    )

    assert evaluation.disposition is filter_engine.OpportunityFilterDisposition.MATCH
    assert all(
        criterion.outcome is filter_engine.CriterionOutcome.PASS
        for criterion in evaluation.criteria
    )


def test_tbmt_radar_item_uses_the_same_generic_filter_api() -> None:
    evaluation = filter_engine.evaluate_opportunity(
        _item(
            source_type=OpportunitySourceType.TBMT,
            raw_id="IB2600463290-00",
        ),
        _profile(include_keywords=("firewall",)),
    )

    assert evaluation.disposition is filter_engine.OpportunityFilterDisposition.MATCH
    assert evaluation.identity.namespace.value == "IB"


def test_missing_budget_is_indeterminate_not_zero() -> None:
    evaluation = filter_engine.evaluate_opportunity(
        _item(price=None),
        _profile(max_budget=Decimal(500000000)),
    )

    assert evaluation.disposition is filter_engine.OpportunityFilterDisposition.INDETERMINATE
    assert evaluation.criteria[0].reason_code == filter_engine.FilterReasonCode.BUDGET_UNKNOWN


def test_unparseable_budget_is_indeterminate_not_zero() -> None:
    evaluation = filter_engine.evaluate_opportunity(
        _item(price="not-a-price"),
        _profile(max_budget=Decimal(500000000)),
    )

    assert evaluation.disposition is filter_engine.OpportunityFilterDisposition.INDETERMINATE
    assert evaluation.criteria[0].reason_code == filter_engine.FilterReasonCode.BUDGET_UNKNOWN


def test_budget_outside_range_is_no_match() -> None:
    evaluation = filter_engine.evaluate_opportunity(
        _item(price=Decimal(600000000)),
        _profile(max_budget=Decimal(500000000)),
    )

    assert evaluation.disposition is filter_engine.OpportunityFilterDisposition.NO_MATCH
    assert evaluation.criteria[0].reason_code == filter_engine.FilterReasonCode.BUDGET_ABOVE_MAX


def test_budget_fail_dominates_unknown_province() -> None:
    evaluation = filter_engine.evaluate_opportunity(
        _item(price=Decimal(600000000), province_code=None, province_status=ProvinceCityStatus.NEEDS_REVIEW),
        _profile(max_budget=Decimal(500000000), province_city_codes=frozenset({"HCM"})),
    )

    assert evaluation.disposition is filter_engine.OpportunityFilterDisposition.NO_MATCH


@pytest.mark.parametrize(
    ("province_code", "province_status", "disposition"),
    [
        ("HCM", ProvinceCityStatus.CONFIRMED, "MATCH"),
        ("HN", ProvinceCityStatus.CONFIRMED, "NO_MATCH"),
        (None, ProvinceCityStatus.NEEDS_REVIEW, "INDETERMINATE"),
    ],
)
def test_province_criterion_is_tri_state(
    province_code: str | None,
    province_status: ProvinceCityStatus,
    disposition: str,
) -> None:
    evaluation = filter_engine.evaluate_opportunity(
        _item(province_code=province_code, province_status=province_status),
        _profile(province_city_codes=frozenset({"HCM"})),
    )

    assert evaluation.criteria[0].outcome.value == (
        "PASS" if disposition == "MATCH" else "FAIL" if disposition == "NO_MATCH" else "UNKNOWN"
    )
    assert evaluation.disposition.value == disposition


def test_tbmt_procuring_address_does_not_create_province_match() -> None:
    evaluation = filter_engine.evaluate_opportunity(
        _item(
            source_type=OpportunitySourceType.TBMT,
            raw_id="IB2600463290-00",
            province_code=None,
            province_status=None,
        ),
        _profile(province_city_codes=frozenset({"HCM"})),
    )

    assert evaluation.disposition is filter_engine.OpportunityFilterDisposition.INDETERMINATE


def _tbmt_location_item(
    location_detail_raw: str | None,
    *,
    source_fields: dict[str, object] | None = None,
    raw_fields: dict[str, object] | None = None,
) -> OpportunityRadarItem:
    item = _item(
        source_type=OpportunitySourceType.TBMT,
        raw_id="IB2600463290-00",
        province_code="LEGACY",
        province_status=ProvinceCityStatus.CONFIRMED,
    )
    return replace(
        item,
        location_detail_raw=location_detail_raw,
        source_fields=source_fields or {},
        raw_fields=raw_fields or {},
    )


@pytest.mark.parametrize(
    ("execution_location", "selected", "expected"),
    [
        ("Hồ Chí Minh", "Hồ Chí Minh", "PASS"),
        ("Hồ Chí Minh", "Đồng Nai", "FAIL"),
        ("Hồ Chí Minh, Đồng Nai", "Hồ Chí Minh", "PASS"),
        ("Hồ Chí Minh, Đồng Nai", "Đồng Nai", "PASS"),
        (None, "Hồ Chí Minh", "UNKNOWN"),
    ],
)
def test_tbmt_execution_location_filter_is_source_authoritative(
    execution_location: str | None,
    selected: str,
    expected: str,
) -> None:
    evaluation = filter_engine.evaluate_opportunity(
        _tbmt_location_item(execution_location),
        _profile(execution_locations=frozenset({selected})),
    )

    assert evaluation.criteria[0].criterion == "execution_location"
    assert evaluation.criteria[0].outcome.value == expected
    assert evaluation.disposition.value == (
        "MATCH" if expected == "PASS" else "NO_MATCH" if expected == "FAIL" else "INDETERMINATE"
    )


def test_tbmt_location_filter_ignores_procuring_and_issue_addresses() -> None:
    item = _tbmt_location_item(
        "Đồng Nai",
        source_fields={
            "procuring_entity_address": "Hồ Chí Minh",
            "investorLocation": "Hồ Chí Minh",
        },
        raw_fields={
            "ĐỊA CHỈ BÊN MỜI THẦU": "Hồ Chí Minh",
            "ĐỊA ĐIỂM PHÁT HÀNH": "Hồ Chí Minh",
        },
    )

    evaluation = filter_engine.evaluate_opportunity(
        item,
        _profile(execution_locations=frozenset({"Hồ Chí Minh"})),
    )

    assert evaluation.criteria[0].outcome is filter_engine.CriterionOutcome.FAIL
    assert evaluation.disposition is filter_engine.OpportunityFilterDisposition.NO_MATCH


def test_tbmt_explicit_workbook_location_outranks_detail_fallback() -> None:
    item = _tbmt_location_item(
        "Đồng Nai",
        source_fields={"provinces": [{"name": "Đồng Nai"}]},
        raw_fields={"ĐỊA ĐIỂM THỰC HIỆN GÓI THẦU": "Hồ Chí Minh"},
    )

    evaluation = filter_engine.evaluate_opportunity(
        item,
        _profile(execution_locations=frozenset({"Hồ Chí Minh"})),
    )

    assert evaluation.criteria[0].outcome is filter_engine.CriterionOutcome.PASS
    assert evaluation.criteria[0].evidence[0].observed_value == "Hồ Chí Minh"


def test_tbmt_legacy_province_filter_does_not_authorize_matching() -> None:
    evaluation = filter_engine.evaluate_opportunity(
        _tbmt_location_item("Đồng Nai"),
        _profile(province_city_codes=frozenset({"LEGACY"})),
    )

    assert evaluation.criteria[0].criterion == "execution_location"
    assert evaluation.criteria[0].outcome is filter_engine.CriterionOutcome.UNKNOWN
    assert evaluation.disposition is filter_engine.OpportunityFilterDisposition.INDETERMINATE


def test_selection_method_allowed_is_pass() -> None:
    evaluation = filter_engine.evaluate_opportunity(
        _item(selection_method="CHAO_HANG_CANH_TRANH"),
        _profile(selection_methods=frozenset({"CHAO_HANG_CANH_TRANH"})),
    )

    assert evaluation.disposition is filter_engine.OpportunityFilterDisposition.MATCH


def test_selection_method_disallowed_is_no_match() -> None:
    evaluation = filter_engine.evaluate_opportunity(
        _item(selection_method="DAU_THAU_RONG_RAI"),
        _profile(selection_methods=frozenset({"CHAO_HANG_CANH_TRANH"})),
    )

    assert evaluation.disposition is filter_engine.OpportunityFilterDisposition.NO_MATCH


def test_missing_selection_method_is_indeterminate() -> None:
    evaluation = filter_engine.evaluate_opportunity(
        _item(selection_method=None, procurement_method="CHAO_HANG_CANH_TRANH"),
        _profile(selection_methods=frozenset({"CHAO_HANG_CANH_TRANH"})),
    )

    assert evaluation.disposition is filter_engine.OpportunityFilterDisposition.INDETERMINATE


def test_procurement_method_never_satisfies_selection_filter() -> None:
    evaluation = filter_engine.evaluate_opportunity(
        _item(selection_method=None, procurement_method="CHAO_HANG_CANH_TRANH"),
        _profile(selection_methods=frozenset({"CHAO_HANG_CANH_TRANH"})),
    )

    assert evaluation.criteria[0].outcome is filter_engine.CriterionOutcome.UNKNOWN


@pytest.mark.parametrize(
    ("source_type", "keyword"),
    [
        (OpportunitySourceType.KHMT, "nhà đầu tư"),
        (OpportunitySourceType.KHMT, "phê duyệt"),
        (OpportunitySourceType.TBMT, "bên mời thầu"),
        (OpportunitySourceType.TBMT, "firewall"),
    ],
)
def test_include_keyword_uses_source_specific_semantic_fields(
    source_type: OpportunitySourceType,
    keyword: str,
) -> None:
    raw_id = "PL2600265077-00" if source_type is OpportunitySourceType.KHMT else "IB2600463290-00"
    evaluation = filter_engine.evaluate_opportunity(
        _item(source_type=source_type, raw_id=raw_id),
        _profile(include_keywords=(keyword,)),
    )

    assert evaluation.disposition is filter_engine.OpportunityFilterDisposition.MATCH


def test_investor_and_procuring_entity_are_not_collapsed() -> None:
    khmt = filter_engine.evaluate_opportunity(
        _item(approval_content=None, procuring_entity=None),
        _profile(include_keywords=("bên mời thầu",)),
    )
    tbmt = filter_engine.evaluate_opportunity(
        _item(
            source_type=OpportunitySourceType.TBMT,
            raw_id="IB2600463290-00",
            investor=None,
            approval_content=None,
        ),
        _profile(include_keywords=("bên mời thầu",)),
    )

    assert khmt.disposition is filter_engine.OpportunityFilterDisposition.INDETERMINATE
    assert tbmt.disposition is filter_engine.OpportunityFilterDisposition.MATCH


def test_exclude_keyword_is_no_match_when_found() -> None:
    evaluation = filter_engine.evaluate_opportunity(
        _item(package_name="Mua sắm restricted thiết bị"),
        _profile(exclude_keywords=("restricted",)),
    )

    assert evaluation.disposition is filter_engine.OpportunityFilterDisposition.NO_MATCH


def test_empty_profile_is_unfiltered() -> None:
    evaluation = filter_engine.evaluate_opportunity(_item(), _profile())

    assert evaluation.disposition is filter_engine.OpportunityFilterDisposition.UNFILTERED
    assert evaluation.criteria == ()
    assert evaluation.matched_fields == ()


def test_filter_profile_has_active_criteria_ignores_name_and_blank_keywords() -> None:
    assert not _profile(
        name="Saved profile",
        include_keywords=("  ",),
        exclude_keywords=("	",),
    ).has_active_criteria
    assert _profile(min_budget=Decimal(0)).has_active_criteria


def test_budget_pass_exposes_structured_observed_and_expected_evidence() -> None:
    evaluation = filter_engine.evaluate_opportunity(
        _item(price=Decimal(1181000000)),
        _profile(min_budget=Decimal(500000000), max_budget=Decimal(1300000000)),
    )

    assert evaluation.disposition is filter_engine.OpportunityFilterDisposition.MATCH
    evidence = evaluation.criteria[0].evidence
    assert evidence == (
        filter_engine.CriterionEvidence(
            field="package_price",
            observed_value="1181000000",
            expected_values=("min=500000000", "max=1300000000"),
            matched_terms=(),
        ),
    )


def test_budget_fail_evidence_preserves_actual_and_maximum() -> None:
    evaluation = filter_engine.evaluate_opportunity(
        _item(price=Decimal(1500000000)),
        _profile(max_budget=Decimal(1300000000)),
    )

    assert evaluation.disposition is filter_engine.OpportunityFilterDisposition.NO_MATCH
    assert evaluation.criteria[0].reason_code is filter_engine.FilterReasonCode.BUDGET_ABOVE_MAX
    assert evaluation.criteria[0].evidence[0].observed_value == "1500000000"
    assert evaluation.criteria[0].evidence[0].expected_values == ("max=1300000000",)


def test_budget_unknown_evidence_preserves_requested_bounds() -> None:
    evaluation = filter_engine.evaluate_opportunity(
        _item(price=None),
        _profile(min_budget=Decimal(500000000), max_budget=Decimal(1300000000)),
    )

    assert evaluation.disposition is filter_engine.OpportunityFilterDisposition.INDETERMINATE
    assert evaluation.criteria[0].reason_code is filter_engine.FilterReasonCode.BUDGET_UNKNOWN
    assert evaluation.criteria[0].evidence[0].observed_value is None
    assert evaluation.criteria[0].evidence[0].expected_values == (
        "min=500000000",
        "max=1300000000",
    )


def test_province_evidence_preserves_observed_and_requested_codes() -> None:
    evaluation = filter_engine.evaluate_opportunity(
        _item(province_code="HCM"),
        _profile(province_city_codes=frozenset({"HN", "HCM"})),
    )

    evidence = evaluation.criteria[0].evidence[0]
    assert evidence.field == "province_city_code"
    assert evidence.observed_value == "HCM"
    assert evidence.expected_values == ("HCM", "HN")


def test_unknown_province_evidence_does_not_invent_a_location() -> None:
    evaluation = filter_engine.evaluate_opportunity(
        _item(province_code=None, province_status=ProvinceCityStatus.NEEDS_REVIEW),
        _profile(province_city_codes=frozenset({"HCM"})),
    )

    assert evaluation.disposition is filter_engine.OpportunityFilterDisposition.INDETERMINATE
    assert evaluation.criteria[0].evidence[0].observed_value is None
    assert evaluation.criteria[0].evidence[0].expected_values == ("HCM",)


def test_include_keyword_evidence_identifies_matching_field_and_term() -> None:
    evaluation = filter_engine.evaluate_opportunity(
        _item(package_name="Cung cấp và lắp đặt Core Switch"),
        _profile(include_keywords=("switch",)),
    )

    evidence = evaluation.criteria[0].evidence
    assert evidence[0].field == "package_name"
    assert evidence[0].matched_terms == ("switch",)


def test_multiple_keyword_fields_keep_declared_deterministic_order() -> None:
    evaluation = filter_engine.evaluate_opportunity(
        _item(package_name="switch", project="switch"),
        _profile(include_keywords=("switch",)),
    )

    assert [entry.field for entry in evaluation.criteria[0].evidence] == [
        "package_name",
        "project",
    ]


def test_exclude_keyword_evidence_identifies_matching_field_and_term() -> None:
    evaluation = filter_engine.evaluate_opportunity(
        _item(package_name="Mua sắm restricted thiết bị"),
        _profile(exclude_keywords=("restricted",)),
    )

    evidence = evaluation.criteria[0].evidence
    assert evidence[0].field == "package_name"
    assert evidence[0].matched_terms == ("restricted",)


def test_selection_method_evidence_preserves_canonical_observed_and_expected_codes() -> None:
    evaluation = filter_engine.evaluate_opportunity(
        _item(selection_method="DAU_THAU_RONG_RAI"),
        _profile(selection_methods=frozenset({"CHAO_HANG_CANH_TRANH", "DAU_THAU_RONG_RAI"})),
    )

    evidence = evaluation.criteria[0].evidence[0]
    assert evidence.field == "selection_method"
    assert evidence.observed_value == "DAU_THAU_RONG_RAI"
    assert evidence.expected_values == ("CHAO_HANG_CANH_TRANH", "DAU_THAU_RONG_RAI")


def test_unknown_selection_method_evidence_does_not_fabricate_a_code() -> None:
    evaluation = filter_engine.evaluate_opportunity(
        _item(selection_method=None),
        _profile(selection_methods=frozenset({"DAU_THAU_RONG_RAI"})),
    )

    assert evaluation.disposition is filter_engine.OpportunityFilterDisposition.INDETERMINATE
    assert evaluation.criteria[0].evidence[0].observed_value is None
    assert evaluation.criteria[0].evidence[0].expected_values == ("DAU_THAU_RONG_RAI",)


def test_identical_evaluations_have_identical_evidence_ordering() -> None:
    profile = _profile(
        min_budget=Decimal(500000000),
        max_budget=Decimal(1300000000),
        province_city_codes=frozenset({"HCM", "HN"}),
        include_keywords=("switch", "mạng"),
        exclude_keywords=("restricted",),
        selection_methods=frozenset({"DAU_THAU_RONG_RAI", "CHAO_HANG_CANH_TRANH"}),
    )
    first = filter_engine.evaluate_opportunity(_item(), profile)
    second = filter_engine.evaluate_opportunity(_item(), profile)

    assert first == second
    assert first.criteria == second.criteria


def test_realistic_match_exposes_each_active_criterion() -> None:
    evaluation = filter_engine.evaluate_opportunity(
        _item(
            package_name="Cung cấp, lắp đặt hệ thống Core Switch và thiết bị mạng",
            price=Decimal(1181000000),
            province_code="HCM",
            selection_method="DAU_THAU_RONG_RAI",
        ),
        _profile(
            min_budget=Decimal(500000000),
            max_budget=Decimal(1300000000),
            province_city_codes=frozenset({"HCM"}),
            include_keywords=("switch", "mạng"),
            selection_methods=frozenset({"DAU_THAU_RONG_RAI"}),
        ),
    )

    assert evaluation.disposition is filter_engine.OpportunityFilterDisposition.MATCH
    assert len(evaluation.criteria) == 4
    assert all(criterion.evidence for criterion in evaluation.criteria)


def test_empty_search_buckets_all_source_items_as_unfiltered() -> None:
    items = (_item(source_row=1), _item(source_row=2), _item(source_row=3))

    result = search.search_opportunities(items, search.TargetedSearchRequest())

    assert result.total_examined == 3
    assert result.matched_count == 0
    assert result.indeterminate_count == 0
    assert result.nonmatched_count == 0
    assert result.unfiltered_count == 3
    assert result.matches == ()
    assert result.indeterminate == ()
    assert result.nonmatches == ()
    assert [item.item.source_row for item in result.unfiltered] == [1, 2, 3]
    assert len(result.evaluated) == 3


def test_name_only_request_is_unfiltered() -> None:
    result = search.search_opportunities(
        (_item(source_row=1),), search.TargetedSearchRequest(name="saved")
    )

    assert result.unfiltered_count == 1
    assert result.matched_count == 0
    assert (
        result.evaluated[0].evaluation.disposition
        is filter_engine.OpportunityFilterDisposition.UNFILTERED
    )


def test_whitespace_only_keywords_are_not_active_criteria() -> None:
    result = search.search_opportunities(
        (_item(source_row=1),),
        search.TargetedSearchRequest(include_keywords=("  ",), exclude_keywords=("	",)),
    )

    assert result.unfiltered_count == 1
    assert result.matched_count == 0


def test_zero_min_budget_is_an_active_filter() -> None:
    evaluation = filter_engine.evaluate_opportunity(
        _item(price=Decimal(0)), _profile(min_budget=Decimal(0))
    )

    assert evaluation.disposition is filter_engine.OpportunityFilterDisposition.MATCH
    assert evaluation.criteria


def test_result_counts_conserve_total_with_unfiltered_bucket() -> None:
    items = (
        _item(source_row=1),
        _item(source_row=2, price=None),
        _item(source_row=3, price=Decimal(900000000)),
        _item(source_row=4),
    )
    result = search.search_opportunities(
        items, search.TargetedSearchRequest(max_budget=Decimal(500000000))
    )

    assert (
        result.matched_count
        + result.indeterminate_count
        + result.nonmatched_count
        + result.unfiltered_count
        == result.total_examined
    )


def test_zero_criteria_scale_does_not_mark_624_items_as_matches() -> None:
    items = tuple(_item(source_row=index) for index in range(1, 625))

    result = search.search_opportunities(items, search.TargetedSearchRequest())

    assert result.total_examined == 624
    assert result.unfiltered_count == 624
    assert result.matched_count == 0
    assert len(result.unfiltered) == 624


def test_generic_search_returns_three_disposition_buckets_in_stable_order() -> None:
    items = (
        _item(source_row=1),
        _item(source_row=2, price=None),
        _item(source_row=3, price=Decimal(900000000)),
    )
    result = search.search_opportunities(
        items,
        search.TargetedSearchRequest(max_budget=Decimal(500000000)),
    )

    assert result.total_examined == 3
    assert result.matched_count == 1
    assert result.indeterminate_count == 1
    assert result.nonmatched_count == 1
    assert [item.item.source_row for item in result.matches] == [1]
    assert [item.item.source_row for item in result.indeterminate] == [2]
    assert [item.item.source_row for item in result.nonmatches] == [3]
    assert [item.item.source_row for item in result.evaluated] == [1, 2, 3]


def test_generic_search_delegates_every_decision_to_filter_authority(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[int] = []
    original = search.evaluate_opportunity

    def tracked(item, profile):
        calls.append(item.source_row)
        return original(item, profile)

    monkeypatch.setattr(search, "evaluate_opportunity", tracked)
    items = (_item(source_row=4), _item(source_row=2))

    result = search.search_opportunities(items, search.TargetedSearchRequest())

    assert calls == [4, 2]
    assert result.unfiltered_count == 2


def test_revisions_remain_distinct_generic_evaluations() -> None:
    items = (
        _item(raw_id="IB2600463290-00", source_type=OpportunitySourceType.TBMT, source_row=1),
        _item(raw_id="IB2600463290-01", source_type=OpportunitySourceType.TBMT, source_row=2),
    )
    result = search.search_opportunities(items, search.TargetedSearchRequest())

    assert result.unfiltered_count == 2
    assert [item.item.identity.raw_id for item in result.unfiltered] == [
        "IB2600463290-00",
        "IB2600463290-01",
    ]
    assert result.unfiltered[0].item.identity != result.unfiltered[1].item.identity


def test_legacy_filter_and_search_facades_remain_available() -> None:
    assert callable(filter_engine.evaluate_plan_package)
    assert callable(search.search_packages)


@pytest.mark.parametrize(
    ("package_name", "expected"),
    [
        ("Bộ Công An", True),
        ("An toàn", True),
        ("An ninh mạng", True),
        ("Ngân sách", False),
        ("Dự án", False),
        ("Cân đối", False),
    ],
)
def test_generic_find_is_literal_case_insensitive_and_accent_sensitive(
    package_name: str,
    expected: bool,
) -> None:
    item = replace(_item(source_type=OpportunitySourceType.TBMT), package_name=package_name)

    result = search.search_opportunities(
        (item,),
        search.TargetedSearchRequest(include_keywords=("An",)),
    )

    assert result.find_hit_count == int(expected)


@pytest.mark.parametrize(
    ("query", "package_name"),
    [
        ("Mạng", "Mạng lưới"),
        ("Mạng", "AN NINH MẠNG"),
        ("máy", "Máy tính"),
        ("camera", "Trang bị CAMERA giám sát"),
    ],
)
def test_generic_find_supports_literal_substrings(
    query: str,
    package_name: str,
) -> None:
    item = replace(_item(source_type=OpportunitySourceType.TBMT), package_name=package_name)

    result = search.search_opportunities(
        (item,),
        search.TargetedSearchRequest(include_keywords=(query,)),
    )

    assert result.find_hit_count == 1


def test_generic_find_searches_raw_tender_id_and_address_fields() -> None:
    item = replace(
        _item(source_type=OpportunitySourceType.TBMT, raw_id="IB2600463290-00"),
        source_fields={"ĐỊA CHỈ BÊN MỜI THẦU": "Quảng Trị"},
        raw_fields={"ĐỊA CHỈ BÊN MỜI THẦU": "Quảng Trị"},
    )

    id_result = search.search_opportunities(
        (item,),
        search.TargetedSearchRequest(include_keywords=("IB26004",)),
    )
    address_result = search.search_opportunities(
        (item,),
        search.TargetedSearchRequest(include_keywords=("Quảng Trị",)),
    )

    assert id_result.find_hit_count == 1
    assert address_result.find_hit_count == 1


def test_generic_find_preserves_all_matching_business_field_evidence() -> None:
    item = replace(
        _item(source_type=OpportunitySourceType.TBMT, package_name="Bộ Công An"),
        source_fields={
            "BÊN MỜI THẦU": "Cục An ninh mạng",
            "NỘI DUNG CHÍNH": "Thiết bị camera",
        },
        raw_fields={
            "BÊN MỜI THẦU": "Cục An ninh mạng",
            "NỘI DUNG CHÍNH": "Thiết bị camera",
        },
    )

    result = search.search_opportunities(
        (item,),
        search.TargetedSearchRequest(include_keywords=("An",)),
    )
    criterion = next(
        criterion
        for criterion in result.evaluated[0].evaluation.criteria
        if criterion.criterion == "include_keywords"
    )

    matched_values = {
        evidence.observed_value
        for evidence in criterion.evidence
        if evidence.matched_terms
    }
    assert result.find_hit_count == 1
    assert "Bộ Công An" in matched_values
    assert "Cục An ninh mạng" in matched_values


def test_generic_find_hit_count_is_separate_from_final_filter_match() -> None:
    item = replace(
        _item(source_type=OpportunitySourceType.TBMT, package_name="Bộ Công An"),
        package_price=Decimal(900000000),
    )

    result = search.search_opportunities(
        (item,),
        search.TargetedSearchRequest(
            include_keywords=("An",),
            max_budget=Decimal(500000000),
        ),
    )

    assert result.find_hit_count == 1
    assert result.matched_count == 0
    assert result.nonmatched_count == 1
