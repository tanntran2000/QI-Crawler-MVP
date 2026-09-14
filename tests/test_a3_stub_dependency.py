"""Frozen stub dependency and route failure evidence regressions (no RealF5)."""

from __future__ import annotations

import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
STUB = REPO / "release_staging/evidence/WP-REL-RECON-01/AO-03/stub/dist/QI-Crawler-Maintenance-Stub.exe"
CONTROLLER = REPO / "release_staging/evidence/WP-REL-RECON-01/AO-03/controller/dist/AO03-Controller.exe"
STUB_SHA = "6f6a4cfdb43d6a63236ee707ddf74ac43b65a49cb2d20e371bb920cd81932f34"
pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows runtime")


def _ps(value: Path | str) -> str:
    return "'" + str(value).replace("'", "''") + "'"


def _env(root: Path) -> dict[str, str]:
    env = os.environ.copy()
    env.update(TEMP=str(root), TMP=str(root), PYTHONDONTWRITEBYTECODE="1",
               QI_CRAWLER_DATA_DIR=str(root / "data"),
               QI_CRAWLER_CONFIG_PATH=str(root / "config.yaml"))
    return env


def _require_stub() -> None:
    if not STUB.is_file() or not CONTROLLER.is_file():
        pytest.skip("retained frozen AO-03 artifacts unavailable")
    assert hashlib.sha256(STUB.read_bytes()).hexdigest() == STUB_SHA


def test_exact_frozen_stub_absent_then_valid_companion(tmp_path: Path) -> None:
    """Only companion state changes; same binary, argv and working directory."""
    _require_stub()
    exe = tmp_path / "QI-Crawler.exe"
    shutil.copyfile(STUB, exe)
    env = _env(tmp_path)
    absent = subprocess.run([str(exe)], cwd=tmp_path, env=env,
                            capture_output=True, text=True, timeout=20, check=False)
    assert absent.returncode == 1, absent
    assert "maintenance_stub_state.json" in absent.stderr
    assert "FileNotFoundError" in absent.stderr
    state = {"controller_path": str(CONTROLLER),
             "controller_sha256": hashlib.sha256(CONTROLLER.read_bytes()).hexdigest()}
    (tmp_path / "maintenance_stub_state.json").write_text(json.dumps(state), encoding="utf-8")
    present = subprocess.run([str(exe)], cwd=tmp_path, env=env,
                             capture_output=True, text=True, timeout=20, check=False)
    assert present.returncode == 0, present.stderr
    assert "BUSINESS_WORKFLOW=BLOCKED" in present.stdout
    assert "RECOVERY_CONTROLLER=VERIFIED" in present.stdout
    assert not present.stderr


def test_canonical_route_with_actual_frozen_stub(tmp_path: Path) -> None:
    """A producer omission must fail even when hostname-based rehearsal passes."""
    _require_stub()
    result = subprocess.run(
        ["powershell.exe", "-NoProfile", "-NonInteractive", "-File",
         str(REPO / "tests/a3_f5_synthetic_route.ps1"),
         "-Root", str(tmp_path / "one-run"), "-UseFrozenStub"],
        cwd=REPO, env=_env(tmp_path), capture_output=True, text=True,
        timeout=120, check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "SYNTHETIC_AGGREGATE_VERDICT=PASS" in result.stdout
    assert "A3_PHASE_PRETRIAL=PASS" in result.stdout
    assert "A3_PHASE_CUTOVER_STUB_STAGED=PASS" in result.stdout
    assert "A3_PHASE_POST_BARRIER_MAINTENANCE=PASS" in result.stdout
    receipts = tmp_path / "one-run/evidence/f5/synthetic-A/receipts"
    for route in ("canonical", "start_menu", "desktop", "post_install", "autostart_task"):
        receipt = json.loads((receipts / f"P4_{route}.json").read_text(encoding="utf-8-sig"))
        assert receipt["result"] == "STUB"
        assert receipt["job_active_after"] == 0
    assert (receipts / "RECOVERY_BOUND.json").is_file()


def test_contained_failure_retains_bounded_stderr(tmp_path: Path) -> None:
    """Child exit 7 must carry its diagnostic without weakening the Job gate."""
    command = f"""
. {_ps(REPO / 'tools/release/a3_job_object.ps1')} -Mode Library
$job=Start-A3ContainedRoute -Kind EXE -Artifact {_ps(Path(sys.executable))} -Arguments @('-c','import sys; print("out"); print("diagnostic",file=sys.stderr); sys.exit(7)') -WorkingDirectory {_ps(tmp_path)} -MaxStdoutBytes 1024 -MaxStderrBytes 1024
try {{
    try {{ Wait-A3ContainedRouteZero -Session $job | Out-Null; throw 'UNEXPECTED_PASS' }}
    catch {{
        if (-not $_.Exception.Data.Contains('route_result')) {{ throw }}
        $_.Exception.Data['route_result'] | ConvertTo-Json -Depth 5 -Compress
    }}
}} finally {{ Close-A3ContainedProcess -Session $job }}
"""
    result = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
                            cwd=REPO, env=_env(tmp_path), capture_output=True,
                            text=True, timeout=30, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    receipt = json.loads(result.stdout)
    assert receipt["launcher_exit_code"] == 7
    assert receipt["active_after"] == 0
    assert "diagnostic" in receipt["stderr"]
    assert receipt["stdout"].strip() == "out"


@pytest.mark.parametrize("fault", ["wrong_hash", "existing_state", "changed_controller", "write_bound"])
def test_state_producer_refuses_untrusted_or_stale_inputs(tmp_path: Path, fault: str) -> None:
    """The producer must neither bless a wrong controller nor overwrite old state."""
    canonical = tmp_path / "QI-Crawler.exe"
    canonical.write_bytes(b"test canonical")
    controller = tmp_path / "controller.exe"
    controller.write_bytes(b"test controller")
    digest = hashlib.sha256(controller.read_bytes()).hexdigest()
    state = tmp_path / "maintenance_stub_state.json"
    if fault == "existing_state":
        state.write_bytes(b"preserve this evidence")
    expected_sha = "0" * 64 if fault == "wrong_hash" else digest
    bound = 1 if fault == "write_bound" else 4096
    after = ""
    if fault == "changed_controller":
        after = f"[IO.File]::WriteAllText({_ps(controller)},'changed'); [void](Assert-F5StubState $identity {_ps(tmp_path)})"
    command = f"""
$ErrorActionPreference='Stop'
. {_ps(REPO / 'tools/release/a3_f5_bounded_io.ps1')}
$tokens=$null;$errors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile({_ps(REPO / 'tools/release/a3_probe_windows.ps1')},[ref]$tokens,[ref]$errors)
foreach($fn in @($ast.FindAll({{param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst]}},$true))) {{ . ([scriptblock]::Create($fn.Extent.Text)) }}
Initialize-F5BoundedIo -Limits @{{TX_STATE=@{{max_file_count=4;max_per_file_bytes={bound};max_aggregate_bytes={bound};max_atomic_overlap_bytes={bound}}}}}
$identity=Initialize-F5StubState -CanonicalPath {_ps(canonical)} -TrialRoot {_ps(tmp_path)} -ControllerPath {_ps(controller)} -ControllerSha256 '{expected_sha}'
{after}
"""
    result = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
                            cwd=REPO, capture_output=True, text=True, timeout=20, check=False)
    assert result.returncode != 0
    expected = {"wrong_hash": "F5_STUB_CONTROLLER_IDENTITY_MISMATCH",
                "existing_state": "immutable bounded artifact already exists",
                "changed_controller": "F5_STUB_CONTROLLER_IDENTITY_MISMATCH",
                "write_bound": "MATERIAL_WRITE_BOUND_EXCEEDED"}
    assert expected[fault] in result.stderr
    if fault == "existing_state":
        assert state.read_bytes() == b"preserve this evidence"
    elif fault in {"wrong_hash", "write_bound"}:
        assert not state.exists()


def test_route_output_overflow_terminates_job_and_reports_bound(tmp_path: Path) -> None:
    command = f"""
. {_ps(REPO / 'tools/release/a3_job_object.ps1')} -Mode Library
$job=Start-A3ContainedRoute -Kind EXE -Artifact {_ps(Path(sys.executable))} -Arguments @('-c','import sys,time; sys.stderr.write("x"*8192); sys.stderr.flush(); time.sleep(20)') -WorkingDirectory {_ps(tmp_path)} -MaxStdoutBytes 1024 -MaxStderrBytes 1024
try {{
    try {{ Wait-A3ContainedRouteZero -Session $job | Out-Null; throw 'UNEXPECTED_PASS' }}
    catch {{
        if ($_.Exception.Message -ne 'JOB_ROUTE_OUTPUT_BOUND_EXCEEDED') {{ throw }}
        $_.Exception.Data['route_result'] | ConvertTo-Json -Depth 5 -Compress
    }}
}} finally {{ Close-A3ContainedProcess -Session $job }}
"""
    result = subprocess.run(["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", command],
                            cwd=REPO, env=_env(tmp_path), capture_output=True,
                            text=True, timeout=30, check=False)
    assert result.returncode == 0, result.stdout + result.stderr
    receipt = json.loads(result.stdout)
    assert receipt["output_bound_exceeded"] is True
    assert receipt["active_after"] == 0
    assert len(receipt["stderr"].encode()) == 1024
