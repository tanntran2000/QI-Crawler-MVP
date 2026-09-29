[CmdletBinding(SupportsShouldProcess)]
param(
    [string]$Root = (Join-Path $PSScriptRoot "..")
)

$ErrorActionPreference = "Stop"
$repositoryRoot = (Resolve-Path -LiteralPath $Root).Path
$normalizedRoot = [IO.Path]::GetFullPath($repositoryRoot).TrimEnd('\')
if ([string]::Equals($normalizedRoot, 'D:\QI-Crawler', [StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing cleanup for the operational installation root"
}
$gitTopLevel = (& git -C $repositoryRoot rev-parse --show-toplevel 2>$null)
if ($LASTEXITCODE -ne 0 -or [string]::IsNullOrWhiteSpace([string]$gitTopLevel)) {
    throw "Cleanup root must be a Git repository top-level"
}
$resolvedTopLevel = [IO.Path]::GetFullPath(([string]$gitTopLevel).Trim()).TrimEnd('\')
if (-not [string]::Equals($resolvedTopLevel, $normalizedRoot, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Cleanup root must be the exact Git top-level"
}
$allowedTargets = @(
    ".pytest_cache", ".ruff_cache", "__pycache__", "build", "dist", ".tmp"
)

function Test-TrackedPath([string]$RelativePath) {
    if (-not (Test-Path -LiteralPath (Join-Path $repositoryRoot ".git"))) { return $false }
    & git -C $repositoryRoot ls-files --error-unmatch -- $RelativePath 2>$null | Out-Null
    return $LASTEXITCODE -eq 0
}

foreach ($relativePath in $allowedTargets) {
    $candidate = Join-Path $repositoryRoot $relativePath
    if (-not (Test-Path -LiteralPath $candidate)) { continue }
    if (-not (Test-Path -LiteralPath $candidate -PathType Container)) {
        Write-Warning "SKIP unsupported cleanup target: $candidate"
        continue
    }
    $resolved = (Resolve-Path -LiteralPath $candidate).Path
    $rootPrefix = "$repositoryRoot$([IO.Path]::DirectorySeparatorChar)"
    if (-not $resolved.StartsWith($rootPrefix, [StringComparison]::OrdinalIgnoreCase)) {
        Write-Warning "SKIP target outside repository: $candidate"
        continue
    }
    if (Test-TrackedPath $relativePath) {
        Write-Warning "SKIP tracked cleanup target: $candidate"
        continue
    }
    if ($PSCmdlet.ShouldProcess($resolved, "Remove approved generated directory")) {
        try {
            Remove-Item -LiteralPath $resolved -Recurse -Force -ErrorAction Stop
        } catch {
            Write-Warning "SKIP access denied or cleanup failure: $resolved"
        }
    }
}
