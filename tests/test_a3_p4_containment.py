"""Real Windows route containment controls for the F5 sandbox."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
HARNESS = REPO / "tests" / "a3_p4_characterize.ps1"
PROBE = REPO / "tools" / "release" / "a3_probe_windows.ps1"


def test_exe_cmd_and_shortcut_descendants_remain_in_job(tmp_path: Path) -> None:
    if sys.platform != "win32" or not shutil.which("powershell.exe"):
        pytest.skip("Windows PowerShell is required")
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-File", str(HARNESS),
         "-Root", str(tmp_path)],
        cwd=REPO, capture_output=True, text=True, timeout=90, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    cases = json.loads(result.stdout)
    assert [case["route"] for case in cases] == ["EXE", "CMD", "SHORTCUT", "GRANDCHILD"]
    for case in cases:
        assert "error" not in case, case
        assert case["child_alive"], case
        assert case["job_active_after_parent_exit"] > 0, case
        assert case["false_zero_rejected_while_child_alive"], case
        assert case["child_in_job"], case
        assert case["native_snapshot_status"] == "SUCCESS", case
        tree = case["native_tree"]
        if tree["enumeration_status"] == "PARTIAL":
            assert tree["descendant_discovery_status"] == "UNRESOLVED", case
            assert tree["unresolved_descendants"], case
            assert all(edge["reason"] == "PROCESS_CREATION_IDENTITY_UNAVAILABLE"
                       for edge in tree["unresolved_descendants"]), case
        else:
            assert tree["enumeration_status"] == "SUCCESS", case
            assert tree["descendant_discovery_status"] == "COMPLETE", case
        assert not case["native_lineage_contains_child"], case
        assert case["job_zero_after_termination"], case
        assert not case["breakaway_ok_enabled"], case
        assert not case["silent_breakaway_ok_enabled"], case


def test_canonical_route_keeps_process_identity_until_p4_receipt() -> None:
    source = PROBE.read_text(encoding="utf-8")
    route = source.split("function Invoke-F5CanonicalRoute {", 1)[1].split(
        "if ($f5OnlyRoute)", 1
    )[0]
    identity = route.index("$routeIdentity=Get-A3ContainedProcessIdentity -Session $routeJob")
    wait = route.index("$routeCompletion=Wait-A3ContainedRouteZero", identity)
    tree = route.index("$routeTreeEvidence=Get-ProcessTreeEvidence @($routeCompletion.launcher_pid)", wait)
    receipt = route.index("$routeReceipt=[ordered]@", tree)
    close = route.index("Close-A3ContainedProcess -Session $routeJob", receipt)
    assert identity < wait < tree < receipt < close
    assert "$script:a3AuthoritativeRootIdentity=$routeIdentity" in route
    assert "launcher_identity=$routeIdentity" in route
