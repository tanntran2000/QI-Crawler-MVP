[CmdletBinding()]
param(
    [string]$EvidenceRoot = 'release_staging\evidence\WP-REL-RECON-01\AO-04',
    [int]$PollMilliseconds = 250,
    [ValidateSet('Sequential', 'F5Only')]
    [string]$Mode = 'Sequential',
    [ValidateSet('Unspecified', 'DryRun', 'RealF5')]
    [string]$ExecutionMode = 'Unspecified',
    [string]$ExistingSandboxPath,
    [string]$RunId,
    [string]$InputManifestPath,
    [string]$ExecutionContextPath,
    [string]$PreexecutionContractPath,
    [string]$TestStateRoot,
    [switch]$TestDispatchBoundary,
    [Int64]$DispatchHoldSeconds = 0,
    [switch]$DryRun
)

$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path -LiteralPath '.').Path
$contextHelper = Join-Path $PSScriptRoot 'a3_f5_execution_context.ps1'
if (-not (Test-Path -LiteralPath $contextHelper -PathType Leaf)) { throw 'EXECUTION_CONTEXT_HELPER_MISSING' }
. $contextHelper
$boundedIoHelper = Join-Path $PSScriptRoot 'a3_f5_bounded_io.ps1'
if (-not (Test-Path -LiteralPath $boundedIoHelper -PathType Leaf)) { throw 'BOUNDED_IO_HELPER_MISSING' }
. $boundedIoHelper
$jobHelper = Join-Path $PSScriptRoot 'a3_job_object.ps1'
if (-not (Test-Path -LiteralPath $jobHelper -PathType Leaf)) { throw 'JOB_OBJECT_HELPER_MISSING' }
. $jobHelper -Mode Library
$nativeLineageHelper = Join-Path $PSScriptRoot 'a3_native_lineage.ps1'
if (-not (Test-Path -LiteralPath $nativeLineageHelper -PathType Leaf)) { throw 'NATIVE_LINEAGE_HELPER_MISSING' }
. $nativeLineageHelper
$phaseHelper = Join-Path $PSScriptRoot 'a3_phase_contract.ps1'
if (-not (Test-Path -LiteralPath $phaseHelper -PathType Leaf)) { throw 'A3_PHASE_HELPER_MISSING' }
. $phaseHelper

$defaultWriteBounds = @{
    EVIDENCE_META = @{max_file_count=256;max_per_file_bytes=8388608;max_aggregate_bytes=67108864;max_atomic_overlap_bytes=8388608}
    PROCESS_CENSUS = @{max_file_count=64;max_per_file_bytes=16777216;max_aggregate_bytes=67108864;max_atomic_overlap_bytes=16777216;max_records=4096;max_field_bytes=32768}
    TX_STATE = @{max_file_count=32;max_per_file_bytes=1048576;max_aggregate_bytes=16777216;max_atomic_overlap_bytes=1048576}
    DB_MANIFEST = @{max_file_count=16;max_per_file_bytes=65536;max_aggregate_bytes=1048576;max_atomic_overlap_bytes=65536;max_entries=4}
    ROUTE_ARTIFACTS = @{max_file_count=64;max_per_file_bytes=8388608;max_aggregate_bytes=67108864;max_atomic_overlap_bytes=8388608;max_stdout_bytes=1048576;max_stderr_bytes=1048576;max_runtime_seconds=60}
    RECOVERY = @{max_file_count=32;max_per_file_bytes=33554432;max_aggregate_bytes=100663296;max_atomic_overlap_bytes=33554432;max_stdout_bytes=1048576;max_stderr_bytes=1048576;max_runtime_seconds=60}
}
Initialize-F5BoundedIo -Limits $defaultWriteBounds

function Initialize-F5BoundsFromContract([string]$ContractPath) {
    if (-not $ContractPath -or -not (Test-Path -LiteralPath $ContractPath -PathType Leaf)) { throw 'MATERIAL_WRITE_BOUND_UNKNOWN: contract' }
    $contract = Get-Content -Raw -LiteralPath $ContractPath | ConvertFrom-Json
    $limits = @{}
    foreach ($entry in @($contract.material_write_bounds)) {
        if (-not $entry.write_class) { throw 'MATERIAL_WRITE_BOUND_UNKNOWN: unnamed class' }
        $limit = @{}
        foreach ($property in $entry.PSObject.Properties) { if ($property.Name -ne 'write_class') { $limit[$property.Name] = $property.Value } }
        $limits[[string]$entry.write_class] = $limit
    }
    foreach ($required in @('EVIDENCE_META','PROCESS_CENSUS','TX_STATE','DB_MANIFEST','ROUTE_ARTIFACTS','RECOVERY')) {
        if (-not $limits.ContainsKey($required)) { throw "MATERIAL_WRITE_BOUND_UNKNOWN: $required" }
    }
    Initialize-F5BoundedIo -Limits $limits
}

function Get-Sha256([string]$Path) {
    $sha = [Security.Cryptography.SHA256]::Create()
    $stream = [IO.File]::OpenRead($Path)
    try {
        return ([BitConverter]::ToString($sha.ComputeHash($stream))).Replace('-', '').ToLowerInvariant()
    } finally {
        $stream.Dispose()
        $sha.Dispose()
    }
}

function Get-CanonicalPath([string]$Path) {
    if (-not $Path -or -not [IO.Path]::IsPathRooted($Path)) {
        throw 'PATH_CONTAINMENT_INVALID'
    }
    try {
        $canonical = $null
        if (Test-Path -LiteralPath $Path) {
            $canonical = (Resolve-Path -LiteralPath $Path -ErrorAction Stop).Path
        } else {
            $canonical = [IO.Path]::GetFullPath($Path)
        }
        $rootName = [IO.Path]::GetPathRoot($canonical)
        if (-not [string]::Equals($canonical, $rootName, [StringComparison]::OrdinalIgnoreCase)) {
            $canonical = $canonical.TrimEnd('\')
        }
        return $canonical
    } catch {
        throw "PATH_CONTAINMENT_INVALID: $($_.Exception.Message)"
    }
}

function Get-SafeRelativePath([string]$Root, [string]$Target) {
    $fullRoot = Get-CanonicalPath $Root
    $fullTarget = Get-CanonicalPath $Target
    $rootName = [IO.Path]::GetPathRoot($fullRoot)
    if (-not $rootName) { throw 'PATH_CONTAINMENT_INVALID' }
    if ([string]::Equals($fullRoot, $fullTarget, [StringComparison]::OrdinalIgnoreCase)) {
        return ''
    }
    $rootPrefix = if ([string]::Equals($fullRoot, $rootName, [StringComparison]::OrdinalIgnoreCase)) {
        $fullRoot
    } else {
        $fullRoot.TrimEnd('\') + '\'
    }
    if (-not $fullTarget.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "PATH_CONTAINMENT_VIOLATION: target is outside root: $fullTarget"
    }
    return $fullTarget.Substring($rootPrefix.Length).Replace('\','/')
}

$f5OnlyRoute = $false
$f5OnlySandbox = $null
$f5OnlyEvidenceRoot = $null
$f5OnlyTestCheckpoint = $false

# F5Only is deliberately an early, isolated route. It must never execute the
# historical F0-F4 setup, copy a runtime, or recreate a sandbox. The guard
# owns identity, lifecycle, lock and capacity authority; RealF5 additionally
# requires the guard-issued execution context before entering the canonical
# production F5 function.
if ($Mode -eq 'F5Only') {
    if (-not $ExistingSandboxPath -or -not [IO.Path]::IsPathRooted($ExistingSandboxPath)) {
        throw 'F5_ONLY_EXISTING_SANDBOX_REQUIRED'
    }
    if (-not (Test-Path -LiteralPath $ExistingSandboxPath -PathType Container)) {
        throw 'F5_ONLY_EXISTING_SANDBOX_INVALID'
    }
    if (-not $RunId) { throw 'F5_ONLY_RUN_ID_REQUIRED' }
    if (-not $InputManifestPath -or -not [IO.Path]::IsPathRooted($InputManifestPath)) {
        throw 'F5_ONLY_INPUT_MANIFEST_REQUIRED'
    }
    if (-not (Test-Path -LiteralPath $InputManifestPath -PathType Leaf)) {
        throw 'F5_ONLY_INPUT_MANIFEST_INVALID'
    }
    $sandbox = Get-CanonicalPath $ExistingSandboxPath
    $manifest = Get-Content -Raw -LiteralPath $InputManifestPath | ConvertFrom-Json
    if ([string]$manifest.sandbox_path -ne $sandbox) {
        throw 'F5_ONLY_SANDBOX_IDENTITY_MISMATCH'
    }
    if ($ExecutionMode -eq 'RealF5') {
        if (-not $ExecutionContextPath) { throw 'EXECUTION_CONTEXT_REQUIRED' }
        if (-not $EvidenceRoot -or -not [IO.Path]::IsPathRooted($EvidenceRoot)) {
            throw 'EXECUTION_CONTEXT_INVALID:EVIDENCE_ROOT_REQUIRED'
        }
        if ($DispatchHoldSeconds -lt 0) { throw 'EXECUTION_CONTEXT_INVALID:DISPATCH_HOLD_NEGATIVE' }
        $evidence = Get-CanonicalPath $EvidenceRoot
        $resourceId = Get-F5ContextResourceId $sandbox
        $stateRoot = if ($TestStateRoot) {
            Join-Path (Get-F5ContextCanonicalPath $TestStateRoot) $resourceId
        } else {
            Join-Path $repo "release_staging\control\a3_f5_guard\$resourceId"
        }
        $statePath = Join-Path $stateRoot 'lifecycle_state.json'
        $lockPath = Join-Path $stateRoot 'sandbox.lock'
        $guardPath = Join-Path $PSScriptRoot 'a3_f5_guard.ps1'
        Assert-F5ExecutionContext `
            -Context (Read-F5ExecutionContext $ExecutionContextPath) `
            -ContextPath $ExecutionContextPath `
            -RunId $RunId `
            -SandboxPath $sandbox `
            -ManifestPath $InputManifestPath `
            -EvidenceRoot $evidence `
            -LifecycleStatePath $statePath `
            -LockPath $lockPath `
            -GuardPath $guardPath `
            -ProbePath $PSCommandPath | Out-Null
        $probeLock = $null
        try {
            $probeLock = [IO.File]::Open($lockPath, [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None)
            $probeLock.Dispose()
            $probeLock = $null
            throw 'EXECUTION_CONTEXT_INVALID:LOCK_NOT_HELD'
        } catch [IO.IOException] {
            if ($null -ne $probeLock) { $probeLock.Dispose() }
        } catch {
            if ($null -ne $probeLock) { $probeLock.Dispose() }
            throw
        }
        if ($env:QI_CRAWLER_F5_TEST_MODE -ne '1') {
            if ($TestDispatchBoundary) {
                throw 'EXECUTION_CONTEXT_INVALID:DISPATCH_TEST_MODE'
            }
        }
        $f5OnlyRoute = $true
        $f5OnlySandbox = $sandbox
        $f5OnlyEvidenceRoot = $evidence
        $f5OnlyTestCheckpoint = [bool]$TestDispatchBoundary
    }
    if ($DryRun -or $ExecutionMode -eq 'DryRun') {
        Write-Output 'F5_ONLY_ROUTE_SELECTED'
        Write-Output 'GENERIC_SETUP_EXECUTED=NO'
        Write-Output 'RUNTIME_COPY_EXECUTED=NO'
        Write-Output 'EXISTING_SANDBOX_ONLY=YES'
        Write-Output "RUN_ID=$RunId"
        Write-Output 'DRY_RUN=YES'
        Write-Output 'F5_EXECUTED=NO'
        exit 0
    }
    if (-not $f5OnlyRoute) {
        throw 'F5_ONLY_REAL_ROUTE_REQUIRES_AO_04_C3_F5_01'
    }
}

$evidence = if ([IO.Path]::IsPathRooted($EvidenceRoot)) { Get-CanonicalPath $EvidenceRoot } else { Join-Path $repo $EvidenceRoot }
if ($f5OnlyTestCheckpoint) {
    # Context, manifest, lifecycle and held lock have already been validated.
    # The checkpoint does not execute P1-P5 and must not load release payloads.
    $stub = Join-Path $f5OnlySandbox 'install\QI-Crawler\QI-Crawler.exe'
    $legacyHash = 'NOT_RUN'
    $stubHash = 'NOT_RUN'
} else {
$candidate = (Resolve-Path -LiteralPath 'release_staging\candidate\QI-Crawler\QI-Crawler.exe').Path
$controller = (Resolve-Path -LiteralPath 'release_staging\evidence\WP-REL-RECON-01\AO-03\controller\dist\AO03-Controller.exe').Path
$stub = (Resolve-Path -LiteralPath 'release_staging\evidence\WP-REL-RECON-01\AO-03\stub\dist\QI-Crawler-Maintenance-Stub.exe').Path
$prep = (Resolve-Path -LiteralPath 'release_staging\evidence\WP-REL-RECON-01\AO-03\transaction\prep_data').Path
    $legacyHash = Get-Sha256 $candidate
    $ao03ControllerHash = Get-Sha256 $controller
    $stubHash = Get-Sha256 $stub
$controllerSource = (Resolve-Path -LiteralPath 'release_staging\evidence\WP-REL-RECON-01\AO-03\controller\ao03_controller.py').Path
}
$python = (Resolve-Path -LiteralPath '.venv\Scripts\python.exe').Path
$observer = (Resolve-Path -LiteralPath 'tools\release\a3_process_observer.py').Path
$recovery = (Resolve-Path -LiteralPath 'tools\release\a3_recovery.py').Path

function Write-Json([string]$Path, $Value) {
    $class = Resolve-F5WriteClass $Path
    Write-F5BoundedJson -Path $Path -Value $Value -WriteClass $class
}

function Write-FsyncJson([string]$Path, $Value) {
    $class = Resolve-F5WriteClass $Path
    Write-F5BoundedJson -Path $Path -Value $Value -WriteClass $class -Immutable
}

function Resolve-F5WriteClass([string]$Path) {
    $normalized = $Path.Replace('\','/').ToLowerInvariant()
    if ($normalized -match '/observer/.*\.(raw|config|snapshot)\.json$' -or $normalized -match '/observer/.*tree\.json$') { return 'PROCESS_CENSUS' }
    if ($normalized -match '/db_(before|at_barrier|after)\.json$') { return 'DB_MANIFEST' }
    if ($normalized -match '/recovery/') { return 'RECOVERY' }
    if ($normalized -match '/receipts/' -or $normalized -match '/routes/' -or $normalized -match '/controller/') { return 'ROUTE_ARTIFACTS' }
    return 'EVIDENCE_META'
}

function Assert-F5StubState($Identity, [string]$TrialRoot) {
    $path = Assert-ObserverPath ([string]$Identity.path) $TrialRoot
    if (-not (Test-Path -LiteralPath $path -PathType Leaf) -or
        (Get-Sha256 $path) -ne $Identity.sha256) { throw 'F5_STUB_STATE_IDENTITY_MISMATCH' }
    if ((Get-Sha256 ([string]$Identity.controller_path)) -ne $Identity.controller_sha256) {
        throw 'F5_STUB_CONTROLLER_IDENTITY_MISMATCH'
    }
    $state = Get-Content -LiteralPath $path -Raw | ConvertFrom-Json
    if ([string]$state.controller_path -cne [string]$Identity.controller_path -or
        [string]$state.controller_sha256 -cne [string]$Identity.controller_sha256) {
        throw 'F5_STUB_STATE_CONTENT_MISMATCH'
    }
    return $true
}

function Initialize-F5StubState([string]$CanonicalPath, [string]$TrialRoot,
    [string]$ControllerPath, [string]$ControllerSha256) {
    [void](Assert-ObserverPath $CanonicalPath $TrialRoot)
    $controllerFull = Get-CanonicalPath $ControllerPath
    if ($ControllerSha256 -notmatch '^[0-9a-fA-F]{64}$' -or
        -not (Test-Path -LiteralPath $controllerFull -PathType Leaf) -or
        (Get-Sha256 $controllerFull) -ne $ControllerSha256.ToLowerInvariant()) {
        throw 'F5_STUB_CONTROLLER_IDENTITY_MISMATCH'
    }
    $path = Join-Path (Split-Path -Parent $CanonicalPath) 'maintenance_stub_state.json'
    [void](Assert-ObserverPath $path $TrialRoot)
    # This is per-trial generated state, not a reusable static fixture. Never
    # overwrite leftovers. Only the two keys consumed by the frozen stub belong
    # here; trial identity is bound separately by the dependency receipt.
    $state = [ordered]@{controller_path=$controllerFull;controller_sha256=$ControllerSha256.ToLowerInvariant()}
    Write-F5BoundedJson -Path $path -Value $state -WriteClass TX_STATE -Immutable
    $identity = [ordered]@{path=$path;sha256=(Get-Sha256 $path);controller_path=$controllerFull;controller_sha256=$state.controller_sha256}
    [void](Assert-F5StubState $identity $TrialRoot)
    return $identity
}

function Get-ProcessTreeEvidence([int[]]$Roots) {
    $all = @()
    $status = 'SUCCESS'
    $errorText = $null
    try { $all = @((Get-A3NativeProcessSnapshot).processes) }
    catch { $status = if ($_.Exception.Message -match 'denied|access') { 'ACCESS_DENIED' } else { 'ERROR' }; $errorText = $_.Exception.Message }
    $ids = [Collections.Generic.HashSet[int]]::new()
    foreach ($root in $Roots) { [void]$ids.Add($root) }
    $rootStatuses = @()
    foreach ($root in $Roots) {
        $rootStatuses += [ordered]@{pid=$root;exists=$(if($status -eq 'SUCCESS'){@($all | Where-Object pid -eq $root).Count -gt 0}else{$null})}
    }
    if ($status -ne 'SUCCESS') {
        return [pscustomobject]@{ids=@($ids);snapshot_status=$status;enumeration_status=$status;enumeration_source='TOOLHELP32';root_pid_status=$rootStatuses;descendant_discovery_status='UNRESOLVED';unresolved_descendants=$errorText}
    }
    # Toolhelp PPIDs outlive their parents and may refer to a reused PID.
    # A child created before the current parent is a proven stale edge, not
    # a descendant. Unknown creation identity remains unresolved/fail-closed.
    $creationTimes = @{}
    $examined = [Collections.Generic.HashSet[int]]::new()
    $rejected = [Collections.Generic.List[object]]::new()
    $unresolved = [Collections.Generic.List[object]]::new()
    $changed = $true
    while ($changed) {
        $changed = $false
        foreach ($proc in $all) {
            if ($proc.ppid -notin $ids -or $ids.Contains([int]$proc.pid) -or
                -not $examined.Add([int]$proc.pid)) { continue }
            try {
                foreach ($identityPid in @([int]$proc.ppid, [int]$proc.pid)) {
                    if (-not $creationTimes.ContainsKey($identityPid)) {
                        $identityProcess = Get-Process -Id $identityPid -ErrorAction Stop
                        $created = $identityProcess.StartTime.ToUniversalTime()
                        if ($created.Year -lt 1970) { throw 'PROCESS_CREATION_TIME_INVALID' }
                        $creationTimes[$identityPid] = $created
                    }
                }
                if ($creationTimes[[int]$proc.pid] -lt $creationTimes[[int]$proc.ppid]) {
                    $rejected.Add([ordered]@{
                        pid=[int]$proc.pid;ppid=[int]$proc.ppid
                        reason='CHILD_PREDATES_PARENT'
                        child_created_utc=$creationTimes[[int]$proc.pid].ToString('o')
                        parent_created_utc=$creationTimes[[int]$proc.ppid].ToString('o')
                    })
                    continue
                }
                if ($ids.Add([int]$proc.pid)) { $changed = $true }
            } catch {
                $unresolved.Add([ordered]@{pid=[int]$proc.pid;ppid=[int]$proc.ppid;reason='PROCESS_CREATION_IDENTITY_UNAVAILABLE'})
            }
        }
    }
    return [pscustomobject]@{
        ids=@($ids);snapshot_status=$status;enumeration_status=$(if($unresolved.Count){'PARTIAL'}else{$status})
        enumeration_source='TOOLHELP32';root_pid_status=$rootStatuses
        descendant_discovery_status=$(if($unresolved.Count){'UNRESOLVED'}else{'COMPLETE'})
        unresolved_descendants=$unresolved.ToArray();rejected_parent_edges=$rejected.ToArray()
    }
}

function Test-ProcessTreeFailClosed([string]$TrialRoot) {
    # Deterministic negative control: an invalid root must not be treated as a
    # proven tree-zero result. The status must remain explicit and auditable.
    $ids = Get-DescendantIds @(-1)
    $status = $script:lastProcessTreeEvidence.enumeration_status
    if ($status -in @('ACCESS_DENIED','ERROR','PARTIAL')) {
        return ($script:lastProcessTreeEvidence.descendant_discovery_status -ne 'COMPLETE')
    }
    $unknownRoot = @(Get-RawCensus @(-1) $TrialRoot)
    return (@($ids).Count -eq 1 -and
        $status -eq 'SUCCESS' -and
        $script:lastProcessTreeEvidence.root_pid_status[0].exists -eq $false -and
        @($unknownRoot | Where-Object { $_.pid -eq -1 -and $_.access_status -eq 'PID_RECEIPT_UNREADABLE' -and $_.relevant }).Count -eq 1)
}

function Get-DescendantIds([int[]]$Roots) {
    $tree = Get-ProcessTreeEvidence $Roots
    $script:lastProcessTreeEvidence = $tree
    if ($tree.enumeration_status -ne 'SUCCESS' -or $tree.descendant_discovery_status -ne 'COMPLETE') {
        # Fail closed without abandoning the evidence run. Root-only cleanup is
        # best-effort; every tree-zero claim remains false until full
        # enumeration is available and the failure is persisted by the caller.
        return @($Roots)
    }
    return @($tree.ids)
}

function Stop-SandboxTree([int[]]$Roots) {
    foreach ($procId in (Get-DescendantIds $Roots | Sort-Object -Descending)) {
        try { Stop-Process -Id $procId -Force -ErrorAction Stop } catch { }
    }
    Start-Sleep -Milliseconds 200
}

function Test-ProcessIdsGone([int[]]$ProcessIds) {
    if ($script:lastProcessTreeEvidence -and
        ($script:lastProcessTreeEvidence.enumeration_status -ne 'SUCCESS' -or
         $script:lastProcessTreeEvidence.descendant_discovery_status -ne 'COMPLETE')) {
        return $false
    }
    foreach ($procId in $ProcessIds) { if (Get-Process -Id $procId -ErrorAction SilentlyContinue) { return $false } }
    return $true
}

function Assert-ObserverPath([string]$Path, [string]$TrialRoot) {
    if (-not $Path -or -not $TrialRoot -or -not [IO.Path]::IsPathRooted($Path)) { throw 'OBSERVER_SCOPE_VIOLATION' }
    $root = [IO.Path]::GetFullPath($TrialRoot).TrimEnd('\')
    $full = [IO.Path]::GetFullPath($Path)
    if (-not ($full.Equals($root, [StringComparison]::OrdinalIgnoreCase) -or
        $full.StartsWith($root + '\', [StringComparison]::OrdinalIgnoreCase))) {
        throw 'OBSERVER_SCOPE_VIOLATION'
    }
    $cursor = $full
    while ($cursor.Length -ge $root.Length) {
        $item = Get-Item -LiteralPath $cursor -Force -ErrorAction SilentlyContinue
        if ($item -and ($item.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'OBSERVER_SCOPE_VIOLATION:REPARSE_POINT' }
        if ($cursor.Equals($root, [StringComparison]::OrdinalIgnoreCase)) { break }
        $cursor = Split-Path -Parent $cursor
    }
    return $full
}

function Get-RawCensus([int[]]$KnownPids, [string]$TrialRoot) {
    $records = [Collections.Generic.List[object]]::new()
    # An empty sandbox identity set cannot authorize a machine-wide census.
    if (@($KnownPids).Count -gt 0) {
        $tree = Get-ProcessTreeEvidence $KnownPids
        if ($tree.enumeration_status -ne 'SUCCESS' -or $tree.descendant_discovery_status -ne 'COMPLETE') {
            throw 'OBSERVER_PROCESS_ENUMERATION_UNRESOLVED'
        }
        $nativeByPid = @{}
        foreach ($nativeProcess in @((Get-A3NativeProcessSnapshot).processes)) {
            $nativeByPid[[int]$nativeProcess.pid] = $nativeProcess
        }
        foreach ($procId in @($tree.ids)) {
            $nativeReceipt = $nativeByPid[[int]$procId]
            $proc = Get-Process -Id $procId -ErrorAction SilentlyContinue
            if (-not $proc) {
                $records.Add([ordered]@{ pid=$procId; parent_pid=$(if($nativeReceipt){[int]$nativeReceipt.ppid}else{$null}); image_path=$null; image_sha256=$null; start_time_utc=$null; command_line=$null; access_status='PID_RECEIPT_UNREADABLE'; metadata_status='UNKNOWN'; evidence_source='sandbox-PID/TOOLHELP32'; relevant=$true })
                continue
            }
            $path = $null; $access = 'PASS'; $cmd = $null; $parent = $null; $digest = $null
            try { $path = $proc.Path } catch { $access = 'ACCESS_DENIED_OR_UNAVAILABLE' }
            if ($nativeReceipt) { $parent = [int]$nativeReceipt.ppid }
            else { $access = 'PID_RECEIPT_UNREADABLE' }
            if (-not $path) { $access = 'ACCESS_DENIED_OR_UNAVAILABLE' }
            if ($path) {
                # Outside executables (for example the job-bound Python controller)
                # are never opened or hashed by the sandbox observer. A path
                # lexically inside the sandbox must pass the reparse check.
                $root = [IO.Path]::GetFullPath($TrialRoot).TrimEnd('\')
                $full = [IO.Path]::GetFullPath($path)
                if ($full.Equals($root, [StringComparison]::OrdinalIgnoreCase) -or
                    $full.StartsWith($root + '\', [StringComparison]::OrdinalIgnoreCase)) {
                    $safePath = Assert-ObserverPath $path $TrialRoot
                } else { $safePath = $null }
                if ($safePath -and (Test-Path -LiteralPath $safePath -PathType Leaf)) {
                    $digest = Get-Sha256 $safePath
                }
            }
            $started = $null
            try { $started = $proc.StartTime.ToUniversalTime().ToString('o') } catch { }
            $records.Add([ordered]@{
                pid=[int]$proc.Id; parent_pid=$parent; image_path=$path
                image_sha256=$digest; start_time_utc=$started; command_line=$cmd
                access_status=$access; metadata_status='UNKNOWN'; evidence_source='sandbox-PID/Get-Process/TOOLHELP32'; relevant=$true
            })
        }
    }
    $boundedRecords = @($records)
    $limit = Get-F5BoundedLimit 'PROCESS_CENSUS'
    Assert-F5BoundedRecords -Records $boundedRecords -MaxRecords ([Int64]$limit.max_records) -MaxFieldBytes ([Int64]$limit.max_field_bytes) -MaxSerializedBytes ([Int64]$limit.max_per_file_bytes) -Label 'PROCESS_CENSUS'
    return ,$boundedRecords
}

function Invoke-Observer([string]$Name, [int[]]$KnownPids, [bool]$Positive, [bool]$RootsAbsent, [string]$TrialRoot, [string]$TrialId = '', [int]$ControllerRootPid = 0, [string]$ControllerTreeStatus = '', [int[]]$ContainedPids = @()) {
    $rawPath = Join-Path $evidence "observer\$Name.raw.json"
    $configPath = Join-Path $evidence "observer\$Name.config.json"
    $outPath = Join-Path $evidence "observer\$Name.snapshot.json"
    $records = Get-RawCensus $KnownPids $TrialRoot
    Write-Json $rawPath $records
    $controllerIds=[Collections.Generic.HashSet[int]]::new()
    if ($ControllerRootPid) { [void]$controllerIds.Add($ControllerRootPid) }
    foreach ($containedPid in $ContainedPids) { [void]$controllerIds.Add($containedPid) }
    $config = [ordered]@{
        trial_root=$TrialRoot; legacy_paths=@((Join-Path $TrialRoot 'install\QI-Crawler\QI-Crawler.exe'))
        controller_paths=@(); stub_paths=@((Join-Path $TrialRoot 'install\QI-Crawler\QI-Crawler.exe'))
        legacy_sha256=$legacyHash; stub_sha256=$stubHash; known_pids=@($KnownPids)
        controller_pids=@($controllerIds)
        route_pids=@($(if($Name -like 'F5_route_*'){$KnownPids}))
    }
    Write-Json $configPath $config
    $args = @($observer, '--records-json', $rawPath, '--config-json', $configPath, '--event', $Name)
    if ($Positive) { $args += '--positive-control' }; if ($RootsAbsent) { $args += '--roots-absent' }
    $processResultPath = Join-Path $evidence "observer\$Name.process.json"
    $processResult = Invoke-F5BoundedProcess -FilePath $python -Arguments $args -WriteClass ROUTE_ARTIFACTS -ResultPath $processResultPath
    if ($processResult.exit_code -ne 0) { throw "observer failed: $Name" }
    $snapshot = ($processResult.stdout | ConvertFrom-Json)
    $script:observerSequence++
    $snapshot | Add-Member -NotePropertyName trial_id -NotePropertyValue $TrialId -Force
    $snapshot | Add-Member -NotePropertyName monotonic_sequence -NotePropertyValue $script:observerSequence -Force
        $snapshot | Add-Member -NotePropertyName observer_source_sha256 -NotePropertyValue (Get-Sha256 $observer) -Force
    $snapshot | Add-Member -NotePropertyName controller_root_pid -NotePropertyValue $(if($ControllerRootPid){$ControllerRootPid}else{$null}) -Force
    $snapshot | Add-Member -NotePropertyName controller_tree_status -NotePropertyValue $ControllerTreeStatus -Force
    Write-F5BoundedJson -Path $outPath -Value $snapshot -WriteClass PROCESS_CENSUS
    return $snapshot
}

$script:observerSequence = 0

function Get-DbManifest([string]$DataRoot, [string]$ObservationRoot = '') {
    $dbRoot = Join-Path $DataRoot 'data\database'
    if ($ObservationRoot) { [void](Assert-ObserverPath $dbRoot $ObservationRoot) }
    $entries = @()
    foreach ($name in @('egp.db','egp.db-wal','egp.db-shm','egp.db-journal')) {
        $path = Join-Path $dbRoot $name
        if ($ObservationRoot) { [void](Assert-ObserverPath $path $ObservationRoot) }
        if (Test-Path -LiteralPath $path -PathType Leaf) {
            $item = Get-Item -LiteralPath $path
            $entries += [ordered]@{name=$name; size_bytes=[int64]$item.Length; sha256=(Get-Sha256 $path)}
        } else { $entries += [ordered]@{name=$name; size_bytes=$null; sha256=$null} }
    }
    return [ordered]@{root=$dbRoot; files=@($entries)}
}

function Get-TreeManifest([string]$Root) {
    $full = Get-CanonicalPath $Root
    $entries = @()
    foreach ($item in @(Get-ChildItem -LiteralPath $full -Recurse -File -Force | Sort-Object FullName)) {
        $entries += [ordered]@{relative=(Get-SafeRelativePath $full $item.FullName); size_bytes=[int64]$item.Length; sha256=(Get-Sha256 $item.FullName)}
    }
    return @($entries)
}

function Get-F5LogicalDigest([string]$DatabasePath, [string]$ResultPath, [string]$ExpectedSchema) {
    $captured = Invoke-F5BoundedProcess -FilePath $python -Arguments @('-m','tools.release.a3_f5_seed_db','--digest',$DatabasePath) -WriteClass RECOVERY -ResultPath $ResultPath
    if ($captured.exit_code -ne 0) { throw 'F5_LOGICAL_DIGEST_PROCESS_FAILED' }
    try { $digest = [string]$captured.stdout | ConvertFrom-Json -ErrorAction Stop } catch { throw 'F5_LOGICAL_DIGEST_MALFORMED' }
    if (-not $digest.sha256 -or [string]$digest.revision -ne $ExpectedSchema) { throw 'F5_LOGICAL_DIGEST_SCHEMA_MISMATCH' }
    return $digest
}

function Assert-F5MaintenanceRecovery {
    param(
        [Parameter(Mandatory=$true)] [string]$EvidenceRoot,
        [Parameter(Mandatory=$true)] [string]$SandboxRoot,
        [Parameter(Mandatory=$true)] [string]$TrialId,
        [Parameter(Mandatory=$true)] [string]$ProcessReceiptPath,
        [Parameter(Mandatory=$true)] [string]$ObserverReceiptPath,
        [Parameter(Mandatory=$true)] [string]$CanonicalPath,
        [Parameter(Mandatory=$true)] [string]$ExpectedStubSha256,
        [Parameter(Mandatory=$true)] $DbBefore,
        [Parameter(Mandatory=$true)] $DbAfter,
        [Parameter(Mandatory=$true)] $LogicalBefore,
        [Parameter(Mandatory=$true)] $LogicalAfter,
        [Parameter(Mandatory=$true)] [string]$ExpectedSchema
    )
    foreach ($path in @($ProcessReceiptPath,$ObserverReceiptPath)) {
        [void](Assert-ObserverPath $path $EvidenceRoot)
        if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw 'F5_RECOVERY_EVIDENCE_MISSING' }
    }
    [void](Assert-ObserverPath $CanonicalPath $SandboxRoot)
    if (-not (Test-Path -LiteralPath $CanonicalPath -PathType Leaf)) { throw 'F5_FINAL_STUB_MISSING' }
    try {
        $process = Get-Content -Raw -LiteralPath $ProcessReceiptPath | ConvertFrom-Json -ErrorAction Stop
        $observer = Get-Content -Raw -LiteralPath $ObserverReceiptPath | ConvertFrom-Json -ErrorAction Stop
        $outcome = [string]$process.stdout | ConvertFrom-Json -ErrorAction Stop
    } catch { throw 'F5_RECOVERY_EVIDENCE_MALFORMED' }
    if ([string]$observer.trial_id -ne $TrialId -or [string]$process.trial_id -ne $TrialId -or
        $observer.legacy_zero_proven -ne $true) { throw 'F5_RECOVERY_TRIAL_IDENTITY_MISMATCH' }
    # Post-barrier recovery must refuse automatic legacy restoration. Exit 2 is
    # the expected *successful safety outcome*, not a migration/restore success.
    if ($process.exit_code -ne 2 -or [string]$outcome.status -ne 'MAINTENANCE_RECOVERY_REQUIRED' -or $outcome.mutated -ne $false) {
        throw 'F5_MAINTENANCE_RECOVERY_OUTCOME_INVALID'
    }
    if ((Get-Sha256 $CanonicalPath) -ne $ExpectedStubSha256) { throw 'F5_FINAL_STUB_IDENTITY_MISMATCH' }
    if (($DbBefore | ConvertTo-Json -Depth 20 -Compress) -cne ($DbAfter | ConvertTo-Json -Depth 20 -Compress)) {
        throw 'F5_FINAL_DB_PHYSICAL_IDENTITY_MISMATCH'
    }
    if (-not $LogicalBefore.sha256 -or -not $LogicalAfter.sha256 -or
        [string]$LogicalBefore.revision -ne $ExpectedSchema -or
        [string]$LogicalAfter.revision -ne $ExpectedSchema -or
        [string]$LogicalBefore.sha256 -cne [string]$LogicalAfter.sha256) {
        throw 'F5_FINAL_DB_LOGICAL_OR_SCHEMA_MISMATCH'
    }
    return $true
}

function Write-F5BoundedShortcut {
    param(
        [Parameter(Mandatory=$true)] [string]$Path,
        [Parameter(Mandatory=$true)] [string]$TargetPath,
        [Parameter(Mandatory=$true)] [string]$Root
    )
    $temporary = $Path + '.bounded.tmp.lnk'
    foreach ($candidate in @($Path,$temporary,$TargetPath)) { [void](Assert-ObserverPath $candidate $Root) }
    if (-not (Test-Path -LiteralPath $TargetPath -PathType Leaf) -or
        (Test-Path -LiteralPath $Path) -or (Test-Path -LiteralPath $temporary)) {
        throw 'F5_SHORTCUT_DESTINATION_INVALID'
    }
    # A shortcut is expected below 8 KiB. Reserve that conservative maximum
    # *before* COM can create anything; actual size is checked again below.
    Assert-F5WriteBudget 'ROUTE_ARTIFACTS' 8192
    try {
        $shell = New-Object -ComObject WScript.Shell
        $shortcut = $shell.CreateShortcut($temporary)
        $shortcut.TargetPath = $TargetPath
        $shortcut.WorkingDirectory = Split-Path -Parent $TargetPath
        $shortcut.Save()
        if (-not (Test-Path -LiteralPath $temporary -PathType Leaf)) { throw 'F5_SHORTCUT_WRITE_FAILED' }
        $size = [Int64](Get-Item -LiteralPath $temporary).Length
        if ($size -gt 8192) { throw 'MATERIAL_WRITE_BOUND_EXCEEDED: ROUTE_ARTIFACTS shortcut' }
        Assert-F5WriteBudget 'ROUTE_ARTIFACTS' $size
        [IO.File]::Move($temporary,$Path)
        Add-F5WriteUsage 'ROUTE_ARTIFACTS' $size
    } catch {
        if (Test-Path -LiteralPath $temporary -PathType Leaf) { Remove-Item -LiteralPath $temporary -Force -ErrorAction SilentlyContinue }
        throw
    }
    return $shell.CreateShortcut($Path).TargetPath
}

function Get-F5EvidenceManifestEntries([string]$Root, [string]$TrialId) {
    $fullRoot = Get-CanonicalPath $Root
    $excluded = @('evidence_manifest.json','gate_inputs.json','aggregate_positive.process.json',
        'aggregate_negative_control.json','aggregate_negative.process.json',
        'AO_04_PROBE_SUMMARY.json','probe_verdict_core.json','probe_verdict.json')
    $entries = @()
    foreach($item in @(Get-ChildItem -LiteralPath $fullRoot -Recurse -File -Force | Sort-Object FullName)) {
        $relative = Get-SafeRelativePath $fullRoot $item.FullName
        if ($relative -in $excluded) { continue }
        $entries += [ordered]@{relative_path=$relative;artifact_role='AO-04-C2 runtime evidence';size_bytes=[Int64]$item.Length;sha256=(Get-Sha256 $item.FullName);trial_id=$TrialId;created_or_observed_timestamp=$item.LastWriteTimeUtc.ToString('o')}
    }
    return ,$entries
}

function Assert-F5EvidenceManifest {
    param(
        [Parameter(Mandatory=$true)] [string]$Root,
        [Parameter(Mandatory=$true)] [string]$ManifestPath,
        [Parameter(Mandatory=$true)] [string]$TrialId,
        [string[]]$RequiredPaths = @()
    )
    [void](Assert-ObserverPath $ManifestPath $Root)
    if (-not (Test-Path -LiteralPath $ManifestPath -PathType Leaf)) { throw 'F5_EVIDENCE_MANIFEST_MISSING' }
    try {
        $parsed = Get-Content -Raw -LiteralPath $ManifestPath | ConvertFrom-Json -ErrorAction Stop
        $persisted = [Collections.Generic.List[object]]::new()
        foreach ($entry in $parsed) { $persisted.Add($entry) }
    }
    catch { throw 'F5_EVIDENCE_MANIFEST_MALFORMED' }
    $actual = Get-F5EvidenceManifestEntries $Root $TrialId
    if ($persisted.Count -ne $actual.Count -or $actual.Count -eq 0) { throw "F5_EVIDENCE_MANIFEST_INCOMPLETE: persisted=$($persisted.Count) actual=$($actual.Count)" }
    $listed = @{}
    for ($index=0; $index -lt $actual.Count; $index++) {
        $expected = $actual[$index]; $entry = $persisted[$index]
        if ([string]$entry.relative_path -cne [string]$expected.relative_path -or
            [string]$entry.trial_id -cne $TrialId -or
            [Int64]$entry.size_bytes -ne [Int64]$expected.size_bytes -or
            [string]$entry.sha256 -cne [string]$expected.sha256) {
            throw 'F5_EVIDENCE_MANIFEST_IDENTITY_MISMATCH'
        }
        $listed[[string]$entry.relative_path] = $true
    }
    foreach ($required in $RequiredPaths) {
        if (-not $listed.ContainsKey($required)) { throw "F5_EVIDENCE_REQUIRED_ARTIFACT_MISSING: $required" }
    }
    return $true
}

function New-EvidenceManifest([string]$Root, [string]$TrialId, [string[]]$RequiredPaths = @()) {
    $entries = Get-F5EvidenceManifestEntries $Root $TrialId
    Assert-F5BoundedRecords -Records @($entries) -MaxRecords 4096 -MaxFieldBytes 32768 -MaxSerializedBytes 8388608 -Label 'EVIDENCE_META_MANIFEST'
    $path=Join-Path $Root 'evidence_manifest.json'
    Write-FsyncJson $path $entries
    [void](Assert-F5EvidenceManifest -Root $Root -ManifestPath $path -TrialId $TrialId -RequiredPaths $RequiredPaths)
    return [pscustomobject]@{path=$path;sha256=(Get-Sha256 $path);entry_count=$entries.Count;verified=$true}
}

function New-Trial([string]$Name) {
    $root = Join-Path $evidence "trials\$Name"
    if (Test-Path -LiteralPath $root) { Remove-Item -LiteralPath $root -Recurse -Force }
    $install = Join-Path $root 'install'; $app = Join-Path $install 'QI-Crawler'; $data = Join-Path $root 'data'
    New-Item -ItemType Directory -Force -Path $app,$data | Out-Null
    Copy-Item -LiteralPath $candidate -Destination (Join-Path $app 'QI-Crawler.exe') -Force
    foreach ($item in @(Get-ChildItem -LiteralPath $prep -Force)) { Copy-Item -LiteralPath $item.FullName -Destination $data -Recurse -Force }
    [IO.File]::WriteAllText((Join-Path $install 'unknown-runtime-sentinel.txt'), 'preserve', [Text.UTF8Encoding]::new($false))
    return [pscustomobject]@{root=$root; install=$install; app=$app; canonical=(Join-Path $app 'QI-Crawler.exe'); data=$data; db=(Join-Path $data 'data\database'); tx=(Join-Path $root 'transaction')}
}

function Start-Python([string[]]$Arguments) {
    $info = [Diagnostics.ProcessStartInfo]::new(); $info.FileName=$python; $info.WorkingDirectory=$repo; $info.UseShellExecute=$false
    foreach ($arg in $Arguments) { [void]$info.ArgumentList.Add($arg) }
    return [Diagnostics.Process]::Start($info)
}

function New-F5HandshakeController([string]$Destination) {
    # The AO-03 controller already has durable A3-F4/A3-F5 pause markers.  The
    # C1 probe uses a private copy with a combined failpoint so the controller
    # cannot pass either side of the barrier until the harness acknowledges the
    # corresponding census.  The source is evidence-only; product/runtime
    # sources are never modified.
    $source = [IO.File]::ReadAllText($controllerSource)
    $source = $source.Replace(
        'if failpoint != expected:',
        'if failpoint != expected and not (failpoint == "A3-F4-F5" and expected in ("A3-F4", "A3-F5")):'
    )
    $source = $source.Replace(
        'continue_file = marker.parent / "continue"',
        'continue_file = marker.parent / f"continue-{expected}"'
    )
    $source = $source.Replace(
        'raw = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")',
        'raw = (json.dumps(payload, indent=2, sort_keys=True) + "\n").encode("utf-8")' + "`n" + '    if len(raw) > 1048576: raise RuntimeError("MATERIAL_WRITE_BOUND_EXCEEDED: TX_STATE")'
    )
    $source = $source.Replace(
        'marker.write_text(expected + "\n", encoding="utf-8")',
        'raw_marker = (expected + "\n").encode("utf-8")' + "`n" + '    if len(raw_marker) > 64: raise RuntimeError("MATERIAL_WRITE_BOUND_EXCEEDED: TX_STATE marker")' + "`n" + '    marker.write_bytes(raw_marker)'
    )
    $parent = Split-Path -Parent $Destination
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
    Write-F5BoundedText -Path $Destination -Text $source -WriteClass ROUTE_ARTIFACTS
    return Get-Sha256 $Destination
}

function Get-JsonFileSha256([string]$Path) {
    return Get-Sha256 $Path
}

function Get-F5Phase([string]$Journal) {
    if (-not (Test-Path -LiteralPath $Journal)) { return $null }
    try { return ((Get-Content -Raw -LiteralPath $Journal) | ConvertFrom-Json).phase } catch { return $null }
}

$f5EventSequence = [Collections.Generic.List[object]]::new()
$f5SequenceNumber = 0
$script:f5CurrentSnapshot = $null
$script:f5CurrentDbManifestSha = $null
$script:f5ObserverSourceSha = Get-Sha256 $observer
$script:f5CanonicalPath = $null
$script:f5LegacyHash = $legacyHash
$script:f5ControllerTreeCount = $null
$script:f5RecoveryProcessRunning = $null
function Add-F5Event([string]$Event, [string]$TrialId, [int]$RelevantPid, [string]$Phase, [string]$Artifact) {
    $script:f5SequenceNumber++
    $canonicalHash = $null
    if ($script:f5CanonicalPath -and (Test-Path -LiteralPath $script:f5CanonicalPath -PathType Leaf)) {
        $canonicalHash = Get-Sha256 $script:f5CanonicalPath
    }
    $snapshot = $script:f5CurrentSnapshot
    $script:f5EventSequence.Add([ordered]@{
        sequence=[int]$script:f5SequenceNumber
        timestamp_utc=(Get-Date).ToUniversalTime().ToString('o')
        actor='AO-04-C1-PROBE'
        event=$Event
        event_name=$Event
        trial_id=$TrialId
        relevant_PID=if($RelevantPid){$RelevantPid}else{$null}
        transaction_phase=$Phase
        evidence_artifact=$Artifact
        observer_source_sha256=$script:f5ObserverSourceSha
        canonical_exe_path=$script:f5CanonicalPath
        canonical_exe_sha256=$canonicalHash
        legacy_recovery_exe_sha256=$script:f5LegacyHash
        process_records=if($snapshot){@($snapshot.records)}else{@()}
        legacy_count=if($snapshot){$snapshot.legacy_count}else{$null}
        unresolved_relevant_count=if($snapshot){$snapshot.unresolved_relevant_count}else{$null}
        legacy_zero_proven=if($snapshot){$snapshot.legacy_zero_proven}else{$null}
        DB_generation_manifest_sha256=$script:f5CurrentDbManifestSha
        controller_process_tree_count=$script:f5ControllerTreeCount
        recovery_process_running=$script:f5RecoveryProcessRunning
    })
}

function Wait-File([string]$Path, [int]$Seconds = 20) {
    $until = (Get-Date).AddSeconds($Seconds)
    while (-not (Test-Path -LiteralPath $Path) -and (Get-Date) -lt $until) { Start-Sleep -Milliseconds $PollMilliseconds }
    return (Test-Path -LiteralPath $Path)
}

function Wait-Phase([string]$Journal, [string]$Expected, [int]$Seconds = 20) {
    $until = (Get-Date).AddSeconds($Seconds)
    while ((Get-Date) -lt $until) {
        if (Test-Path -LiteralPath $Journal) { try { if ((Get-Content -Raw -LiteralPath $Journal | ConvertFrom-Json).phase -eq $Expected) { return $true } } catch { } }
        Start-Sleep -Milliseconds $PollMilliseconds
    }
    return $false
}

function Wait-AnyPhase([string]$Journal, [string[]]$Expected, [int]$Seconds = 20) {
    $until = (Get-Date).AddSeconds($Seconds)
    while ((Get-Date) -lt $until) {
        if (Test-Path -LiteralPath $Journal) { try { if ((Get-Content -Raw -LiteralPath $Journal | ConvertFrom-Json).phase -in $Expected) { return $true } } catch { } }
        Start-Sleep -Milliseconds $PollMilliseconds
    }
    return $false
}

function Invoke-RecoveryCli($Trial, [string]$ObserverJson, [switch]$Barrier, [string]$Failpoint, [string]$PauseFile, [string]$TrialId = '') {
    $args = @('-m','tools.release.a3_recovery','--canonical',$Trial.canonical,'--recovery',(Join-Path $Trial.tx 'legacy\QI-Crawler.exe'),'--transaction-root',$Trial.tx,'--db-root',$Trial.db,'--legacy-sha256',$legacyHash,'--expected-schema','0020_add_tender_operational_revision_events','--observer-json',$ObserverJson)
    if ($Barrier) { $args += '--barrier-confirmed' }; if ($Failpoint) { $args += @('--failpoint',$Failpoint) }; if ($PauseFile) { $args += @('--pause-file',$PauseFile) }
    $script:recoveryInvocationSequence++
    $capturePath = Join-Path $evidence ("recovery\cli_{0:D3}.process.json" -f $script:recoveryInvocationSequence)
    $captured = Invoke-F5BoundedProcess -FilePath $python -Arguments $args -WriteClass RECOVERY -ResultPath $capturePath -TrialId $TrialId
    $text = ([string]$captured.stdout).Trim()
    $parsed = if($text){try{$text|ConvertFrom-Json}catch{$null}}else{$null}
    return [pscustomobject]@{exit_code=$captured.exit_code; output=$text; json=$parsed; receipt_path=$capturePath}
}

$script:recoveryInvocationSequence = 0

function Start-RecoveryProcess($Trial, [string]$ObserverJson, [string]$Failpoint, [string]$PauseFile) {
    $args = @('-m','tools.release.a3_recovery','--canonical',$Trial.canonical,'--recovery',(Join-Path $Trial.tx 'legacy\QI-Crawler.exe'),'--transaction-root',$Trial.tx,'--db-root',$Trial.db,'--legacy-sha256',$legacyHash,'--expected-schema','0020_add_tender_operational_revision_events','--observer-json',$ObserverJson,'--failpoint',$Failpoint,'--pause-file',$PauseFile)
    return Start-Python $args
}

function Invoke-ControllerTrial([string]$Name, [string]$Failpoint) {
    $trial=New-Trial $Name; $marker=Join-Path $trial.tx "markers\$Failpoint.ready"; $before=Get-DbManifest $trial.data; $unknownBefore=Get-TreeManifest $trial.install
    $proc=Start-Python @($controllerSource,'--install-root',$trial.install,'--tx-root',$trial.tx,'--stub',$stub,'--db-root',$trial.data,'--failpoint',$Failpoint)
    if (-not (Wait-File $marker)) { Stop-SandboxTree @($proc.Id); throw "$Name controller did not reach $Failpoint" }
    $treeIds=Get-DescendantIds @($proc.Id); $treeEvidence=$script:lastProcessTreeEvidence; Write-Json (Join-Path $evidence "observer\${Name}_tree.json") $treeEvidence; Stop-SandboxTree @($proc.Id); $treeDead=Test-ProcessIdsGone $treeIds
    $observerSnapshot=Invoke-Observer "${Name}_zero" @($proc.Id) $true $true $trial.root
    $observerJson=Join-Path $evidence "observer\${Name}_zero.snapshot.json"
    $legacyBefore=Get-TreeManifest $trial.install
    $first=Invoke-RecoveryCli $trial $observerJson
    $second=Invoke-RecoveryCli $trial $observerJson
    $after=Get-DbManifest $trial.data; $unknownAfter=Get-TreeManifest $trial.install
    $finalHash=Get-Sha256 $trial.canonical
    $result=[ordered]@{failpoint=$Failpoint; controller_pid=$proc.Id; controller_tree_dead=$treeDead; controller_tree_evidence=$treeEvidence; observer_zero=$observerSnapshot; recovery=$first; idempotence=$second; final_state=if($finalHash -eq $legacyHash -and $first.json.status -eq 'LEGACY_READY'){'LEGACY_READY'}else{'RECOVERY_REQUIRED'}; db_before=$before; db_after=$after; db_generation_unchanged=(($before|ConvertTo-Json -Compress) -eq ($after|ConvertTo-Json -Compress)); unknown_files_unchanged=(($unknownBefore|ConvertTo-Json -Compress) -eq ($unknownAfter|ConvertTo-Json -Compress)); install_manifest_before_count=$legacyBefore.Count; final_sha256=$finalHash}
    Write-Json (Join-Path $evidence "recovery\$Name.json") $result
    return $result
}

if (-not $f5OnlyRoute) {
New-Item -ItemType Directory -Force -Path $evidence | Out-Null
$trial = Join-Path $evidence 'sandbox'
if (Test-Path -LiteralPath $trial) { Remove-Item -LiteralPath $trial -Recurse -Force }
New-Item -ItemType Directory -Force -Path $trial | Out-Null
$trialInstall = Join-Path $trial 'install'; $trialData = Join-Path $trial 'data'
Copy-Item -LiteralPath (Split-Path -Parent $candidate) -Destination $trialInstall -Recurse -Force
Copy-Item -LiteralPath $prep -Destination $trialData -Recurse -Force
$config = Join-Path $trial 'config.yaml'; $sourceConfig = Join-Path $prep 'config.yaml'
$configText = (Get-Content -Raw -LiteralPath $sourceConfig).Replace($prep, $trialData)
[IO.File]::WriteAllText($config, $configText, [Text.UTF8Encoding]::new($false))

# Real positive control: exact retained v0.9 candidate is launched only in the sandbox.
$legacyPath = Join-Path $trialInstall 'QI-Crawler.exe'
$start = [Diagnostics.ProcessStartInfo]::new(); $start.FileName=$legacyPath; $start.WorkingDirectory=(Split-Path -Parent $legacyPath); $start.UseShellExecute=$false
$start.Environment['QI_CRAWLER_DATA_DIR']=$trialData; $start.Environment['QI_CRAWLER_CONFIG_PATH']=$config
$legacyProcess=[Diagnostics.Process]::Start($start); Start-Sleep -Milliseconds 1000
$running=Invoke-Observer 'positive_running' @($legacyProcess.Id) $true $false $trialInstall
if ($running.legacy_count -lt 1) { Stop-SandboxTree @($legacyProcess.Id); throw 'real v0.9 positive control did not observe legacy' }
Stop-SandboxTree @($legacyProcess.Id)
$terminated=Invoke-Observer 'positive_terminated' @($legacyProcess.Id) $true $true $trialInstall
if (-not $terminated.legacy_zero_proven) { throw 'legacy zero proof failed after sandbox termination' }

$controllerResults=@{}
foreach($spec in @(@('F2','A3-F2'),@('F3','A3-F3'),@('F4','A3-F4'))){ $controllerResults[$spec[0]]=Invoke-ControllerTrial $spec[0] $spec[1] }

# R0-R3: a real recovery subprocess is paused at each durable phase, then its exact
# sandbox process tree is hard-killed and recovery is retried idempotently.
$failpointResults=@{}
foreach($point in @('R0','R1','R2','R3')) {
    $rtrial=New-Trial "recovery_$point"; $recoveryRoot=Join-Path $rtrial.root 'recovery'; New-Item -ItemType Directory -Force -Path $recoveryRoot | Out-Null
    $recoveryPath=Join-Path $rtrial.tx 'legacy\QI-Crawler.exe'; New-Item -ItemType Directory -Force -Path (Split-Path -Parent $recoveryPath) | Out-Null
    Copy-Item -LiteralPath $candidate -Destination $recoveryPath -Force; Copy-Item -LiteralPath $stub -Destination $rtrial.canonical -Force
    $obs=Invoke-Observer "recovery_${point}_zero" @() $true $true $rtrial.root; $obsJson=Join-Path $evidence "observer\recovery_${point}_zero.snapshot.json"
    $pause=Join-Path $rtrial.tx "markers\$point.pause"; $recoveryProc=Start-RecoveryProcess $rtrial $obsJson $point $pause
    if (-not (Wait-File $pause)) { Stop-SandboxTree @($recoveryProc.Id); throw "recovery $point did not reach pause" }
    $recoveryTreeIds=Get-DescendantIds @($recoveryProc.Id); $recoveryTreeEvidence=$script:lastProcessTreeEvidence; Write-Json (Join-Path $evidence "observer\recovery_${point}_tree.json") $recoveryTreeEvidence; Stop-SandboxTree @($recoveryProc.Id); $recoveryTreeDead=Test-ProcessIdsGone $recoveryTreeIds; Remove-Item -LiteralPath $pause -Force -ErrorAction SilentlyContinue
    $retry=Invoke-RecoveryCli $rtrial $obsJson; $again=Invoke-RecoveryCli $rtrial $obsJson
    $failpointResults[$point]=[ordered]@{hard_kill_marker=$true; process_tree_dead=$recoveryTreeDead; process_tree_evidence=$recoveryTreeEvidence; retry=$retry; idempotence=$again; final_sha256=(Get-Sha256 $rtrial.canonical); final_state=if($retry.json.status -eq 'LEGACY_READY'){'LEGACY_READY'}else{'RECOVERY_REQUIRED'}}
    Write-Json (Join-Path $evidence "recovery\$point.json") $failpointResults[$point]
}
}

function Invoke-F5CanonicalRoute {
param(
    [Parameter(Mandatory=$true)] [pscustomobject]$Trial,
    [Parameter(Mandatory=$true)] [string]$TrialId,
    [Parameter(Mandatory=$true)] [string]$EvidenceRoot,
    [Parameter(Mandatory=$true)] [string]$StubPath,
    [Parameter(Mandatory=$true)] [string]$PythonPath,
    [Parameter(Mandatory=$true)] [string]$LegacyExecutableSha256,
    [Parameter(Mandatory=$true)] [string]$StubSha256,
    [switch]$TestCheckpoint
)

# This is the one canonical P1→P5 implementation. Sequential callers pass a
# trial created by their historical setup; F5Only callers pass the already
# prepared existing sandbox. No setup or copy is performed here.
$f5 = $Trial
$evidence = Get-CanonicalPath $EvidenceRoot
$stub = Get-CanonicalPath $StubPath
$python = Get-CanonicalPath $PythonPath
$legacyHash = $LegacyExecutableSha256
$stubHash = $StubSha256
if (-not $TestCheckpoint) {
    foreach ($required in @($f5.root, $f5.install, $f5.data, $f5.db, $f5.tx, $f5.canonical)) {
        [void](Assert-ObserverPath $required $f5.root)
        if (-not (Test-Path -LiteralPath $required)) {
            throw "F5_EXISTING_SANDBOX_LAYOUT_INVALID: $required"
        }
    }
}
Write-Output 'CANONICAL_F5_ROUTE_ENTERED=YES'
if ($TestCheckpoint) {
    if ($env:QI_CRAWLER_F5_TEST_MODE -eq '1' -and $env:QI_CRAWLER_F5_TEST_CANONICAL_FAILURE -eq '1') {
        Write-Output 'CANONICAL_F5_TEST_FAILURE=YES'
        return [pscustomobject]@{ test_checkpoint = $false; test_failure = $true; final_probe_result = 'HOLD' }
    }
    Write-Output 'CANONICAL_F5_TEST_CHECKPOINT=PASS'
    Write-Output 'P1_P5_EFFECTS_EXECUTED=NO'
    Write-Output 'GENERIC_SETUP_EXECUTED=NO'
    Write-Output 'NEW_TRIAL=NO'
    Write-Output 'NEW_SANDBOX=NO'
    Write-Output 'RUNTIME_COPY_EXECUTED=NO'
    Write-Output 'REAL_F5_EXECUTED=NO'
    return [pscustomobject]@{ test_checkpoint = $true; final_probe_result = 'NOT_RUN' }
}
$phaseModel = $null
$routeContract = Get-Content -Raw -LiteralPath $PreexecutionContractPath | ConvertFrom-Json
if ([string]$routeContract.schema -eq 'AO-04-C3-F5-PREEXECUTION-CONTRACT-PHASE-V1') {
    $phaseIdentity = $routeContract.phase_helper_identity
    if (-not $phaseIdentity -or
        -not [string]::Equals((Get-CanonicalPath ([string]$phaseIdentity.path)), (Get-CanonicalPath $phaseHelper), [StringComparison]::OrdinalIgnoreCase) -or
        ([string]$phaseIdentity.sha256).ToLowerInvariant() -ne (Get-Sha256 $phaseHelper)) {
        throw 'A3_PHASE_INVALID: phase helper identity differs at route'
    }
    $phaseModel = $routeContract.phase_model
    [void](Assert-A3Phase -Sandbox $f5.root -Model $phaseModel -ExpectedPhase 'PRETRIAL')
    Write-Output 'A3_PHASE_PRETRIAL=PASS'
}
Initialize-F5BoundsFromContract $PreexecutionContractPath

# F5 semantic timing: the private evidence-only controller copy pauses at both
# A3-F4 and A3-F5. P1 is frozen at the first marker; only then is the F4
# acknowledgement created. The controller persists BARRIER_CONFIRMED and
# blocks at F5, where P2 is frozen before the hard-kill acknowledgement.
# No production process is touched by this function's tests.
$f5Evidence=Join-Path $evidence "f5\$trialId"
New-Item -ItemType Directory -Force -Path $f5Evidence | Out-Null
$evidence=$f5Evidence
$stubState=Initialize-F5StubState -CanonicalPath $f5.canonical -TrialRoot $f5.root -ControllerPath $controller -ControllerSha256 $ao03ControllerHash
Write-FsyncJson (Join-Path $f5Evidence 'receipts\STUB_DEPENDENCY.json') ([ordered]@{trial_id=$trialId;identity=$stubState;write_class='TX_STATE';ready_before_controller_start=$true})
$f5Before=Get-DbManifest $f5.data $f5.root
$f5LogicalBefore=Get-F5LogicalDigest -DatabasePath (Join-Path $f5.db 'egp.db') -ResultPath (Join-Path $evidence 'recovery\db_logical_before.process.json') -ExpectedSchema '0020_add_tender_operational_revision_events'
$script:f5CanonicalPath=$f5.canonical
$f5DbBeforePath=Join-Path $evidence 'f5\db_before.json'; Write-Json $f5DbBeforePath $f5Before; $script:f5CurrentDbManifestSha=Get-JsonFileSha256 $f5DbBeforePath
$f5HandshakeController=Join-Path $evidence 'controller\ao03_controller_f5_handshake.py'
$f5HandshakeSha=New-F5HandshakeController $f5HandshakeController
$f5MarkerP1=Join-Path $f5.tx 'markers\A3-F4.ready'
$f5MarkerP2=Join-Path $f5.tx 'markers\A3-F5.ready'
$f5Journal=Join-Path $f5.tx 'cutover.json'
Add-F5Event 'F5_START' $trialId 0 (Get-F5Phase $f5Journal) 'recovery\F5.json'
Add-F5Event 'P0_BEFORE_CUTOVER_TRIAL' $trialId 0 (Get-F5Phase $f5Journal) 'trials\F5\transaction\cutover.json'
$p0=Invoke-Observer 'P0_BEFORE_CUTOVER_TRIAL' @() $true $true $f5.root $trialId 0 'NOT_STARTED'
$f5Job = Start-A3ContainedProcess -FilePath $python -Arguments @($f5HandshakeController,'--install-root',$f5.install,'--tx-root',$f5.tx,'--stub',$stub,'--db-root',$f5.data,'--failpoint','A3-F4-F5') -WorkingDirectory $repo
$f5Proc = [pscustomobject]@{ Id = $f5Job.ProcessId }
try {
$jobCreated = (Get-A3JobActiveCount -Session $f5Job) -gt 0
$jobMembership = @(Get-A3JobProcessIds -Session $f5Job)
if (-not $jobCreated -or $f5Proc.Id -notin $jobMembership) { throw 'F5_CONTROLLER_JOB_ASSIGNMENT_UNPROVEN' }
Write-FsyncJson (Join-Path $f5Evidence 'receipts\JOB_CREATED.json') ([ordered]@{trial_id=$trialId;job_created=$jobCreated;controller_pid=$f5Proc.Id;controller_assigned=($f5Proc.Id -in $jobMembership);job_active_process_count=(Get-A3JobActiveCount -Session $f5Job);timestamp_utc=(Get-Date).ToUniversalTime().ToString('o')})
if(-not (Wait-File $f5MarkerP1)){throw 'F5 did not reach explicit pre-barrier handshake'}
if ($phaseModel) {
    [void](Assert-A3Phase -Sandbox $f5.root -Model $phaseModel -ExpectedPhase 'CUTOVER_STUB_STAGED')
    Write-Output 'A3_PHASE_CUTOVER_STUB_STAGED=PASS'
}
$positiveTree=Get-ProcessTreeEvidence @($f5Proc.Id)
Write-Json (Join-Path $f5Evidence 'observer\positive_running.tree.json') $positiveTree
$positiveTreePass=($positiveTree.enumeration_status -eq 'SUCCESS' -and @($positiveTree.ids).Count -ge 1 -and $positiveTree.root_pid_status[0].exists -eq $true -and $positiveTree.descendant_discovery_status -eq 'COMPLETE')
$p1JobMembers=@(Get-A3JobProcessIds -Session $f5Job)
if (-not $positiveTreePass -or @($positiveTree.ids | Where-Object { $_ -notin $p1JobMembers }).Count -gt 0) { throw 'F5_P1_JOB_LINEAGE_UNPROVEN' }
Add-F5Event 'P1_CENSUS_START' $trialId $f5Proc.Id (Get-F5Phase $f5Journal) 'observer\F5_P1_BEFORE_BARRIER.snapshot.json'
$p1=Invoke-Observer 'F5_P1_BEFORE_BARRIER' @($f5Proc.Id) $true $true $f5.root $trialId $f5Proc.Id 'ALIVE_BARRIER_CANDIDATE' $p1JobMembers
$script:f5CurrentSnapshot=$p1
Write-FsyncJson (Join-Path $f5Evidence 'receipts\P1.json') $p1
Add-F5Event 'P1_CENSUS_FROZEN' $trialId $f5Proc.Id (Get-F5Phase $f5Journal) 'observer\F5_P1_BEFORE_BARRIER.snapshot.json'
Add-F5Event 'BARRIER_CONFIRM_START' $trialId $f5Proc.Id (Get-F5Phase $f5Journal) 'trials\F5\transaction\cutover.json'
$f5ContinueP1=Join-Path (Split-Path -Parent $f5MarkerP1) 'continue-A3-F4'; Write-F5BoundedText -Path $f5ContinueP1 -Text '' -WriteClass TX_STATE
if(-not (Wait-File $f5MarkerP2)){throw 'F5 did not reach explicit post-barrier handshake'}
if((Get-F5Phase $f5Journal) -ne 'BARRIER_CONFIRMED'){throw 'F5 barrier phase was not persisted before P2'}
if ($phaseModel) {
    [void](Assert-A3Phase -Sandbox $f5.root -Model $phaseModel -ExpectedPhase 'POST_BARRIER_MAINTENANCE')
    Write-Output 'A3_PHASE_POST_BARRIER_MAINTENANCE=PASS'
}
Add-F5Event 'BARRIER_CONFIRMED_PERSISTED' $trialId $f5Proc.Id (Get-F5Phase $f5Journal) 'trials\F5\transaction\cutover.json'
Write-FsyncJson (Join-Path $f5Evidence 'receipts\BARRIER_CONFIRMED.json') ([ordered]@{trial_id=$trialId;event_name='BARRIER_CONFIRMED';transaction_phase=(Get-F5Phase $f5Journal);controller_root_pid=$f5Proc.Id;controller_alive=$true;receipt_flush_method='FileStream.Flush(true)';timestamp_utc=(Get-Date).ToUniversalTime().ToString('o')})
Add-F5Event 'P2_CENSUS_START' $trialId $f5Proc.Id (Get-F5Phase $f5Journal) 'observer\F5_P2_AFTER_BARRIER.snapshot.json'
$p2JobTree=Get-ProcessTreeEvidence @($f5Proc.Id)
$p2JobMembers=@(Get-A3JobProcessIds -Session $f5Job)
if ($p2JobTree.enumeration_status -ne 'SUCCESS' -or @($p2JobTree.ids | Where-Object { $_ -notin $p2JobMembers }).Count -gt 0) { throw 'F5_P2_JOB_LINEAGE_UNPROVEN' }
$p2=Invoke-Observer 'F5_P2_AFTER_BARRIER' @($f5Proc.Id) $true $true $f5.root $trialId $f5Proc.Id 'ALIVE_BARRIER_CONFIRMED' $p2JobMembers
$p2ControllerAlive=[bool](Get-Process -Id $f5Proc.Id -ErrorAction SilentlyContinue)
$jobActiveAtP2=Get-A3JobActiveCount -Session $f5Job
$jobMembersAtP2=@(Get-A3JobProcessIds -Session $f5Job)
if (-not $p2ControllerAlive -or $jobActiveAtP2 -lt 1 -or $f5Proc.Id -notin $jobMembersAtP2) { throw 'JOB_ACTIVE_PROCESS_COUNT_AT_P2_INVALID' }
$p2 | Add-Member -NotePropertyName controller_alive -NotePropertyValue $p2ControllerAlive -Force
$p2 | Add-Member -NotePropertyName job_active_process_count -NotePropertyValue $jobActiveAtP2 -Force
$p2 | Add-Member -NotePropertyName receipt_flush_method -NotePropertyValue 'FileStream.Flush(true)' -Force
$script:f5CurrentSnapshot=$p2
$script:f5P2ReceiptPath=Join-Path $f5Evidence 'receipts\P2.json'
Write-FsyncJson $script:f5P2ReceiptPath ([ordered]@{trial_id=$trialId;event_name='P2';snapshot=$p2;controller_alive=$p2ControllerAlive;job_active_process_count=$jobActiveAtP2;controller_tree_status='ALIVE_BARRIER_CONFIRMED';receipt_flush_method='FileStream.Flush(true)';persisted_sequence=$script:f5SequenceNumber;timestamp_utc=(Get-Date).ToUniversalTime().ToString('o')})
Add-F5Event 'P2_CENSUS_FROZEN' $trialId $f5Proc.Id (Get-F5Phase $f5Journal) 'observer\F5_P2_AFTER_BARRIER.snapshot.json'
Add-F5Event 'P2_CAPTURE_FINISHED' $trialId $f5Proc.Id (Get-F5Phase $f5Journal) 'observer\F5_P2_AFTER_BARRIER.snapshot.json'
$f5TreeIds=Get-DescendantIds @($f5Proc.Id)
$f5TreeEvidence=$script:lastProcessTreeEvidence
$jobMembersBefore=@(Get-A3JobProcessIds -Session $f5Job)
if (-not $p2.legacy_zero_proven -or $f5TreeEvidence.enumeration_status -ne 'SUCCESS' -or
    $f5TreeEvidence.descendant_discovery_status -ne 'COMPLETE' -or
    @($f5TreeIds | Where-Object { $_ -notin $jobMembersBefore }).Count -gt 0) { throw 'F5_PROCESS_REVALIDATION_FAILED' }
$writerProbeCapture=Invoke-F5BoundedProcess -FilePath $python -Arguments @('-m','tools.release.a3_recovery','--writer-probe',(Join-Path $f5.db 'egp.db')) -WriteClass RECOVERY -ResultPath (Join-Path $f5Evidence 'recovery\writer_probe.process.json')
$writerProbe=([string]$writerProbeCapture.stdout).Trim()
try { $writerJson=$writerProbe|ConvertFrom-Json } catch { throw 'F5_WRITER_REVALIDATION_FAILED' }
if ($writerProbeCapture.exit_code -ne 0 -or -not [bool]$writerJson.success) { throw 'F5_WRITER_REVALIDATION_FAILED' }
Add-F5Event 'WRITER_REVALIDATION_PASS' $trialId $f5Proc.Id (Get-F5Phase $f5Journal) 'recovery\writer_probe.process.json'
$canonicalStubSha=Get-Sha256 (Assert-ObserverPath $f5.canonical $f5.root)
if ($canonicalStubSha -ne $stubHash) { throw 'F5_CANONICAL_STUB_VERIFICATION_FAILED' }
Add-F5Event 'CANONICAL_STUB_VERIFICATION_PASS' $trialId $f5Proc.Id (Get-F5Phase $f5Journal) 'receipts\BARRIER_CONFIRMED.json'
$f5DbAtBarrier=Get-DbManifest $f5.data $f5.root
$f5DbAtBarrierPath=Join-Path $evidence 'f5\db_at_barrier.json'; Write-Json $f5DbAtBarrierPath $f5DbAtBarrier; $script:f5CurrentDbManifestSha=Get-JsonFileSha256 $f5DbAtBarrierPath
$jobActiveBefore=Get-A3JobActiveCount -Session $f5Job
if ($jobActiveBefore -lt 1 -or $f5Proc.Id -notin @(Get-A3JobProcessIds -Session $f5Job)) { throw 'JOB_ACTIVE_PROCESS_COUNT_BEFORE_INVALID' }
Write-Json (Join-Path $f5Evidence 'observer\controller_tree_before_kill.json') $f5TreeEvidence
Write-FsyncJson (Join-Path $f5Evidence 'receipts\CONTROLLER_KILL_REQUESTED.json') ([ordered]@{trial_id=$trialId;event_name='CONTROLLER_KILL_REQUESTED';transaction_phase=(Get-F5Phase $f5Journal);controller_root_pid=$f5Proc.Id;controller_alive=$true;job_active_process_count_before=$jobActiveBefore;p2_receipt_persisted=(Test-Path -LiteralPath $script:f5P2ReceiptPath);receipt_flush_method='FileStream.Flush(true)';process_tree_evidence=$f5TreeEvidence;timestamp_utc=(Get-Date).ToUniversalTime().ToString('o')})
Add-F5Event 'CONTROLLER_KILL_REQUESTED' $trialId $f5Proc.Id (Get-F5Phase $f5Journal) 'recovery\F5.json'
Add-F5Event 'JOB_TERMINATE' $trialId $f5Proc.Id (Get-F5Phase $f5Journal) 'receipts\JOB_OBJECT.json'
$jobTermination=Stop-A3ContainedProcess -Session $f5Job
$jobActiveAfter=Get-A3JobActiveCount -Session $f5Job
if ($jobActiveAfter -ne 0 -or $jobTermination.active_after -ne 0) { throw 'JOB_ACTIVE_PROCESS_COUNT_AFTER_NOT_ZERO' }
Add-F5Event 'JOB_ZERO' $trialId 0 (Get-F5Phase $f5Journal) 'receipts\JOB_OBJECT.json'
$outerAlive=[bool](Get-Process -Id $PID -ErrorAction SilentlyContinue)
$lockRetained=$false
try { $unexpectedLock=[IO.File]::Open($lockPath,[IO.FileMode]::Open,[IO.FileAccess]::ReadWrite,[IO.FileShare]::None); $unexpectedLock.Dispose() }
catch [IO.IOException] { $lockRetained=$true }
if (-not $outerAlive -or -not $lockRetained) { throw 'F5_OUTER_OR_LOCK_LOST_AFTER_JOB_KILL' }
Write-FsyncJson (Join-Path $f5Evidence 'receipts\JOB_OBJECT.json') ([ordered]@{trial_id=$trialId;controller_pid=$f5Proc.Id;active_at_p2=$jobActiveAtP2;active_before=$jobActiveBefore;active_after=$jobActiveAfter;termination_authority='TerminateJobObject';outer_orchestrator_alive=$outerAlive;exclusive_trial_lock_retained=$lockRetained;timestamp_utc=(Get-Date).ToUniversalTime().ToString('o')})
$f5TreeDead=$true
$script:f5ControllerTreeCount=0
$script:f5RecoveryProcessRunning=$false
Write-FsyncJson (Join-Path $f5Evidence 'receipts\CONTROLLER_TREE_DEAD.json') ([ordered]@{trial_id=$trialId;event_name='CONTROLLER_TREE_DEAD';controller_process_tree_count=0;job_active_process_count_after=$jobActiveAfter;recovery_process_running=$false;process_tree_evidence=$f5TreeEvidence;receipt_flush_method='FileStream.Flush(true)';timestamp_utc=(Get-Date).ToUniversalTime().ToString('o')})
Add-F5Event 'CONTROLLER_TREE_DEAD' $trialId 0 (Get-F5Phase $f5Journal) 'recovery\F5.json'
Add-F5Event 'P3_CENSUS_START' $trialId 0 (Get-F5Phase $f5Journal) 'observer\F5_P3_AFTER_CONTROLLER_KILL.snapshot.json'
$p3TreeStatus=if($f5TreeDead){'DEAD'}else{'UNRESOLVED_ENUMERATION'}
$p3=Invoke-Observer 'F5_P3_AFTER_CONTROLLER_KILL' @() $true $true $f5.root $trialId $f5Proc.Id $p3TreeStatus
$script:f5CurrentSnapshot=$p3
Write-FsyncJson (Join-Path $f5Evidence 'receipts\P3.json') $p3
Add-F5Event 'P3_CENSUS_FROZEN' $trialId 0 (Get-F5Phase $f5Journal) 'observer\F5_P3_AFTER_CONTROLLER_KILL.snapshot.json'
$routes=@()
$canonicalRoute=$f5.canonical
if ($phaseModel) {
    [void](Assert-A3Phase -Sandbox $f5.root -Model $phaseModel -ExpectedPhase 'POST_BARRIER_MAINTENANCE')
}
$routeDefinitions=@(
    [ordered]@{name='canonical';artifact=$canonicalRoute;invoke='direct'},
    [ordered]@{name='start_menu';artifact=(Join-Path $f5.root 'routes\start_menu\QI-Crawler.lnk');invoke='shortcut'},
    [ordered]@{name='desktop';artifact=(Join-Path $f5.root 'routes\desktop\QI-Crawler.lnk');invoke='shortcut'},
    [ordered]@{name='post_install';artifact=(Join-Path $f5.root 'routes\post_install\launch.cmd');invoke='cmd'},
    [ordered]@{name='autostart_task';artifact=(Join-Path $f5.root 'routes\autostart_task\launch.cmd');invoke='cmd'}
)
foreach($definition in $routeDefinitions) {
    $routeName=$definition.name; $artifact=$definition.artifact
    [void](Assert-ObserverPath $artifact $f5.root)
    New-Item -ItemType Directory -Force -Path (Split-Path -Parent $artifact) | Out-Null
    if($definition.invoke -eq 'shortcut') { $resolvedTarget=Write-F5BoundedShortcut -Path $artifact -TargetPath $canonicalRoute -Root $f5.root }
    elseif($definition.invoke -eq 'cmd') { Write-F5BoundedText -Path $artifact -Text ('@echo off' + "`r`n" + 'start "" "' + $canonicalRoute + '"' + "`r`n") -WriteClass ROUTE_ARTIFACTS; $resolvedTarget=$canonicalRoute }
    else { $resolvedTarget=$canonicalRoute }
    [void](Assert-ObserverPath $artifact $f5.root)
    $resolvedSha=Get-Sha256 (Assert-ObserverPath $resolvedTarget $f5.root)
    $routeKind=switch($definition.invoke){'direct'{'EXE'}'shortcut'{'SHORTCUT'}'cmd'{'CMD'}}
    $routeJob=$null
    try {
        [void](Assert-F5StubState $stubState $f5.root)
        $routeLimit=Get-F5BoundedLimit 'ROUTE_ARTIFACTS'
        $routeJob=Start-A3ContainedRoute -Kind $routeKind -Artifact $artifact -WorkingDirectory (Split-Path -Parent $artifact) -MaxStdoutBytes $routeLimit.max_stdout_bytes -MaxStderrBytes $routeLimit.max_stderr_bytes
        $routeCompletion=Wait-A3ContainedRouteZero -Session $routeJob -TimeoutMilliseconds 10000 -MinimumTotalProcesses $(if($routeKind -eq 'EXE'){1}else{2})
    } catch {
        $failure=[ordered]@{trial_id=$trialId;route_type=$routeName;route_kind=$routeKind;artifact=$artifact;resolved_target_sha=$resolvedSha;result='FAIL';error=$_.Exception.Message;process_result=$_.Exception.Data['route_result']}
        Write-FsyncJson (Join-Path $f5Evidence ("receipts\P4_{0}_FAIL.json" -f $routeName)) $failure
        throw
    } finally {
        if ($routeJob) { Close-A3ContainedProcess -Session $routeJob }
    }
    $routeTreeEvidence=Get-ProcessTreeEvidence @($routeCompletion.launcher_pid)
    $routeObs=Invoke-Observer "F5_route_$routeName" @() $true $true $f5.root $trialId 0 'JOB_ZERO'
    $routeResult=if($resolvedSha -eq $stubHash -and $routeCompletion.active_after -eq 0 -and
        $routeCompletion.launcher_exit_code -eq 0 -and $routeObs.legacy_zero_proven -and
        $routeTreeEvidence.enumeration_status -eq 'SUCCESS'){'STUB'}else{'HOLD'}
    $routeReceipt=[ordered]@{trial_id=$trialId;route_type=$routeName;route_artifact=$artifact;resolved_target=$resolvedTarget;resolved_target_sha=$resolvedSha;invocation_method=$definition.invoke;result=$routeResult;spawned_process_identity=$routeCompletion.observed_job_pids;job_process_total=$routeCompletion.total_job_processes;job_active_after=$routeCompletion.active_after;launcher_exit_code=$routeCompletion.launcher_exit_code;stdout=$routeCompletion.stdout;stderr=$routeCompletion.stderr;process_tree_evidence=$routeTreeEvidence;fresh_p4_census=$routeObs}
    Write-FsyncJson (Join-Path $f5Evidence ("receipts\P4_{0}.json" -f $routeName)) $routeReceipt
    $routes += $routeReceipt
    Add-F5Event "P4_ROUTE_$routeName" $trialId 0 (Get-F5Phase $f5Journal) ("receipts\P4_{0}.json" -f $routeName)
}
$p5=Invoke-Observer 'P5_BEFORE_MECHANICAL_RESTORE' @() $true $true $f5.root $trialId 0 'DEAD'
Write-FsyncJson (Join-Path $f5Evidence 'receipts\P5.json') $p5
$f5RecoveryBefore=Get-DbManifest $f5.data $f5.root
Add-F5Event 'P5_BEFORE_MECHANICAL_RESTORE' $trialId 0 (Get-F5Phase $f5Journal) 'receipts\P5.json'
$barrierJson=Join-Path $f5Evidence 'observer\F5_P3_AFTER_CONTROLLER_KILL.snapshot.json'; $maintenance=Invoke-RecoveryCli $f5 $barrierJson -Barrier -TrialId $trialId
$f5After=Get-DbManifest $f5.data $f5.root
$f5LogicalAfter=Get-F5LogicalDigest -DatabasePath (Join-Path $f5.db 'egp.db') -ResultPath (Join-Path $evidence 'recovery\db_logical_after.process.json') -ExpectedSchema '0020_add_tender_operational_revision_events'
[void](Assert-F5StubState $stubState $f5.root)
$recoveryVerified=Assert-F5MaintenanceRecovery -EvidenceRoot $f5Evidence -SandboxRoot $f5.root -TrialId $trialId -ProcessReceiptPath $maintenance.receipt_path -ObserverReceiptPath $barrierJson -CanonicalPath $f5.canonical -ExpectedStubSha256 $stubHash -DbBefore $f5Before -DbAfter $f5After -LogicalBefore $f5LogicalBefore -LogicalAfter $f5LogicalAfter -ExpectedSchema '0020_add_tender_operational_revision_events'
Write-FsyncJson (Join-Path $f5Evidence 'receipts\RECOVERY_BOUND.json') ([ordered]@{trial_id=$trialId;recovery_status=$maintenance.json.status;recovery_process_sha256=(Get-Sha256 $maintenance.receipt_path);p3_observer_sha256=(Get-Sha256 $barrierJson);final_stub_sha256=(Get-Sha256 $f5.canonical);db_physical_unchanged=$true;db_logical_sha256=$f5LogicalAfter.sha256;db_schema=$f5LogicalAfter.revision;verified=$recoveryVerified})
$f5Result=[ordered]@{trial_id=$trialId;P0=$p0;P1=$p1;P2=$p2;P3=$p3;P5=$p5;db_before=$f5Before;db_at_barrier=$f5DbAtBarrier;db_after=$f5After;db_logical_before=$f5LogicalBefore;db_logical_after=$f5LogicalAfter;sqlite_writer_probe=$writerProbe;maintenance_recovery=$maintenance;recovery_verified=$recoveryVerified;normal_launch_routes=$routes;controller_tree_killed=$true;controller_tree_dead=$f5TreeDead;db_unchanged=(($f5Before|ConvertTo-Json -Compress)-eq($f5After|ConvertTo-Json -Compress));handshake_controller_source=$f5HandshakeController;handshake_controller_sha256=$f5HandshakeSha;event_sequence=$f5EventSequence}
Write-Json (Join-Path $evidence 'recovery\F5.json') $f5Result
$f5EventsPath=Join-Path $evidence 'f5\event_sequence.json'; Write-FsyncJson $f5EventsPath $f5EventSequence
$f5EventsSha=Get-JsonFileSha256 $f5EventsPath
Write-Json (Join-Path $evidence 'f5\event_sequence.sha256.json') ([ordered]@{path=$f5EventsPath;sha256=$f5EventsSha;event_count=$f5EventSequence.Count;capture_finished_before_kill=(($f5EventSequence | Where-Object event -eq 'P2_CAPTURE_FINISHED').sequence -lt ($f5EventSequence | Where-Object event -eq 'CONTROLLER_KILL_REQUESTED').sequence)})

$observerSelfCheck=[ordered]@{purpose='bounded observer P5 invariant';p5_event_name=$p5.event_name;legacy_zero_proven=$p5.legacy_zero_proven;unresolved_relevant_count=$p5.unresolved_relevant_count;record_count=@($p5.records).Count;temp_tree_created=$false}
$observerSelfTestPass=($observerSelfCheck.p5_event_name -eq 'P5_BEFORE_MECHANICAL_RESTORE' -and $observerSelfCheck.legacy_zero_proven -and $observerSelfCheck.unresolved_relevant_count -eq 0)
Write-F5BoundedJson -Path (Join-Path $f5Evidence 'observer\P5_PURPOSE_SELF_CHECK.json') -Value $observerSelfCheck -WriteClass PROCESS_CENSUS
$writerJson=$writerProbe|ConvertFrom-Json
$routeContractPass=(@($routes).Count -eq 5 -and @($routes|Where-Object {$_.result -ne 'STUB' -or $_.resolved_target -ne $canonicalRoute}).Count -eq 0)
$receiptPaths=@('STUB_DEPENDENCY','JOB_CREATED','P1','BARRIER_CONFIRMED','P2','CONTROLLER_KILL_REQUESTED','JOB_OBJECT','CONTROLLER_TREE_DEAD','P3','P5')|ForEach-Object {Join-Path $f5Evidence ("receipts\$_.json")}
$receiptsComplete=(@($receiptPaths|Where-Object {-not (Test-Path -LiteralPath $_)}).Count -eq 0)
$processTreeFailClosedPass=Test-ProcessTreeFailClosed $f5.root
$requiredSequence=@('P1_CENSUS_FROZEN','BARRIER_CONFIRMED_PERSISTED','P2_CAPTURE_FINISHED','WRITER_REVALIDATION_PASS','CANONICAL_STUB_VERIFICATION_PASS','JOB_TERMINATE','JOB_ZERO','P3_CENSUS_START')
$sequenceNumbers=@(foreach ($requiredEvent in $requiredSequence) { $match=@($f5EventSequence | Where-Object { $_.event -eq $requiredEvent }); if ($match.Count -ne 1) { -1 } else { [int]$match[0].sequence } })
$barrierSequencePass=($sequenceNumbers.Count -eq $requiredSequence.Count -and @($sequenceNumbers | Where-Object { $_ -lt 0 }).Count -eq 0)
for ($sequenceIndex=1; $sequenceIndex -lt $sequenceNumbers.Count; $sequenceIndex++) { if ($sequenceNumbers[$sequenceIndex] -le $sequenceNumbers[$sequenceIndex - 1]) { $barrierSequencePass=$false } }
$manifestRequired=@($receiptPaths + @((Join-Path $f5Evidence 'receipts\RECOVERY_BOUND.json'),(Join-Path $f5Evidence 'observer\P0_BEFORE_CUTOVER_TRIAL.snapshot.json'),(Join-Path $f5Evidence 'f5\event_sequence.json'),$maintenance.receipt_path,(Join-Path $f5Evidence 'recovery\db_logical_before.process.json'),(Join-Path $f5Evidence 'recovery\db_logical_after.process.json')) + @($routes | ForEach-Object {Join-Path $f5Evidence ("receipts\P4_{0}.json" -f $_.route_type)})) | ForEach-Object {Get-SafeRelativePath $f5Evidence $_}
$evidenceManifest=New-EvidenceManifest -Root $f5Evidence -TrialId $trialId -RequiredPaths $manifestRequired
$gates=[ordered]@{observer_self_test=$observerSelfTestPass;legacy_zero_P1=$p1.legacy_zero_proven;legacy_zero_P2=$p2.legacy_zero_proven;legacy_zero_P3=$p3.legacy_zero_proven;unresolved_relevant_zero_P1_P2_P3=($p1.unresolved_relevant_count -eq 0 -and $p2.unresolved_relevant_count -eq 0 -and $p3.unresolved_relevant_count -eq 0);controller_alive_at_P2=$p2ControllerAlive;job_created=$jobCreated;controller_assigned_to_job=($f5Proc.Id -in $jobMembership);job_active_at_P2=($jobActiveAtP2 -gt 0 -and $f5Proc.Id -in $jobMembersAtP2);job_descendants_contained=(@($f5TreeIds | Where-Object { $_ -notin $jobMembersBefore }).Count -eq 0);writer_revalidation=[bool]$writerJson.success;canonical_stub_verified=($canonicalStubSha -eq $stubHash);job_active_before_kill=($jobActiveBefore -gt 0);job_active_after_kill=($jobActiveAfter -eq 0);outer_orchestrator_alive=$outerAlive;exclusive_trial_lock_retained=$lockRetained;barrier_sequence=$barrierSequencePass;controller_tree_dead_at_P3=$f5TreeDead;process_tree_positive_control=$positiveTreePass;process_tree_fail_closed_test=$processTreeFailClosedPass;route_contract=$routeContractPass;sqlite_writer_quiescence=[bool]$writerJson.success;db_generation_unchanged=$f5Result.db_unchanged;recovery_verified=$recoveryVerified;final_schema_expected=([string]$f5LogicalAfter.revision -eq '0020_add_tender_operational_revision_events');final_logical_digest_unchanged=([string]$f5LogicalBefore.sha256 -ceq [string]$f5LogicalAfter.sha256);final_stub_identity=((Get-Sha256 $f5.canonical) -eq $stubHash);evidence_receipts_complete=$receiptsComplete;evidence_manifest_complete=$evidenceManifest.verified}
$gateInput=Join-Path $f5Evidence 'gate_inputs.json'; Write-Json $gateInput ([ordered]@{gate_contract='F5_CANONICAL_V1';mandatory_gates=$gates})
$positiveCapture=Invoke-F5BoundedProcess -FilePath $python -Arguments @('-m','tools.release.a3_process_observer','--aggregate-gates-json',$gateInput) -WriteClass ROUTE_ARTIFACTS -ResultPath (Join-Path $f5Evidence 'aggregate_positive.process.json'); $positiveOut=([string]$positiveCapture.stdout).Trim(); $positiveExit=$positiveCapture.exit_code
$negativeInput=Join-Path $f5Evidence 'aggregate_negative_control.json'; $negativeGates=[ordered]@{}; foreach($key in $gates.Keys){$negativeGates[$key]=$gates[$key]}; $negativeGates['route_contract']=$false; Write-Json $negativeInput ([ordered]@{gate_contract='F5_CANONICAL_V1';mandatory_gates=$negativeGates}); $negativeCapture=Invoke-F5BoundedProcess -FilePath $python -Arguments @('-m','tools.release.a3_process_observer','--aggregate-gates-json',$negativeInput) -WriteClass ROUTE_ARTIFACTS -ResultPath (Join-Path $f5Evidence 'aggregate_negative.process.json'); $negativeOut=([string]$negativeCapture.stdout).Trim(); $negativeExit=$negativeCapture.exit_code; $negativePass=($negativeExit -ne 0 -and $negativeOut -match 'HOLD')
$finalProbeResult=if($positiveExit -eq 0 -and $negativePass){'PASS'}else{'HOLD'}
$summary=[ordered]@{executable_sha256=$legacyHash;F5=$f5Result;production_touched=$false;database_mutated=$false;final_probe_result=$finalProbeResult}
if ($null -ne $controllerResults) { $summary['F2']=$controllerResults.F2; $summary['F3']=$controllerResults.F3; $summary['F4']=$controllerResults.F4 }
if ($null -ne $failpointResults) { $summary['R0_R3']=$failpointResults }
Write-Json (Join-Path $evidence 'AO_04_PROBE_SUMMARY.json') $summary
$core=[ordered]@{trial_id=$trialId;mandatory_gates=$gates;positive_aggregate=$positiveOut;positive_exit_code=$positiveExit;negative_control_output=$negativeOut;negative_control_exit_code=$negativeExit;negative_control_pass=$negativePass;final_probe_result=$finalProbeResult;observer_purpose_self_check=$observerSelfCheck;bounded_io_usage=(Get-F5BoundedIoUsage)}
Write-Json (Join-Path $f5Evidence 'probe_verdict_core.json') $core
$wrapper=[ordered]@{trial_id=$trialId;final_probe_result=$finalProbeResult;mandatory_gates=$gates;evidence_manifest=$evidenceManifest.path;evidence_manifest_sha256=$evidenceManifest.sha256;core_verdict_sha256=(Get-JsonFileSha256 (Join-Path $f5Evidence 'probe_verdict_core.json'))}
Write-Json (Join-Path $f5Evidence 'probe_verdict.json') $wrapper
Write-Output ("AO-04-C2 probe FINAL_PROBE_RESULT=$finalProbeResult exit_code=$([int]$(if($finalProbeResult -eq 'PASS'){0}else{2})) trial_id=$trialId evidence_manifest_sha256=$($evidenceManifest.sha256)")
if($finalProbeResult -ne 'PASS'){ throw 'F5_CANONICAL_ROUTE_VERDICT_HOLD' }
return [pscustomobject]@{ final_probe_result=$finalProbeResult; f5=$f5Result; evidence_manifest=$evidenceManifest.path; evidence_manifest_sha256=$evidenceManifest.sha256 }
} finally {
    Close-A3ContainedProcess -Session $f5Job
}
}

if ($f5OnlyRoute) {
    $existingTrial = [pscustomobject]@{
        root = $f5OnlySandbox
        install = Join-Path $f5OnlySandbox 'install'
        app = Join-Path $f5OnlySandbox 'install\QI-Crawler'
        canonical = Join-Path $f5OnlySandbox 'install\QI-Crawler\QI-Crawler.exe'
        data = Join-Path $f5OnlySandbox 'data'
        db = Join-Path $f5OnlySandbox 'data\data\database'
        tx = Join-Path $f5OnlySandbox 'transaction'
    }
    $routeOutput = @(Invoke-F5CanonicalRoute -Trial $existingTrial -TrialId $RunId -EvidenceRoot $f5OnlyEvidenceRoot -StubPath $stub -PythonPath $python -LegacyExecutableSha256 $legacyHash -StubSha256 $stubHash -TestCheckpoint:$f5OnlyTestCheckpoint)
    $routeOutput | ForEach-Object { Write-Output $_ }
    if (@($routeOutput | Where-Object { $_.test_failure -eq $true }).Count -gt 0) { exit 91 }
    Write-Output 'F5_ONLY_ROUTE_SELECTED'
    Write-Output 'EXISTING_SANDBOX_ONLY=YES'
    Write-Output 'NEW_RUNTIME_COPY=0'
    Write-Output 'NEW_SANDBOX=NO'
    Write-Output 'SEQUENTIAL_FALLBACK=NO'
    Write-Output 'GUARDED_EXECUTION_CONTEXT=PASS'
    Write-Output 'REAL_F5_EXECUTED=NO'
    exit 0
}

$trialId='AO04-C2-F5-' + (Get-Date).ToUniversalTime().ToString('yyyyMMddTHHmmssfffZ')
$f5=New-Trial 'F5'
$routeOutput = @(Invoke-F5CanonicalRoute -Trial $f5 -TrialId $trialId -EvidenceRoot $evidence -StubPath $stub -PythonPath $python -LegacyExecutableSha256 $legacyHash -StubSha256 $stubHash)
$routeOutput | ForEach-Object { Write-Output $_ }
if (@($routeOutput | Where-Object { $_.test_failure -eq $true }).Count -gt 0) { exit 91 }
