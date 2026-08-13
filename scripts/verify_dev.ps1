[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
python -m pytest
ruff check .
git diff --check
$changes = @(& git diff --name-status; & git diff --cached --name-status)
$protected = '^(src/|tests/|alembic/|packaging/|scripts/)'
$deleted = $changes | Where-Object { $_ -match '^D\s+' -and $_ -match $protected }
git diff --name-status
if ($deleted) {
    Write-Error "FAIL: unexpected protected source deletion detected.`n$($deleted -join "`n")"
    exit 1
}
