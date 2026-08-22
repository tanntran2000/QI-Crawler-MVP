$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
$generatedTargets = @("build", "dist\QI-Crawler")

function Test-TrackedPath([string]$RelativePath) {
    & git -C $projectRoot ls-files --error-unmatch -- $RelativePath 2>$null | Out-Null
    return $LASTEXITCODE -eq 0
}

function Remove-GeneratedTarget([string]$RelativePath) {
    $candidate = Join-Path $projectRoot $RelativePath
    if (-not (Test-Path -LiteralPath $candidate)) { return }
    if (Test-TrackedPath $RelativePath) {
        throw "Khong the xoa duong dan tracked: $RelativePath"
    }
    $resolved = (Resolve-Path -LiteralPath $candidate).Path
    $prefix = "$projectRoot$([IO.Path]::DirectorySeparatorChar)"
    if (-not $resolved.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        throw "Duong dan build nam ngoai project: $resolved"
    }
    Remove-Item -LiteralPath $resolved -Recurse -Force
}

foreach ($target in $generatedTargets) {
    Remove-GeneratedTarget $target
}

$browserRoot = if ($env:QI_CRAWLER_BROWSER_DIR) {
    $env:QI_CRAWLER_BROWSER_DIR
} else {
    Join-Path $env:LOCALAPPDATA "ms-playwright"
}

if (-not (Test-Path -LiteralPath $python)) {
    throw "Khong tim thay .venv. Hay tao moi truong build truoc."
}

if (-not (Test-Path -LiteralPath $browserRoot)) {
    throw "Khong tim thay Chromium. Chay: .\.venv\Scripts\python.exe -m playwright install chromium"
}

Push-Location $projectRoot
try {
    & $python -m PyInstaller --noconfirm --clean "packaging\QI-Crawler.spec"
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller build that bai voi exit code $LASTEXITCODE"
    }
    $exe = Join-Path $projectRoot "dist\QI-Crawler\QI-Crawler.exe"
    if (-not (Test-Path -LiteralPath $exe)) {
        throw "Build xong nhung khong tim thay QI-Crawler.exe"
    }
    Write-Host "Build thanh cong: $exe" -ForegroundColor Green
    Write-Host "Phan phoi TOAN BO thu muc dist\QI-Crawler, khong chi copy file EXE."
} finally {
    Pop-Location
}
