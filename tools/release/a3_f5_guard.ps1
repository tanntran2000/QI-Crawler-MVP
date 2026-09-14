[CmdletBinding()]
param(
    [ValidateSet('F5Only')]
    [string]$Mode = 'F5Only',
    [Parameter(Mandatory = $true)]
    [string]$ExistingSandboxPath,
    [Parameter(Mandatory = $true)]
    [string]$RunId,
    [Parameter(Mandatory = $true)]
    [string]$InputManifestPath,
    [switch]$DryRun,
    [ValidateSet('Unspecified', 'DryRun', 'RealF5')]
    [string]$ExecutionMode = 'Unspecified',
    [string]$ExecutionContextPath,
    [string]$EvidenceRoot,
    [Int64]$SafetyReserveBytes = 4294967296,
    [Int64]$RecoveryReserveBytes = 0,
    [Int64]$NextOperationPeakBytes = 0,
    [Int64]$RemainingPeakAfterOperationBytes = 0,
    [Int64]$FreeNowBytes = -1,
    [Int64]$HoldLockSeconds = 0,
    [switch]$TestDispatchBoundary,
    [switch]$CapacityProbeOnly,
    [switch]$PreflightOnly,
    [string]$PreexecutionContractPath,
    [string]$CapacityProbePath,
    [Int64]$DispatchHoldSeconds = 0,
    [switch]$SimulateStorageFailure,
    [string]$TestStateRoot,
    [string]$TestGlobalLockPath,
    [string]$TestMaterialWritePath
)

$ErrorActionPreference = 'Stop'
$repo = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..\..')).Path
$contextHelper = Join-Path $PSScriptRoot 'a3_f5_execution_context.ps1'
if (-not (Test-Path -LiteralPath $contextHelper -PathType Leaf)) { throw 'EXECUTION_CONTEXT_HELPER_MISSING' }
. $contextHelper
$phaseHelper = Join-Path $PSScriptRoot 'a3_phase_contract.ps1'
if (-not (Test-Path -LiteralPath $phaseHelper -PathType Leaf)) { throw 'A3_PHASE_HELPER_MISSING' }
. $phaseHelper

function Fail-Guard([string]$Code, [string]$Detail = '') {
    if ($Detail) { throw "GUARD_FAILURE:$Code : $Detail" }
    throw "GUARD_FAILURE:$Code"
}

function Test-AbsolutePath([string]$Path) {
    return [IO.Path]::IsPathRooted($Path)
}

function Get-Json([string]$Path) {
    try { return (Get-Content -Raw -LiteralPath $Path | ConvertFrom-Json) }
    catch { Fail-Guard 'INPUT_MANIFEST_INVALID' $_.Exception.Message }
}

function Get-Hash([string]$Path) {
    $sha = [Security.Cryptography.SHA256]::Create()
    $stream = [IO.File]::OpenRead($Path)
    try {
        return ([BitConverter]::ToString($sha.ComputeHash($stream))).Replace('-', '').ToLowerInvariant()
    } finally {
        $stream.Dispose()
        $sha.Dispose()
    }
}

function Normalize-Relative([string]$Path) {
    return ([string]$Path).Replace('\', '/').TrimStart('/')
}

function Get-CanonicalPath([string]$Path) {
    if (-not $Path -or -not [IO.Path]::IsPathRooted($Path)) {
        Fail-Guard 'PATH_CONTAINMENT_INVALID' 'path must be absolute'
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
        Fail-Guard 'PATH_CONTAINMENT_INVALID' $_.Exception.Message
    }
}

function Get-SafeRelativePath([string]$Root, [string]$Target) {
    $fullRoot = Get-CanonicalPath $Root
    $fullTarget = Get-CanonicalPath $Target
    $rootName = [IO.Path]::GetPathRoot($fullRoot)
    if (-not $rootName) { Fail-Guard 'PATH_CONTAINMENT_INVALID' 'root has no path root' }
    if ([string]::Equals($fullRoot, $fullTarget, [StringComparison]::OrdinalIgnoreCase)) {
        return ''
    }
    $rootPrefix = if ([string]::Equals($fullRoot, $rootName, [StringComparison]::OrdinalIgnoreCase)) {
        $fullRoot
    } else {
        $fullRoot.TrimEnd('\') + '\'
    }
    if (-not $fullTarget.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        Fail-Guard 'PATH_CONTAINMENT_VIOLATION' "target is outside root: $fullTarget"
    }
    return Normalize-Relative $fullTarget.Substring($rootPrefix.Length)
}

function Get-RelativeFiles([string]$Root) {
    $fullRoot = Get-CanonicalPath $Root
    $result = @{}
    foreach ($item in @(Get-ChildItem -LiteralPath $fullRoot -File -Recurse -Force)) {
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            Fail-Guard 'RUNTIME_REPARSE_POINT' $item.FullName
        }
        $relative = Get-SafeRelativePath $fullRoot $item.FullName
        $result[$relative] = [pscustomobject]@{
            path = $item.FullName
            size_bytes = [Int64]$item.Length
            sha256 = Get-Hash $item.FullName
        }
    }
    return $result
}

function Test-RuntimeManifest($Manifest, [string]$Sandbox) {
    $runtime = Join-Path $Sandbox 'runtime'
    if (-not (Test-Path -LiteralPath $runtime -PathType Container)) {
        Fail-Guard 'EXISTING_SANDBOX_INVALID' 'runtime directory is missing'
    }
    if (-not [string]::Equals((Get-CanonicalPath ([string]$Manifest.runtime_root)), (Get-CanonicalPath $runtime), [StringComparison]::OrdinalIgnoreCase)) {
        Fail-Guard 'RUNTIME_MANIFEST_INVALID' 'runtime_root does not match existing sandbox'
    }
    if (-not $Manifest.runtime_build_identity) {
        Fail-Guard 'RUNTIME_MANIFEST_INVALID' 'runtime build identity is absent'
    }
    $actual = Get-RelativeFiles $runtime
    $expected = @{}
    $runtimeEntries = @($Manifest.runtime_manifest)
    if ($runtimeEntries.Count -eq 0) {
        Fail-Guard 'RUNTIME_MANIFEST_INVALID' 'runtime manifest is empty'
    }
    foreach ($entry in $runtimeEntries) {
        if (-not $entry.relative_path -or $entry.sha256 -notmatch '^[0-9a-fA-F]{64}$') {
            Fail-Guard 'RUNTIME_MANIFEST_INVALID'
        }
        if ([string]$entry.tracked -ne 'NO' -or
            [string]$entry.reparse_point -ne 'NO' -or
            [string]$entry.read_status -ne 'PASS') {
            Fail-Guard 'RUNTIME_MANIFEST_INVALID' "unsafe file metadata: $($entry.relative_path)"
        }
        $relative = Normalize-Relative $entry.relative_path
        if ($relative.StartsWith('../') -or $relative -eq '..' -or [IO.Path]::IsPathRooted($relative)) {
            Fail-Guard 'RUNTIME_MANIFEST_INVALID' "path escapes runtime: $relative"
        }
        $expected[$relative] = $entry
    }
    if ($expected.Count -ne $runtimeEntries.Count) {
        Fail-Guard 'RUNTIME_MANIFEST_INVALID' 'duplicate runtime relative path'
    }
    $missing = @($expected.Keys | Where-Object { -not $actual.ContainsKey($_) })
    $extra = @($actual.Keys | Where-Object { -not $expected.ContainsKey($_) })
    $mismatch = @(
        $expected.Keys | Where-Object {
            $actual.ContainsKey($_) -and
            ([Int64]$expected[$_].size_bytes -ne [Int64]$actual[$_].size_bytes -or
             ([string]$expected[$_].sha256).ToLowerInvariant() -ne $actual[$_].sha256)
        }
    )
    if ($missing.Count -or $extra.Count -or $mismatch.Count) {
        Fail-Guard 'RUNTIME_IDENTITY_MISMATCH' ("missing=$($missing.Count);extra=$($extra.Count);mismatch=$($mismatch.Count)")
    }
    return [ordered]@{ file_count = $actual.Count; logical_bytes = [Int64](($actual.Values | Measure-Object size_bytes -Sum).Sum); missing = 0; extra = 0; mismatches = 0 }
}

function Test-ExecutionInputs($Manifest) {
    if ($null -eq $Manifest.execution_inputs) { Fail-Guard 'UNBOUND_EXECUTION_INPUT' 'execution_inputs is absent' }
    $entries = @($Manifest.execution_inputs)
    if ($entries.Count -eq 0) { Fail-Guard 'UNBOUND_EXECUTION_INPUT' 'execution_inputs is empty' }
    foreach ($entry in $entries) {
        if ($entry.classification -notin @('EXECUTION_INPUT', 'GENERATED_EXECUTION_INPUT')) {
            Fail-Guard 'UNBOUND_EXECUTION_INPUT' ([string]$entry.path)
        }
        if (-not $entry.path -or -not (Test-AbsolutePath ([string]$entry.path))) {
            Fail-Guard 'UNBOUND_EXECUTION_INPUT' 'execution input path is not absolute'
        }
        if (-not (Test-Path -LiteralPath $entry.path -PathType Leaf)) {
            Fail-Guard 'EXECUTION_INPUT_MISSING' ([string]$entry.path)
        }
        $item = Get-Item -LiteralPath $entry.path -Force
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            Fail-Guard 'EXECUTION_INPUT_REPARSE_POINT' ([string]$entry.path)
        }
        if ([string]$entry.tracked -ne 'NO') {
            Fail-Guard 'EXECUTION_INPUT_TRACKED' ([string]$entry.path)
        }
        if ([string]$entry.reparse_point -ne 'NO') {
            Fail-Guard 'EXECUTION_INPUT_REPARSE_POINT' ([string]$entry.path)
        }
        if ([string]$entry.read_status -ne 'PASS') {
            Fail-Guard 'EXECUTION_INPUT_READ_ERROR' ([string]$entry.path)
        }
        $actualSha = Get-Hash $entry.path
        if ([Int64]$entry.size_bytes -ne [Int64]$item.Length -or
            ([string]$entry.sha256).ToLowerInvariant() -ne $actualSha) {
            Fail-Guard 'EXECUTION_INPUT_DRIFT' ([string]$entry.path)
        }
        if ($entry.classification -eq 'GENERATED_EXECUTION_INPUT' -and
            (-not $entry.generated_from -or -not $entry.generator_identity -or -not $entry.generated_sha256)) {
            Fail-Guard 'GENERATED_INPUT_LINEAGE_MISSING' ([string]$entry.path)
        }
    }
    if ($null -ne $Manifest.environment_allowlist) {
        foreach ($property in $Manifest.environment_allowlist.psobject.Properties) {
            if ($property.Name -match '(?i)(secret|password|token|cookie|credential)' -and $null -ne $property.Value) {
                Fail-Guard 'ENV_SECRET_UNSAFE' $property.Name
            }
        }
    }
    return $true
}

function Test-ContractInputBound($Manifest, [string]$ContractPath) {
    if (-not $ContractPath) { Fail-Guard 'PREEXECUTION_CONTRACT_REQUIRED' 'contract path is required' }
    if (-not (Test-AbsolutePath $ContractPath)) {
        Fail-Guard 'PREEXECUTION_CONTRACT_REQUIRED' 'contract path must be absolute'
    }
    if (-not (Test-Path -LiteralPath $ContractPath -PathType Leaf)) {
        Fail-Guard 'PREEXECUTION_CONTRACT_REQUIRED' $ContractPath
    }
    $canonicalContract = Get-CanonicalPath $ContractPath
    $bound = @($Manifest.execution_inputs | Where-Object {
        $_.path -and [string]::Equals((Get-CanonicalPath ([string]$_.path)), $canonicalContract, [StringComparison]::OrdinalIgnoreCase)
    })
    if ($bound.Count -ne 1) {
        Fail-Guard 'PREEXECUTION_CONTRACT_UNBOUND' $canonicalContract
    }
    $entry = $bound[0]
    $item = Get-Item -LiteralPath $canonicalContract -Force
    $actualSha = Get-Hash $canonicalContract
    if ([string]$entry.tracked -ne 'NO' -or [string]$entry.reparse_point -ne 'NO' -or
        [string]$entry.read_status -ne 'PASS' -or [Int64]$entry.size_bytes -ne [Int64]$item.Length -or
        ([string]$entry.sha256).ToLowerInvariant() -ne $actualSha) {
        Fail-Guard 'PREEXECUTION_CONTRACT_DRIFT' $canonicalContract
    }
    try { return (Get-Content -Raw -LiteralPath $canonicalContract | ConvertFrom-Json) }
    catch { Fail-Guard 'PREEXECUTION_CONTRACT_INVALID' $_.Exception.Message }
}

function Test-ContractIdentity($Contract, [string]$Sandbox, $Manifest, $RuntimeResult) {
    $schema = [string]$Contract.schema
    $phaseAware = $schema -eq 'AO-04-C3-F5-PREEXECUTION-CONTRACT-PHASE-V1'
    if (-not $Contract -or $schema -notin @('AO-04-C3-F5-PREEXECUTION-CONTRACT-V1','AO-04-C3-F5-PREEXECUTION-CONTRACT-FM021-V1','AO-04-C3-F5-PREEXECUTION-CONTRACT-PHASE-V1')) {
        Fail-Guard 'PREEXECUTION_CONTRACT_INVALID' 'schema mismatch'
    }
    $expectedStatus = if ($schema -in @('AO-04-C3-F5-PREEXECUTION-CONTRACT-FM021-V1','AO-04-C3-F5-PREEXECUTION-CONTRACT-PHASE-V1')) { 'READY_FOR_MATERIALIZATION' } else { 'VALID' }
    if ([string]$Contract.contract_status -ne $expectedStatus) {
        Fail-Guard 'PREEXECUTION_CONTRACT_HOLD' ([string]$Contract.contract_status)
    }
    if (-not [string]::Equals((Get-CanonicalPath ([string]$Contract.sandbox_path)), $Sandbox, [StringComparison]::OrdinalIgnoreCase)) {
        Fail-Guard 'PREEXECUTION_CONTRACT_SANDBOX_MISMATCH' ([string]$Contract.sandbox_path)
    }
    if ([string]$Contract.sandbox_resource_id -ne (Get-SandboxResourceId $Sandbox)) {
        Fail-Guard 'PREEXECUTION_CONTRACT_SANDBOX_MISMATCH' 'resource id differs'
    }
    $volume = [IO.Path]::GetPathRoot($Sandbox)
    if (-not [string]::Equals([string]$Contract.volume_root, $volume, [StringComparison]::OrdinalIgnoreCase)) {
        Fail-Guard 'PREEXECUTION_CONTRACT_VOLUME_MISMATCH' ([string]$Contract.volume_root)
    }
    $route = $Contract.canonical_route_identity
    if (-not $route -or [string]$route.function -ne 'Invoke-F5CanonicalRoute' -or
        [string]$route.mode -ne 'F5Only' -or [string]$route.execution_mode -ne 'RealF5') {
        Fail-Guard 'PREEXECUTION_CONTRACT_ROUTE_MISMATCH' 'canonical route identity differs'
    }
    $probePath = Join-Path $PSScriptRoot 'a3_probe_windows.ps1'
    $guardPath = Get-CanonicalPath $PSCommandPath
    if (-not $Contract.guard_identity -or -not $Contract.probe_identity) {
        Fail-Guard 'PREEXECUTION_CONTRACT_INVALID' 'guard/probe identity is absent'
    }
    if (-not [string]::Equals((Get-CanonicalPath ([string]$Contract.guard_identity.path)), $guardPath, [StringComparison]::OrdinalIgnoreCase) -or
        ([string]$Contract.guard_identity.sha256).ToLowerInvariant() -ne (Get-Hash $guardPath)) {
        Fail-Guard 'PREEXECUTION_CONTRACT_ROUTE_MISMATCH' 'guard identity differs'
    }
    if (-not [string]::Equals((Get-CanonicalPath ([string]$Contract.probe_identity.path)), (Get-CanonicalPath $probePath), [StringComparison]::OrdinalIgnoreCase) -or
        ([string]$Contract.probe_identity.sha256).ToLowerInvariant() -ne (Get-Hash $probePath)) {
        Fail-Guard 'PREEXECUTION_CONTRACT_ROUTE_MISMATCH' 'probe identity differs'
    }
    $probeSource = Get-Content -Raw -LiteralPath $probePath
    if (($probeSource | Select-String -Pattern 'function Invoke-F5CanonicalRoute' -AllMatches).Matches.Count -ne 1) {
        Fail-Guard 'PREEXECUTION_CONTRACT_ROUTE_MISMATCH' 'canonical route function count is not one'
    }
    $runtime = $Contract.runtime_identity
    if (-not $runtime -or -not [string]$runtime.build_identity -or
        -not [string]::Equals((Get-CanonicalPath ([string]$runtime.runtime_root)), (Get-CanonicalPath (Join-Path $Sandbox 'runtime')), [StringComparison]::OrdinalIgnoreCase)) {
        Fail-Guard 'PREEXECUTION_CONTRACT_RUNTIME_MISMATCH' 'runtime identity is incomplete'
    }
    if ([string]$runtime.build_identity -ne [string]$Manifest.runtime_build_identity -or
        [Int64]$runtime.file_count -ne [Int64]$RuntimeResult.file_count -or
        [Int64]$runtime.logical_bytes -ne [Int64]$RuntimeResult.logical_bytes) {
        Fail-Guard 'PREEXECUTION_CONTRACT_RUNTIME_MISMATCH' 'runtime identity differs'
    }
    if ($null -eq $Contract.required_layout) {
        Fail-Guard 'PREEXECUTION_CONTRACT_LAYOUT_UNBOUND' 'required_layout is absent'
    }
    if ($null -eq $Contract.capacity_operations) {
        Fail-Guard 'PREEXECUTION_CONTRACT_CAPACITY_UNBOUND' 'capacity_operations is absent'
    }
    if ($phaseAware) {
        $helperIdentity = $Contract.phase_helper_identity
        if (-not $helperIdentity -or
            -not [string]::Equals((Get-CanonicalPath ([string]$helperIdentity.path)), (Get-CanonicalPath $phaseHelper), [StringComparison]::OrdinalIgnoreCase) -or
            ([string]$helperIdentity.sha256).ToLowerInvariant() -ne (Get-Hash $phaseHelper)) {
            Fail-Guard 'A3_PHASE_INVALID' 'phase helper identity differs'
        }
        Test-A3PhaseModel $Contract.phase_model
        if ([string]$Contract.phase_model.expected_phase -ne 'PRETRIAL') {
            Fail-Guard 'A3_PHASE_INVALID' 'fresh-trial contract must declare PRETRIAL'
        }
        [void](Assert-A3Phase -Sandbox $Sandbox -Model $Contract.phase_model -ExpectedPhase 'PRETRIAL')
        if ([bool]$Contract.contract_grants_execution_authority -or
            [string]$Contract.execution_authority_source -ne 'EXTERNAL_PLANNER_WORK_ORDER') {
            Fail-Guard 'A3_PHASE_INVALID' 'contract cannot grant execution authority'
        }
    }
    if ($schema -in @('AO-04-C3-F5-PREEXECUTION-CONTRACT-FM021-V1','AO-04-C3-F5-PREEXECUTION-CONTRACT-PHASE-V1')) {
        $observerPath = Join-Path $PSScriptRoot 'a3_process_observer.py'
        $observerIdentity = $Contract.observer_identity
        if (-not $observerIdentity -or
            -not [string]::Equals((Get-CanonicalPath ([string]$observerIdentity.path)), (Get-CanonicalPath $observerPath), [StringComparison]::OrdinalIgnoreCase) -or
            ([string]$observerIdentity.sha256).ToLowerInvariant() -ne (Get-Hash $observerPath)) {
            Fail-Guard 'PREEXECUTION_CONTRACT_OBSERVER_IDENTITY_MISMATCH' 'sandbox observer identity differs'
        }
        $jobPath = Join-Path $PSScriptRoot 'a3_job_object.ps1'
        $jobIdentity = $Contract.job_helper_identity
        if (-not $jobIdentity -or
            -not [string]::Equals((Get-CanonicalPath ([string]$jobIdentity.path)), (Get-CanonicalPath $jobPath), [StringComparison]::OrdinalIgnoreCase) -or
            ([string]$jobIdentity.sha256).ToLowerInvariant() -ne (Get-Hash $jobPath)) {
            Fail-Guard 'PREEXECUTION_CONTRACT_JOB_IDENTITY_MISMATCH' 'Job helper identity differs'
        }
        $nativePath = Join-Path $PSScriptRoot 'a3_native_lineage.ps1'
        $nativeIdentity = $Contract.native_lineage_identity
        if (-not $nativeIdentity -or
            -not [string]::Equals((Get-CanonicalPath ([string]$nativeIdentity.path)), (Get-CanonicalPath $nativePath), [StringComparison]::OrdinalIgnoreCase) -or
            ([string]$nativeIdentity.sha256).ToLowerInvariant() -ne (Get-Hash $nativePath)) {
            Fail-Guard 'PREEXECUTION_CONTRACT_NATIVE_LINEAGE_IDENTITY_MISMATCH' 'native lineage identity differs'
        }
        Test-Fm021FixtureIdentity $Contract $Sandbox
        Test-Fm021WriteBounds $Contract
        Write-Output 'FIXTURE_IDENTITIES=PASS'
        Write-Output 'MATERIAL_WRITE_BOUNDS=PASS'
    }
}

function Test-Fm021FixtureIdentity($Contract, [string]$Sandbox) {
    $fixtures = @($Contract.fixture_identities)
    $expectedSchema = '0020_add_tender_operational_revision_events'
    $dbFixtures = @($fixtures | Where-Object { [string]$_.id -eq 'SYNTHETIC_DB_0020' })
    if ($fixtures.Count -ne 2 -or $dbFixtures.Count -ne 1) {
        Fail-Guard 'PREEXECUTION_CONTRACT_FIXTURE_MISMATCH' 'fixture identities are incomplete'
    }
    $dbFixture = $dbFixtures[0]
    $recovery = $Contract.recovery_semantics
    if (-not $recovery -or [string]$recovery.model -ne 'PRE_MIGRATION_DB_GENERATION_INVARIANCE' -or
        [string]$recovery.start_schema -ne $expectedSchema -or
        [string]$recovery.end_schema -ne $expectedSchema -or
        [string]$recovery.schema_downgrade -ne 'OUT_OF_SCOPE' -or
        [string]$dbFixture.schema -ne $expectedSchema) {
        Fail-Guard 'PREEXECUTION_CONTRACT_FIXTURE_MISMATCH' 'pre-migration recovery contract is invalid'
    }
    $seedIdentity = $Contract.seed_spec_identity
    if (-not $seedIdentity -or -not (Test-Path -LiteralPath ([string]$seedIdentity.path) -PathType Leaf) -or
        ([string]$seedIdentity.sha256).ToLowerInvariant() -ne (Get-Hash ([string]$seedIdentity.path))) {
        Fail-Guard 'PREEXECUTION_CONTRACT_FIXTURE_MISMATCH' 'seed specification identity differs'
    }
    try { $seedSpec = Get-Content -Raw -LiteralPath ([string]$seedIdentity.path) | ConvertFrom-Json }
    catch { Fail-Guard 'PREEXECUTION_CONTRACT_FIXTURE_MISMATCH' 'seed specification is invalid' }
    if ([string]$seedSpec.target_revision -ne $expectedSchema -or
        ([string]$seedSpec.expected_logical_digest).ToLowerInvariant() -ne ([string]$dbFixture.logical_digest).ToLowerInvariant() -or
        [bool]$seedSpec.business_data_required) {
        Fail-Guard 'PREEXECUTION_CONTRACT_FIXTURE_MISMATCH' 'seed specification contradicts the frozen fixture'
    }
    $sandboxPrefix = $Sandbox.TrimEnd('\') + '\'
    foreach ($fixture in $fixtures) {
        $relative = Normalize-Relative ([string]$fixture.relative_path)
        if (-not $relative -or $relative.StartsWith('../') -or [IO.Path]::IsPathRooted($relative)) {
            Fail-Guard 'PREEXECUTION_CONTRACT_FIXTURE_MISMATCH' 'fixture path is invalid'
        }
        $path = Get-CanonicalPath (Join-Path $Sandbox $relative.Replace('/','\'))
        if (-not $path.StartsWith($sandboxPrefix, [StringComparison]::OrdinalIgnoreCase) -or -not (Test-Path -LiteralPath $path -PathType Leaf)) {
            Fail-Guard 'PREEXECUTION_CONTRACT_FIXTURE_MISMATCH' $relative
        }
        $item = Get-Item -LiteralPath $path
        if ([Int64]$fixture.size_bytes -ne [Int64]$item.Length -or ([string]$fixture.sha256).ToLowerInvariant() -ne (Get-Hash $path)) {
            Fail-Guard 'PREEXECUTION_CONTRACT_FIXTURE_MISMATCH' ([string]$fixture.id)
        }
        if ([string]$fixture.id -eq 'SYNTHETIC_DB_0020') {
            if (-not (Test-Path -LiteralPath ([string]$fixture.source_path) -PathType Leaf) -or
                ([string]$fixture.sha256).ToLowerInvariant() -ne (Get-Hash ([string]$fixture.source_path))) {
                Fail-Guard 'PREEXECUTION_CONTRACT_FIXTURE_MISMATCH' 'frozen database source differs'
            }
            if ([string]$fixture.logical_digest_algorithm -ne 'qi-sqlite-logical-v1') {
                Fail-Guard 'PREEXECUTION_CONTRACT_FIXTURE_MISMATCH' 'logical digest algorithm'
            }
            $tool = $Contract.logical_digest_tool
            if (-not $tool -or -not (Test-Path -LiteralPath ([string]$tool.path) -PathType Leaf) -or
                ([string]$tool.sha256).ToLowerInvariant() -ne (Get-Hash ([string]$tool.path))) {
                Fail-Guard 'PREEXECUTION_CONTRACT_FIXTURE_MISMATCH' 'logical digest tool'
            }
            $python = Join-Path $repo '.venv\Scripts\python.exe'
            if (-not (Test-Path -LiteralPath $python -PathType Leaf)) { Fail-Guard 'PREEXECUTION_CONTRACT_FIXTURE_MISMATCH' 'python unavailable' }
            try { $digestRaw = @(& $python ([string]$tool.path) '--digest' $path 2>&1); $digestExit = $LASTEXITCODE; $digest = (($digestRaw -join "`n") | ConvertFrom-Json) }
            catch { Fail-Guard 'PREEXECUTION_CONTRACT_FIXTURE_MISMATCH' 'logical digest failed' }
            if ($digestExit -ne 0 -or [string]$digest.revision -ne $expectedSchema) {
                Fail-Guard 'PREEXECUTION_CONTRACT_FIXTURE_MISMATCH' 'database schema is not pre-migration 0020'
            }
            if ([string]$digest.algorithm -ne [string]$fixture.logical_digest_algorithm -or
                ([string]$digest.sha256).ToLowerInvariant() -ne ([string]$fixture.logical_digest).ToLowerInvariant()) {
                Fail-Guard 'PREEXECUTION_CONTRACT_FIXTURE_MISMATCH' 'logical digest differs'
            }
        }
    }
}

function Test-Fm021WriteBounds($Contract) {
    $required = @('EVIDENCE_META','PROCESS_CENSUS','TX_STATE','DB_MANIFEST','ROUTE_ARTIFACTS','RECOVERY')
    $entries = @($Contract.material_write_bounds)
    if ($entries.Count -ne $required.Count) { Fail-Guard 'PREEXECUTION_CONTRACT_WRITE_BOUND_UNKNOWN' 'class count' }
    foreach ($name in $required) {
        $matches = @($entries | Where-Object { [string]$_.write_class -eq $name })
        if ($matches.Count -ne 1) { Fail-Guard 'PREEXECUTION_CONTRACT_WRITE_BOUND_UNKNOWN' $name }
        $entry = $matches[0]
        foreach ($field in @('max_file_count','max_per_file_bytes','max_aggregate_bytes','max_atomic_overlap_bytes')) {
            if ($null -eq $entry.$field -or [Int64]$entry.$field -lt 1) { Fail-Guard 'PREEXECUTION_CONTRACT_WRITE_BOUND_UNKNOWN' "$name.$field" }
        }
        if ($name -eq 'PROCESS_CENSUS' -and ($null -eq $entry.max_records -or $null -eq $entry.max_field_bytes)) {
            Fail-Guard 'PREEXECUTION_CONTRACT_WRITE_BOUND_UNKNOWN' $name
        }
        if ($name -eq 'DB_MANIFEST' -and [Int64]$entry.max_entries -ne 4) {
            Fail-Guard 'PREEXECUTION_CONTRACT_WRITE_BOUND_UNKNOWN' $name
        }
        if ($name -in @('ROUTE_ARTIFACTS','RECOVERY') -and
            ($null -eq $entry.max_stdout_bytes -or $null -eq $entry.max_stderr_bytes -or $null -eq $entry.max_runtime_seconds)) {
            Fail-Guard 'PREEXECUTION_CONTRACT_WRITE_BOUND_UNKNOWN' $name
        }
    }
    foreach ($binding in @(
        @('bounded_io_identity', (Join-Path $PSScriptRoot 'a3_f5_bounded_io.ps1')),
        @('recovery_identity', (Join-Path $PSScriptRoot 'a3_recovery.py'))
    )) {
        $identity = $Contract.($binding[0])
        $expectedPath = Get-CanonicalPath $binding[1]
        if (-not $identity -or -not [string]::Equals((Get-CanonicalPath ([string]$identity.path)), $expectedPath, [StringComparison]::OrdinalIgnoreCase) -or
            ([string]$identity.sha256).ToLowerInvariant() -ne (Get-Hash $expectedPath)) {
            Fail-Guard 'PREEXECUTION_CONTRACT_WRITE_BOUND_IDENTITY_MISMATCH' ([string]$binding[0])
        }
    }
}

function Test-ExistingSandboxLayout($Contract, [string]$Sandbox) {
    $entries = @($Contract.required_layout)
    if ($entries.Count -eq 0) { Fail-Guard 'PREEXECUTION_CONTRACT_LAYOUT_UNBOUND' 'required_layout is empty' }
    $generatedAbsent = @()
    foreach ($entry in $entries) {
        if (-not $entry.id -or -not $entry.relative_path -or -not $entry.classification -or -not $entry.kind -or
            $null -eq $entry.must_exist_before_dispatch -or $null -eq $entry.may_be_created_during_f5 -or
            $null -eq $entry.expected_max_bytes -or -not $entry.bound_source -or -not $entry.recovery_requirement) {
            Fail-Guard 'PREEXECUTION_CONTRACT_LAYOUT_UNBOUND' ([string]$entry.id)
        }
        $relative = Normalize-Relative ([string]$entry.relative_path)
        if ($relative.StartsWith('../') -or $relative -eq '..' -or [IO.Path]::IsPathRooted($relative)) {
            Fail-Guard 'PREEXECUTION_CONTRACT_LAYOUT_UNBOUND' 'layout path escapes sandbox'
        }
        $target = Join-Path $Sandbox ($relative.Replace('/', '\'))
        $exists = Test-Path -LiteralPath $target
        if (-not $exists) {
            if ([bool]$entry.must_exist_before_dispatch) {
                Fail-Guard 'EXISTING_SANDBOX_LAYOUT_INVALID' "$relative is required before dispatch"
            }
            if ([string]$entry.classification -notin @('GENERATED_EMPTY_CONTROL_DIRECTORY', 'GENERATED_BOUNDED_EVIDENCE', 'GENERATED_BOUNDED_TRANSACTION_STATE')) {
                Fail-Guard 'EXISTING_SANDBOX_LAYOUT_INVALID' "$relative is missing and is not a generated path"
            }
            $generatedAbsent += $relative
            continue
        }
        $item = Get-Item -LiteralPath $target -Force
        if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            Fail-Guard 'EXISTING_SANDBOX_LAYOUT_INVALID' "$relative is a reparse point"
        }
        if ([string]$entry.kind -eq 'directory' -and -not $item.PSIsContainer) {
            Fail-Guard 'EXISTING_SANDBOX_LAYOUT_INVALID' "$relative is not a directory"
        }
        if ([string]$entry.kind -eq 'file' -and $item.PSIsContainer) {
            Fail-Guard 'EXISTING_SANDBOX_LAYOUT_INVALID' "$relative is not a file"
        }
    }
    return [ordered]@{ pass = $true; generated_absent = @($generatedAbsent); required_count = $entries.Count }
}

function Test-CapacityContract($Contract, [string]$Sandbox) {
    $allowedOperations = @('MATERIALIZATION', 'EVIDENCE', 'TX_STATE', 'DB_MANIFEST', 'DB_SNAPSHOT', 'ROUTE_ARTIFACTS', 'RECOVERY')
    $operations = @($Contract.capacity_operations)
    if ($operations.Count -eq 0) { Fail-Guard 'PREEXECUTION_CONTRACT_CAPACITY_UNBOUND' 'no capacity operations' }
    if ([Int64]$Contract.recovery_reserve_bytes -lt 2147483648 -or [Int64]$Contract.safety_reserve_bytes -lt 4294967296) {
        Fail-Guard 'PREEXECUTION_CONTRACT_CAPACITY_UNBOUND' 'reserve policy is below the required minimum'
    }
    if ([Int64]$Contract.max_runtime_copies -ne 0 -or [Int64]$Contract.max_new_sandboxes -ne 0 -or
        [Int64]$Contract.max_automatic_retries -ne 0 -or [Int64]$Contract.max_concurrent_trials -ne 1) {
        Fail-Guard 'PREEXECUTION_CONTRACT_CAPACITY_UNBOUND' 'copy/retry/concurrency policy is unsafe'
    }
    foreach ($operation in $operations) {
        if ([string]$operation.operation_id -notin $allowedOperations) {
            Fail-Guard 'PREEXECUTION_CONTRACT_CAPACITY_UNBOUND' ([string]$operation.operation_id)
        }
        foreach ($field in @('max_write_bytes', 'temporary_overhead_bytes', 'peak_bytes', 'remaining_worst_case_after')) {
            if ([string]$operation.$field -notmatch '^[0-9]+$') {
                Fail-Guard 'PREEXECUTION_CONTRACT_CAPACITY_UNBOUND' "$($operation.operation_id).$field"
            }
        }
        if (-not $operation.bound_source -or [bool]$operation.fail_closed_if_unknown -ne $true) {
            Fail-Guard 'PREEXECUTION_CONTRACT_CAPACITY_UNBOUND' "$($operation.operation_id) has no fail-closed bound"
        }
        if ([Int64]$operation.max_write_bytes + [Int64]$operation.temporary_overhead_bytes -gt [Int64]$operation.peak_bytes) {
            Fail-Guard 'PREEXECUTION_CONTRACT_CAPACITY_UNBOUND' "$($operation.operation_id) peak is below write plus overhead"
        }
        if (-not [string]::Equals([string]$operation.target_volume, [string]$Contract.volume_root, [StringComparison]::OrdinalIgnoreCase)) {
            Fail-Guard 'PREEXECUTION_CONTRACT_VOLUME_MISMATCH' ([string]$operation.target_volume)
        }
    }
    $first = $operations[0]
    if ([Int64]$Contract.next_operation_peak_bytes -ne [Int64]$first.peak_bytes -or
        [Int64]$Contract.remaining_peak_bytes -ne [Int64]$first.remaining_worst_case_after -or
        [Int64]$Contract.next_operation_peak_bytes -le 0 -or [Int64]$Contract.remaining_peak_bytes -lt 0) {
        Fail-Guard 'PREEXECUTION_CONTRACT_CAPACITY_UNBOUND' 'top-level capacity does not bind first operation'
    }
    $measurement = Get-AvailableFreeBytesForPath $Sandbox
    $left = [Int64]$measurement.free_now_bytes - [Int64]$Contract.next_operation_peak_bytes
    $right = [Int64]$Contract.remaining_peak_bytes + [Int64]$Contract.recovery_reserve_bytes + [Int64]$Contract.safety_reserve_bytes
    if ($left -le $right) {
        Fail-Guard 'CAPACITY_INSUFFICIENT' "free=$($measurement.free_now_bytes);next=$($Contract.next_operation_peak_bytes);remaining=$($Contract.remaining_peak_bytes);recovery=$($Contract.recovery_reserve_bytes);safety=$($Contract.safety_reserve_bytes)"
    }
    return [ordered]@{
        pass = $true
        free_now_bytes = [Int64]$measurement.free_now_bytes
        volume_root = [string]$measurement.volume_root
        measurement_method = [string]$measurement.measurement_method
        next_operation_peak_bytes = [Int64]$Contract.next_operation_peak_bytes
        remaining_peak_bytes = [Int64]$Contract.remaining_peak_bytes
        recovery_reserve_bytes = [Int64]$Contract.recovery_reserve_bytes
        safety_reserve_bytes = [Int64]$Contract.safety_reserve_bytes
        projected_free_after_operation = $left
    }
}

function Get-ContractCapacityBinding($Contract) {
    return [ordered]@{
        SafetyReserveBytes = [Int64]$Contract.safety_reserve_bytes
        RecoveryReserveBytes = [Int64]$Contract.recovery_reserve_bytes
        NextOperationPeakBytes = [Int64]$Contract.next_operation_peak_bytes
        RemainingPeakAfterOperationBytes = [Int64]$Contract.remaining_peak_bytes
    }
}

function Get-AvailableFreeBytesForPath([string]$Path) {
    if (-not (Test-AbsolutePath $Path)) {
        Fail-Guard 'CAPACITY_MEASUREMENT_ERROR' 'capacity path must be an absolute filesystem path'
    }
    try {
        $canonical = Get-CanonicalPath $Path
        $root = [IO.Path]::GetPathRoot($canonical)
        if (-not $root) { throw 'capacity path has no filesystem volume root' }
        $driveInfo = New-Object -TypeName 'System.IO.DriveInfo' -ArgumentList @($root)
        if ($driveInfo.DriveType -eq [IO.DriveType]::NoRootDirectory -or -not $driveInfo.IsReady) {
            throw "filesystem volume is unavailable: $root"
        }
        $available = [Int64]$driveInfo.AvailableFreeSpace
        if ($available -lt 0) { throw 'filesystem volume returned a negative free-space value' }
        return [ordered]@{
            free_now_bytes = $available
            volume_root = [string]$driveInfo.Name
            measurement_method = 'System.IO.DriveInfo.AvailableFreeSpace'
        }
    } catch {
        Fail-Guard 'CAPACITY_MEASUREMENT_ERROR' $_.Exception.Message
    }
}

function Test-Capacity([string]$Sandbox) {
    if ($SafetyReserveBytes -lt 4294967296) { Fail-Guard 'CAPACITY_UNKNOWN' 'safety reserve is below 4 GiB' }
    if (-not $DryRun -and ($NextOperationPeakBytes -le 0 -or $RemainingPeakAfterOperationBytes -lt 0)) {
        Fail-Guard 'CAPACITY_UNKNOWN' 'real F5 capacity peaks are not explicitly bounded'
    }
    $testCapacityOverride = ($TestDispatchBoundary -and $env:QI_CRAWLER_F5_TEST_MODE -eq '1')
    $measurement = if (($DryRun -or $testCapacityOverride) -and $FreeNowBytes -ge 0) {
        [ordered]@{
            free_now_bytes = [Int64]$FreeNowBytes
            volume_root = 'TEST_OVERRIDE'
            measurement_method = 'TEST_OVERRIDE'
        }
    } else {
        Get-AvailableFreeBytesForPath $Sandbox
    }
    $free = [Int64]$measurement.free_now_bytes
    $isDryNoWrite = [bool]$DryRun -and $NextOperationPeakBytes -eq 0 -and $RemainingPeakAfterOperationBytes -eq 0 -and $RecoveryReserveBytes -eq 0
    if ($isDryNoWrite) {
        return [ordered]@{ free_now_bytes = $free; volume_root = $measurement.volume_root; measurement_method = $measurement.measurement_method; next_operation_peak_bytes = 0; remaining_peak_bytes = 0; recovery_reserve_bytes = 0; safety_reserve_bytes = $SafetyReserveBytes; pass = $true; mode = 'DRY_RUN_NO_MATERIAL_WRITE' }
    }
    if ($NextOperationPeakBytes -lt 0 -or $RemainingPeakAfterOperationBytes -lt 0 -or $RecoveryReserveBytes -lt 0) {
        Fail-Guard 'CAPACITY_UNKNOWN' 'negative capacity component'
    }
    $left = $free - $NextOperationPeakBytes
    $right = $RemainingPeakAfterOperationBytes + $RecoveryReserveBytes + $SafetyReserveBytes
    if ($left -le $right) {
        Fail-Guard 'CAPACITY_INSUFFICIENT' "free=$free;next=$NextOperationPeakBytes;remaining=$RemainingPeakAfterOperationBytes;reserve=$RecoveryReserveBytes;safety=$SafetyReserveBytes"
    }
    return [ordered]@{ free_now_bytes = $free; volume_root = $measurement.volume_root; measurement_method = $measurement.measurement_method; next_operation_peak_bytes = $NextOperationPeakBytes; remaining_peak_bytes = $RemainingPeakAfterOperationBytes; recovery_reserve_bytes = $RecoveryReserveBytes; safety_reserve_bytes = $SafetyReserveBytes; pass = $true; projected_free_after_operation = $left }
}

if ($CapacityProbeOnly) {
    if ($env:QI_CRAWLER_F5_TEST_MODE -ne '1') {
        Fail-Guard 'TEST_OVERRIDE_FORBIDDEN' 'capacity probe requires QI_CRAWLER_F5_TEST_MODE=1'
    }
    if (-not $CapacityProbePath) {
        Fail-Guard 'CAPACITY_MEASUREMENT_ERROR' 'capacity probe path is required'
    }
    $probeMeasurement = Get-AvailableFreeBytesForPath $CapacityProbePath
    Write-Output 'CAPACITY_MEASUREMENT_STATUS=PASS'
    Write-Output "CAPACITY_FREE_NOW_BYTES=$($probeMeasurement.free_now_bytes)"
    Write-Output "CAPACITY_VOLUME_ROOT=$($probeMeasurement.volume_root)"
    Write-Output "CAPACITY_MEASUREMENT_METHOD=$($probeMeasurement.measurement_method)"
    return
}

function Get-TextSha256([string]$Value) {
    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [Text.Encoding]::UTF8.GetBytes($Value)
        return ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '').ToLowerInvariant()
    } finally {
        $sha.Dispose()
    }
}

function Get-SandboxResourceId([string]$Sandbox) {
    $canonical = (Get-CanonicalPath $Sandbox).TrimEnd('\').ToLowerInvariant().Replace('\', '/')
    return Get-TextSha256 $canonical
}

function Get-LifecycleStateRoot([string]$ResourceId) {
    if ($TestStateRoot) {
        return Join-Path (Get-CanonicalPath $TestStateRoot) $ResourceId
    }
    return Join-Path $repo ("release_staging\control\a3_f5_guard\$ResourceId")
}

function Read-LifecycleState([string]$Path, [string]$ResourceId, [string]$CanonicalSandbox) {
    if (-not (Test-Path -LiteralPath $Path)) { return $null }
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        Fail-Guard 'STATE_CORRUPT' 'lifecycle state path is not a file'
    }
    try {
        $state = Get-Content -Raw -LiteralPath $Path | ConvertFrom-Json
    } catch {
        Fail-Guard 'STATE_CORRUPT' 'lifecycle state is not valid JSON'
    }
    $required = @('sandbox_resource_id', 'canonical_sandbox_path', 'last_run_id', 'last_evidence_root', 'input_manifest_sha256', 'execution_state', 'updated_utc')
    foreach ($field in $required) {
        if ($null -eq $state.$field -or [string]::IsNullOrWhiteSpace([string]$state.$field)) {
            Fail-Guard 'STATE_CORRUPT' "missing field $field"
        }
    }
    if ([string]$state.sandbox_resource_id -ne $ResourceId -or
        -not [string]::Equals([string]$state.canonical_sandbox_path, $CanonicalSandbox, [StringComparison]::OrdinalIgnoreCase)) {
        Fail-Guard 'STATE_RESOURCE_MISMATCH' $Path
    }
    $allowed = @('PREPARED', 'RUNNING', 'POST_BARRIER', 'POST_KILL_VERIFICATION', 'INCOMPLETE', 'INCOMPLETE_STORAGE_FAILURE', 'COMPLETED', 'FAILED')
    if ([string]$state.execution_state -notin $allowed) {
        Fail-Guard 'STATE_CORRUPT' "unknown execution state $($state.execution_state)"
    }
    return $state
}

function Test-GitIdentity($Manifest) {
    $actualHead = (& git -C $repo rev-parse HEAD 2>$null).Trim()
    $headExit = $LASTEXITCODE
    $actualBranch = (& git -C $repo branch --show-current 2>$null).Trim()
    $branchExit = $LASTEXITCODE
    if ($headExit -ne 0 -or $branchExit -ne 0) {
        Fail-Guard 'GIT_IDENTITY_UNAVAILABLE'
    }
    if (-not $actualHead -or $actualHead -ne [string]$Manifest.head) {
        Fail-Guard 'GIT_HEAD_DRIFT' "expected=$($Manifest.head);actual=$actualHead"
    }
    if (-not $actualBranch -or $actualBranch -ne [string]$Manifest.branch) {
        Fail-Guard 'GIT_BRANCH_DRIFT' "expected=$($Manifest.branch);actual=$actualBranch"
    }
    $actualStatus = @(& git -C $repo status --short 2>$null)
    if ($LASTEXITCODE -ne 0) { Fail-Guard 'GIT_STATUS_UNAVAILABLE' }
    $expectedStatus = @($Manifest.git_status | ForEach-Object { [string]$_ })
    if (($actualStatus -join "`n") -ne ($expectedStatus -join "`n")) {
        Fail-Guard 'GIT_STATUS_DRIFT'
    }
}

function Write-LifecycleState([string]$Path, $Payload) {
    $parent = Split-Path -Parent $Path
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
    $temporary = "$Path.$PID.$([Guid]::NewGuid().ToString('N')).tmp"
    $stream = $null
    try {
        $text = (($Payload | ConvertTo-Json -Depth 8) + "`n")
        $encoding = New-Object Text.UTF8Encoding($false)
        $bytes = $encoding.GetBytes($text)
        $stream = [IO.File]::Open($temporary, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
        $stream.Write($bytes, 0, $bytes.Length)
        try { $stream.Flush($true) } catch { $stream.Flush() }
        $stream.Dispose()
        $stream = $null
        if (Test-Path -LiteralPath $Path -PathType Leaf) {
            $backup = "$Path.$PID.$([Guid]::NewGuid().ToString('N')).bak"
            [IO.File]::Replace($temporary, $Path, $backup, $true)
            if (Test-Path -LiteralPath $backup) { Remove-Item -LiteralPath $backup -Force -ErrorAction SilentlyContinue }
        } elseif (Test-Path -LiteralPath $Path) {
            Fail-Guard 'STATE_WRITE_FAILURE' 'lifecycle state destination is not a file'
        } else {
            [IO.File]::Move($temporary, $Path)
        }
        return $Payload
    } catch {
        if ($null -ne $stream) { $stream.Dispose() }
        if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary -Force -ErrorAction SilentlyContinue }
        throw
    }
}

function New-LifecyclePayload(
    [string]$State,
    [string]$RunId,
    [string]$ResourceId,
    [string]$CanonicalSandbox,
    [string]$EvidenceRootValue,
    [string]$ManifestSha,
    [string]$FailureReason = ''
) {
    return [ordered]@{
        schema = 'AO-04-C3-F5-LIFECYCLE-V2'
        sandbox_resource_id = $ResourceId
        canonical_sandbox_path = $CanonicalSandbox
        last_run_id = $RunId
        last_evidence_root = $EvidenceRootValue
        input_manifest_sha256 = $ManifestSha
        execution_state = $State
        updated_utc = (Get-Date).ToUniversalTime().ToString('o')
        pid = $PID
        failure_reason = $FailureReason
    }
}

function Set-LifecycleState(
    [string]$Path,
    [string]$State,
    [string]$RunId,
    [string]$ResourceId,
    [string]$CanonicalSandbox,
    [string]$EvidenceRootValue,
    [string]$ManifestSha,
    [string]$FailureReason = ''
) {
    $payload = New-LifecyclePayload $State $RunId $ResourceId $CanonicalSandbox $EvidenceRootValue $ManifestSha $FailureReason
    try {
        return Write-LifecycleState $Path $payload
    } catch {
        Fail-Guard 'STATE_WRITE_FAILURE' $_.Exception.Message
    }
}

$lock = $null
$globalLock = $null
$statePath = $null
$lockPath = $null
$globalLockPath = if ($TestGlobalLockPath) { $TestGlobalLockPath } else { Join-Path ([IO.Path]::GetTempPath()) 'qi-crawler-a3-f5-guard-global.lock' }
$evidence = $null
$sandbox = $null
$resourceId = $null
$stateRoot = $null
$manifestSha = $null
try {
    if ($Mode -ne 'F5Only') { Fail-Guard 'F5_ONLY_REQUIRED' }
    if (-not (Test-AbsolutePath $ExistingSandboxPath)) { Fail-Guard 'EXISTING_SANDBOX_INVALID' 'sandbox path must be absolute' }
    if (-not (Test-AbsolutePath $InputManifestPath)) { Fail-Guard 'INPUT_MANIFEST_INVALID' 'manifest path must be absolute' }
    $testHooksAllowed = ($env:QI_CRAWLER_F5_TEST_MODE -eq '1' -and ($DryRun -or $TestDispatchBoundary))
    if (($TestStateRoot -or $TestMaterialWritePath) -and -not $testHooksAllowed) {
        Fail-Guard 'TEST_OVERRIDE_FORBIDDEN' 'test-only filesystem hooks require QI_CRAWLER_F5_TEST_MODE=1 and a bounded test dispatch'
    }
    if ($TestDispatchBoundary -and ($env:QI_CRAWLER_F5_TEST_MODE -ne '1' -or $ExecutionMode -ne 'RealF5')) {
        Fail-Guard 'TEST_OVERRIDE_FORBIDDEN' 'dispatch boundary requires QI_CRAWLER_F5_TEST_MODE=1 and ExecutionMode=RealF5'
    }
    if ($DispatchHoldSeconds -lt 0) { Fail-Guard 'TEST_OVERRIDE_FORBIDDEN' 'DispatchHoldSeconds must be non-negative' }
    if ($TestStateRoot -and -not (Test-AbsolutePath $TestStateRoot)) { Fail-Guard 'TEST_OVERRIDE_FORBIDDEN' 'TestStateRoot must be absolute' }
    if ($TestMaterialWritePath -and -not (Test-AbsolutePath $TestMaterialWritePath)) { Fail-Guard 'TEST_OVERRIDE_FORBIDDEN' 'TestMaterialWritePath must be absolute' }
    if ($TestGlobalLockPath -and $env:QI_CRAWLER_F5_TEST_MODE -ne '1') {
        Fail-Guard 'TEST_OVERRIDE_FORBIDDEN' 'TestGlobalLockPath requires QI_CRAWLER_F5_TEST_MODE=1'
    }
    if ($TestGlobalLockPath -and -not (Test-AbsolutePath $TestGlobalLockPath)) { Fail-Guard 'TEST_OVERRIDE_FORBIDDEN' 'TestGlobalLockPath must be absolute' }
    if ($TestGlobalLockPath) { $globalLockPath = Get-CanonicalPath $TestGlobalLockPath }
    if (-not (Test-Path -LiteralPath $ExistingSandboxPath -PathType Container)) { Fail-Guard 'EXISTING_SANDBOX_INVALID' 'sandbox does not exist' }
    $sandbox = Get-CanonicalPath $ExistingSandboxPath
    $resourceId = Get-SandboxResourceId $sandbox
    $stateRoot = Get-LifecycleStateRoot $resourceId
    $statePath = Join-Path $stateRoot 'lifecycle_state.json'
    $lockPath = Join-Path $stateRoot 'sandbox.lock'
    if (-not (Test-Path -LiteralPath $InputManifestPath -PathType Leaf)) { Fail-Guard 'INPUT_MANIFEST_INVALID' 'manifest does not exist' }
    $manifest = Get-Json $InputManifestPath
    $manifestSha = Get-Hash $InputManifestPath
    if (-not [string]::Equals((Get-CanonicalPath ([string]$manifest.sandbox_path)), $sandbox, [StringComparison]::OrdinalIgnoreCase)) { Fail-Guard 'EXISTING_SANDBOX_INVALID' 'manifest sandbox identity differs' }
    if (-not $manifest.head -or -not $manifest.branch -or $null -eq $manifest.git_status) { Fail-Guard 'INPUT_MANIFEST_INVALID' 'Git identity fields are incomplete' }
    Test-GitIdentity $manifest
    $runtimeResult = Test-RuntimeManifest $manifest $sandbox
    [void](Test-ExecutionInputs $manifest)

    if ($PreflightOnly) {
        if (-not $PreexecutionContractPath) {
            Fail-Guard 'PREEXECUTION_CONTRACT_REQUIRED' 'preflight requires a frozen contract'
        }
        $preflightContract = Test-ContractInputBound $manifest $PreexecutionContractPath
        Test-ContractIdentity $preflightContract $sandbox $manifest $runtimeResult
        $layout = Test-ExistingSandboxLayout $preflightContract $sandbox
        $preflightCapacity = Test-CapacityContract $preflightContract $sandbox
        Write-Output 'PREEXECUTION_CONTRACT=PASS'
        Write-Output 'EXISTING_SANDBOX_LAYOUT=PASS'
        Write-Output 'CAPACITY_CONTRACT=PASS'
        Write-Output "CAPACITY_FREE_NOW_BYTES=$($preflightCapacity.free_now_bytes)"
        Write-Output "CAPACITY_VOLUME_ROOT=$($preflightCapacity.volume_root)"
        Write-Output 'F5_EXECUTED=NO'
        Write-Output 'REAL_SANDBOX_MUTATION=NO'
        exit 0
    }

    New-Item -ItemType Directory -Force -Path $stateRoot | Out-Null

    try { $globalLock = [IO.File]::Open($globalLockPath, [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None) }
    catch { Fail-Guard 'CONCURRENT_TRIAL_BLOCKED' $globalLockPath }
    try { $lock = [IO.File]::Open($lockPath, [IO.FileMode]::OpenOrCreate, [IO.FileAccess]::ReadWrite, [IO.FileShare]::None) }
    catch { Fail-Guard 'CONCURRENT_TRIAL_BLOCKED' $lockPath }
    $previous = Read-LifecycleState $statePath $resourceId $sandbox
    if ($previous -and [string]$previous.execution_state -in @('PREPARED', 'RUNNING', 'POST_BARRIER', 'POST_KILL_VERIFICATION', 'INCOMPLETE', 'INCOMPLETE_STORAGE_FAILURE')) {
        Fail-Guard 'PREVIOUS_TRIAL_INCOMPLETE' ([string]$previous.execution_state)
    }
    if ($previous -and $previous.last_run_id -eq $RunId) { Fail-Guard 'RUN_ID_REUSE' $RunId }
    $evidence = if ($EvidenceRoot) { $EvidenceRoot } else { Join-Path $repo "release_staging\evidence\AO-04-C3-F5-GUARD-$RunId" }
    if (-not (Test-AbsolutePath $evidence)) { $evidence = Join-Path $repo $evidence }
    New-Item -ItemType Directory -Force -Path $evidence | Out-Null
    $evidence = Get-CanonicalPath $evidence
    # Revalidate at the point of use after the exclusive lock is acquired.
    # This closes the TOCTOU window between preflight identity checks and the
    # first material evidence write.
    Test-GitIdentity $manifest
    $runtimeResult = Test-RuntimeManifest $manifest $sandbox
    [void](Test-ExecutionInputs $manifest)
    if ($DryRun) { $ExecutionMode = 'DryRun' }
    if ($ExecutionMode -eq 'Unspecified') {
        Fail-Guard 'REAL_F5_REQUIRES_AO_04_C3_F5_01' 'guard work order does not authorize real F5'
    }
    if ($DryRun -and $ExecutionMode -eq 'RealF5') {
        Fail-Guard 'EXECUTION_MODE_CONFLICT' 'DryRun cannot be combined with RealF5'
    }
    $executionContract = $null
    if ($ExecutionMode -eq 'RealF5') {
        if (-not $PreexecutionContractPath) {
            Fail-Guard 'CAPACITY_UNKNOWN' 'RealF5 requires a frozen preexecution contract'
        }
        $executionContract = Test-ContractInputBound $manifest $PreexecutionContractPath
        if (-not $TestDispatchBoundary -and [string]$executionContract.schema -ne 'AO-04-C3-F5-PREEXECUTION-CONTRACT-PHASE-V1') {
            Fail-Guard 'A3_PHASE_INVALID' 'historical contract cannot authorize a future trial'
        }
        Test-ContractIdentity $executionContract $sandbox $manifest $runtimeResult
        if (-not $TestDispatchBoundary) {
            [void](Test-ExistingSandboxLayout $executionContract $sandbox)
        }
        $binding = Get-ContractCapacityBinding $executionContract
        if (($PSBoundParameters.ContainsKey('SafetyReserveBytes') -and $SafetyReserveBytes -ne $binding.SafetyReserveBytes) -or
            ($PSBoundParameters.ContainsKey('RecoveryReserveBytes') -and $RecoveryReserveBytes -ne $binding.RecoveryReserveBytes) -or
            ($PSBoundParameters.ContainsKey('NextOperationPeakBytes') -and $NextOperationPeakBytes -ne $binding.NextOperationPeakBytes) -or
            ($PSBoundParameters.ContainsKey('RemainingPeakAfterOperationBytes') -and $RemainingPeakAfterOperationBytes -ne $binding.RemainingPeakAfterOperationBytes)) {
            Fail-Guard 'PREEXECUTION_CONTRACT_CAPACITY_MISMATCH' 'CLI capacity values differ from frozen contract'
        }
        $SafetyReserveBytes = $binding.SafetyReserveBytes
        $RecoveryReserveBytes = $binding.RecoveryReserveBytes
        $NextOperationPeakBytes = $binding.NextOperationPeakBytes
        $RemainingPeakAfterOperationBytes = $binding.RemainingPeakAfterOperationBytes
    }
    $capacity = Test-Capacity $sandbox
    Set-LifecycleState $statePath 'PREPARED' $RunId $resourceId $sandbox $evidence $manifestSha | Out-Null
    Set-LifecycleState $statePath 'RUNNING' $RunId $resourceId $sandbox $evidence $manifestSha | Out-Null

    if ($SimulateStorageFailure) {
        Set-LifecycleState $statePath 'INCOMPLETE_STORAGE_FAILURE' $RunId $resourceId $sandbox $evidence $manifestSha 'simulated bounded write failure; retry is disabled' | Out-Null
        Fail-Guard 'INCOMPLETE_STORAGE_FAILURE' 'simulated bounded write failure; retry is disabled'
    }

    if ($TestMaterialWritePath) {
        $materialStream = $null
        try {
            $materialStream = [IO.File]::Open($TestMaterialWritePath, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
            $markerBytes = [Text.Encoding]::UTF8.GetBytes('C2_TEST_MATERIAL_WRITE')
            $materialStream.Write($markerBytes, 0, $markerBytes.Length)
            $materialStream.Flush()
            $materialStream.Dispose()
            $materialStream = $null
        } catch {
            if ($null -ne $materialStream) { $materialStream.Dispose() }
            Set-LifecycleState $statePath 'INCOMPLETE_STORAGE_FAILURE' $RunId $resourceId $sandbox $evidence $manifestSha $_.Exception.Message | Out-Null
            Fail-Guard 'INCOMPLETE_STORAGE_FAILURE' 'test-owned material write failed; retry is disabled'
        }
    }

    if ($ExecutionMode -eq 'DryRun') {
        Write-Output 'F5_ONLY_ROUTE_SELECTED'
        Write-Output 'EXISTING_SANDBOX_ONLY=YES'
        Write-Output 'NEW_RUNTIME_COPY=0'
        Write-Output 'MAX_CONCURRENT_TRIALS=1'
        Write-Output 'MAX_AUTOMATIC_RETRIES=0'
        Write-Output 'MAX_RUNTIME_COPY_BYTES=0'
        Write-Output 'MAX_RUNTIME_COPY_FILES=0'
        Write-Output 'LOCK_ACQUIRED=YES'
        Write-Output 'LOCK_HOLDER_IN_KILLED_JOB_OBJECT=NO'
        Write-Output 'CAPACITY_GATE=PASS'
        Write-Output "CAPACITY_FREE_NOW_BYTES=$($capacity.free_now_bytes)"
        Write-Output "CAPACITY_VOLUME_ROOT=$($capacity.volume_root)"
        Write-Output "CAPACITY_MEASUREMENT_METHOD=$($capacity.measurement_method)"
        Write-Output 'INPUT_MANIFEST=PASS'
        Write-Output 'POINT_OF_USE_REVALIDATION=PASS'
        Write-Output 'NO_F0_F4_SETUP=YES'
        Write-Output 'DRY_RUN_GUARD_RESULT=PASS'
        Write-Output "SANDBOX_RESOURCE_ID=$resourceId"
        Write-Output "LIFECYCLE_STATE_ROOT=$stateRoot"
        if ($HoldLockSeconds -gt 0) { Start-Sleep -Seconds $HoldLockSeconds }
        Set-LifecycleState $statePath 'COMPLETED' $RunId $resourceId $sandbox $evidence $manifestSha | Out-Null
        Write-Output 'F5_EXECUTED=NO'
        exit 0
    }

    if ($ExecutionMode -ne 'RealF5') { Fail-Guard 'EXECUTION_MODE_INVALID' $ExecutionMode }
    if ($ExecutionContextPath -and -not (Test-AbsolutePath $ExecutionContextPath)) {
        Fail-Guard 'EXECUTION_CONTEXT_INVALID' 'context path must be absolute'
    }
    $probePath = Join-Path $PSScriptRoot 'a3_probe_windows.ps1'
    if (-not (Test-Path -LiteralPath $probePath -PathType Leaf)) { Fail-Guard 'EXECUTION_CONTEXT_INVALID' 'probe is missing' }
    $contextPath = if ($ExecutionContextPath) { Get-CanonicalPath $ExecutionContextPath } else { Join-Path $evidence 'F5_EXECUTION_CONTEXT.json' }
    $evidencePrefix = $evidence.TrimEnd('\') + '\'
    if (-not $contextPath.StartsWith($evidencePrefix, [StringComparison]::OrdinalIgnoreCase)) {
        Fail-Guard 'EXECUTION_CONTEXT_INVALID' 'context must be under evidence root'
    }
    try {
        $context = New-F5ExecutionContext `
            -ContextPath $contextPath `
            -RunId $RunId `
            -ResourceId $resourceId `
            -SandboxPath $sandbox `
            -ManifestPath $InputManifestPath `
            -ManifestSha $manifestSha `
            -GuardPath $PSCommandPath `
            -ProbePath $probePath `
            -EvidenceRoot $evidence `
            -LifecycleStatePath $statePath `
            -LockPath $lockPath
        Write-F5ExecutionContext $contextPath $context
        $probeArgs = @(
            '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
            '-File', $probePath,
            '-Mode', 'F5Only',
            '-ExecutionMode', 'RealF5',
            '-ExecutionContextPath', $contextPath,
            '-PreexecutionContractPath', (Get-CanonicalPath $PreexecutionContractPath),
            '-ExistingSandboxPath', $sandbox,
            '-RunId', $RunId,
            '-InputManifestPath', $InputManifestPath,
            '-EvidenceRoot', $evidence
        )
        if ($TestStateRoot) { $probeArgs += @('-TestStateRoot', $TestStateRoot) }
        if ($TestDispatchBoundary) { $probeArgs += '-TestDispatchBoundary' }
        if ($DispatchHoldSeconds -gt 0) { $probeArgs += @('-DispatchHoldSeconds', [string]$DispatchHoldSeconds) }
        $probeOutput = @(& powershell.exe @probeArgs 2>&1)
        $probeExit = $LASTEXITCODE
        $probeOutput | ForEach-Object { Write-Output $_ }
        if ($probeExit -ne 0) {
            Set-LifecycleState $statePath 'FAILED' $RunId $resourceId $sandbox $evidence $manifestSha 'guarded F5 probe failed' | Out-Null
            Fail-Guard 'F5_PROBE_FAILED' "exit=$probeExit"
        }
        Set-LifecycleState $statePath 'COMPLETED' $RunId $resourceId $sandbox $evidence $manifestSha | Out-Null
        Write-Output 'F5_ONLY_ROUTE_SELECTED'
        Write-Output 'EXISTING_SANDBOX_ONLY=YES'
        Write-Output 'NEW_RUNTIME_COPY=0'
        Write-Output 'MAX_CONCURRENT_TRIALS=1'
        Write-Output 'MAX_AUTOMATIC_RETRIES=0'
        Write-Output 'MAX_RUNTIME_COPY_BYTES=0'
        Write-Output 'MAX_RUNTIME_COPY_FILES=0'
        Write-Output 'LOCK_ACQUIRED=YES'
        Write-Output 'CAPACITY_GATE=PASS'
        Write-Output 'INPUT_MANIFEST=PASS'
        Write-Output 'POINT_OF_USE_REVALIDATION=PASS'
        Write-Output 'NO_F0_F4_SETUP=YES'
        Write-Output 'GUARDED_EXECUTION_CONTEXT=PASS'
        Write-Output "EXECUTION_CONTEXT_PATH=$contextPath"
        Write-Output "SANDBOX_RESOURCE_ID=$resourceId"
        Write-Output "LIFECYCLE_STATE_ROOT=$stateRoot"
        Write-Output 'REAL_F5_DISPATCH=PASS'
        Write-Output 'F5_EXECUTED=NO'
        exit 0
    } catch {
        if ($_.Exception.Message -notmatch '^GUARD_FAILURE:') {
            try { Set-LifecycleState $statePath 'FAILED' $RunId $resourceId $sandbox $evidence $manifestSha $_.Exception.Message | Out-Null } catch { }
        }
        throw
    }

}
catch {
    $message = $_.Exception.Message
    if ($message -match '^GUARD_FAILURE:(?<code>[^ :]+)(?: : (?<detail>.*))?$') {
        if ($Matches.detail) { Write-Output "$($Matches.code) : $($Matches.detail)" }
        else { Write-Output $Matches.code }
    }
    else { Write-Output $message }
    exit 1
}
finally {
    if ($null -ne $lock) { $lock.Dispose() }
    if ($null -ne $globalLock) { $globalLock.Dispose() }
}
