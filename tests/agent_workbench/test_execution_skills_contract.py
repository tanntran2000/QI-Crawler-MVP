"""Discriminating contracts for the Micro-C execution and review skills."""

import json
from pathlib import Path

ROOT = Path(__file__).parents[2]
SKILLS = ROOT / "plugins" / "qi-agent-workbench" / "skills"
EVALS = ROOT / "plugins" / "qi-agent-workbench" / "evals"
TEMPLATE = (
    ROOT / "plugins" / "qi-agent-workbench" / "references" / "handoff-template.md"
)


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
        headers = [i for i, line in enumerate(lines) if line == "REPORT_METADATA = REQUIRED"]
        bindings = [i for i, line in enumerate(lines) if line.startswith("REPORT_ADMISSION_CONTRACT = ")]
        if len(headers) != 1 or len(bindings) != 1 or bindings[0] <= headers[0]:
            return False
        keys = [
            line.split("=", 1)[0].strip()
            for line in lines[headers[0] + 1 : bindings[0]]
            if "=" in line
        ]
        return keys == list(expected_keys) and lines[bindings[0]] == admission_line

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
    }
    rejected = {name: not metadata_contract_valid(mutant) for name, mutant in mutants.items()}

    assert metadata_contract_valid(template)
    assert rejected == {name: True for name in mutants}


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
