"""Sandbox-only authority for the canonical A3 RealF5 observer."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from tools.release.a3_process_observer import A3ProcessObserver, ObserverConfig, ProcessClass

REPO = Path(__file__).resolve().parents[1]
PROBE = REPO / "tools" / "release" / "a3_probe_windows.ps1"


def test_realf5_probe_has_no_production_observer_target() -> None:
    source = PROBE.read_text(encoding="utf-8")
    census = source.split("function Get-RawCensus", 1)[1].split("function Invoke-Observer", 1)[0]
    config = source.split("function Invoke-Observer", 1)[1].split("$script:observerSequence", 1)[0]
    assert "d:\\qi-crawler\\qi-crawler.exe" not in census.lower()
    assert "production_paths" not in config
    assert "Get-Process -ErrorAction SilentlyContinue" not in census


def test_external_process_cannot_become_sandbox_authority(tmp_path: Path) -> None:
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    outside = tmp_path / "external" / "QI-Crawler.exe"
    observer = A3ProcessObserver(ObserverConfig(trial_root=sandbox), known_pids=frozenset({42}))
    record = observer.classify_record(
        {"pid": 42, "image_path": str(outside), "access_status": "PASS", "image_sha256": "a" * 64}
    )
    assert record.classification == ProcessClass.OBSERVER_SCOPE_VIOLATION
    snapshot = observer.census(
        [{"pid": 42, "image_path": str(outside), "access_status": "PASS"}],
        event_name="outside",
        positive_control_passed=True,
        known_legacy_roots_absent=True,
    )
    assert snapshot.legacy_zero_proven is False


def test_disposable_external_process_is_not_observer_owned(tmp_path: Path) -> None:
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    process = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(15)"])
    try:
        observer = A3ProcessObserver(ObserverConfig(trial_root=sandbox))
        record = observer.classify_record(
            {"pid": process.pid, "image_path": sys.executable, "access_status": "PASS"}
        )
        assert record.classification == ProcessClass.IRRELEVANT
        assert process.poll() is None
    finally:
        process.terminate()
        process.wait(timeout=10)


def test_sibling_prefix_and_outside_identity_fail_closed(tmp_path: Path) -> None:
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    outside = tmp_path / "sandbox-other" / "QI-Crawler.exe"
    with pytest.raises(ValueError, match="OBSERVER_SCOPE_VIOLATION"):
        ObserverConfig(trial_root=sandbox, legacy_paths=frozenset({outside}))


def test_outside_hash_request_is_rejected_by_probe_contract() -> None:
    source = PROBE.read_text(encoding="utf-8")
    census = source.split("function Get-RawCensus", 1)[1].split("function Invoke-Observer", 1)[0]
    assert "Assert-ObserverPath" in census
    assert "StartsWith($TrialRoot.ToLowerInvariant())" not in census


@pytest.mark.parametrize("outside_name", ["sandbox-other", "external"])
def test_powershell_path_guard_rejects_outside_before_file_access(
    tmp_path: Path, outside_name: str
) -> None:
    powershell = shutil.which("powershell.exe") or shutil.which("powershell")
    if not powershell:
        pytest.skip("Windows PowerShell 5.1 unavailable")
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    outside = tmp_path / outside_name / "not-present.exe"
    source = PROBE.read_text(encoding="utf-8")
    function = source.split("function Assert-ObserverPath", 1)[1].split(
        "function Get-RawCensus", 1
    )[0]
    command = (
        "function Assert-ObserverPath" + function
        + f"Assert-ObserverPath '{outside}' '{sandbox}'"
    )
    result = subprocess.run(
        [powershell, "-NoProfile", "-NonInteractive", "-Command", command],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert result.returncode != 0
    assert "OBSERVER_SCOPE_VIOLATION" in result.stderr


def test_census_does_not_hash_or_query_external_executable(tmp_path: Path) -> None:
    powershell = shutil.which("powershell.exe") or shutil.which("powershell")
    if not powershell:
        pytest.skip("Windows PowerShell 5.1 unavailable")
    sandbox = tmp_path / "sandbox"
    sandbox.mkdir()
    outside = tmp_path / "external" / "controller.exe"
    source = PROBE.read_text(encoding="utf-8")
    path_guard = "function Assert-ObserverPath" + source.split(
        "function Assert-ObserverPath", 1
    )[1].split("function Get-RawCensus", 1)[0]
    census = "function Get-RawCensus" + source.split("function Get-RawCensus", 1)[1].split(
        "function Invoke-Observer", 1
    )[0]
    fixture = f"""
function Get-ProcessTreeEvidence {{ param([int[]]$Roots)
  return [pscustomobject]@{{ids=@(42);enumeration_status='SUCCESS';descendant_discovery_status='COMPLETE'}}
}}
function Get-Process {{ param([int]$Id)
  if ($Id -ne 42) {{ throw 'EXTERNAL_PROCESS_QUERY' }}
  return [pscustomobject]@{{Id=42;Path='{outside}';StartTime=(Get-Date)}}
}}
function Get-CimInstance {{ param([string]$ClassName,[string]$Filter)
  if ($Filter -ne 'ProcessId = 42') {{ throw 'BROAD_PROCESS_QUERY' }}
  return [pscustomobject]@{{CommandLine='synthetic';ParentProcessId=1}}
}}
function Test-Path {{ throw 'OUTSIDE_TEST_PATH' }}
function Get-Sha256 {{ throw 'OUTSIDE_HASH' }}
function Get-F5BoundedLimit {{ return @{{max_records=10;max_field_bytes=1024;max_per_file_bytes=65536}} }}
function Assert-F5BoundedRecords {{ }}
$result = @(Get-RawCensus @(42) '{sandbox}')
if ($result.Count -ne 1 -or $result[0].image_sha256) {{ throw 'CENSUS_RESULT_INVALID' }}
'SANDBOX_CENSUS_ONLY'
"""
    result = subprocess.run(
        [powershell, "-NoProfile", "-NonInteractive", "-Command", path_guard + census + fixture],
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
    assert "SANDBOX_CENSUS_ONLY" in result.stdout
