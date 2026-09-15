"""The merge gate must never turn an incomplete dependency graph green."""

import json
import subprocess
import sys
from pathlib import Path

import pytest

GATE = Path(__file__).resolve().parents[1] / "scripts" / "ci_gate.py"
JOBS = ("code-quality", "tests-ubuntu-312", "tests-windows-312", "compatibility-ubuntu-311")


def run_gate(needs: object) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(GATE), json.dumps(needs)],
        capture_output=True, text=True, check=False,
    )


def test_complete_success_graph_passes() -> None:
    result = run_gate({job: {"result": "success"} for job in JOBS})
    assert result.returncode == 0, result.stderr
    assert "CI_GATE=PASS" in result.stdout


@pytest.mark.parametrize("outcome", ["failure", "cancelled", "skipped", "unknown", None])
def test_each_non_success_result_fails_closed(outcome: str | None) -> None:
    for job in JOBS:
        needs = {name: {"result": "success"} for name in JOBS}
        needs[job] = {"result": outcome}
        result = run_gate(needs)
        assert result.returncode == 1
        assert job in result.stdout


@pytest.mark.parametrize("needs", [{}, [], None, {job: {} for job in JOBS}])
def test_missing_or_malformed_graph_fails_closed(needs: object) -> None:
    assert run_gate(needs).returncode == 1
