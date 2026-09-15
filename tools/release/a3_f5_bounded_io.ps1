# Central fail-closed persistence boundary for the AO-04 canonical F5 route.
# Windows PowerShell 5.1 compatible; callers must initialize exact limits.

$script:F5BoundedLimits = $null
$script:F5BoundedUsage = @{}
$script:F5Utf8NoBom = New-Object Text.UTF8Encoding($false)

function Initialize-F5BoundedIo {
    param([Parameter(Mandatory=$true)] [hashtable]$Limits)
    if ($Limits.Count -eq 0) { throw 'MATERIAL_WRITE_BOUND_UNKNOWN: no limits supplied' }
    $script:F5BoundedLimits = $Limits
    $script:F5BoundedUsage = @{}
    foreach ($name in $Limits.Keys) {
        $limit = $Limits[$name]
        foreach ($required in @('max_file_count','max_per_file_bytes','max_aggregate_bytes','max_atomic_overlap_bytes')) {
            if ($null -eq $limit[$required] -or [Int64]$limit[$required] -lt 1) {
                throw "MATERIAL_WRITE_BOUND_UNKNOWN: $name.$required"
            }
        }
        $script:F5BoundedUsage[[string]$name] = [ordered]@{ file_count = 0; aggregate_bytes = [Int64]0 }
    }
}

function Get-F5BoundedLimit([string]$WriteClass) {
    if ($null -eq $script:F5BoundedLimits -or -not $script:F5BoundedLimits.ContainsKey($WriteClass)) {
        throw "MATERIAL_WRITE_BOUND_UNKNOWN: $WriteClass"
    }
    return $script:F5BoundedLimits[$WriteClass]
}

function Assert-F5WriteBudget([string]$WriteClass, [Int64]$ByteCount) {
    $limit = Get-F5BoundedLimit $WriteClass
    $usage = $script:F5BoundedUsage[$WriteClass]
    if ($ByteCount -lt 0 -or
        $ByteCount -gt [Int64]$limit.max_per_file_bytes -or
        $ByteCount -gt [Int64]$limit.max_atomic_overlap_bytes -or
        ([Int64]$usage.file_count + 1) -gt [Int64]$limit.max_file_count -or
        ([Int64]$usage.aggregate_bytes + $ByteCount) -gt [Int64]$limit.max_aggregate_bytes) {
        throw "MATERIAL_WRITE_BOUND_EXCEEDED: class=$WriteClass bytes=$ByteCount"
    }
}

function Add-F5WriteUsage([string]$WriteClass, [Int64]$ByteCount) {
    $usage = $script:F5BoundedUsage[$WriteClass]
    $usage.file_count = [Int64]$usage.file_count + 1
    $usage.aggregate_bytes = [Int64]$usage.aggregate_bytes + $ByteCount
}

function Write-F5BoundedBytes {
    param(
        [Parameter(Mandatory=$true)] [string]$Path,
        [Parameter(Mandatory=$true)] [AllowEmptyCollection()] [byte[]]$Bytes,
        [Parameter(Mandatory=$true)] [string]$WriteClass,
        [switch]$Immutable
    )
    Assert-F5WriteBudget $WriteClass $Bytes.Length
    if ($Immutable -and (Test-Path -LiteralPath $Path)) { throw "immutable bounded artifact already exists: $Path" }
    $parent = Split-Path -Parent $Path
    if ($parent) { New-Item -ItemType Directory -Force -Path $parent | Out-Null }
    $temporary = $Path + '.bounded.tmp'
    if (Test-Path -LiteralPath $temporary) { throw "MATERIAL_WRITE_TEMP_EXISTS: $temporary" }
    $stream = $null
    try {
        $stream = [IO.File]::Open($temporary, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
        $stream.Write($Bytes, 0, $Bytes.Length)
        $stream.Flush($true)
        $stream.Dispose(); $stream = $null
        if ($Immutable) { [IO.File]::Move($temporary, $Path) }
        else { Move-Item -LiteralPath $temporary -Destination $Path -Force }
        Add-F5WriteUsage $WriteClass $Bytes.Length
    } catch {
        if ($null -ne $stream) { $stream.Dispose() }
        if (Test-Path -LiteralPath $temporary) { Remove-Item -LiteralPath $temporary -Force -ErrorAction SilentlyContinue }
        throw
    }
}

function Write-F5BoundedText {
    param(
        [Parameter(Mandatory=$true)] [string]$Path,
        [AllowEmptyString()] [string]$Text,
        [Parameter(Mandatory=$true)] [string]$WriteClass,
        [switch]$Immutable
    )
    Write-F5BoundedBytes -Path $Path -Bytes $script:F5Utf8NoBom.GetBytes($Text) -WriteClass $WriteClass -Immutable:$Immutable
}

function Write-F5BoundedJson {
    param(
        [Parameter(Mandatory=$true)] [string]$Path,
        [Parameter(Mandatory=$true)] [AllowEmptyCollection()] $Value,
        [Parameter(Mandatory=$true)] [string]$WriteClass,
        [switch]$Immutable
    )
    $json = if ($Value -is [array] -and $Value.Count -eq 0) { '[]' } else { $Value | ConvertTo-Json -Depth 30 }
    $text = $json + "`n"
    Write-F5BoundedText -Path $Path -Text $text -WriteClass $WriteClass -Immutable:$Immutable
}

function Assert-F5BoundedRecords {
    param(
        [Parameter(Mandatory=$true)] [AllowEmptyCollection()] [object[]]$Records,
        [Parameter(Mandatory=$true)] [Int64]$MaxRecords,
        [Parameter(Mandatory=$true)] [Int64]$MaxFieldBytes,
        [Parameter(Mandatory=$true)] [Int64]$MaxSerializedBytes,
        [Parameter(Mandatory=$true)] [string]$Label
    )
    if ($Records.Count -gt $MaxRecords) { throw "MATERIAL_WRITE_BOUND_EXCEEDED: $Label record_count" }
    foreach ($record in $Records) {
        if ($record -isnot [Collections.IDictionary] -and $record -isnot [pscustomobject]) {
            throw "MATERIAL_WRITE_BOUND_INVALID: $Label record_shape"
        }
        $fields = if ($record -is [Collections.IDictionary]) { $record.GetEnumerator() } else { $record.PSObject.Properties }
        foreach ($property in $fields) {
            $fieldName = if ($record -is [Collections.IDictionary]) { $property.Key } else { $property.Name }
            if ($null -ne $property.Value -and $property.Value -is [string] -and
                $script:F5Utf8NoBom.GetByteCount([string]$property.Value) -gt $MaxFieldBytes) {
                throw "MATERIAL_WRITE_BOUND_EXCEEDED: $Label field=$fieldName"
            }
        }
    }
    $json = if ($Records.Count -eq 0) { '[]' } else { $Records | ConvertTo-Json -Depth 30 }
    $serialized = $json + "`n"
    if ($script:F5Utf8NoBom.GetByteCount($serialized) -gt $MaxSerializedBytes) {
        throw "MATERIAL_WRITE_BOUND_EXCEEDED: $Label serialized_bytes"
    }
}

function ConvertTo-F5CommandLine([string[]]$Arguments) {
    $quoted = foreach ($argument in $Arguments) {
        if ($argument -notmatch '[\s"]') { $argument }
        else { '"' + ($argument -replace '(\\*)"', '$1$1\"' -replace '(\\+)$', '$1$1') + '"' }
    }
    return ($quoted -join ' ')
}

function Start-F5CommandArtifact {
    param(
        [Parameter(Mandatory=$true)] [string]$Path,
        [string[]]$Arguments = @(),
        [Parameter(Mandatory=$true)] [string]$WorkingDirectory
    )
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf)) { throw 'F5_CMD_ARTIFACT_MISSING' }
    $invocation = @{
        FilePath = $Path
        WorkingDirectory = $WorkingDirectory
        WindowStyle = 'Hidden'
        PassThru = $true
    }
    if ($Arguments.Count -gt 0) {
        $invocation.ArgumentList = ConvertTo-F5CommandLine $Arguments
    }
    return Start-Process @invocation
}

function Invoke-F5BoundedProcess {
    param(
        [Parameter(Mandatory=$true)] [string]$FilePath,
        [string[]]$Arguments = @(),
        [Parameter(Mandatory=$true)] [string]$WriteClass,
        [Parameter(Mandatory=$true)] [string]$ResultPath,
        [string]$TrialId = ''
    )
    $limit = Get-F5BoundedLimit $WriteClass
    foreach ($required in @('max_stdout_bytes','max_stderr_bytes','max_runtime_seconds')) {
        if ($null -eq $limit[$required] -or [Int64]$limit[$required] -lt 1) {
            throw "MATERIAL_WRITE_BOUND_UNKNOWN: $WriteClass.$required"
        }
    }
    if (-not ('F5BoundedProcessRunner' -as [type])) {
        Add-Type -TypeDefinition @'
using System;
using System.Diagnostics;
using System.IO;
using System.Threading.Tasks;

public sealed class F5BoundedProcessResult {
    public int ExitCode;
    public byte[] Stdout;
    public byte[] Stderr;
    public bool Overflow;
    public bool TimedOut;
}

public static class F5BoundedProcessRunner {
    private static byte[] ReadBounded(Stream stream, long limit, Process process, F5BoundedProcessResult result) {
        using (var memory = new MemoryStream()) {
            var buffer = new byte[4096];
            while (true) {
                int count = stream.Read(buffer, 0, buffer.Length);
                if (count == 0) break;
                if (memory.Length + count > limit) {
                    result.Overflow = true;
                    try { process.Kill(); } catch { }
                    break;
                }
                memory.Write(buffer, 0, count);
            }
            return memory.ToArray();
        }
    }

    public static F5BoundedProcessResult Run(string file, string arguments, long stdoutLimit, long stderrLimit, int timeoutMs) {
        var result = new F5BoundedProcessResult();
        var info = new ProcessStartInfo(file, arguments) {
            UseShellExecute = false,
            CreateNoWindow = true,
            RedirectStandardOutput = true,
            RedirectStandardError = true
        };
        using (var process = new Process { StartInfo = info }) {
            if (!process.Start()) throw new InvalidOperationException("BOUNDED_PROCESS_START_FAILED");
            var stdoutTask = Task.Factory.StartNew(() => ReadBounded(process.StandardOutput.BaseStream, stdoutLimit, process, result));
            var stderrTask = Task.Factory.StartNew(() => ReadBounded(process.StandardError.BaseStream, stderrLimit, process, result));
            if (!process.WaitForExit(timeoutMs)) {
                result.TimedOut = true;
                try { process.Kill(); } catch { }
            }
            process.WaitForExit();
            Task.WaitAll(stdoutTask, stderrTask);
            result.Stdout = stdoutTask.Result;
            result.Stderr = stderrTask.Result;
            result.ExitCode = process.ExitCode;
        }
        return result;
    }
}
'@
    }
    $captured = [F5BoundedProcessRunner]::Run(
        $FilePath,
        (ConvertTo-F5CommandLine $Arguments),
        [Int64]$limit.max_stdout_bytes,
        [Int64]$limit.max_stderr_bytes,
        [int]([Int64]$limit.max_runtime_seconds * 1000)
    )
    if ($captured.TimedOut) { throw "MATERIAL_WRITE_BOUND_EXCEEDED: $WriteClass runtime" }
    if ($captured.Overflow) { throw "MATERIAL_WRITE_BOUND_EXCEEDED: $WriteClass process_output" }
    try {
        $result = [ordered]@{
            exit_code = $captured.ExitCode
            stdout = $script:F5Utf8NoBom.GetString($captured.Stdout)
            stderr = $script:F5Utf8NoBom.GetString($captured.Stderr)
            stdout_bytes = $captured.Stdout.Length
            stderr_bytes = $captured.Stderr.Length
        }
        if ($TrialId) { $result['trial_id'] = $TrialId }
        Write-F5BoundedJson -Path $ResultPath -Value $result -WriteClass $WriteClass
        return [pscustomobject]$result
    } finally { }
}

function Get-F5BoundedIoUsage {
    return $script:F5BoundedUsage
}
