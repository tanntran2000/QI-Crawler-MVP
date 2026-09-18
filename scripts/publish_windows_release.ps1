[CmdletBinding()]
param(
    [switch]$Publish,
    [string]$RepoRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$PublishRoot,
    [string]$CandidateRoot,
    [Parameter(Mandatory = $true)]
    [string]$Version,
    [string]$ExpectedAlembicHead
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

function Convert-UtcTimestamp([object]$Value, [string]$Label) {
    $parsedTimestamp = [DateTimeOffset]::MinValue
    if ($Value -is [DateTime]) {
        $parsedTimestamp = [DateTimeOffset]([DateTime]$Value)
    } elseif ($Value -is [DateTimeOffset]) {
        $parsedTimestamp = [DateTimeOffset]$Value
    } elseif ($Value -is [string] -and -not [string]::IsNullOrWhiteSpace($Value) -and
        [DateTimeOffset]::TryParse(
            $Value,
            [Globalization.CultureInfo]::InvariantCulture,
            [Globalization.DateTimeStyles]::RoundtripKind,
            [ref]$parsedTimestamp
        )) {
        if (-not $Value.EndsWith("Z", [StringComparison]::Ordinal)) {
            throw "$Label khong phai UTC chuan"
        }
    } else {
        throw "$Label khong phai timestamp hop le"
    }
    if ($parsedTimestamp.Offset -ne [TimeSpan]::Zero) {
        throw "$Label khong phai UTC"
    }
    return $parsedTimestamp.UtcDateTime.ToString(
        "yyyy-MM-ddTHH:mm:ss.fffffff'Z'",
        [Globalization.CultureInfo]::InvariantCulture
    )
}

function Get-RequiredStringField([object]$Object, [string]$Name, [string]$Label) {
    $property = $Object.PSObject.Properties[$Name]
    if ($null -eq $property) {
        throw "$Label thieu hoac rong: $Name"
    }
    if ($Name -eq "build_timestamp_utc") {
        return Convert-UtcTimestamp $property.Value "$Label $Name"
    }
    if (-not ($property.Value -is [string]) -or
        [string]::IsNullOrWhiteSpace([string]$property.Value)) {
        throw "$Label thieu hoac rong: $Name"
    }
    return ([string]$property.Value).Trim()
}

function Assert-ProvenanceFormat(
    [hashtable]$Fields,
    [string]$Label,
    [string]$ReleaseVersion,
    [string]$ExpectedHead,
    [switch]$Manifest,
    [switch]$Receipt
) {
    if ($Fields.product -ne "QI-Crawler") {
        throw "$Label product khong hop le"
    }
    if ($Fields.version -notmatch '^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$' -or
        $Fields.version -ne $ReleaseVersion) {
        throw "$Label version khong hop le"
    }
    if ($Fields.source_git_sha -notmatch '^[0-9A-Fa-f]{40}$') {
        throw "$Label source_git_sha khong hop le"
    }
    if ($Fields.source_branch -match '[\r\n]') {
        throw "$Label source_branch khong hop le"
    }
    Convert-UtcTimestamp $Fields.build_timestamp_utc "$Label build_timestamp_utc" | Out-Null
    if ($Fields.alembic_head -notmatch '^[A-Za-z0-9_]+$' -or
        $Fields.alembic_head -ne $ExpectedHead) {
        throw "$Label alembic_head khong hop le"
    }
    if ($Fields.portable_exe_sha256 -notmatch '^[0-9A-Fa-f]{64}$') {
        throw "$Label portable_exe_sha256 khong hop le"
    }
    if ($Manifest) {
        if ($Fields.metadata_schema_version -ne "qi-crawler-installed-release-v1") {
            throw "$Label metadata schema khong duoc ho tro"
        }
        if ($Fields.release_channel -ne "INTERNAL_CANDIDATE") {
            throw "$Label release_channel khong duoc ho tro"
        }
    }
    if ($Receipt) {
        if ($Fields.receipt_schema_version -ne "qi-crawler-release-artifact-v1") {
            throw "$Label receipt schema khong duoc ho tro"
        }
        if ($Fields.installer_sha256 -notmatch '^[0-9A-Fa-f]{64}$') {
            throw "$Label installer_sha256 khong hop le"
        }
    }
}

function Read-BuildInfo([string]$PathValue) {
    $records = @{}
    foreach ($line in Get-Content -LiteralPath $PathValue -Encoding UTF8) {
        if ([string]::IsNullOrWhiteSpace($line) -or $line -notmatch '^([^=\s]+)=(.*)$') {
            throw "BUILD_INFO co dong khong hop le"
        }
        $key = $Matches[1]
        $value = $Matches[2]
        if ($records.ContainsKey($key)) {
            throw "BUILD_INFO trung khoa: $key"
        }
        if ([string]::IsNullOrWhiteSpace($value)) {
            throw "BUILD_INFO co gia tri rong: $key"
        }
        $records[$key] = $value.Trim()
    }
    return $records
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

function Assert-Candidate([string]$Root, [string]$ReleaseVersion, [string]$ExpectedHead) {
    $bundle = Join-Path $Root "QI-Crawler"
    $exe = Join-Path $bundle "QI-Crawler.exe"
    $installer = Join-Path $Root "QI-Crawler-Setup-v$ReleaseVersion.exe"
    $versionFile = Join-Path $bundle "VERSION.txt"
    $whatsNew = Join-Path $bundle "WHAT_IS_NEW.txt"
    $capabilities = Join-Path $bundle "CAPABILITIES.txt"
    $buildInfo = Join-Path $bundle "BUILD_INFO.txt"
    $manifestPath = Join-Path $bundle "release_manifest.json"
    $receiptPath = Join-Path $Root "release_artifact_receipt.json"
    Resolve-ExistingPath $exe "Portable EXE" | Out-Null
    Resolve-ExistingPath $installer "Installer" | Out-Null
    Resolve-ExistingPath $versionFile "Installed VERSION" | Out-Null
    Resolve-ExistingPath $whatsNew "Installed WHAT_IS_NEW" | Out-Null
    Resolve-ExistingPath $capabilities "Installed CAPABILITIES" | Out-Null
    Resolve-ExistingPath $buildInfo "BUILD_INFO" | Out-Null
    Resolve-ExistingPath $manifestPath "Release manifest" | Out-Null
    Resolve-ExistingPath $receiptPath "Artifact receipt" | Out-Null
    try {
        $manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
        $receipt = Get-Content -LiteralPath $receiptPath -Raw -Encoding UTF8 | ConvertFrom-Json
    } catch {
        throw "Release manifest hoac artifact receipt khong hop le"
    }
    $manifestFields = @{}
    foreach ($field in @(
        "metadata_schema_version", "product", "version", "source_git_sha",
        "source_branch", "build_timestamp_utc", "alembic_head", "release_channel",
        "portable_exe_sha256"
    )) {
        $manifestFields[$field] = Get-RequiredStringField $manifest $field "Release manifest"
    }
    Assert-ProvenanceFormat $manifestFields "Release manifest" $ReleaseVersion $ExpectedHead -Manifest
    if ($manifest.PSObject.Properties.Name -contains "installer_sha256") {
        throw "Installed release manifest khong duoc chua installer SHA"
    }
    if ($manifestFields.portable_exe_sha256 -ne (Get-Sha256 $exe)) {
        throw "Hash portable EXE khong khop release manifest"
    }
    $receiptFields = @{}
    foreach ($field in @(
        "receipt_schema_version", "product", "version", "source_git_sha", "source_branch",
        "build_timestamp_utc", "alembic_head", "portable_exe_sha256", "installer_sha256"
    )) {
        $receiptFields[$field] = Get-RequiredStringField $receipt $field "Artifact receipt"
    }
    Assert-ProvenanceFormat $receiptFields "Artifact receipt" $ReleaseVersion $ExpectedHead -Receipt
    if ($receiptFields.portable_exe_sha256 -ne (Get-Sha256 $exe) -or
        $receiptFields.installer_sha256 -ne (Get-Sha256 $installer)) {
        throw "Artifact receipt khong khop portable/installer hash"
    }
    foreach ($field in @(
        "product", "version", "source_git_sha", "source_branch", "build_timestamp_utc",
        "alembic_head", "portable_exe_sha256"
    )) {
        if ($manifestFields[$field] -cne $receiptFields[$field]) {
            throw "Release manifest va artifact receipt khong khop: $field"
        }
    }
    $infoFields = Read-BuildInfo $buildInfo
    $infoFields["build_timestamp_utc"] = Convert-UtcTimestamp `
        $infoFields["build_timestamp_utc"] "BUILD_INFO build_timestamp_utc"
    foreach ($field in @(
        "metadata_schema_version", "product", "version", "source_git_sha",
        "source_branch", "build_timestamp_utc", "alembic_head", "release_channel",
        "portable_exe_sha256"
    )) {
        if (-not $infoFields.ContainsKey($field)) {
            throw "BUILD_INFO thieu khoa: $field"
        }
        if ([string]$infoFields[$field] -cne [string]$manifestFields[$field]) {
            throw "BUILD_INFO va release manifest khong khop: $field"
        }
    }
    return @{
        Bundle = $bundle
        Exe = $exe
        Installer = $installer
        BuildInfo = $buildInfo
        Manifest = $manifestPath
        Receipt = $receiptPath
    }
}

if (-not $Publish) {
    Write-Host "Khong publish: chi build/kiem tra candidate, khong cham vao Crawler tool." -ForegroundColor Yellow
    exit 0
}

if ([string]::IsNullOrWhiteSpace($ExpectedAlembicHead)) {
    throw "ExpectedAlembicHead la bat buoc khi publish"
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
$candidateParts = Assert-Candidate $candidate $Version $ExpectedAlembicHead

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
    Copy-Item -LiteralPath $candidateParts.Receipt -Destination (Join-Path $stagedCurrent "release_artifact_receipt.json") -Force

    $stagedExe = Join-Path $stagedCurrent "QI-Crawler\QI-Crawler.exe"
    $stagedInstaller = Join-Path $stagedCurrent (Split-Path -Leaf $candidateParts.Installer)

    if (-not (Test-Path -LiteralPath $stagedExe) -or -not (Test-Path -LiteralPath $stagedInstaller) -or
        -not (Test-Path -LiteralPath (Join-Path $stagedBundle "BUILD_INFO.txt")) -or
        -not (Test-Path -LiteralPath (Join-Path $stagedBundle "release_manifest.json")) -or
        -not (Test-Path -LiteralPath (Join-Path $stagedCurrent "release_artifact_receipt.json"))) {
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
