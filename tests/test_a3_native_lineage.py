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
