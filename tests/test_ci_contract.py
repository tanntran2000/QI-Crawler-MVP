"""Protect actual workflow wiring, beyond unit tests of the final gate."""

from pathlib import Path

import yaml

from scripts.ci_gate import REQUIRED_JOBS


def test_workflow_keeps_required_coverage_and_fail_closed_wiring() -> None:
    workflow = yaml.safe_load(
        (Path(__file__).resolve().parents[1] / ".github/workflows/ci.yml").read_text()
    )
    jobs = workflow["jobs"]
    gate = jobs["required-ci-gate"]
    assert set(gate["needs"]) == set(REQUIRED_JOBS)
    assert gate["if"] == "${{ always() }}"
    for name in REQUIRED_JOBS:
        job = jobs[name]
        assert job["timeout-minutes"] > 0
        assert "if" not in job
        assert not job.get("continue-on-error")
        assert all(not step.get("continue-on-error") for step in job["steps"])
        if name != "code-quality":
            commands = "\n".join(step.get("run", "") for step in job["steps"])
            assert "--ci-collection-baseline" in commands
            assert "--collect-only" in commands
            assert "--junitxml" in commands
            assert "pip freeze" in commands
            assert "git rev-parse HEAD" in commands
            assert any(step.get("uses", "").startswith("actions/upload-artifact@")
                       and "always()" in step.get("if", "") for step in job["steps"])
    assert "scripts/ci_gate.py" in gate["steps"][-1]["run"]
    assert gate["steps"][-1]["env"]["CI_NEEDS"] == "${{ toJSON(needs) }}"
