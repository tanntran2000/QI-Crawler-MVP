"""Discriminating contracts for the Micro-C execution and review skills."""

import json
from pathlib import Path

ROOT = Path(__file__).parents[2]
SKILLS = ROOT / "plugins" / "qi-agent-workbench" / "skills"
EVALS = ROOT / "plugins" / "qi-agent-workbench" / "evals"
TEMPLATE = (
    ROOT / "plugins" / "qi-agent-workbench" / "references" / "handoff-template.md"
)
OPERATING_MODEL = ROOT / "docs" / "agent" / "OPERATING_MODEL.md"
AGENT_LOOP = SKILLS / "qi-agent-loop" / "SKILL.md"


def _load(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _impact_contract_valid(text: str) -> bool:
    required = (
        "impact_radius != edit_radius != test_radius",
        "CodeGraph = impact intelligence only",
        "TOOL_UNAVAILABLE → governed manual fallback",
        "IMPACT_SCOPE_GRANT = FORBIDDEN",
    )
    return all(token in text for token in required) and "CodeGraph impact_radius -> edit_radius" not in text


def _python_contract_valid(text: str) -> bool:
    required = (
        "approved Work Order required",
        "no architecture replan",
        "minimal complete fix",
        "TDD / systematic debugging only when applicable",
    )
    return all(token in text for token in required) and "Approved Work Order may be replaced by brainstorming/replanning" not in text


def _evidence_contract_valid(text: str) -> bool:
    required = (
        "BASELINE / NEGATIVE PROOF",
        "TARGETED LOCAL",
        "FULL LOCAL",
        "RUFF / DIFF",
        "HOSTED CI",
        "UNVERIFIED CLAIM",
        "LIMITATION",
        "BUILDER CLAIM != MACHINE EVIDENCE",
        "UNVERIFIED_CLAIM = LIMITATION",
    )
    return all(token in text for token in required) and "Builder claim is sufficient machine evidence" not in text


def _tool_evidence_contract_valid(text: str) -> bool:
    required = (
        "DISCOVERED",
        "CONFIGURED",
        "CALLABLE",
        "SMOKE_VERIFIED",
        "APPROVED_FOR_TASK",
        "USED_WITH_EVIDENCE",
        "TOOL_APPLICABILITY",
        "FALLBACK_AUTHORIZED",
        "FALLBACK_EQUIVALENCE",
        "IMPACT_RADIUS",
        "EDIT_RADIUS",
        "TEST_RADIUS",
        "LIMITATIONS",
    )
    return all(token in text for token in required) and "CONFIGURED = SMOKE_VERIFIED" not in text


def _review_contract_valid(text: str) -> bool:
    required = (
        "ROLE",
        "STATUS",
        "PARENT_WP",
        "MICRO_WP",
        "BASE_SHA",
        "HEAD_SHA",
        "CHANGED_PATHS",
        "CONTRACT_COVERAGE",
        "VERIFICATION",
        "DEVIATIONS",
        "UNRESOLVED_FINDINGS",
        "SPINE_IMPACT",
        "GIT_STATE",
        "EXACTLY_ONE_NEXT_ACTION",
        "NEXT_AUTHORITY",
        "REVIEWER_INDEPENDENT = YES",
        "REVIEWER_EDIT = REFUSE",
        "END OF HANDOFF",
    )
    return all(token in text for token in required) and "Reviewer may edit audited output" not in text


def _template_fields(text: str) -> set[str]:
    return {
        line.split("=", 1)[0].strip()
        for line in text.splitlines()
        if "=" in line and not line.lstrip().startswith("#")
    }


def test_impact_skill_has_separate_radii_and_governed_fallback() -> None:
    assert _impact_contract_valid(_load(SKILLS / "qi-impact-map" / "SKILL.md"))


def test_impact_mutant_cannot_grant_edit_scope() -> None:
    mutant = _load(SKILLS / "qi-impact-map" / "SKILL.md") + "\nCodeGraph impact_radius -> edit_radius\n"
    assert not _impact_contract_valid(mutant)


def test_python_skill_requires_approved_bounded_change() -> None:
    assert _python_contract_valid(_load(SKILLS / "qi-python-change" / "SKILL.md"))


def test_python_mutant_cannot_replan_architecture() -> None:
    mutant = _load(SKILLS / "qi-python-change" / "SKILL.md") + "\nApproved Work Order may be replaced by brainstorming/replanning\n"
    assert not _python_contract_valid(mutant)


def test_evidence_skill_distinguishes_claims_from_machine_evidence() -> None:
    assert _evidence_contract_valid(_load(SKILLS / "qi-evidence-check" / "SKILL.md"))


def test_evidence_mutant_cannot_promote_builder_claim() -> None:
    mutant = _load(SKILLS / "qi-evidence-check" / "SKILL.md") + "\nBuilder claim is sufficient machine evidence\n"
    assert not _evidence_contract_valid(mutant)


def test_evidence_skill_records_independent_tool_health_and_use() -> None:
    assert _tool_evidence_contract_valid(_load(SKILLS / "qi-evidence-check" / "SKILL.md"))


def test_configured_tool_mutant_cannot_claim_smoke_verification() -> None:
    text = _load(SKILLS / "qi-evidence-check" / "SKILL.md")
    assert not _tool_evidence_contract_valid(text + "\nCONFIGURED = SMOKE_VERIFIED\n")


def test_review_skill_requires_independent_no_edit_handoff() -> None:
    assert _review_contract_valid(_load(SKILLS / "qi-review-handoff" / "SKILL.md"))


def test_review_mutant_cannot_authorize_reviewer_edits() -> None:
    mutant = _load(SKILLS / "qi-review-handoff" / "SKILL.md") + "\nReviewer may edit audited output\n"
    assert not _review_contract_valid(mutant)


def test_handoff_template_enforces_exact_report_metadata_contract() -> None:
    template = _load(TEMPLATE)
    expected_keys = (
        "WO_ID",
        "RUN_OR_ATTEMPT_ID",
        "REPORT_ID",
        "SOURCE_TASK_ID",
        "DESTINATION_TASK_ID",
        "OBJECT_ID",
        "IN_REPLY_TO",
    )
    admission_line = (
        "REPORT_ADMISSION_CONTRACT = "
        "docs/agent/OPERATING_MODEL.md#supervised-report-identity-and-admission; "
        "USE_CANONICAL_RULES_THERE"
    )

    def metadata_contract_valid(candidate: str) -> bool:
        lines = candidate.splitlines()
        headers = [
            i for i, line in enumerate(lines) if line == "REPORT_METADATA = REQUIRED"
        ]
        bindings = [
            i
            for i, line in enumerate(lines)
            if line.startswith("REPORT_ADMISSION_CONTRACT = ")
        ]
        if len(headers) != 1 or len(bindings) != 1 or bindings[0] <= headers[0]:
            return False
        keys = [
            line.split("=", 1)[0].strip()
            for line in lines[headers[0] + 1 : bindings[0]]
            if "=" in line
        ]
        return keys == list(expected_keys) and lines[bindings[0]] == admission_line

    lines = template.splitlines()
    binding_index = next(
        i for i, line in enumerate(lines) if line.startswith("REPORT_ADMISSION_CONTRACT = ")
    )
    binding_line = lines.pop(binding_index)
    header_index = lines.index("REPORT_METADATA = REQUIRED")
    lines.insert(header_index, binding_line)
    binding_before_header = "\n".join(lines) + "\n"

    mutants = {
        "duplicate metadata key": template.replace("WO_ID =\n", "WO_ID =\nWO_ID =\n", 1),
        "eighth metadata key": template.replace(
            "IN_REPLY_TO =\n", "IN_REPLY_TO =\nEXTRA_METADATA =\n", 1
        ),
        "noncanonical admission target": template.replace(
            "docs/agent/OPERATING_MODEL.md#supervised-report-identity-and-admission",
            "docs/agent/OTHER.md#report-admission",
            1,
        ),
        "duplicate metadata header": template.replace(
            "REPORT_METADATA = REQUIRED\n",
            "REPORT_METADATA = REQUIRED\nREPORT_METADATA = REQUIRED\n",
            1,
        ),
        "duplicate admission binding": template.replace(
            admission_line + "\n", admission_line + "\n" + admission_line + "\n", 1
        ),
        "wrong metadata order": template.replace(
            "WO_ID =\nRUN_OR_ATTEMPT_ID =\n",
            "RUN_OR_ATTEMPT_ID =\nWO_ID =\n",
            1,
        ),
        "binding before metadata header": binding_before_header,
    }
    rejected = {name: not metadata_contract_valid(mutant) for name, mutant in mutants.items()}

    assert metadata_contract_valid(template)
    assert rejected == {name: True for name in mutants}


def _operating_section(text: str, title: str) -> str:
    marker = f"## {title}"
    lines = text.splitlines()
    try:
        start = lines.index(marker)
    except ValueError:
        return ""
    end = next(
        (index for index in range(start + 1, len(lines)) if lines[index].startswith("## ")),
        len(lines),
    )
    return "\n".join(lines[start:end])


def _impact_readiness_contract_valid(skill_text: str, overview_section: str) -> bool:
    skill_required = (
        "STRUCTURAL_EXPLORATION = CHECK_CODEBASE_MEMORY_READINESS",
        "WHEN .codegraph/ EXISTS, INVOKE CODEGRAPH FIRST",
        "WHEN CBM_INDEX_READY, USE RELEVANT GRAPH TOOLS WITHOUT DUPLICATING EVERY QUERY",
        "BATCH check_index_coverage FOR ALL RELIED-ON EVIDENCE FILES",
        "PARTIAL/STALE/UNKNOWN COVERAGE = DIRECT SOURCE FALLBACK",
        "GRAPH ABSENCE = NO PROOF OF NO CALLER, DEAD CODE, OR DELETION AUTHORITY",
        "FALLBACK SUFFICIENT = CONTINUE; MATERIAL CLAIM INSUFFICIENT = HOLD",
        "GRAPH OUTPUT GRANTS SCOPE = NO",
        "STATIC_ROUTING_CONTRACT_VERIFIED = STATIC MARKDOWN ONLY; RUNTIME ENFORCEMENT NOT PROVEN",
    )
    skill_forbidden = (
        "GRAPH OUTPUT GRANTS SCOPE = YES",
        "STATIC_ROUTING_CONTRACT_VERIFIED = RUNTIME ENFORCEMENT VERIFIED",
        "FULL_REPOSITORY_COVERAGE = PROVEN",
    )
    overview_required = (
        "Codebase Memory readiness",
        "`qi-impact-map` owns the detailed routing contract",
        "graph output is evidence only and grants no scope or authority",
    )
    overview_forbidden = (
        "check_index_coverage",
        "WHEN .codegraph/ EXISTS",
        "PARTIAL/STALE/UNKNOWN COVERAGE",
    )
    normalized_overview = " ".join(overview_section.split()).casefold()
    return (
        all(item in skill_text for item in skill_required)
        and not any(item in skill_text for item in skill_forbidden)
        and all(item.casefold() in normalized_overview for item in overview_required)
        and not any(item.casefold() in normalized_overview for item in overview_forbidden)
    )


def test_impact_readiness_routes_graph_coverage_and_bounded_fallback() -> None:
    skill = _load(SKILLS / "qi-impact-map" / "SKILL.md")
    overview = _operating_section(
        _load(ROOT / "docs" / "agent" / "QI_AGENT_WORKBENCH.md"),
        "6. Impact, edit, and test radii",
    )

    assert _impact_readiness_contract_valid(skill, overview)

    mutants = (
        skill.replace(
            "WHEN .codegraph/ EXISTS, INVOKE CODEGRAPH FIRST",
            "WHEN .codegraph/ EXISTS, INVOKE CODEGRAPH AFTER OTHER TOOLS",
            1,
        ),
        skill.replace(
            "GRAPH ABSENCE = NO PROOF OF NO CALLER, DEAD CODE, OR DELETION AUTHORITY",
            "GRAPH ABSENCE = PROOF OF NO CALLER, DEAD CODE, OR DELETION AUTHORITY",
            1,
        ),
        skill.replace(
            "FALLBACK SUFFICIENT = CONTINUE; MATERIAL CLAIM INSUFFICIENT = HOLD",
            "FALLBACK SUFFICIENT = CONTINUE; MATERIAL CLAIM INSUFFICIENT = CONTINUE",
            1,
        ),
        skill.replace(
            "GRAPH OUTPUT GRANTS SCOPE = NO",
            "GRAPH OUTPUT GRANTS SCOPE = YES",
            1,
        ),
        skill.replace(
            "STATIC_ROUTING_CONTRACT_VERIFIED = STATIC MARKDOWN ONLY; RUNTIME ENFORCEMENT NOT PROVEN",
            "STATIC_ROUTING_CONTRACT_VERIFIED = RUNTIME ENFORCEMENT VERIFIED",
            1,
        ),
        skill + "\nGRAPH OUTPUT GRANTS SCOPE = YES",
        skill + "\nSTATIC_ROUTING_CONTRACT_VERIFIED = RUNTIME ENFORCEMENT VERIFIED",
        skill + "\nFULL_REPOSITORY_COVERAGE = PROVEN",
    )
    assert all(not _impact_readiness_contract_valid(mutant, overview) for mutant in mutants)

    duplicated_algorithm = overview + "\ncheck_index_coverage\n"
    assert not _impact_readiness_contract_valid(skill, duplicated_algorithm)


def _helper_contract_valid(section: str) -> bool:
    required = (
        "HELPER_IS = OWNER_ROLE_CAPABILITY; NOT_FIFTH_ROLE; NOT_TAKEOVER",
        "HELPER_AUTHORITY_SOURCE = EXPLICIT_HUMAN_PLANNING_AUTHORITY_OR_ACTIVE_LEASE_DELEGATION_CLAUSE",
        "HELPER_DEFAULT_DISPATCH_BUDGET = 0; EACH_WP_SETS_FINITE_BUDGET",
        "HELPER_DEPTH = 1; PROMPT_GOVERNED_UNLESS_TOOL_ENFORCEMENT_IS_SEPARATELY_VERIFIED",
        "HELPER_BRIEF = TASK_MESSAGE_FROM_AUTHORITY; TEN_TASK_ENVELOPE_CONCEPTS; NO_NEW_SCHEMA_OR_ROLE",
        "QUESTION, OBJECT, READ_ALLOWLIST, TOOLS, DATA, SENSITIVITY, EXCLUSIONS, BUDGET, STOP_RULE, RETURN_OWNER",
        "SENSITIVE_UNTRACKED_OR_OPERATIONAL_CONTENT=FORBIDDEN_UNLESS_EXPLICITLY_AUTHORIZED",
        "HELPER_RESULT=SUPPORTING_EVIDENCE_ONLY",
        "HELPER_CANNOT = ADVANCE_STATE, CONSUME_TRANSITION, OPEN_CORRECTION, CREATE_VERDICT, GRANT_AUTHORITY",
        "HELPER_RESULT_PROMOTION_TO_BUILDER_TESTER_REVIEWER_COMPLETION_OR_PASS=FORBIDDEN",
        "HELPER_OWNER_VERIFIES_EVIDENCE_BEFORE_CITATION = YES",
    )
    forbidden = (
        "HELPER_RESULT=ROLE_REPORT",
        "HELPER_RESULT=REVIEWER_VERDICT",
        "HELPER_RESULT=AUTHORITY",
    )
    return all(item in section for item in required) and not any(
        item in section for item in forbidden
    )


def _provenance_contract_valid(text: str) -> bool:
    required = (
        "PROVENANCE_LABELS = PROMPT_GOVERNED, OBSERVED, TOOL_ENFORCED",
        "UNKNOWN = UNKNOWN",
        "CLEAN_GIT_STATUS_PROVES_ALL_HELPER_WRITES_READS_OR_TRANSMISSION = NO",
        "VERIFICATION_CLAIMS = STATIC_CONTRACT_VERIFIED, SCENARIO_REPLAY_VERIFIED, DELEGATION_PILOT_VERIFIED, AUTONOMOUS_ENFORCEMENT_NOT_PROVEN",
        "STATIC_CONTRACT_VERIFIED = TEXT_CONTRACT_EVIDENCE_ONLY; NOT_RUNTIME_ENFORCEMENT",
    )
    return all(item in text for item in required)


def _correction_contract_valid(section: str) -> bool:
    required = (
        "CORRECTION_BUDGET_FOLLOWS_AUTHORITY_LEASE = ACROSS_REVISION, NAME, TASK, SESSION, MODEL, TAKEOVER",
        "CORRECTION_ATTEMPT_UNIT = ONE_PLANNER_OPENED_ATTEMPT",
        "SEPARATE_ACCOUNTING_CATEGORIES = DEVELOPMENT_RED_GREEN, VERIFIED_TRANSIENT_INFRA_RERUN, BOUNDED_METADATA_COMPLETION",
        "DISPATCH_TIMEOUT_ERROR_OR_UNKNOWN = ATTEMPT_USED_AS_APPLICABLE; NO_SILENT_RESEND",
        "BUDGET_RESET_BY_RENAME_OR_REVISION = FORBIDDEN",
        "BUDGET_EXHAUSTION = HOLD_AND_REPORT",
        "BUDGET_CANNOT_CHANGE_ACCEPTANCE_OR_REVALIDATE_STALE_EVIDENCE = YES",
    )
    return all(item in section for item in required)


def _stop_contract_valid(section: str) -> bool:
    required = (
        "STOP_STATES = STOP_REQUESTED, STOP_CONFIRMED, STOP_STATUS_UNKNOWN",
        "NO_WRITER_TRANSFER_OR_CONFLICTING_RESOURCE_WORK_UNTIL_STOP_CONFIRMED = YES",
        "STOP_STATUS_UNKNOWN = HOLD_NO_TRANSFER",
    )
    forbidden = "STOP_STATUS_UNKNOWN = ALLOW_TRANSFER"
    return all(item in section for item in required) and forbidden not in section


def _finding_contract_valid(section: str) -> bool:
    expected = (
        "FINDING_ID",
        "SEVERITY",
        "INTEGRATION_DISPOSITION",
        "FIX_AUTHORITY",
        "LOCATION",
        "IMPACT",
        "EVIDENCE",
        "RESOLUTION_CONDITION",
    )
    fields = next(
        (
            tuple(part.strip() for part in line.split("=", 1)[1].split(","))
            for line in section.splitlines()
            if line.startswith("REVIEWER_FINDING_FIELDS = ")
        ),
        (),
    )
    required = (
        "FINDING_DIMENSIONS_ARE_INDEPENDENT = SEVERITY, INTEGRATION_DISPOSITION, FIX_AUTHORITY",
        "REVIEWER_VERDICT = PASS, HOLD, FAIL",
        "FIX_AUTHORITY_VERIFICATION_AND_CORRECTION_ROUTING = PLANNER",
        "OUT_OF_SCOPE_FINDING_MAY_BLOCK = YES; SEVERITY_ALONE_DECIDES_BLOCKING = NO",
    )
    return fields == expected and all(item in section for item in required)


def _report_admission_documented(text: str) -> bool:
    normalized = " ".join(text.split())
    required = (
        "REPORT_METADATA = WO_ID, RUN_OR_ATTEMPT_ID, REPORT_ID, SOURCE_TASK_ID, DESTINATION_TASK_ID, OBJECT_ID, IN_REPLY_TO",
        "`REPORT_ID` must be non-empty and unseen for that pending transition",
        "wrong-route, wrong-object or wrong-attempt reports are `HOLD` and cannot advance state",
        "duplicate `REPORT_ID` cannot advance or redispatch",
        "supervised admission tracking, not exactly-once transport",
        "This is a documented contract, not an executable admission engine.",
    )
    return all(item in normalized for item in required)


def _agent_loop_routes_helpers(text: str) -> bool:
    required = (
        "../../../../docs/agent/OPERATING_MODEL.md#bounded-role-helper-delegation",
        "only routes helper requests and grants no delegation authority",
    )
    duplicated_contract = (
        "HELPER_RESULT=SUPPORTING_EVIDENCE_ONLY",
        "CORRECTION_BUDGET_FOLLOWS_AUTHORITY_LEASE",
    )
    return all(item in text for item in required) and not any(
        item in text for item in duplicated_contract
    )


def test_handoff_template_contains_exact_object_and_terminal_sentinel() -> None:
    fields = _template_fields(_load(TEMPLATE))
    required = {
        "ROLE",
        "REPORT_METADATA",
        "WO_ID",
        "RUN_OR_ATTEMPT_ID",
        "REPORT_ID",
        "SOURCE_TASK_ID",
        "DESTINATION_TASK_ID",
        "OBJECT_ID",
        "IN_REPLY_TO",
        "REPORT_ADMISSION_CONTRACT",
        "STATUS",
        "PARENT_WP",
        "MICRO_WP",
        "BASE_SHA",
        "HEAD_SHA",
        "CHANGED_PATHS",
        "CONTRACT_COVERAGE",
        "VERIFICATION",
        "DEVIATIONS",
        "UNRESOLVED_FINDINGS",
        "SPINE_IMPACT",
        "GIT_STATE",
        "EXACTLY_ONE_NEXT_ACTION",
        "NEXT_AUTHORITY",
    }
    template = _load(TEMPLATE)
    assert required <= fields
    assert "END OF HANDOFF" in template


def test_incomplete_handoff_fixture_is_rejected() -> None:
    fixture = json.loads(_load(EVALS / "incomplete-handoff.json"))
    assert fixture["expected"] == "HOLD"
    assert {"BASE_SHA", "HEAD_SHA", "VERIFICATION", "END OF HANDOFF"} <= set(fixture["missing"])


def test_reviewer_edit_fixture_is_rejected() -> None:
    fixture = json.loads(_load(EVALS / "reviewer-edit-request.json"))
    assert fixture["expected"] == "HOLD"
    assert fixture["wrong_but_plausible"] == "REVIEWER_EDIT = ALLOWED"


def test_helper_result_is_bounded_supporting_evidence() -> None:
    section = _operating_section(
        _load(OPERATING_MODEL), "Bounded role-helper delegation"
    )
    assert _helper_contract_valid(section)
    mutant = section.replace(
        "HELPER_RESULT=SUPPORTING_EVIDENCE_ONLY",
        "HELPER_RESULT=ROLE_REPORT",
        1,
    )
    assert not _helper_contract_valid(mutant)
    promoted = section.replace(
        "HELPER_RESULT_PROMOTION_TO_BUILDER_TESTER_REVIEWER_COMPLETION_OR_PASS=FORBIDDEN",
        "HELPER_RESULT_PROMOTION_TO_BUILDER_TESTER_REVIEWER_COMPLETION_OR_PASS=ALLOWED",
        1,
    )
    assert not _helper_contract_valid(promoted)


def test_helper_provenance_labels_and_enforcement_claims_stay_distinct() -> None:
    text = _load(OPERATING_MODEL)
    assert _provenance_contract_valid(text)
    mutant = text.replace(
        "AUTONOMOUS_ENFORCEMENT_NOT_PROVEN", "AUTONOMOUS_ENFORCEMENT_VERIFIED", 1
    )
    assert not _provenance_contract_valid(mutant)


def test_correction_accounting_cannot_reset_or_accept_stale_evidence() -> None:
    section = _operating_section(
        _load(OPERATING_MODEL), "Finite correction accounting"
    )
    assert _correction_contract_valid(section)
    mutant = section.replace(
        "BUDGET_RESET_BY_RENAME_OR_REVISION = FORBIDDEN",
        "BUDGET_RESET_BY_RENAME_OR_REVISION = ALLOWED",
        1,
    )
    assert not _correction_contract_valid(mutant)


def test_unknown_stop_status_blocks_writer_transfer() -> None:
    section = _operating_section(
        _load(OPERATING_MODEL), "Bounded role-helper delegation"
    )
    assert _stop_contract_valid(section)
    mutant = section.replace(
        "STOP_STATUS_UNKNOWN = HOLD_NO_TRANSFER",
        "STOP_STATUS_UNKNOWN = ALLOW_TRANSFER",
        1,
    )
    assert not _stop_contract_valid(mutant)


def test_reviewer_finding_keeps_three_dimensions_independent() -> None:
    section = _operating_section(
        _load(OPERATING_MODEL), "Canonical Reviewer finding shape"
    )
    assert _finding_contract_valid(section)
    mutant = section.replace("INTEGRATION_DISPOSITION", "SEVERITY", 1)
    assert not _finding_contract_valid(mutant)


def test_agent_loop_routes_helper_authority_to_operating_model() -> None:
    text = _load(AGENT_LOOP)
    assert _agent_loop_routes_helpers(text)
    mutant = text.replace(
        "grants no delegation authority", "grants delegation authority", 1
    )
    assert not _agent_loop_routes_helpers(mutant)


def test_report_admission_remains_supervised_static_contract_text() -> None:
    text = _load(OPERATING_MODEL)
    assert _report_admission_documented(text)
    mutant = text.replace("wrong-object", "right-object", 1)
    assert not _report_admission_documented(mutant)


def _source_provenance_contract_valid(text: str) -> bool:
    required = (
        "SOURCE_TASK_ID_PROVENANCE=INDEPENDENTLY_OBSERVED_FROM_SUPERVISED_DISPATCH_OR_RECEIPT",
        "OBSERVED_DELIVERY_ID_MUST_MATCH=SOURCE_TASK_ID",
        "PAYLOAD_ASSERTION_ROLE_MODEL_NAME_OR_MATCHING_TEXT_ALONE_ESTABLISHES_CANONICAL_SOURCE_OR_VERDICT=NO",
        "UNKNOWN_OR_MISMATCHED_SOURCE=HOLD; CANNOT_ADVANCE=YES",
        "SOURCE_IDENTITY_ASSURANCE=DOCUMENTED_SUPERVISED; NOT_CRYPTOGRAPHIC; NOT_AUTONOMOUS",
    )
    return all(item in text for item in required)


def test_report_source_provenance_uses_supervised_dispatch_identity() -> None:
    text = _load(OPERATING_MODEL)
    assert _source_provenance_contract_valid(text)
    mutant = text.replace(
        "UNKNOWN_OR_MISMATCHED_SOURCE=HOLD; CANNOT_ADVANCE=YES",
        "UNKNOWN_OR_MISMATCHED_SOURCE=ACCEPT; CANNOT_ADVANCE=NO",
        1,
    )
    assert not _source_provenance_contract_valid(mutant)


def _helper_dispatch_contract_valid(text: str) -> bool:
    required = (
        "HELPER_CONTEXT_CHANNEL=APPROVED_NATIVE_HELPER_DISPATCH_UNDER_ACTIVE_LEASE",
        "HELPER_CONTEXT_CONTENT=EXACT_ALLOWLISTED_TRACKED_CONTENT_ONLY",
        "APPROVED_DISPATCH_GRANTS_WIDER_ACCESS=NO",
        "HELPER_INITIATED_NETWORK_CONNECTOR_EXTERNAL_TOOL_OR_OTHER_EXTERNAL_TRANSMISSION=FORBIDDEN_UNLESS_EXPLICITLY_AUTHORIZED",
        "SENSITIVE_UNTRACKED_OR_OPERATIONAL_CONTENT=FORBIDDEN_UNLESS_EXPLICITLY_AUTHORIZED",
    )
    return all(item in text for item in required)


def test_helper_dispatch_context_does_not_expand_access() -> None:
    text = _load(OPERATING_MODEL)
    assert _helper_dispatch_contract_valid(text)
    mutant = text.replace(
        "APPROVED_DISPATCH_GRANTS_WIDER_ACCESS=NO",
        "APPROVED_DISPATCH_GRANTS_WIDER_ACCESS=YES",
        1,
    )
    assert not _helper_dispatch_contract_valid(mutant)


def _helper_entry_contract_valid(text: str) -> bool:
    required = (
        "HELPER_IS_ROLE_OR_AGENT_ENTRY=NO",
        "HELPER_INPUTS=ACTIVE_LEASE_EXACT_BRIEF_AND_READ_ALLOWLIST_ONLY",
        "HELPER_CANNOT_DECLARE=READY, PROMPT_READY, START_IMPLEMENTATION, START_AUDIT",
        "CANONICAL_ROLE_OR_TAKEOVER_ASSIGNMENT_REQUIRES=NORMAL_FULL_OR_DELTA_ROLE_AND_ROADMAP_ENTRY_GATES",
        "SUBAGENT_OR_TOOL_IDENTITY_ALONE_ASSIGNS_AUTHORITY=NO",
        "CANONICAL_ROLE_ASSIGNMENT_REQUIRES=EXPLICIT_ASSIGNMENT_OR_TAKEOVER, EXACT_OBJECT_AND_SCOPE, APPLICABLE_ROLE_READ_IN_AND_INDEPENDENCE_GATES, PRIOR_OWNER_CESSATION_CONFIRMED_AND_NO_CONFLICT",
    )
    return all(item in text for item in required)


def test_helper_read_in_does_not_grant_role_entry_or_readiness() -> None:
    text = _load(OPERATING_MODEL)
    assert _helper_entry_contract_valid(text)
    mutant = text.replace(
        "SUBAGENT_OR_TOOL_IDENTITY_ALONE_ASSIGNS_AUTHORITY=NO",
        "SUBAGENT_OR_TOOL_IDENTITY_ALONE_ASSIGNS_AUTHORITY=YES",
        1,
    )
    assert not _helper_entry_contract_valid(mutant)
