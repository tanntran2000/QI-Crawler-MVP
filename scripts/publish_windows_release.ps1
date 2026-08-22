[CmdletBinding()]
param(
    [switch]$Publish,
    [string]$RepoRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$PublishRoot,
    [string]$CandidateRoot,
    [string]$Version = "0.7.1"
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
    Resolve-ExistingPath $exe "Portable EXE" | Out-Null
    Resolve-ExistingPath $installer "Installer" | Out-Null
    return @{
        Bundle = $bundle
        Exe = $exe
        Installer = $installer
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

    $stagedExe = Join-Path $stagedCurrent "QI-Crawler\QI-Crawler.exe"
    $stagedInstaller = Join-Path $stagedCurrent (Split-Path -Leaf $candidateParts.Installer)
    $commit = (& git -C $repo rev-parse HEAD).Trim()
    $branch = (& git -C $repo branch --show-current).Trim()
    $timestamp = (Get-Date).ToUniversalTime().ToString("o")
    $info = @(
        "product=QI-Crawler",
        "version=$Version",
        "commit_sha=$commit",
        "source_branch=$branch",
        "build_timestamp_utc=$timestamp",
        "portable_exe_sha256=$(Get-Sha256 $stagedExe)",
        "installer_sha256=$(Get-Sha256 $stagedInstaller)"
    )
    $info | Set-Content -LiteralPath (Join-Path $stagedCurrent "BUILD_INFO.txt") -Encoding UTF8

    if (-not (Test-Path -LiteralPath $stagedExe) -or -not (Test-Path -LiteralPath $stagedInstaller)) {
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
