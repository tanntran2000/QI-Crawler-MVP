"""Native, non-admin lineage controls for the sandbox F5 observer."""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
NATIVE = REPO / "tools" / "release" / "a3_native_lineage.ps1"
PROBE = REPO / "tools" / "release" / "a3_probe_windows.ps1"
JOB_HELPER = REPO / "tools" / "release" / "a3_job_object.ps1"


def _ps(path: Path) -> str:
    return "'" + str(path).replace("'", "''") + "'"


def _run(script: str) -> subprocess.CompletedProcess[str]:
    if sys.platform != "win32" or not shutil.which("powershell.exe"):
        pytest.skip("Windows PowerShell is required")
    return subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", script],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )


def test_native_snapshot_reads_own_pid_and_ppid_without_cim() -> None:
    result = _run(
        f"$ErrorActionPreference='Stop'; . {_ps(NATIVE)}; "
        "$snap=Get-A3NativeProcessSnapshot; "
        "$own=@($snap.processes | Where-Object { $_.pid -eq $PID }); "
        "[pscustomobject]@{status=$snap.status;count=$own.Count;"
        "pid=$own[0].pid;ppid=$own[0].ppid;"
        "source=$own[0].evidence_source;metadata=$own[0].metadata_status} "
        "| ConvertTo-Json -Compress"
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    assert payload["status"] == "SUCCESS"
    assert payload["count"] == 1
    assert payload["pid"] > 0
    assert payload["ppid"] > 0
    assert payload["source"] == "TOOLHELP32"
    assert payload["metadata"] == "UNKNOWN"


def test_canonical_tree_uses_native_snapshot_on_cim_denied_host() -> None:
    result = _run(
        f"$ErrorActionPreference='Stop'; . {_ps(NATIVE)}; "
        f"$source=Get-Content -Raw -LiteralPath {_ps(PROBE)}; "
        "$tokens=$null;$parseErrors=$null;"
        "$ast=[Management.Automation.Language.Parser]::ParseInput($source,[ref]$tokens,[ref]$parseErrors);"
        "$fn=@($ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst]},$true));"
        "foreach($f in $fn){. ([scriptblock]::Create($f.Extent.Text))};"
        "$tree=Get-ProcessTreeEvidence @($PID);"
        "[pscustomobject]@{status=$tree.enumeration_status;source=$tree.enumeration_source;"
        "contains_own=($PID -in $tree.ids);discovery=$tree.descendant_discovery_status}"
        "| ConvertTo-Json -Compress"
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    assert payload == {
        "status": "SUCCESS",
        "source": "TOOLHELP32",
        "contains_own": True,
        "discovery": "COMPLETE",
    }


@pytest.mark.skipif(sys.platform != "win32", reason="Windows Job Objects only")
def test_route_identity_is_retained_through_job_zero_before_close(tmp_path: Path) -> None:
    """The route identity must come from the owned handle after the Job drains."""
    route = tmp_path / "route.py"
    route.write_text("import time\ntime.sleep(0.1)\n", encoding="utf-8")
    result = _run(
        f"$ErrorActionPreference='Stop'; . {_ps(JOB_HELPER)} -Mode Library; "
        "$job=$null; try { "
        f"$job=Start-A3ContainedProcess -FilePath {_ps(Path(sys.executable))} "
        f"-Arguments @({_ps(route)}) -WorkingDirectory {_ps(tmp_path)}; "
        "$before=Get-A3ContainedProcessIdentity -Session $job; "
        "$completion=Wait-A3ContainedRouteZero -Session $job -TimeoutMilliseconds 10000; "
        "$after=Get-A3ContainedProcessIdentity -Session $job; "
        "[pscustomobject]@{before=$before;after=$after;active=(Get-A3JobActiveCount -Session $job); "
        "process_handle_retained=($job.ProcessHandle -ne [IntPtr]::Zero); "
        "launcher_exit=$completion.launcher_exit_code} | ConvertTo-Json -Depth 4 -Compress "
        "} finally { if($job){Close-A3ContainedProcess -Session $job} }",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    assert payload["active"] == 0
    assert payload["process_handle_retained"] is True
    assert payload["launcher_exit"] == 0
    for key in ("before", "after"):
        assert payload[key]["pid"] > 0
        assert payload[key]["creation_time_utc"]
        assert payload[key]["identity_source"] == "PROCESS_HANDLE"


@pytest.mark.parametrize("case", ["valid", "older_child", "unknown_child", "unknown_parent", "absent_parent"])
def test_native_parent_edges_require_compatible_creation_times(case: str) -> None:
    result = _run(
        f"$ErrorActionPreference='Stop'; $case='{case}'; "
        f"$source=Get-Content -Raw -LiteralPath {_ps(PROBE)}; "
        "$tokens=$null;$parseErrors=$null;"
        "$ast=[Management.Automation.Language.Parser]::ParseInput($source,[ref]$tokens,[ref]$parseErrors);"
        "$fn=@($ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst]},$true));"
        "foreach($f in $fn){. ([scriptblock]::Create($f.Extent.Text))};"
        "function Get-A3NativeProcessSnapshot { [pscustomobject]@{processes=@("
        "$(if($case -ne 'absent_parent'){@{pid=100;ppid=1}}),@{pid=200;ppid=100},@{pid=300;ppid=200})} };"
        "function Get-Process { param($Id,$ErrorAction) "
        "if (($case -eq 'unknown_child' -and $Id -eq 200) -or "
        "($case -in @('unknown_parent','absent_parent') -and $Id -eq 100)) { throw 'METADATA_UNAVAILABLE' };"
        "$offset=switch($Id){100{10}200{20}300{30}};"
        "if ($case -eq 'older_child' -and $Id -eq 200) {$offset=1};"
        "[pscustomobject]@{StartTime=([datetime]'2026-01-01T00:00:00Z').AddSeconds($offset)} };"
        "Get-ProcessTreeEvidence @(100) | ConvertTo-Json -Depth 8 -Compress"
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    assert payload["snapshot_status"] == "SUCCESS"
    if case == "absent_parent":
        assert payload["root_pid_status"][0]["exists"] is False
    if case == "valid":
        assert set(payload["ids"]) == {100, 200, 300}
        assert payload["descendant_discovery_status"] == "COMPLETE"
    elif case == "older_child":
        assert payload["ids"] == [100]
        assert payload["descendant_discovery_status"] == "COMPLETE"
        assert payload["rejected_parent_edges"][0]["reason"] == "CHILD_PREDATES_PARENT"
    else:
        assert payload["enumeration_status"] != "SUCCESS"
        assert payload["descendant_discovery_status"] == "UNRESOLVED"
        assert payload["unresolved_descendants"]


@pytest.mark.parametrize("case", ["valid", "stale_child", "unknown_child"])
def test_retained_root_identity_survives_terminated_root_and_rejects_stale_edges(
    case: str,
) -> None:
    """A retained handle identity replaces an unavailable PID-only parent lookup."""
    result = _run(
        f"$ErrorActionPreference='Stop'; $case='{case}'; "
        f"$source=Get-Content -Raw -LiteralPath {_ps(PROBE)}; "
        "$tokens=$null;$parseErrors=$null;"
        "$ast=[Management.Automation.Language.Parser]::ParseInput($source,[ref]$tokens,[ref]$parseErrors);"
        "$fn=@($ast.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst]},$true));"
        "foreach($f in $fn){. ([scriptblock]::Create($f.Extent.Text))};"
        "function Get-A3NativeProcessSnapshot { [pscustomobject]@{processes=@("
        "@{pid=200;ppid=100},@{pid=300;ppid=200})} };"
        "function Get-Process { param($Id,$ErrorAction) "
        "if ($Id -eq 100) { throw 'METADATA_UNAVAILABLE' }; "
        "if ($case -eq 'unknown_child' -and $Id -eq 200) { throw 'METADATA_UNAVAILABLE' }; "
        "$offset=switch($Id){200{20}300{30}}; "
        "if ($case -eq 'stale_child' -and $Id -eq 200) {$offset=1}; "
        "[pscustomobject]@{StartTime=([datetime]'2026-01-01T00:00:00Z').AddSeconds($offset)} };"
        "$rootIdentity=[pscustomobject]@{pid=100;creation_time_utc='2026-01-01T00:00:10Z';identity_source='PROCESS_HANDLE'};"
        "Get-ProcessTreeEvidence @(100) -AuthoritativeRootIdentity $rootIdentity | ConvertTo-Json -Depth 8 -Compress"
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout.strip().splitlines()[-1])
    assert payload["snapshot_status"] == "SUCCESS"
    assert payload["root_pid_status"][0]["exists"] is False
    if case == "valid":
        assert set(payload["ids"]) == {100, 200, 300}
        assert payload["descendant_discovery_status"] == "COMPLETE"
    elif case == "stale_child":
        assert payload["ids"] == [100]
        assert payload["descendant_discovery_status"] == "COMPLETE"
        assert payload["rejected_parent_edges"][0]["reason"] == "CHILD_PREDATES_PARENT"
    else:
        assert payload["enumeration_status"] == "PARTIAL"
        assert payload["descendant_discovery_status"] == "UNRESOLVED"
        assert payload["unresolved_descendants"]
