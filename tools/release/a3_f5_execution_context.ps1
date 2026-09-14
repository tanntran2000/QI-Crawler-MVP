# Shared, bounded identity checks for the guarded F5 execution seam.
# This file is dot-sourced by the guard and probe; it has no top-level effects.

function Get-F5ContextCanonicalPath([string]$Path) {
    if (-not $Path -or -not [IO.Path]::IsPathRooted($Path)) {
        throw 'EXECUTION_CONTEXT_INVALID:PATH_NOT_ABSOLUTE'
    }
    try {
        if (Test-Path -LiteralPath $Path) {
            return (Resolve-Path -LiteralPath $Path -ErrorAction Stop).Path.TrimEnd('\')
        }
        return ([IO.Path]::GetFullPath($Path)).TrimEnd('\')
    } catch {
        throw "EXECUTION_CONTEXT_INVALID:PATH_UNRESOLVED:$($_.Exception.Message)"
    }
}

function Get-F5ContextSha256([string]$Path) {
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw "EXECUTION_CONTEXT_INVALID:FILE_MISSING:$Path"
    }
    $sha = [Security.Cryptography.SHA256]::Create()
    $stream = [IO.File]::OpenRead($Path)
    try {
        return ([BitConverter]::ToString($sha.ComputeHash($stream))).Replace('-', '').ToLowerInvariant()
    } finally {
        $stream.Dispose()
        $sha.Dispose()
    }
}

function Get-F5ContextResourceId([string]$SandboxPath) {
    $canonical = (Get-F5ContextCanonicalPath $SandboxPath).ToLowerInvariant().Replace('\', '/')
    $sha = [Security.Cryptography.SHA256]::Create()
    try {
        $bytes = [Text.Encoding]::UTF8.GetBytes($canonical)
        return ([BitConverter]::ToString($sha.ComputeHash($bytes))).Replace('-', '').ToLowerInvariant()
    } finally {
        $sha.Dispose()
    }
}

function Read-F5ExecutionContext([string]$Path) {
    if (-not $Path -or -not (Test-Path -LiteralPath $Path -PathType Leaf)) {
        throw 'EXECUTION_CONTEXT_REQUIRED'
    }
    try {
        return (Get-Content -Raw -LiteralPath $Path | ConvertFrom-Json)
    } catch {
        throw "EXECUTION_CONTEXT_INVALID:$($_.Exception.Message)"
    }
}

function Write-F5ExecutionContext([string]$Path, $Context) {
    $parent = Split-Path -Parent $Path
    New-Item -ItemType Directory -Force -Path $parent | Out-Null
    $text = (($Context | ConvertTo-Json -Depth 8) + "`n")
    $encoding = New-Object Text.UTF8Encoding($false)
    $temporary = "$Path.$PID.$([Guid]::NewGuid().ToString('N')).tmp"
    $stream = $null
    try {
        $bytes = $encoding.GetBytes($text)
        $stream = [IO.File]::Open($temporary, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
        $stream.Write($bytes, 0, $bytes.Length)
        try { $stream.Flush($true) } catch { $stream.Flush() }
        $stream.Dispose()
        $stream = $null
        if (Test-Path -LiteralPath $Path -PathType Leaf) {
            [IO.File]::Replace($temporary, $Path, $null, $true)
        } elseif (Test-Path -LiteralPath $Path) {
            throw 'EXECUTION_CONTEXT_INVALID:CONTEXT_PATH_NOT_FILE'
        } else {
            [IO.File]::Move($temporary, $Path)
        }
    } finally {
        if ($null -ne $stream) { $stream.Dispose() }
        if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary -Force -ErrorAction SilentlyContinue }
    }
}

function New-F5ExecutionContext(
    [string]$ContextPath,
    [string]$RunId,
    [string]$ResourceId,
    [string]$SandboxPath,
    [string]$ManifestPath,
    [string]$ManifestSha,
    [string]$GuardPath,
    [string]$ProbePath,
    [string]$EvidenceRoot,
    [string]$LifecycleStatePath,
    [string]$LockPath
) {
    return [ordered]@{
        schema = 'AO-04-C3-F5-EXECUTION-CONTEXT-V1'
        execution_mode = 'RealF5'
        context_path = (Get-F5ContextCanonicalPath $ContextPath)
        run_id = $RunId
        sandbox_resource_id = $ResourceId
        canonical_sandbox_path = (Get-F5ContextCanonicalPath $SandboxPath)
        input_manifest_path = (Get-F5ContextCanonicalPath $ManifestPath)
        input_manifest_sha256 = $ManifestSha
        guard_path = (Get-F5ContextCanonicalPath $GuardPath)
        guard_identity_sha256 = (Get-F5ContextSha256 $GuardPath)
        probe_path = (Get-F5ContextCanonicalPath $ProbePath)
        probe_identity_sha256 = (Get-F5ContextSha256 $ProbePath)
        evidence_root = (Get-F5ContextCanonicalPath $EvidenceRoot)
        lifecycle_state_path = (Get-F5ContextCanonicalPath $LifecycleStatePath)
        lock_path = (Get-F5ContextCanonicalPath $LockPath)
        lifecycle_state = 'RUNNING'
        created_utc = (Get-Date).ToUniversalTime().ToString('o')
    }
}

function Assert-F5ExecutionContext(
    $Context,
    [string]$ContextPath,
    [string]$RunId,
    [string]$SandboxPath,
    [string]$ManifestPath,
    [string]$EvidenceRoot,
    [string]$LifecycleStatePath,
    [string]$LockPath,
    [string]$GuardPath,
    [string]$ProbePath
) {
    $required = @(
        'schema', 'execution_mode', 'context_path', 'run_id',
        'sandbox_resource_id', 'canonical_sandbox_path',
        'input_manifest_path', 'input_manifest_sha256',
        'guard_path', 'guard_identity_sha256',
        'probe_path', 'probe_identity_sha256',
        'evidence_root', 'lifecycle_state_path', 'lock_path',
        'lifecycle_state', 'created_utc'
    )
    foreach ($field in $required) {
        if ($null -eq $Context.$field -or [string]::IsNullOrWhiteSpace([string]$Context.$field)) {
            throw "EXECUTION_CONTEXT_INVALID:MISSING_$($field.ToUpperInvariant())"
        }
    }
    if ([string]$Context.schema -ne 'AO-04-C3-F5-EXECUTION-CONTEXT-V1') { throw 'EXECUTION_CONTEXT_INVALID:SCHEMA' }
    if ([string]$Context.execution_mode -ne 'RealF5') { throw 'EXECUTION_CONTEXT_INVALID:MODE' }
    if ([string]$Context.lifecycle_state -ne 'RUNNING') { throw 'EXECUTION_CONTEXT_INVALID:LIFECYCLE_STATE' }

    $expectedContext = Get-F5ContextCanonicalPath $ContextPath
    $expectedSandbox = Get-F5ContextCanonicalPath $SandboxPath
    $expectedManifest = Get-F5ContextCanonicalPath $ManifestPath
    $expectedEvidence = Get-F5ContextCanonicalPath $EvidenceRoot
    $expectedState = Get-F5ContextCanonicalPath $LifecycleStatePath
    $expectedLock = Get-F5ContextCanonicalPath $LockPath
    $expectedGuard = Get-F5ContextCanonicalPath $GuardPath
    $expectedProbe = Get-F5ContextCanonicalPath $ProbePath

    $pathChecks = @(
        @('context_path', [string]$Context.context_path, $expectedContext),
        @('canonical_sandbox_path', [string]$Context.canonical_sandbox_path, $expectedSandbox),
        @('input_manifest_path', [string]$Context.input_manifest_path, $expectedManifest),
        @('evidence_root', [string]$Context.evidence_root, $expectedEvidence),
        @('lifecycle_state_path', [string]$Context.lifecycle_state_path, $expectedState),
        @('guard_path', [string]$Context.guard_path, $expectedGuard),
        @('probe_path', [string]$Context.probe_path, $expectedProbe),
        @('lock_path', [string]$Context.lock_path, $expectedLock)
    )
    foreach ($check in $pathChecks) {
        if (-not [string]::Equals($check[1], $check[2], [StringComparison]::OrdinalIgnoreCase)) {
            throw "EXECUTION_CONTEXT_INVALID:$($check[0])"
        }
    }
    if ([string]$Context.run_id -ne $RunId) { throw 'EXECUTION_CONTEXT_INVALID:RUN_ID' }
    $resourceId = Get-F5ContextResourceId $expectedSandbox
    if ([string]$Context.sandbox_resource_id -ne $resourceId) { throw 'EXECUTION_CONTEXT_INVALID:SANDBOX_RESOURCE_ID' }
    if ([string]$Context.input_manifest_sha256 -ne (Get-F5ContextSha256 $expectedManifest)) { throw 'EXECUTION_CONTEXT_INVALID:MANIFEST_IDENTITY' }
    if ([string]$Context.guard_identity_sha256 -ne (Get-F5ContextSha256 $expectedGuard)) { throw 'EXECUTION_CONTEXT_INVALID:GUARD_IDENTITY' }
    if ([string]$Context.probe_identity_sha256 -ne (Get-F5ContextSha256 $expectedProbe)) { throw 'EXECUTION_CONTEXT_INVALID:PROBE_IDENTITY' }

    if (-not (Test-Path -LiteralPath $expectedState -PathType Leaf)) { throw 'EXECUTION_CONTEXT_INVALID:LIFECYCLE_STATE_MISSING' }
    try { $state = Get-Content -Raw -LiteralPath $expectedState | ConvertFrom-Json }
    catch { throw 'EXECUTION_CONTEXT_INVALID:LIFECYCLE_STATE_JSON' }
    if ([string]$state.execution_state -ne 'RUNNING') { throw 'EXECUTION_CONTEXT_INVALID:LIFECYCLE_STATE' }
    if ([string]$state.last_run_id -ne $RunId -or
        [string]$state.sandbox_resource_id -ne $resourceId -or
        -not [string]::Equals([string]$state.canonical_sandbox_path, $expectedSandbox, [StringComparison]::OrdinalIgnoreCase) -or
        [string]$state.input_manifest_sha256 -ne [string]$Context.input_manifest_sha256 -or
        -not [string]::Equals([string]$state.last_evidence_root, $expectedEvidence, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'EXECUTION_CONTEXT_INVALID:LIFECYCLE_BINDING'
    }
    return $true
}
