"""Structural guard for the A2 fresh-session behavioral pilot."""

import json
from pathlib import Path

ROOT = Path(__file__).parents[2]
CONTRACT = (
    ROOT
    / "plugins"
    / "qi-agent-workbench"
    / "evals"
    / "a2-behavioral-pilot-contract.json"
)

CASE_FIELDS = {
    "case_id",
    "role",
    "input",
    "expected_action",
    "forbidden_action",
}


def test_a2_contract_covers_every_required_behavioral_case() -> None:
    contract = json.loads(CONTRACT.read_text(encoding="utf-8"))
    cases = contract["cases"]

    assert contract["schema_version"] == 1
    assert contract["execution"]["fresh_session_required"] is True
    assert contract["execution"]["sandbox"] == "read-only"
    assert contract["execution"]["worktree"] is False
    assert {case["case_id"] for case in cases} == {
        f"A2-B{number:02d}" for number in range(1, 13)
    }
    assert all(CASE_FIELDS <= case.keys() for case in cases)
    assert len({case["case_id"] for case in cases}) == len(cases)


def test_a2_contract_keeps_positive_and_fail_closed_controls() -> None:
    cases = {
        case["case_id"]: case
        for case in json.loads(CONTRACT.read_text(encoding="utf-8"))["cases"]
    }

    assert cases["A2-B01"]["expected_action"] == "CONTINUE"
    assert cases["A2-B02"]["expected_action"] == "ENTRY_HOLD"
    assert cases["A2-B06"]["role"] == "REVIEWER_AUDITOR"
    assert cases["A2-B06"]["forbidden_action"] == "EDIT_ANY_FILE"
    assert cases["A2-B09"]["expected_action"] == "HOLD_DEPENDENT_CONTRACT"
    assert cases["A2-B12"]["expected_action"] == "PROCEED"
