from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PLUGIN_ROOT = REPO_ROOT / "plugins" / "qi-agent-workbench"
SKILL_PATH = PLUGIN_ROOT / "skills" / "qi-context-boot" / "SKILL.md"
CONTEXT_MAP_PATH = PLUGIN_ROOT / "references" / "context-map.md"
MANIFEST_PATH = PLUGIN_ROOT / ".codex-plugin" / "plugin.json"
EVAL_ROOT = PLUGIN_ROOT / "evals"


def _skill_text() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


def _fixture(name: str) -> dict[str, object]:
    return json.loads((EVAL_ROOT / name).read_text(encoding="utf-8"))


def _declared_boot_states(skill: str) -> list[set[str]]:
    declarations = re.findall(
        r"^\s*(?:BOOT_RESULT|READY_STATE|BOOT_REPORT_STATES)\s*=\s*(.+?)\s*$",
        skill,
        flags=re.MULTILINE,
    )
    return [{part.strip() for part in declaration.split("|")} for declaration in declarations]


def _boot_state_contract_is_valid(skill: str) -> bool:
    declarations = _declared_boot_states(skill)
    return (
        declarations
        and all(states == {"READY", "ENTRY_HOLD"} for states in declarations)
        and "NEEDS_REPLAN is not a Boot state" in skill
    )


def _role_contract_is_valid(skill: str) -> bool:
    fallback = re.compile(
        r"(?:codex|gpt|model|runtime).*?(?:->|means|select|assign).*?builder_single_writer",
        re.IGNORECASE,
    )
    return (
        "ROLE > MODEL NAME" in skill
        and "MODEL_NAME != AGENT_ROLE" in skill
        and not any(fallback.search(line) for line in skill.splitlines())
    )


def _read_only_contract_is_valid(skill: str) -> bool:
    positive_grant = re.compile(
        r"boot\s+(?:may|can)\s+(?:edit|commit|push|merge|release)", re.IGNORECASE
    )
    return (
        "QI_CONTEXT_BOOT = READ_ONLY" in skill
        and "WHAT_I_AM_ALLOWED_TO_DO" in skill
        and "WHAT_I_AM_NOT_ALLOWED_TO_DO" in skill
        and "Boot may not edit, commit, push, merge, or release" in skill
        and not positive_grant.search(skill)
    )


def _contract_value(text: str, key: str) -> str | None:
    match = re.search(rf"^{re.escape(key)}\s*=\s*(.+?)\s*$", text, re.MULTILINE)
    return match.group(1) if match else None


def _head_reconciliation_contract_is_valid(skill: str) -> bool:
    expected = {
        "EXPLAINED_GOVERNED_DIVERGENCE": "RECONCILE",
        "UNEXPLAINED_MATERIAL_DIVERGENCE": "ENTRY_HOLD",
        "DOCS_ONLY_AUTHORITY_SCOPE_ACCEPTANCE_CHANGE": "ENTRY_HOLD",
        "SOURCE_CHANGE_IN_APPROVED_SCOPE_WITH_EXACT_LINEAGE": "RECONCILE_ELIGIBLE",
        "SOURCE_CHANGE_OUTSIDE_SCOPE_OR_UNEXPLAINED": "ENTRY_HOLD",
    }
    return (
        "SHA_DIFFERENCE != AUTOMATIC_HOLD" in skill
        and all(_contract_value(skill, key) == value for key, value in expected.items())
        and "DOCS_ONLY = AUTOMATICALLY_SAFE" not in skill
    )


def _read_write_scope_contract_is_valid(skill: str) -> bool:
    return (
        _contract_value(skill, "BOOT_WRITE_SCOPE") == "NONE"
        and _contract_value(skill, "IMPLEMENTATION_WRITE_SCOPE")
        == "APPROVED_WORK_ORDER_ONLY"
        and _contract_value(skill, "BOOT_PRODUCT_PATH_READ")
        == "ALLOWED_WHEN_RELEVANT"
        and _contract_value(skill, "BOOT_PRODUCT_PATH_WRITE") == "FORBIDDEN"
        and "READING_PRODUCT_CODE != EDITING_PRODUCT_CODE" in skill
    )


def test_invalid_boot_state_mutant_is_rejected() -> None:
    case = _fixture("stale-current.json")
    skill = _skill_text()

    assert {"id", "scenario", "wrong_but_plausible", "expected"} <= case.keys()
    assert case["CURRENT_HEAD"] != case["LIVE_GIT_HEAD"]
    assert case["wrong_but_plausible"] == "CURRENT_ONLY -> READY"
    assert case["expected"] == "ENTRY_HOLD"
    mutant = skill.replace(
        "BOOT_RESULT = READY | ENTRY_HOLD",
        "BOOT_RESULT = READY | ENTRY_HOLD | NEEDS_REPLAN",
    )
    assert not _boot_state_contract_is_valid(mutant)


def test_current_boot_state_contract_is_complete() -> None:
    assert _boot_state_contract_is_valid(_skill_text())


def test_model_name_fallback_mutant_is_rejected() -> None:
    case = _fixture("model-name-role.json")
    skill = _skill_text()

    assert {"id", "scenario", "wrong_but_plausible", "expected"} <= case.keys()
    assert case["RUNTIME_MODEL"] == "Codex"
    assert case["wrong_but_plausible"] == "Codex -> BUILDER_SINGLE_WRITER"
    assert case["expected"] == "ENTRY_HOLD"
    mutant = skill + "\nFallback: Codex -> BUILDER_SINGLE_WRITER\n"
    assert not _role_contract_is_valid(mutant)


def test_current_role_contract_is_complete() -> None:
    assert _role_contract_is_valid(_skill_text())
    assert "Human explicit assignment -> approved Work Order -> governed CURRENT" in _skill_text()


def test_read_only_contradiction_mutant_is_rejected() -> None:
    skill = _skill_text()

    mutant = skill + "\nBoot may commit changes.\n"
    assert not _read_only_contract_is_valid(mutant)


def test_current_read_only_contract_is_complete() -> None:
    assert _read_only_contract_is_valid(_skill_text())


def test_boot_sha_01_governed_successor_is_reconcilable() -> None:
    assert _head_reconciliation_contract_is_valid(_skill_text())
    assert _contract_value(_skill_text(), "EXPLAINED_GOVERNED_DIVERGENCE") == "RECONCILE"


def test_boot_sha_02_docs_authority_widening_holds() -> None:
    skill = _skill_text()
    mutant = skill.replace(
        "DOCS_ONLY_AUTHORITY_SCOPE_ACCEPTANCE_CHANGE = ENTRY_HOLD",
        "DOCS_ONLY_AUTHORITY_SCOPE_ACCEPTANCE_CHANGE = RECONCILE",
    )
    assert _contract_value(skill, "DOCS_ONLY_AUTHORITY_SCOPE_ACCEPTANCE_CHANGE") == "ENTRY_HOLD"
    assert not _head_reconciliation_contract_is_valid(mutant)


def test_boot_sha_03_approved_source_lineage_is_reconcilable() -> None:
    assert (
        _contract_value(_skill_text(), "SOURCE_CHANGE_IN_APPROVED_SCOPE_WITH_EXACT_LINEAGE")
        == "RECONCILE_ELIGIBLE"
    )


def test_boot_sha_04_unexplained_source_change_holds() -> None:
    assert (
        _contract_value(_skill_text(), "SOURCE_CHANGE_OUTSIDE_SCOPE_OR_UNEXPLAINED")
        == "ENTRY_HOLD"
    )


def test_boot_scope_01_relevant_product_read_is_allowed() -> None:
    assert _read_write_scope_contract_is_valid(_skill_text())
    assert _contract_value(_skill_text(), "BOOT_PRODUCT_PATH_READ") == "ALLOWED_WHEN_RELEVANT"


def test_boot_scope_02_product_write_is_forbidden() -> None:
    skill = _skill_text()
    mutant = skill.replace("BOOT_PRODUCT_PATH_WRITE = FORBIDDEN", "BOOT_PRODUCT_PATH_WRITE = ALLOWED")
    assert _contract_value(skill, "BOOT_PRODUCT_PATH_WRITE") == "FORBIDDEN"
    assert not _read_write_scope_contract_is_valid(mutant)


def test_health_and_foreign_context_boundaries_are_explicit() -> None:
    skill = _skill_text()
    for token in (
        "DISCOVERED != CONFIGURED != CALLABLE != SMOKE_VERIFIED",
        "CONFIG_SNAPSHOT != CURRENT_SESSION_CAPABILITY",
        "FOREIGN_CONTEXT = ADVISORY_ONLY",
        "FOREIGN_CONTEXT != QI_AUTHORITY",
        "FOREIGN_MEMORY != CURRENT",
        "FOREIGN_MEMORY != WORK_ORDER",
        "INSTRUCTION_CONFLICT = ENTRY_HOLD",
    ):
        assert token in skill


def test_plugin_manifest_and_context_map_contract() -> None:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    context_map = CONTEXT_MAP_PATH.read_text(encoding="utf-8")

    assert manifest["name"] == "qi-agent-workbench"
    assert manifest["skills"] == "./skills/"
    assert "autonomous" not in json.dumps(manifest).lower()
    for source in (
        "MEMORY_INDEX",
        "MASTER_ROADMAP",
        "MASTER_ROADMAP_DELTA",
        "CURRENT",
        "live Git/GitHub",
        "READY | ENTRY_HOLD",
    ):
        assert source in context_map


def test_role_resolution_uses_governed_chain() -> None:
    skill = _skill_text()

    assert "Human explicit assignment -> approved Work Order -> governed CURRENT" in skill
    assert "ROLE > MODEL NAME" in skill
