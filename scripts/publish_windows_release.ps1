[CmdletBinding()]
param(
    [switch]$Publish,
    [string]$RepoRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$PublishRoot,
    [string]$CandidateRoot,
    [Parameter(Mandatory = $true)]
    [string]$Version
)

$ErrorActionPreference = "Stop"

function Resolve-ExistingPath([string]$PathValue, [string]$Label) {
    if (-not (Test-Path -LiteralPath $PathValue)) {
        throw "$Label khong ton tai: $PathValue"
    }
    return (Resolve-Path -LiteralPath $PathValue).Path
}

function Get-Sha256([string]$PathValue) {
    return (Get-FileHash -LiteralPath $PathValue -Algorithm SHA256).Hash.ToUpperInvariant()
}

function Assert-RepositoryReady([string]$Root) {
    $branch = (& git -C $Root branch --show-current).Trim()
    if ($LASTEXITCODE -ne 0 -or $branch -ne "main") {
        throw "Publish chi duoc phep tren nhanh main (hien tai: $branch)"
    }
    $status = (& git -C $Root status --porcelain)
    if ($LASTEXITCODE -ne 0) {
        throw "Khong the kiem tra trang thai Git"
    }
    if ($status) {
        throw "Publish yeu cau working tree sach"
    }
}

function Assert-Candidate([string]$Root, [string]$ReleaseVersion) {
    $bundle = Join-Path $Root "QI-Crawler"
    $exe = Join-Path $bundle "QI-Crawler.exe"
    $installer = Join-Path $Root "QI-Crawler-Setup-v$ReleaseVersion.exe"
    $buildInfo = Join-Path $Root "BUILD_INFO.txt"
    $manifestPath = Join-Path $Root "release_manifest.json"
    Resolve-ExistingPath $exe "Portable EXE" | Out-Null
    Resolve-ExistingPath $installer "Installer" | Out-Null
    Resolve-ExistingPath $buildInfo "BUILD_INFO" | Out-Null
    Resolve-ExistingPath $manifestPath "Release manifest" | Out-Null
    try {
        $manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
    } catch {
        throw "Release manifest khong hop le: $manifestPath"
    }
    if ($manifest.product -ne "QI-Crawler" -or $manifest.version -ne $ReleaseVersion) {
        throw "Release manifest khong khop version/product"
    }
    if ($manifest.alembic_head -ne "0013_add_candidate_review_events") {
        throw "Release manifest thieu Alembic head 0013_add_candidate_review_events"
    }
    if ($manifest.portable_exe_sha256 -ne (Get-Sha256 $exe)) {
        throw "Hash portable EXE khong khop release manifest"
    }
    if ($manifest.installer_sha256 -ne (Get-Sha256 $installer)) {
        throw "Hash installer khong khop release manifest"
    }
    $infoText = Get-Content -LiteralPath $buildInfo -Raw -Encoding UTF8
    foreach ($required in @(
        "product=QI-Crawler",
        "version=$ReleaseVersion",
        "alembic_head=0013_add_candidate_review_events",
        "portable_exe_sha256=$($manifest.portable_exe_sha256)",
        "installer_sha256=$($manifest.installer_sha256)"
    )) {
        if ($infoText -notmatch [regex]::Escape($required)) {
            throw "BUILD_INFO thieu thong tin: $required"
        }
    }
    return @{
        Bundle = $bundle
        Exe = $exe
        Installer = $installer
        BuildInfo = $buildInfo
        Manifest = $manifestPath
    }
}

if (-not $Publish) {
    Write-Host "Khong publish: chi build/kiem tra candidate, khong cham vao Crawler tool." -ForegroundColor Yellow
    exit 0
}

$repo = Resolve-ExistingPath $RepoRoot "Repository"
Assert-RepositoryReady $repo

if (-not $PublishRoot) {
    $PublishRoot = Join-Path (Split-Path -Parent $repo) "Crawler tool"
}
$publishParent = Split-Path -Parent $PublishRoot
New-Item -ItemType Directory -Path $publishParent -Force | Out-Null
$publishRootResolved = [IO.Path]::GetFullPath($PublishRoot)

if (-not $CandidateRoot) {
    throw "Can -CandidateRoot den mot thu muc candidate da duoc build va smoke-test"
}
$candidate = Resolve-ExistingPath $CandidateRoot "Candidate"
$candidateParts = Assert-Candidate $candidate $Version

$publishStage = Join-Path $publishParent ("Crawler tool.publish-" + [guid]::NewGuid().ToString("N"))
$rotationStage = Join-Path $publishParent ("Crawler tool.rotate-" + [guid]::NewGuid().ToString("N"))
$oldPreviousBackup = Join-Path $rotationStage "Previous-backup"
$oldCurrentMoved = $false
$oldPreviousMoved = $false
$newCurrentMoved = $false

try {
    New-Item -ItemType Directory -Path $publishStage -Force | Out-Null
    $stagedCurrent = Join-Path $publishStage "Current"
    $stagedBundle = Join-Path $stagedCurrent "QI-Crawler"
    New-Item -ItemType Directory -Path $stagedBundle -Force | Out-Null
    Get-ChildItem -LiteralPath $candidateParts.Bundle -Force | Copy-Item -Destination $stagedBundle -Recurse -Force
    Copy-Item -LiteralPath $candidateParts.Installer -Destination (Join-Path $stagedCurrent (Split-Path -Leaf $candidateParts.Installer)) -Force
    Copy-Item -LiteralPath $candidateParts.BuildInfo -Destination (Join-Path $stagedCurrent "BUILD_INFO.txt") -Force
    Copy-Item -LiteralPath $candidateParts.Manifest -Destination (Join-Path $stagedCurrent "release_manifest.json") -Force

    $stagedExe = Join-Path $stagedCurrent "QI-Crawler\QI-Crawler.exe"
    $stagedInstaller = Join-Path $stagedCurrent (Split-Path -Leaf $candidateParts.Installer)

    if (-not (Test-Path -LiteralPath $stagedExe) -or -not (Test-Path -LiteralPath $stagedInstaller) -or
        -not (Test-Path -LiteralPath (Join-Path $stagedCurrent "BUILD_INFO.txt")) -or
        -not (Test-Path -LiteralPath (Join-Path $stagedCurrent "release_manifest.json"))) {
        throw "Candidate staging khong day du"
    }

    New-Item -ItemType Directory -Path $rotationStage -Force | Out-Null
    $current = Join-Path $publishRootResolved "Current"
    $previous = Join-Path $publishRootResolved "Previous"
    if (Test-Path -LiteralPath $previous) {
        Move-Item -LiteralPath $previous -Destination $oldPreviousBackup
        $oldPreviousMoved = $true
    }
    if (Test-Path -LiteralPath $current) {
        Move-Item -LiteralPath $current -Destination $previous
        $oldCurrentMoved = $true
    }
    New-Item -ItemType Directory -Path $publishRootResolved -Force | Out-Null
    Move-Item -LiteralPath $stagedCurrent -Destination $current
    $newCurrentMoved = $true
    if ($oldPreviousMoved) {
        Remove-Item -LiteralPath $oldPreviousBackup -Recurse -Force
        $oldPreviousMoved = $false
    }
    Write-Host "Publish thanh cong: $current" -ForegroundColor Green
} catch {
    if ($newCurrentMoved) {
        Remove-Item -LiteralPath (Join-Path $publishRootResolved "Current") -Recurse -Force -ErrorAction SilentlyContinue
    }
    if ($oldCurrentMoved -and (Test-Path -LiteralPath (Join-Path $publishRootResolved "Previous"))) {
        Move-Item -LiteralPath (Join-Path $publishRootResolved "Previous") -Destination (Join-Path $publishRootResolved "Current") -Force
    }
    if ($oldPreviousMoved -and (Test-Path -LiteralPath $oldPreviousBackup)) {
        Move-Item -LiteralPath $oldPreviousBackup -Destination (Join-Path $publishRootResolved "Previous") -Force
    }
    throw
} finally {
    if (Test-Path -LiteralPath $publishStage) {
        Remove-Item -LiteralPath $publishStage -Recurse -Force -ErrorAction SilentlyContinue
    }
    if (Test-Path -LiteralPath $rotationStage) {
        Remove-Item -LiteralPath $rotationStage -Recurse -Force -ErrorAction SilentlyContinue
    }
}
