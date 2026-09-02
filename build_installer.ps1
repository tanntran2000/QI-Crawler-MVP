[CmdletBinding()]
param(
    [switch]$Publish
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$standaloneBuild = Join-Path $projectRoot "build_windows.ps1"
$installerScript = Join-Path $projectRoot "packaging\QI-Crawler.iss"
$publishScript = Join-Path $projectRoot "scripts\publish_windows_release.ps1"
$candidateRoot = Join-Path $projectRoot "release_staging\candidate"
$isccCandidates = @(
    $env:QI_CRAWLER_ISCC,
    (Get-Command ISCC.exe -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Source -ErrorAction SilentlyContinue),
    "${env:ProgramFiles(x86)}\Inno Setup 7\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 7\ISCC.exe",
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
    "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
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

$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path -LiteralPath $python)) {
    throw "Khong tim thay .venv. Hay tao moi truong build truoc."
}

function Get-CanonicalVersion {
    Push-Location $projectRoot
    try {
        $value = (& $python -c "import sys; sys.path.insert(0, 'src'); from qi_crawler import __version__; print(__version__)").Trim()
    } finally {
        Pop-Location
    }
    if ($LASTEXITCODE -ne 0 -or $value -notmatch '^\d+\.\d+\.\d+$') {
        throw "Khong doc duoc canonical version tu qi_crawler.__version__"
    }
    return $value
}

function Get-AlembicHead {
    Push-Location $projectRoot
    try {
        $output = @(& $python -m alembic heads 2>&1)
    } finally {
        Pop-Location
    }
    if ($LASTEXITCODE -ne 0) {
        throw "Khong doc duoc Alembic head"
    }
    $heads = @($output | Where-Object { $_ -match '\(head\)' } | ForEach-Object { ($_ -split '\s+')[0] })
    if ($heads.Count -ne 1 -or -not $heads[0]) {
        throw "Alembic phai co dung mot head; phat hien: $($heads -join ', ')"
    }
    return $heads[0]
}

function Get-RuntimeSchemaRevision {
    Push-Location $projectRoot
    try {
        $value = (& $python -c "import sys; sys.path.insert(0, 'src'); from qi_crawler.db import CURRENT_SCHEMA_REVISION; print(CURRENT_SCHEMA_REVISION)").Trim()
        $exitCode = $LASTEXITCODE
    } finally {
        Pop-Location
    }
    if ($exitCode -ne 0 -or [string]::IsNullOrWhiteSpace($value)) {
        throw "Khong doc duoc runtime schema revision tu qi_crawler.db.CURRENT_SCHEMA_REVISION"
    }
    return $value
}

function Get-Sha256([string]$PathValue) {
    return (Get-FileHash -LiteralPath $PathValue -Algorithm SHA256).Hash.ToUpperInvariant()
}

$version = Get-CanonicalVersion
$runtimeSchema = Get-RuntimeSchemaRevision
$alembicHead = Get-AlembicHead
if ($runtimeSchema -ne $alembicHead) {
    throw "Runtime schema ($runtimeSchema) khong khop Alembic single head ($alembicHead)"
}
$installerOutput = Join-Path $projectRoot "dist\installer\QI-Crawler-Setup-v$version.exe"

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
    & $iscc "/DAppVersion=$version" $installerScript
    if ($LASTEXITCODE -ne 0) {
        throw "Inno Setup build that bai voi exit code $LASTEXITCODE"
    }
} finally {
    Pop-Location
}

if (-not (Test-Path -LiteralPath $installerOutput)) {
    throw "Build xong nhung khong tim thay QI-Crawler-Setup-v$version.exe"
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

if (Test-Path -LiteralPath $candidateRoot) {
    Remove-Item -LiteralPath $candidateRoot -Recurse -Force
}
New-Item -ItemType Directory -Path (Join-Path $candidateRoot "QI-Crawler") -Force | Out-Null
Get-ChildItem -LiteralPath (Join-Path $projectRoot "dist\QI-Crawler") -Force |
    Copy-Item -Destination (Join-Path $candidateRoot "QI-Crawler") -Recurse -Force
Copy-Item -LiteralPath $installerOutput -Destination $candidateRoot -Force

$portableExe = Join-Path $candidateRoot "QI-Crawler\QI-Crawler.exe"
$candidateInstaller = Join-Path $candidateRoot (Split-Path -Leaf $installerOutput)
$commit = (& git -C $projectRoot rev-parse HEAD).Trim()
$branch = (& git -C $projectRoot branch --show-current).Trim()
$timestamp = (Get-Date).ToUniversalTime().ToString("o")
$portableHash = Get-Sha256 $portableExe
$installerHash = Get-Sha256 $candidateInstaller
$buildInfo = @(
    "product=QI-Crawler",
    "version=$version",
    "commit_sha=$commit",
    "source_branch=$branch",
    "build_timestamp_utc=$timestamp",
    "alembic_head=$alembicHead",
    "portable_exe_sha256=$portableHash",
    "installer_sha256=$installerHash"
)
$buildInfo | Set-Content -LiteralPath (Join-Path $candidateRoot "BUILD_INFO.txt") -Encoding UTF8
$manifest = [ordered]@{
    product = "QI-Crawler"
    version = $version
    commit_sha = $commit
    build_timestamp_utc = $timestamp
    alembic_head = $alembicHead
    release_channel = "team_bid_verified"
    portable_exe_sha256 = $portableHash
    installer_sha256 = $installerHash
}
$manifest | ConvertTo-Json -Depth 3 | Set-Content -LiteralPath (Join-Path $candidateRoot "release_manifest.json") -Encoding UTF8

if ($Publish) {
    try {
        & $publishScript -Publish -RepoRoot $projectRoot -CandidateRoot $candidateRoot -Version $version -ExpectedAlembicHead $alembicHead
        if ($LASTEXITCODE -ne 0) {
            throw "Publish that bai voi exit code $LASTEXITCODE"
        }
    } finally {
        if (Test-Path -LiteralPath $candidateRoot) {
            Remove-Item -LiteralPath $candidateRoot -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
} else {
    Write-Host "Build candidate hoan tat; khong publish vao Crawler tool. Candidate: $candidateRoot" -ForegroundColor Yellow
}

Write-Host "Installer thanh cong: $installerOutput" -ForegroundColor Green
Write-Host "Release manifest: $(Join-Path $candidateRoot 'release_manifest.json')" -ForegroundColor Green
Write-Host "Installer chi cai app; du lieu Bid luon nam o %LOCALAPPDATA%\QI-Crawler." -ForegroundColor Green
