"""Exercise evidence collection through a real nested pytest process."""

import json
import os
import subprocess
import sys
from pathlib import Path


def invoke(root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(Path(__file__).resolve().parents[1] / "scripts")
    environment.pop("PYTEST_ADDOPTS", None)
    return subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "-p", "ci_test_evidence", "-p", "no:cacheprovider",
         *arguments], cwd=root, env=environment, capture_output=True, text=True, check=False,
    )


def test_evidence_accounts_for_execution_and_detects_lost_collection(tmp_path: Path) -> None:
    source = tmp_path / "test_sample.py"
    source.write_text("import pytest\ndef test_ok(): pass\ndef test_skip(): pytest.skip('platform')\n")
    baseline = tmp_path / "baseline"
    result = invoke(tmp_path, "--collect-only", "--ci-evidence-dir", str(baseline))
    assert result.returncode == 0, result.stderr
    baseline_file = baseline / "collection.json"
    run = tmp_path / "run"
    result = invoke(tmp_path, "--ci-evidence-dir", str(run), "--ci-collection-baseline", str(baseline_file))
    assert result.returncode == 0, result.stdout + result.stderr
    evidence = json.loads((run / "result.json").read_text())
    assert evidence["collected"] == 2
    assert evidence["outcomes"] == {"passed": 1, "skipped": 1}
    source.write_text("def test_ok(): pass\n")
    result = invoke(tmp_path, "--ci-evidence-dir", str(tmp_path / "lost"),
                    "--ci-collection-baseline", str(baseline_file))
    assert result.returncode != 0
    assert "CI_COLLECTION_MISMATCH" in result.stdout + result.stderr


def test_failure_is_retained_as_failed_evidence(tmp_path: Path) -> None:
    (tmp_path / "test_sample.py").write_text("def test_bad(): assert False\n")
    result = invoke(tmp_path, "--ci-evidence-dir", str(tmp_path / "evidence"))
    assert result.returncode == 1
    evidence = json.loads((tmp_path / "evidence" / "result.json").read_text())
    assert evidence["outcomes"] == {"failed": 1}
    assert evidence["exit_status"] == 1
