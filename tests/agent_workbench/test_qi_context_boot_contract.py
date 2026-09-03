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


def _scope_path_set_is_valid(paths: list[str]) -> bool:
    forbidden_prefixes = ("src/qi_crawler/", "alembic/")
    return not any(
        path.replace("\\", "/").lower().startswith(prefix)
        for path in paths
        for prefix in forbidden_prefixes
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


def test_product_path_leakage_mutant_is_rejected() -> None:
    allowed = [
        "plugins/qi-agent-workbench/skills/qi-context-boot/SKILL.md",
        "tests/agent_workbench/test_qi_context_boot_contract.py",
    ]
    leaked = allowed + ["src/qi_crawler/gui.py", "alembic/versions/0021_bad.py"]
    assert _scope_path_set_is_valid(allowed)
    assert not _scope_path_set_is_valid(leaked)


def test_current_product_scope_contract_is_complete() -> None:
    skill = _skill_text()
    assert "PRODUCT_PATH_LEAKAGE = ENTRY_HOLD" in skill
    assert "FORBIDDEN_PRODUCT_PATHS = src/qi_crawler/...; alembic/..." in skill


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
