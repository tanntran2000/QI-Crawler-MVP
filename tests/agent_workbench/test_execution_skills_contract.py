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


def test_review_skill_requires_independent_no_edit_handoff() -> None:
    assert _review_contract_valid(_load(SKILLS / "qi-review-handoff" / "SKILL.md"))


def test_review_mutant_cannot_authorize_reviewer_edits() -> None:
    mutant = _load(SKILLS / "qi-review-handoff" / "SKILL.md") + "\nReviewer may edit audited output\n"
    assert not _review_contract_valid(mutant)


def test_handoff_template_contains_exact_object_and_terminal_sentinel() -> None:
    fields = _template_fields(_load(TEMPLATE))
    required = {
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
