# One disposable execution of the on-disk Invoke-F5CanonicalRoute function.
# It deliberately does not call the RealF5 guard or touch the designated sandbox.
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)] [string]$Root,
    [ValidateSet('none','p1_bound','cmd_path','cmd_exit','p4_survivor','p4_unknown',
        'budget','manifest','recovery','recovery_missing','db_mismatch')]
    [string]$Fault='none',
    [switch]$UseFrozenStub
)
$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path -LiteralPath '.').Path
$PollMilliseconds = 250
$probe = Join-Path $repo 'tools/release/a3_probe_windows.ps1'
. (Join-Path $repo 'tools/release/a3_f5_bounded_io.ps1')
. (Join-Path $repo 'tools/release/a3_job_object.ps1') -Mode Library
. (Join-Path $repo 'tools/release/a3_native_lineage.ps1')
$phaseHelper=Join-Path $repo 'tools/release/a3_phase_contract.ps1'
. $phaseHelper
$tokens=$null; $parseErrors=$null
$ast=[Management.Automation.Language.Parser]::ParseFile($probe,[ref]$tokens,[ref]$parseErrors)
if (@($parseErrors).Count -ne 0) { throw 'SYNTHETIC_PROBE_PARSE_FAILED' }
foreach($definition in @($ast.FindAll({param($node) $node -is [Management.Automation.Language.FunctionDefinitionAst]},$true))) {
    $definitionText=$definition.Extent.Text
    if($definition.Name -eq 'Invoke-F5CanonicalRoute' -and $Fault -ne 'none') {
        $needle='';$injection=''
        switch($Fault) {
            'p1_bound' { $needle='Write-FsyncJson (Join-Path $f5Evidence ''receipts\P1.json'') $p1'; $injection="throw 'FAULT_P1_BOUND'; " }
            'cmd_path' { $needle='$routeJob=Start-A3ContainedRoute -Kind $routeKind'; $injection="if(`$routeKind -eq 'CMD'){throw 'FAULT_CMD_PATH'}; " }
            'cmd_exit' { $needle='$routeCompletion=Wait-A3ContainedRouteZero -Session $routeJob'; $injection="if(`$routeKind -eq 'CMD'){throw 'FAULT_CMD_EXIT'}; " }
            'p4_survivor' { $needle='-TimeoutMilliseconds 10000 -MinimumTotalProcesses'; $injection='-TimeoutMilliseconds $(if($routeKind -eq ''CMD''){1}else{10000}) -MinimumTotalProcesses' }
            'p4_unknown' { $needle='$routeTreeEvidence=Get-ProcessTreeEvidence @($routeCompletion.launcher_pid)'; $injection='$routeTreeEvidence.enumeration_status=''ERROR''; ' }
            'budget' { $needle='Write-F5BoundedText -Path $artifact -Text'; $injection="throw 'FAULT_BUDGET'; " }
            'manifest' { $needle='$evidenceManifest=New-EvidenceManifest'; $injection='Remove-Item -LiteralPath (Join-Path $f5Evidence ''receipts\P3.json'') -Force; ' }
            'recovery' { $needle='$maintenance=Invoke-RecoveryCli'; $injection="throw 'FAULT_RECOVERY'; " }
            'recovery_missing' { $needle='$f5After=Get-DbManifest $f5.data $f5.root'; $injection='Remove-Item -LiteralPath $maintenance.receipt_path -Force; ' }
            'db_mismatch' { $needle='$f5LogicalAfter=Get-F5LogicalDigest'; $injection='$f5After.files[0].sha256=''0000000000000000000000000000000000000000000000000000000000000000''; ' }
        }
        if($definitionText.Split(@($needle),[StringSplitOptions]::None).Count -ne 2) { throw "SYNTHETIC_FAULT_ANCHOR_INVALID: $Fault" }
        if($Fault -eq 'p4_survivor') { $definitionText=$definitionText.Replace($needle,$injection) }
        elseif($Fault -eq 'p4_unknown') { $definitionText=$definitionText.Replace($needle,$needle+'; '+$injection) }
        else { $definitionText=$definitionText.Replace($needle,$injection+$needle) }
    }
    . ([scriptblock]::Create($definitionText))
}
$root = Get-CanonicalPath $Root
if (Test-Path -LiteralPath $root) { throw 'SYNTHETIC_ROOT_ALREADY_EXISTS' }
$sandboxRoot=Join-Path $root 'sandbox'
$app=Join-Path $sandboxRoot 'install/QI-Crawler'
$data=Join-Path $sandboxRoot 'data'
$db=Join-Path $data 'data/database'
$tx=Join-Path $sandboxRoot 'transaction'
$evidenceRoot=Join-Path $root 'evidence'
$fixtureRoot=Join-Path $root 'fixture'
New-Item -ItemType Directory -Force -Path $app,$db,$tx,$evidenceRoot,$fixtureRoot | Out-Null
$legacy=Join-Path $fixtureRoot 'legacy.exe'
$stub=Join-Path $fixtureRoot 'stub.exe'
Copy-Item -LiteralPath (Join-Path $env:WINDIR 'System32/whoami.exe') -Destination $legacy
Copy-Item -LiteralPath (Join-Path $env:WINDIR 'System32/hostname.exe') -Destination $stub
if ($UseFrozenStub) {
    $v09=Join-Path $repo 'release_staging/candidate/QI-Crawler/QI-Crawler.exe'
    if ((Get-Sha256 $v09) -ne '0970fc2e0cae7017cdd9508a2aad64488e1cc363a175391d7758ca1ba609d026') { throw 'FROZEN_V09_IDENTITY_MISMATCH' }
    Copy-Item -LiteralPath $v09 -Destination $legacy -Force
    $frozen=Join-Path $repo 'release_staging/evidence/WP-REL-RECON-01/AO-03/stub/dist/QI-Crawler-Maintenance-Stub.exe'
    if ((Get-Sha256 $frozen) -ne '6f6a4cfdb43d6a63236ee707ddf74ac43b65a49cb2d20e371bb920cd81932f34') { throw 'FROZEN_STUB_IDENTITY_MISMATCH' }
    Copy-Item -LiteralPath $frozen -Destination $stub -Force
}
$canonical=Join-Path $app 'QI-Crawler.exe'
Copy-Item -LiteralPath $legacy -Destination $canonical
$python=(Resolve-Path -LiteralPath '.venv/Scripts/python.exe').Path
$observer=(Resolve-Path -LiteralPath 'tools/release/a3_process_observer.py').Path
if ($UseFrozenStub) {
    $controllerSource=(Resolve-Path -LiteralPath 'release_staging/evidence/WP-REL-RECON-01/AO-03/controller/ao03_controller.py').Path
    $controller=(Resolve-Path -LiteralPath 'release_staging/evidence/WP-REL-RECON-01/AO-03/controller/dist/AO03-Controller.exe').Path
} else {
    # The actor is test-owned. No historical release material is a CI dependency.
    $controllerSource=(Resolve-Path -LiteralPath 'tests/a3_ci_controller.py').Path
    $controller=$python
}
$ao03ControllerHash=Get-Sha256 $controller
$seedProcess=Start-Process -FilePath $python -ArgumentList (ConvertTo-F5CommandLine @('-m','tools.release.a3_f5_seed_db','--output',(Join-Path $db 'egp.db'))) -WorkingDirectory $repo -WindowStyle Hidden -PassThru -Wait
if ($seedProcess.ExitCode -ne 0) { throw 'SYNTHETIC_DB_SEED_FAILED' }
$legacyHash=Get-Sha256 $legacy
$stubHash=Get-Sha256 $stub
$script:f5ObserverSourceSha=Get-Sha256 $observer
$script:f5LegacyHash=$legacyHash
$script:f5CurrentSnapshot=$null
$script:f5CurrentDbManifestSha=$null
$script:f5ControllerTreeCount=$null
$script:f5RecoveryProcessRunning=$null
$script:f5SequenceNumber=0
$f5EventSequence=[Collections.Generic.List[object]]::new()
$script:observerSequence=0
$script:recoveryInvocationSequence=0
$controllerResults=$null; $failpointResults=$null
$lockPath=Join-Path $root 'synthetic.lock'
$lock=[IO.File]::Open($lockPath,[IO.FileMode]::OpenOrCreate,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None)
$limits=@(
    @{write_class='EVIDENCE_META';max_file_count=256;max_per_file_bytes=8388608;max_aggregate_bytes=67108864;max_atomic_overlap_bytes=8388608},
    @{write_class='PROCESS_CENSUS';max_file_count=64;max_per_file_bytes=16777216;max_aggregate_bytes=67108864;max_atomic_overlap_bytes=16777216;max_records=4096;max_field_bytes=32768},
    @{write_class='TX_STATE';max_file_count=32;max_per_file_bytes=1048576;max_aggregate_bytes=16777216;max_atomic_overlap_bytes=1048576},
    @{write_class='DB_MANIFEST';max_file_count=16;max_per_file_bytes=65536;max_aggregate_bytes=1048576;max_atomic_overlap_bytes=65536;max_entries=4},
    @{write_class='ROUTE_ARTIFACTS';max_file_count=64;max_per_file_bytes=8388608;max_aggregate_bytes=67108864;max_atomic_overlap_bytes=8388608;max_stdout_bytes=1048576;max_stderr_bytes=1048576;max_runtime_seconds=60},
    @{write_class='RECOVERY';max_file_count=32;max_per_file_bytes=33554432;max_aggregate_bytes=100663296;max_atomic_overlap_bytes=33554432;max_stdout_bytes=1048576;max_stderr_bytes=1048576;max_runtime_seconds=60}
)
$PreexecutionContractPath=Join-Path $root 'preexecution.json'
$syntheticContract=@{material_write_bounds=$limits}
if ($UseFrozenStub) {
    $phaseHelper=Join-Path $repo 'tools/release/a3_phase_contract.ps1'
    $syntheticContract.schema='AO-04-C3-F5-PREEXECUTION-CONTRACT-PHASE-V1'
    $syntheticContract.phase_helper_identity=@{path=$phaseHelper;sha256=(Get-Sha256 $phaseHelper)}
    $syntheticContract.phase_model=@{
        schema='A3-F5-PHASE-MODEL-V1';expected_phase='PRETRIAL'
        pretrial_exe_sha256=$legacyHash;maintenance_stub_sha256=$stubHash
    }
}
[IO.File]::WriteAllText($PreexecutionContractPath,($syntheticContract|ConvertTo-Json -Depth 10),[Text.UTF8Encoding]::new($false))
$trial=[pscustomobject]@{root=$sandboxRoot;install=(Join-Path $sandboxRoot 'install');app=$app;canonical=$canonical;data=$data;db=$db;tx=$tx}
try {
    $result=Invoke-F5CanonicalRoute -Trial $trial -TrialId 'synthetic-A' -EvidenceRoot $evidenceRoot -StubPath $stub -PythonPath $python -LegacyExecutableSha256 $legacyHash -StubSha256 $stubHash
    if ($result.final_probe_result -ne 'PASS') { throw 'SYNTHETIC_ROUTE_NOT_PASS' }
    @($result | Where-Object { $_ -is [string] -and $_ -like 'A3_PHASE_*=PASS' }) | ForEach-Object { Write-Output $_ }
    Write-Output 'SYNTHETIC_AGGREGATE_VERDICT=PASS'
    Write-Output ('SYNTHETIC_EVIDENCE_MANIFEST_SHA256=' + $result.evidence_manifest_sha256)
} finally {
    $lock.Dispose()
}
