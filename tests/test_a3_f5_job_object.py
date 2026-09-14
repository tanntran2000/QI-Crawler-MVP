"""Synthetic Windows Job containment and canonical F5 route regressions."""

from __future__ import annotations

import shutil
import subprocess
import sys
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
JOB_HELPER = REPO / "tools" / "release" / "a3_job_object.ps1"
PROBE = REPO / "tools" / "release" / "a3_probe_windows.ps1"


def _powershell() -> str:
    executable = shutil.which("powershell.exe") or shutil.which("powershell")
    if executable is None:
        pytest.skip("Windows PowerShell is required for the Job Object contract")
    return executable


def _ps_string(value: Path | str) -> str:
    return "'" + str(value).replace("'", "''") + "'"


@pytest.mark.skipif(sys.platform != "win32", reason="Windows Job Objects only")
def test_f5_controller_child_and_grandchild_are_contained_and_terminated(
    tmp_path: Path,
) -> None:
    """Reverting to a PID kill or losing Job inheritance must fail this test."""
    grandchild = tmp_path / "grandchild.py"
    grandchild.write_text(
        "import os, pathlib, sys, time\n"
        "pathlib.Path(sys.argv[1], 'grandchild.pid').write_text(str(os.getpid()))\n"
        "time.sleep(30)\n",
        encoding="utf-8",
    )
    child = tmp_path / "child.py"
    child.write_text(
        "import os, pathlib, subprocess, sys, time\n"
        "root = pathlib.Path(sys.argv[1])\n"
        "subprocess.Popen([sys.executable, str(root / 'grandchild.py'), str(root)])\n"
        "(root / 'child.pid').write_text(str(os.getpid()))\n"
        "time.sleep(30)\n",
        encoding="utf-8",
    )
    controller = tmp_path / "controller.py"
    controller.write_text(
        "import os, pathlib, subprocess, sys, time\n"
        "root = pathlib.Path(sys.argv[1])\n"
        "subprocess.Popen([sys.executable, str(root / 'child.py'), str(root)])\n"
        "(root / 'controller.pid').write_text(str(os.getpid()))\n"
        "time.sleep(30)\n",
        encoding="utf-8",
    )

    command = f"""
. {_ps_string(JOB_HELPER)} -Mode Library
$lock = [IO.File]::Open({_ps_string(tmp_path / 'outer.lock')}, [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
$job = $null
try {{
    $job = Start-A3ContainedProcess -FilePath {_ps_string(sys.executable)} -Arguments @({_ps_string(controller)}, {_ps_string(tmp_path)}) -WorkingDirectory {_ps_string(tmp_path)}
    $deadline = (Get-Date).AddSeconds(15)
    while ((Get-Date) -lt $deadline -and -not ((Test-Path -LiteralPath {_ps_string(tmp_path / 'controller.pid')}) -and (Test-Path -LiteralPath {_ps_string(tmp_path / 'child.pid')}) -and (Test-Path -LiteralPath {_ps_string(tmp_path / 'grandchild.pid')}))) {{ Start-Sleep -Milliseconds 50 }}
    $expected = @('controller.pid','child.pid','grandchild.pid') | ForEach-Object {{ [int](Get-Content -Raw -LiteralPath (Join-Path {_ps_string(tmp_path)} $_)) }}
    $members = @(Get-A3JobProcessIds -Session $job)
    if (@($expected | Where-Object {{ $_ -notin $members }}).Count -ne 0) {{ throw 'JOB_MEMBERSHIP_MISSING' }}
    Write-Output "JOB_ACTIVE_AT_P2=$(Get-A3JobActiveCount -Session $job)"
    Write-Output "MEMBERSHIP_COUNT=$($expected.Count)"
    Stop-A3ContainedProcess -Session $job | Out-Null
    Write-Output "JOB_ACTIVE_AFTER=$(Get-A3JobActiveCount -Session $job)"
    Write-Output "OUTER_ALIVE=$([bool](Get-Process -Id $PID -ErrorAction SilentlyContinue))"
    $lock.WriteByte(65); $lock.Flush()
    Write-Output 'LOCK_RETAINED=YES'
}} finally {{
    if ($null -ne $job) {{ Close-A3ContainedProcess -Session $job }}
    $lock.Dispose()
}}
"""
    result = subprocess.run(
        [_powershell(), "-NoProfile", "-NonInteractive", "-Command", command],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "MEMBERSHIP_COUNT=3" in result.stdout
    assert "JOB_ACTIVE_AFTER=0" in result.stdout
    assert "OUTER_ALIVE=True" in result.stdout
    assert "LOCK_RETAINED=YES" in result.stdout


@pytest.mark.skipif(sys.platform != "win32", reason="Windows Job Objects only")
def test_job_owner_exit_terminates_contained_controller(tmp_path: Path) -> None:
    """A failed outer probe must not strand a sandbox writer after its handle closes."""
    controller = tmp_path / "controller.py"
    controller.write_text("import time\ntime.sleep(8)\n", encoding="utf-8")
    command = f"""
. {_ps_string(JOB_HELPER)} -Mode Library
$job = Start-A3ContainedProcess -FilePath {_ps_string(sys.executable)} -Arguments @({_ps_string(controller)}) -WorkingDirectory {_ps_string(tmp_path)}
Write-Output "CONTROLLER_PID=$($job.ProcessId)"
"""
    owner = subprocess.run(
        [_powershell(), "-NoProfile", "-NonInteractive", "-Command", command],
        cwd=REPO,
        text=True,
        capture_output=True,
        timeout=20,
        check=False,
    )
    assert owner.returncode == 0, owner.stdout + owner.stderr
    pid = int(owner.stdout.split("CONTROLLER_PID=", 1)[1].splitlines()[0])
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        state = subprocess.run(
            [_powershell(), "-NoProfile", "-NonInteractive", "-Command",
             f"if (Get-Process -Id {pid} -ErrorAction SilentlyContinue) {{ 'ALIVE' }} else {{ 'EXITED' }}"],
            cwd=REPO,
            text=True,
            capture_output=True,
            timeout=10,
            check=False,
        )
        if "EXITED" in state.stdout:
            break
        time.sleep(0.1)
    assert "EXITED" in state.stdout


def test_canonical_f5_route_binds_controller_to_job_and_never_pid_kills_it() -> None:
    """Removing actual route integration must fail even if the helper self-test passes."""
    source = PROBE.read_text(encoding="utf-8")
    route = source.split("function Invoke-F5CanonicalRoute {", 1)[1].split(
        "if ($f5OnlyRoute)", 1
    )[0]
    assert "Start-A3ContainedProcess" in route
    assert "Get-A3JobProcessIds" in route
    assert "Stop-A3ContainedProcess" in route
    assert "Stop-SandboxTree @($f5Proc.Id)" not in route


def test_canonical_f5_barrier_sequence_has_p2_alive_before_job_kill() -> None:
    """Reordering writer/stub checks or P3 around the Job kill must fail."""
    source = PROBE.read_text(encoding="utf-8")
    route = source.split("function Invoke-F5CanonicalRoute {", 1)[1].split(
        "if ($f5OnlyRoute)", 1
    )[0]
    markers = [
        "'P1_CENSUS_FROZEN'",
        "'BARRIER_CONFIRMED_PERSISTED'",
        "'P2_CAPTURE_FINISHED'",
        "'WRITER_REVALIDATION_PASS'",
        "'CANONICAL_STUB_VERIFICATION_PASS'",
        "'JOB_TERMINATE'",
        "'JOB_ZERO'",
        "'P3_CENSUS_START'",
    ]
    positions = [route.index(marker) for marker in markers]
    assert positions == sorted(positions)
    assert "JOB_ACTIVE_PROCESS_COUNT_AT_P2" in route
