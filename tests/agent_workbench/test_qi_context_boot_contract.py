from __future__ import annotations

import json
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


def test_stale_current_counterexample_requires_entry_hold() -> None:
    case = _fixture("stale-current.json")
    skill = _skill_text()

    assert case["CURRENT_HEAD"] != case["LIVE_GIT_HEAD"]
    assert case["present_but_wrong"] == "CURRENT_ONLY -> READY"
    assert case["required"] == "ENTRY_HOLD"
    assert "CURRENT_HEAD != LIVE_GIT_HEAD" in skill
    assert "STALE_CURRENT = ENTRY_HOLD" in skill
    assert "CURRENT_ONLY = ENTRY_HOLD" in skill


def test_model_name_never_assigns_role() -> None:
    case = _fixture("model-name-role.json")
    skill = _skill_text()

    assert case["RUNTIME_MODEL"] == "Codex"
    assert case["present_but_wrong"] == "Codex -> BUILDER_SINGLE_WRITER"
    assert case["required"] == "ENTRY_HOLD"
    assert "MODEL_NAME != AGENT_ROLE" in skill
    assert "RUNTIME/MODEL/VENDOR/TOOL" in skill
    assert "MODEL_NAME_ROLE = ENTRY_HOLD" in skill


def test_boot_is_read_only_and_not_implementation_authorization() -> None:
    skill = _skill_text()

    assert "QI_CONTEXT_BOOT = READ_ONLY" in skill
    assert "BOOT_RESULT = READY | ENTRY_HOLD" in skill
    assert "CONTEXT_ENTRY_READY" in skill
    assert "IMPLEMENTATION_AUTHORIZED = NO" in skill
    for operation in ("edit", "commit", "push", "merge", "release"):
        assert operation in skill.lower()
    assert "Spine mutation" in skill
    assert "role self-assignment" in skill


def test_product_path_leakage_is_entry_hold() -> None:
    skill = _skill_text()

    assert "PRODUCT_PATH_LEAKAGE = ENTRY_HOLD" in skill
    for forbidden in ("src/qi_crawler/", "alembic/", "GUI", "API"):
        assert forbidden in skill


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

    assert (
        "Human explicit assignment -> approved Work Order -> governed CURRENT"
        in skill
    )
    assert "MODEL_NAME != AGENT_ROLE" in skill
    assert "model/tool/runtime/vendor" in skill.lower()
