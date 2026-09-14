# Shared, read-only phase observation for the A3 sandbox trial. A contract
# declares an expected checkpoint; the sandbox and transaction decide reality.
function Get-A3PhaseFileSha([string]$Path) {
    $sha = [Security.Cryptography.SHA256]::Create()
    $stream = [IO.File]::OpenRead($Path)
    try { return ([BitConverter]::ToString($sha.ComputeHash($stream))).Replace('-', '').ToLowerInvariant() }
    finally { $stream.Dispose(); $sha.Dispose() }
}

function Test-A3PhaseModel($Model) {
    if (-not $Model -or [string]$Model.schema -ne 'A3-F5-PHASE-MODEL-V1') {
        throw 'A3_PHASE_INVALID: missing or unsupported phase model'
    }
    if ([string]$Model.expected_phase -notin @('PRETRIAL','CUTOVER_STUB_STAGED','POST_BARRIER_MAINTENANCE')) {
        throw 'A3_PHASE_INVALID: expected phase is unknown'
    }
    foreach ($name in @('pretrial_exe_sha256','maintenance_stub_sha256')) {
        if ([string]$Model.$name -cnotmatch '^[0-9a-f]{64}$') {
            throw "A3_PHASE_INVALID: $name"
        }
    }
    if ([string]$Model.pretrial_exe_sha256 -ceq [string]$Model.maintenance_stub_sha256) {
        throw 'A3_PHASE_INVALID: pretrial and maintenance identities are equal'
    }
}

function Get-A3ObservedPhase([string]$Sandbox, $Model, [string]$LifecycleStatePath = '') {
    Test-A3PhaseModel $Model
    if (-not [IO.Path]::IsPathRooted($Sandbox) -or -not (Test-Path -LiteralPath $Sandbox -PathType Container)) {
        throw 'A3_PHASE_INVALID: sandbox path'
    }
    $canonical = Join-Path $Sandbox 'install\QI-Crawler\QI-Crawler.exe'
    $companion = Join-Path $Sandbox 'install\QI-Crawler\maintenance_stub_state.json'
    $journal = Join-Path $Sandbox 'transaction\cutover.json'
    $transaction = Join-Path $Sandbox 'transaction'
    if (-not (Test-Path -LiteralPath $transaction -PathType Container) -or
        -not (Test-Path -LiteralPath $canonical -PathType Leaf)) {
        return [pscustomobject]@{ phase = 'UNKNOWN'; overlay = 'NONE'; journal_phase = 'UNKNOWN' }
    }
    foreach ($path in @($canonical, $transaction, $journal, $companion)) {
        if (Test-Path -LiteralPath $path) {
            $item = Get-Item -LiteralPath $path -Force
            if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
                throw 'A3_PHASE_INVALID: reparse point'
            }
        }
    }
    $exeSha = Get-A3PhaseFileSha $canonical
    $journalPhase = ''
    if (Test-Path -LiteralPath $journal -PathType Leaf) {
        try { $journalPhase = [string]((Get-Content -Raw -LiteralPath $journal | ConvertFrom-Json).phase) }
        catch { throw 'A3_PHASE_INVALID: malformed transaction' }
        if (-not $journalPhase) { throw 'A3_PHASE_INVALID: missing transaction phase' }
    }
    $companionPresent = Test-Path -LiteralPath $companion
    $legacy = Join-Path $Sandbox 'transaction\legacy\QI-Crawler.exe'
    $markers = Join-Path $Sandbox 'transaction\markers'
    $phase = 'UNKNOWN'
    if ($exeSha -ceq [string]$Model.pretrial_exe_sha256 -and
        -not $companionPresent -and -not $journalPhase -and
        -not (Test-Path -LiteralPath $legacy) -and -not (Test-Path -LiteralPath $markers)) {
        $phase = 'PRETRIAL'
    } elseif ($exeSha -ceq [string]$Model.maintenance_stub_sha256 -and
        $journalPhase -in @('STUB_VERIFIED','BARRIER_CANDIDATE')) {
        $phase = 'CUTOVER_STUB_STAGED'
    } elseif ($exeSha -ceq [string]$Model.maintenance_stub_sha256 -and
        $journalPhase -in @('BARRIER_CONFIRMED','COMPLETE')) {
        $phase = 'POST_BARRIER_MAINTENANCE'
    }
    $overlay = 'NONE'
    if ($LifecycleStatePath -and (Test-Path -LiteralPath $LifecycleStatePath -PathType Leaf)) {
        try { $state = Get-Content -Raw -LiteralPath $LifecycleStatePath | ConvertFrom-Json }
        catch { throw 'A3_PHASE_INVALID: malformed lifecycle state' }
        if ([string]$state.execution_state -eq 'FAILED') { $overlay = 'FAILED' }
    }
    return [pscustomobject]@{ phase = $phase; overlay = $overlay; journal_phase = $journalPhase; executable_sha256 = $exeSha }
}

function Assert-A3Phase([string]$Sandbox, $Model, [string]$ExpectedPhase, [string]$LifecycleStatePath = '') {
    Test-A3PhaseModel $Model
    if ($ExpectedPhase -notin @('PRETRIAL','CUTOVER_STUB_STAGED','POST_BARRIER_MAINTENANCE')) {
        throw 'A3_PHASE_INVALID: requested phase is unknown'
    }
    $observed = Get-A3ObservedPhase -Sandbox $Sandbox -Model $Model -LifecycleStatePath $LifecycleStatePath
    if ($observed.phase -cne $ExpectedPhase) {
        throw "A3_PHASE_MISMATCH: expected=$ExpectedPhase observed=$($observed.phase) journal=$($observed.journal_phase)"
    }
    return $observed
}
