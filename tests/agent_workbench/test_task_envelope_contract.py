from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "qi-agent-workbench"
SKILL_PATH = PLUGIN_ROOT / "skills" / "qi-task-envelope" / "SKILL.md"
TEMPLATE_PATH = PLUGIN_ROOT / "references" / "task-envelope-template.md"
CONTEXT_MAP_PATH = PLUGIN_ROOT / "references" / "context-map.md"
EVAL_ROOT = PLUGIN_ROOT / "evals"

EXPECTED_FIELDS = {
    "MISSION",
    "ASSIGNED_ROLE",
    "BASELINE",
    "SCOPE",
    "EXCLUSIONS",
    "INVARIANTS",
    "ACCEPTANCE",
    "REQUIRED_SKILLS_TOOLS",
    "VERIFICATION",
    "NEXT_AUTHORITY",
}
EXPECTED_FIELD_ORDER = [
    "MISSION",
    "ASSIGNED_ROLE",
    "BASELINE",
    "SCOPE",
    "EXCLUSIONS",
    "INVARIANTS",
    "ACCEPTANCE",
    "REQUIRED_SKILLS_TOOLS",
    "VERIFICATION",
    "NEXT_AUTHORITY",
]


def _skill_text() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def _template_text() -> str:
    return TEMPLATE_PATH.read_text(encoding="utf-8")


def _context_map_text() -> str:
    return CONTEXT_MAP_PATH.read_text(encoding="utf-8")


def _fixture(name: str) -> dict[str, object]:
    return json.loads((EVAL_ROOT / name).read_text(encoding="utf-8"))


def _declared_skill_fields(skill: str) -> set[str]:
    match = re.search(r"^TASK_ENVELOPE_FIELDS\s*=\s*(.+?)\s*$", skill, re.MULTILINE)
    if not match:
        return set()
    return {field.strip() for field in match.group(1).split(",") if field.strip()}


def _template_fields(template: str) -> list[str]:
    block = template.split("TASK_ENVELOPE", 1)[-1]
    fields: list[str] = []
    for line in block.splitlines():
        field = line.strip().strip("`").split("=", 1)[0].strip()
        if field in EXPECTED_FIELDS:
            fields.append(field)
    return fields


def _scope_contract_is_valid(skill: str) -> bool:
    contradictory = re.compile(
        r"(?:widen|expand).*scope.*(?:ready|allowed)|ENVELOPE_SCOPE_MISMATCH\s*=\s*READY",
        re.IGNORECASE,
    )
    return (
        "TASK_ENVELOPE != WORK_ORDER" in skill
        and "ENVELOPE_SCOPE_MISMATCH = ENTRY_HOLD" in skill
        and "router never grants edit scope" in skill.lower()
        and not contradictory.search(skill)
    )


def _migration_route_is_valid(skill: str) -> bool:
    route = re.search(r"^migration_schema\s*→\s*(.+)$", skill, re.MULTILINE)
    if not route:
        route = re.search(r"^migration_schema\s*->\s*(.+)$", skill, re.MULTILINE)
    if not route:
        return False
    route_text = route.group(1)
    required = (
        "qi-context-boot",
        "qi-impact-map",
        "canonical migration/data-safety contracts",
        "qi-evidence-check",
        "qi-review-handoff",
    )
    return all(token in route_text for token in required)


def _external_route_is_valid(skill: str) -> bool:
    router_lines = [line for line in skill.splitlines() if "→" in line or "->" in line]
    return (
        "NO_EXTERNAL_MCP_AUTOMATION = ENTRY_HOLD" in skill
        and not any(
            re.search(r"(?:external|mcp|automation)", line, re.IGNORECASE)
            for line in router_lines
        )
    )


def _mismatch_contract_is_valid(skill: str) -> bool:
    contradictory = re.search(
        r"ROLE_BASELINE_SCOPE_AUTHORITY_MISMATCH\s*=\s*(?!ENTRY_HOLD\b)\S+",
        skill,
    )
    return "ROLE_BASELINE_SCOPE_AUTHORITY_MISMATCH = ENTRY_HOLD" in skill and not contradictory


def test_exact_task_envelope_fields_reject_extra_field_mutant() -> None:
    skill = _skill_text()
    template = _template_text()
    mutant = skill.replace(
        "TASK_ENVELOPE_FIELDS = ",
        "TASK_ENVELOPE_FIELDS = EDIT_SCOPE, ",
    )

    assert _template_fields(template) == EXPECTED_FIELD_ORDER
    assert _declared_skill_fields(mutant) != EXPECTED_FIELDS
    assert _declared_skill_fields(skill) == EXPECTED_FIELDS


def test_scope_widening_mutant_is_rejected() -> None:
    fixture = _fixture("envelope-scope-widening.json")
    skill = _skill_text()
    mutant = skill + "\nEnvelope may widen scope and remain READY.\n"

    assert fixture["wrong_but_plausible"] == "WIDENED_SCOPE -> READY"
    assert fixture["expected"] == "ENTRY_HOLD"
    assert not _scope_contract_is_valid(mutant)
    assert _scope_contract_is_valid(skill)


def test_migration_generic_route_mutant_is_rejected() -> None:
    fixture = _fixture("migration-routing.json")
    skill = _skill_text()
    mutant = re.sub(
        r"canonical migration/data-safety contracts",
        "qi-python-change",
        skill,
        count=1,
    )

    assert fixture["task_family"] == "migration_schema"
    assert fixture["wrong_but_plausible"] == "generic Python route -> READY"
    assert not _migration_route_is_valid(mutant)
    assert _migration_route_is_valid(skill)


def test_external_route_mutant_is_rejected() -> None:
    skill = _skill_text()
    mutant = skill.replace(
        "migration_schema →",
        "migration_schema → external/MCP automation +",
    )

    assert not _external_route_is_valid(mutant)
    assert _external_route_is_valid(skill)


def test_role_baseline_scope_authority_mismatch_is_hold() -> None:
    skill = _skill_text()
    mutant = skill.replace(
        "ROLE_BASELINE_SCOPE_AUTHORITY_MISMATCH = ENTRY_HOLD",
        "ROLE_BASELINE_SCOPE_AUTHORITY_MISMATCH = READY",
    )

    assert not _mismatch_contract_is_valid(mutant)
    assert _mismatch_contract_is_valid(skill)


def test_context_map_routes_task_envelope_without_granting_authority() -> None:
    context_map = _context_map_text()

    assert "qi-task-envelope" in context_map
    assert "TASK_ENVELOPE" in context_map
    assert "subordinate" in context_map.lower()
