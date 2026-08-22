[CmdletBinding()]
param(
    [switch]$Publish
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$standaloneBuild = Join-Path $projectRoot "build_windows.ps1"
$installerScript = Join-Path $projectRoot "packaging\QI-Crawler.iss"
$installerOutput = Join-Path $projectRoot "dist\installer\QI-Crawler-Setup-v0.7.1.exe"
$publishScript = Join-Path $projectRoot "scripts\publish_windows_release.ps1"
$candidateRoot = Join-Path $projectRoot "release_staging\candidate"
$isccCandidates = @(
    $env:QI_CRAWLER_ISCC,
    (Get-Command ISCC.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue),
    "${env:ProgramFiles(x86)}\Inno Setup 7\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 7\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }

if (-not (Test-Path -LiteralPath $installerScript)) {
    throw "Khong tim thay packaging\QI-Crawler.iss"
}
if (-not (Test-Path -LiteralPath $publishScript)) {
    throw "Khong tim thay scripts\publish_windows_release.ps1"
}
if (-not $isccCandidates) {
    throw "Khong tim thay Inno Setup 6/7. Cai Inno Setup, sau do chay lai build_installer.ps1."
}
$iscc = @($isccCandidates)[0]

& $standaloneBuild
if ($LASTEXITCODE -ne 0) {
    throw "Build QI-Crawler onedir that bai voi exit code $LASTEXITCODE"
}

$bundle = Join-Path $projectRoot "dist\QI-Crawler\QI-Crawler.exe"
if (-not (Test-Path -LiteralPath $bundle)) {
    throw "Khong tim thay QI-Crawler.exe trong dist\QI-Crawler"
}

Push-Location $projectRoot
try {
    & $iscc $installerScript
    if ($LASTEXITCODE -ne 0) {
        throw "Inno Setup build that bai voi exit code $LASTEXITCODE"
    }
} finally {
    Pop-Location
}

if (-not (Test-Path -LiteralPath $installerOutput)) {
    throw "Build xong nhung khong tim thay QI-Crawler-Setup-v0.7.1.exe"
}

$smokeData = Join-Path $env:TEMP ("qi-crawler-installer-smoke-" + [guid]::NewGuid().ToString("N"))
$previousDataRoot = $env:QI_CRAWLER_DATA_DIR
try {
    $env:QI_CRAWLER_DATA_DIR = $smokeData
    & $bundle --smoke-test-documents
    if ($LASTEXITCODE -ne 0) {
        throw "Standalone smoke test that bai voi exit code $LASTEXITCODE"
    }
} finally {
    if ($previousDataRoot) { $env:QI_CRAWLER_DATA_DIR = $previousDataRoot }
    else { Remove-Item Env:QI_CRAWLER_DATA_DIR -ErrorAction SilentlyContinue }
    if (Test-Path -LiteralPath $smokeData) {
        Remove-Item -LiteralPath $smokeData -Recurse -Force -ErrorAction SilentlyContinue
    }
}

if ($Publish) {
    if (Test-Path -LiteralPath $candidateRoot) {
        Remove-Item -LiteralPath $candidateRoot -Recurse -Force
    }
    New-Item -ItemType Directory -Path (Join-Path $candidateRoot "QI-Crawler") -Force | Out-Null
    Get-ChildItem -LiteralPath (Join-Path $projectRoot "dist\QI-Crawler") -Force |
        Copy-Item -Destination (Join-Path $candidateRoot "QI-Crawler") -Recurse -Force
    Copy-Item -LiteralPath $installerOutput -Destination $candidateRoot -Force
    try {
        & $publishScript -Publish -RepoRoot $projectRoot -CandidateRoot $candidateRoot -Version "0.7.1"
        if ($LASTEXITCODE -ne 0) {
            throw "Publish that bai voi exit code $LASTEXITCODE"
        }
    } finally {
        if (Test-Path -LiteralPath $candidateRoot) {
            Remove-Item -LiteralPath $candidateRoot -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
} else {
    Write-Host "Build dev hoan tat; khong publish vao Crawler tool. Dung -Publish sau khi merge vao main." -ForegroundColor Yellow
}

Write-Host "Installer thanh cong: $installerOutput" -ForegroundColor Green
Write-Host "Installer chi cai app; du lieu Bid luon nam o %LOCALAPPDATA%\QI-Crawler." -ForegroundColor Green
