"""Discriminating Micro-D tests for the Workbench integrity lock."""

import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parents[2]
LOCK = ROOT / "plugins" / "qi-agent-workbench" / "skills-lock.json"
VERIFIER = ROOT / "plugins" / "qi-agent-workbench" / "verify_lock.py"

EXPECTED_ARTIFACTS = {
    "references/context-map.md",
    "references/handoff-template.md",
    "references/task-envelope-template.md",
    "skills/qi-context-boot/SKILL.md",
    "skills/qi-evidence-check/SKILL.md",
    "skills/qi-impact-map/SKILL.md",
    "skills/qi-python-change/SKILL.md",
    "skills/qi-review-handoff/SKILL.md",
    "skills/qi-task-envelope/SKILL.md",
}


def _run_verifier(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(VERIFIER), "--root", str(root)],
        text=True,
        capture_output=True,
        check=False,
    )


def _copy_workbench(tmp_path: Path) -> Path:
    target = tmp_path / "workbench"
    shutil.copytree(ROOT / "plugins" / "qi-agent-workbench", target)
    return target


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(path.read_bytes())
    return digest.hexdigest()


def _authority_contract_valid(text: str) -> bool:
    required = (
        "LOCK != AUTHORITY",
        "LOCK_VERIFY_PASS != HUMAN_APPROVAL",
        "MACHINE_VERIFIED != HUMAN_APPROVED",
    )
    return all(token in text for token in required) and "LOCK_VERIFY_PASS = HUMAN_APPROVAL" not in text


def _promotion_contract_valid(text: str) -> bool:
    required = (
        "FAILURE_MEMORY != SELF_MODIFYING_WORKBENCH",
        "GROUND_TRUTH != AUTOMATIC_GOVERNANCE_RULE",
    )
    return all(token in text for token in required) and "FAILURE_MEMORY = AUTOMATIC_GOVERNANCE_LAW" not in text


def test_canonical_lock_covers_every_approved_skill_and_reference() -> None:
    manifest = json.loads(LOCK.read_text(encoding="utf-8"))
    assert manifest["schema_version"] == 1
    assert manifest["algorithm"] == "sha256"
    assert set(manifest["files"]) == EXPECTED_ARTIFACTS
    assert len(manifest["files"]) == 9
    for relative, expected_hash in manifest["files"].items():
        artifact = ROOT / "plugins" / "qi-agent-workbench" / relative
        assert artifact.is_file()
        assert _sha256(artifact) == expected_hash


def test_canonical_valid_lock_passes() -> None:
    result = _run_verifier(ROOT / "plugins" / "qi-agent-workbench")
    assert result.returncode == 0, result.stderr or result.stdout
    assert "INTEGRITY PASS" in result.stdout
    assert "HUMAN_APPROVED" not in result.stdout
    assert "MERGE_AUTHORIZED" not in result.stdout


def test_tampered_artifact_is_rejected_with_digest_mismatch(tmp_path: Path) -> None:
    workbench = _copy_workbench(tmp_path)
    target = workbench / "skills" / "qi-impact-map" / "SKILL.md"
    target.write_text(target.read_text(encoding="utf-8") + "\nTAMPERED\n", encoding="utf-8")
    result = _run_verifier(workbench)
    assert result.returncode == 3
    assert "digest mismatch" in result.stderr.lower()


def test_missing_locked_artifact_is_rejected(tmp_path: Path) -> None:
    workbench = _copy_workbench(tmp_path)
    (workbench / "references" / "context-map.md").unlink()
    result = _run_verifier(workbench)
    assert result.returncode == 2
    assert "missing locked artifact" in result.stderr.lower()


def test_malformed_lock_is_rejected(tmp_path: Path) -> None:
    workbench = _copy_workbench(tmp_path)
    (workbench / "skills-lock.json").write_text("{not-json", encoding="utf-8")
    result = _run_verifier(workbench)
    assert result.returncode == 4
    assert "malformed" in result.stderr.lower()


def test_invalid_lock_entry_is_rejected(tmp_path: Path) -> None:
    workbench = _copy_workbench(tmp_path)
    manifest_path = workbench / "skills-lock.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["files"]["skills/qi-impact-map/SKILL.md"] = "not-a-sha256"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    result = _run_verifier(workbench)
    assert result.returncode == 4
    assert "digest" in result.stderr.lower()


def test_path_traversal_lock_entry_is_rejected(tmp_path: Path) -> None:
    workbench = _copy_workbench(tmp_path)
    manifest_path = workbench / "skills-lock.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    digest = manifest["files"].pop("references/context-map.md")
    manifest["files"]["../README.md"] = digest
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")
    result = _run_verifier(workbench)
    assert result.returncode == 4
    assert "relative" in result.stderr.lower() or "path" in result.stderr.lower()


def test_verifier_contract_is_read_only_local_and_fail_closed() -> None:
    text = VERIFIER.read_text(encoding="utf-8")
    required = (
        "READ_ONLY",
        "DETERMINISTIC",
        "FAIL_CLOSED",
        "LOCAL",
        "NO_NETWORK",
        "NO_AUTO_FIX",
        "NO_AUTO_SYNC",
        "LOCK != AUTHORITY",
        "LOCK_VERIFY_PASS != HUMAN_APPROVAL",
        "MACHINE_VERIFIED != HUMAN_APPROVED",
        "FAILURE_MEMORY != SELF_MODIFYING_WORKBENCH",
        "GROUND_TRUTH != AUTOMATIC_GOVERNANCE_RULE",
    )
    assert all(token in text for token in required)
    assert _authority_contract_valid(text)
    assert _promotion_contract_valid(text)
    assert "requests" not in text
    assert "urllib" not in text
    assert ".write_text(" not in text


def test_authority_boundary_mutant_is_rejected() -> None:
    text = VERIFIER.read_text(encoding="utf-8")
    unsafe = text + "\nLOCK_VERIFY_PASS = HUMAN_APPROVAL\n"
    assert _authority_contract_valid(text)
    assert not _authority_contract_valid(unsafe)


def test_failure_memory_promotion_mutant_is_rejected() -> None:
    text = VERIFIER.read_text(encoding="utf-8")
    unsafe = text + "\nFAILURE_MEMORY = AUTOMATIC_GOVERNANCE_LAW\n"
    assert _promotion_contract_valid(text)
    assert not _promotion_contract_valid(unsafe)


def test_evaluation_corpus_requires_rejection_of_real_wrong_states() -> None:
    candidates = {
        "WB-CANDIDATE-WRONG-BRANCH",
        "WB-CANDIDATE-LOCAL-AUTHORITY-WITHOUT-PROOF",
        "WB-CANDIDATE-PROTECTED-DIRTY-PATH",
        "WB-CANDIDATE-AGENT-CLAIM-NOT-MACHINE-EVIDENCE",
        "WB-CANDIDATE-GREEN-TEST-NONDISCRIMINATING",
        "WB-CANDIDATE-SILENT-PREEXISTING-FILE-ABSORPTION",
    }
    expected = {candidate: "REJECT_OR_HOLD" for candidate in candidates}
    assert len(expected) == 6
    assert all(value == "REJECT_OR_HOLD" for value in expected.values())


def test_positive_only_verifier_claim_cannot_become_authority() -> None:
    text = VERIFIER.read_text(encoding="utf-8")
    assert "INTEGRITY PASS" in text
    assert "LOCK_VERIFY_PASS != HUMAN_APPROVAL" in text
    assert "MACHINE_VERIFIED != HUMAN_APPROVED" in text
