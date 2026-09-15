[CmdletBinding()]
param(
    [Alias('Mode')]
    [ValidateSet('PositiveControl', 'Library')]
    [string]$JobHelperMode = 'PositiveControl'
)

$ErrorActionPreference = 'Stop'

if ($JobHelperMode -notin @('PositiveControl', 'Library')) {
    Write-Output 'JOB_OBJECT_MODE_INVALID'
    exit 64
}

Add-Type -TypeDefinition @'
using System;
using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;
using System.IO;
using System.IO.Pipes;
using System.Threading.Tasks;

public sealed class A3ContainedSession {
    public IntPtr JobHandle;
    public IntPtr ProcessHandle;
    public Int32 ProcessId;
    public A3RouteCapture Capture;
}

public sealed class A3RouteCapture : IDisposable {
    public readonly AnonymousPipeServerStream Out = new AnonymousPipeServerStream(PipeDirection.In, HandleInheritability.Inheritable);
    public readonly AnonymousPipeServerStream Err = new AnonymousPipeServerStream(PipeDirection.In, HandleInheritability.Inheritable);
    public readonly AnonymousPipeServerStream Input = new AnonymousPipeServerStream(PipeDirection.Out, HandleInheritability.Inheritable);
    public Task<byte[]> OutTask, ErrTask;
    public volatile bool Overflow;
    private byte[] Drain(Stream stream, int limit, IntPtr job) {
        using (var memory = new MemoryStream()) {
            var buffer = new byte[4096];
            while (true) {
                int count = stream.Read(buffer, 0, buffer.Length);
                if (count == 0) break;
                int keep = Math.Min(count, limit - (int)memory.Length);
                memory.Write(buffer, 0, keep);
                if (keep != count) {
                    Overflow = true;
                    A3JobObjectNative.TerminateJobObject(job, 0xA304);
                    break;
                }
            }
            return memory.ToArray();
        }
    }
    public void Start(IntPtr job, int stdoutLimit, int stderrLimit) {
        Out.DisposeLocalCopyOfClientHandle();
        Err.DisposeLocalCopyOfClientHandle();
        Input.DisposeLocalCopyOfClientHandle();
        Input.Dispose(); // EOF on child stdin; no interactive input.
        OutTask = Task.Factory.StartNew(() => Drain(Out, stdoutLimit, job));
        ErrTask = Task.Factory.StartNew(() => Drain(Err, stderrLimit, job));
    }
    public void Complete() {
        if (!Task.WaitAll(new Task[] { OutTask, ErrTask }, 5000)) {
            throw new InvalidOperationException("JOB_ROUTE_CAPTURE_TIMEOUT");
        }
    }
    public void Dispose() { Out.Dispose(); Err.Dispose(); Input.Dispose(); }
}

public static class A3JobObjectNative {
    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    public struct StartupInfo {
        public Int32 cb;
        public string lpReserved;
        public string lpDesktop;
        public string lpTitle;
        public Int32 dwX, dwY, dwXSize, dwYSize, dwXCountChars, dwYCountChars;
        public Int32 dwFillAttribute, dwFlags;
        public Int16 wShowWindow, cbReserved2;
        public IntPtr lpReserved2, hStdInput, hStdOutput, hStdError;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct ProcessInformation {
        public IntPtr hProcess, hThread;
        public Int32 dwProcessId, dwThreadId;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct BasicLimitInformation {
        public Int64 PerProcessUserTimeLimit, PerJobUserTimeLimit;
        public UInt32 LimitFlags;
        public UIntPtr MinimumWorkingSetSize, MaximumWorkingSetSize;
        public UInt32 ActiveProcessLimit;
        public UIntPtr Affinity;
        public UInt32 PriorityClass, SchedulingClass;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct IoCounters {
        public UInt64 ReadOperationCount, WriteOperationCount, OtherOperationCount;
        public UInt64 ReadTransferCount, WriteTransferCount, OtherTransferCount;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct ExtendedLimitInformation {
        public BasicLimitInformation BasicLimitInformation;
        public IoCounters IoInfo;
        public UIntPtr ProcessMemoryLimit, JobMemoryLimit;
        public UIntPtr PeakProcessMemoryUsed, PeakJobMemoryUsed;
    }

    [DllImport("kernel32.dll", EntryPoint = "CreateProcessW", CharSet = CharSet.Unicode, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool CreateProcess(
        string applicationName, StringBuilder commandLine,
        IntPtr processAttributes, IntPtr threadAttributes,
        [MarshalAs(UnmanagedType.Bool)] bool inheritHandles, UInt32 creationFlags,
        IntPtr environment, string currentDirectory,
        ref StartupInfo startupInfo, out ProcessInformation processInformation);

    [DllImport("kernel32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    public static extern IntPtr CreateJobObject(IntPtr lpJobAttributes, string lpName);

    [DllImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool AssignProcessToJobObject(IntPtr hJob, IntPtr hProcess);

    [DllImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool SetInformationJobObject(
        IntPtr hJob, Int32 JobObjectInformationClass,
        ref ExtendedLimitInformation lpJobObjectInformation,
        UInt32 cbJobObjectInformationLength);

    [DllImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool TerminateJobObject(IntPtr hJob, UInt32 uExitCode);

    [DllImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool QueryInformationJobObject(
        IntPtr hJob,
        Int32 JobObjectInformationClass,
        IntPtr lpJobObjectInformation,
        UInt32 cbJobObjectInformationLength,
        out UInt32 lpReturnLength);

    [DllImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool CloseHandle(IntPtr hObject);

    [DllImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool TerminateProcess(IntPtr hProcess, UInt32 exitCode);

    [DllImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool GetExitCodeProcess(IntPtr hProcess, out UInt32 exitCode);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern UInt32 ResumeThread(IntPtr hThread);

    [DllImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    public static extern bool IsProcessInJob(
        IntPtr processHandle, IntPtr jobHandle,
        [MarshalAs(UnmanagedType.Bool)] out bool result);

    private static string Quote(string value) {
        if (value == null) throw new ArgumentNullException("value");
        if (value.Length > 0 && value.IndexOfAny(new char[] {' ', '\t', '"'}) < 0) return value;
        StringBuilder output = new StringBuilder("\"");
        int slashes = 0;
        foreach (char ch in value) {
            if (ch == '\\') { slashes++; continue; }
            if (ch == '"') {
                output.Append('\\', slashes * 2 + 1);
                output.Append('"');
                slashes = 0;
                continue;
            }
            output.Append('\\', slashes);
            slashes = 0;
            output.Append(ch);
        }
        output.Append('\\', slashes * 2);
        output.Append('"');
        return output.ToString();
    }

    public static A3ContainedSession StartContained(string executable, string[] arguments, string cwd) {
        return StartContained(executable, arguments, cwd, 0, 0);
    }

    public static A3ContainedSession StartContained(string executable, string[] arguments, string cwd, int stdoutLimit, int stderrLimit) {
        IntPtr job = IntPtr.Zero;
        A3RouteCapture capture = null;
        ProcessInformation process = new ProcessInformation();
        try {
            job = CreateJobObject(IntPtr.Zero, null);
            if (job == IntPtr.Zero) throw new Win32Exception(Marshal.GetLastWin32Error(), "CreateJobObject failed");
            ExtendedLimitInformation limits = new ExtendedLimitInformation();
            // The last Job handle closing (including an orchestrator crash)
            // must not leave a controller writer running in the sandbox.
            limits.BasicLimitInformation.LimitFlags = 0x00002000; // JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
            if (!SetInformationJobObject(job, 9, ref limits,
                (UInt32)Marshal.SizeOf(typeof(ExtendedLimitInformation)))) {
                throw new Win32Exception(Marshal.GetLastWin32Error(), "SetInformationJobObject failed");
            }
            StringBuilder command = new StringBuilder(Quote(executable));
            foreach (string argument in arguments) command.Append(' ').Append(Quote(argument));
            StartupInfo startup = new StartupInfo();
            startup.cb = Marshal.SizeOf(typeof(StartupInfo));
            if (stdoutLimit > 0 && stderrLimit > 0) {
                capture = new A3RouteCapture();
                startup.dwFlags = 0x00000100; // STARTF_USESTDHANDLES
                startup.hStdOutput = capture.Out.ClientSafePipeHandle.DangerousGetHandle();
                startup.hStdError = capture.Err.ClientSafePipeHandle.DangerousGetHandle();
                startup.hStdInput = capture.Input.ClientSafePipeHandle.DangerousGetHandle();
            }
            // CREATE_SUSPENDED | CREATE_NO_WINDOW: no controller code can run
            // or spawn descendants before the Job assignment is verified.
            if (!CreateProcess(executable, command, IntPtr.Zero, IntPtr.Zero, capture != null,
                0x08000004, IntPtr.Zero, cwd, ref startup, out process)) {
                throw new Win32Exception(Marshal.GetLastWin32Error(), "CreateProcess suspended failed");
            }
            if (!AssignProcessToJobObject(job, process.hProcess)) {
                throw new Win32Exception(Marshal.GetLastWin32Error(), "AssignProcessToJobObject failed");
            }
            bool assigned;
            if (!IsProcessInJob(process.hProcess, job, out assigned) || !assigned || ActiveCount(job) != 1) {
                throw new InvalidOperationException("controller Job membership is not proven");
            }
            if (capture != null) capture.Start(job, stdoutLimit, stderrLimit);
            if (ResumeThread(process.hThread) == UInt32.MaxValue) {
                throw new Win32Exception(Marshal.GetLastWin32Error(), "ResumeThread failed");
            }
            CloseHandle(process.hThread);
            process.hThread = IntPtr.Zero;
            A3ContainedSession session = new A3ContainedSession();
            session.JobHandle = job;
            session.ProcessHandle = process.hProcess;
            session.ProcessId = process.dwProcessId;
            session.Capture = capture;
            return session;
        }
        catch {
            if (process.hProcess != IntPtr.Zero) TerminateProcess(process.hProcess, 0xA304);
            if (capture != null) capture.Dispose();
            if (process.hThread != IntPtr.Zero) CloseHandle(process.hThread);
            if (process.hProcess != IntPtr.Zero) CloseHandle(process.hProcess);
            if (job != IntPtr.Zero) CloseHandle(job);
            throw;
        }
    }

    public static Int32[] ActiveProcessIds(IntPtr hJob) {
        Int32 size = 65536;
        IntPtr buffer = Marshal.AllocHGlobal(size);
        try {
            UInt32 returned;
            if (!QueryInformationJobObject(hJob, 3, buffer, (UInt32)size, out returned)) {
                throw new Win32Exception(Marshal.GetLastWin32Error(), "Job membership query failed");
            }
            Int32 count = Marshal.ReadInt32(buffer, 4);
            if (count < 0 || 8L + (long)count * IntPtr.Size > size) {
                throw new InvalidOperationException("Job membership list exceeds bound");
            }
            Int32[] ids = new Int32[count];
            for (Int32 i = 0; i < count; i++) {
                ids[i] = checked((Int32)Marshal.ReadIntPtr(buffer, 8 + i * IntPtr.Size).ToInt64());
            }
            return ids;
        }
        finally { Marshal.FreeHGlobal(buffer); }
    }

    public static UInt32 ActiveCount(IntPtr hJob) {
        // JOBOBJECT_BASIC_PROCESS_ID_LIST (information class 3) reports the
        // active process IDs and avoids relying on the platform's padding for
        // JOBOBJECT_BASIC_ACCOUNTING_INFORMATION.
        Int32 size = 4096;
        IntPtr buffer = Marshal.AllocHGlobal(size);
        try {
            UInt32 returned;
            if (!QueryInformationJobObject(hJob, 3, buffer, (UInt32)size, out returned)) {
                throw new Win32Exception(Marshal.GetLastWin32Error());
            }
            return (UInt32)Marshal.ReadInt32(buffer, 4);
        }
        finally {
            Marshal.FreeHGlobal(buffer);
        }
    }

    public static Int32 TotalProcessCount(IntPtr hJob) {
        IntPtr buffer = Marshal.AllocHGlobal(48);
        try {
            UInt32 returned;
            if (!QueryInformationJobObject(hJob, 1, buffer, 48, out returned)) {
                throw new Win32Exception(Marshal.GetLastWin32Error(), "Job accounting query failed");
            }
            Int32 total = Marshal.ReadInt32(buffer, 36);
            if (total < 1) throw new InvalidOperationException("Job total-process count invalid");
            return total;
        }
        finally { Marshal.FreeHGlobal(buffer); }
    }
}
'@

function Start-A3ContainedProcess {
    param([string]$FilePath, [string[]]$Arguments, [string]$WorkingDirectory)
    if (-not (Test-Path -LiteralPath $FilePath -PathType Leaf) -or
        -not (Test-Path -LiteralPath $WorkingDirectory -PathType Container)) {
        throw 'JOB_CONTROLLER_INPUT_INVALID'
    }
    return [A3JobObjectNative]::StartContained($FilePath, $Arguments, $WorkingDirectory)
}

function Start-A3ContainedRoute {
    param(
        [ValidateSet('EXE','CMD','SHORTCUT')][string]$Kind,
        [string]$Artifact,
        [string[]]$Arguments = @(),
        [string]$WorkingDirectory,
        [ValidateRange(1,1048576)] [int]$MaxStdoutBytes = 1048576,
        [ValidateRange(1,1048576)] [int]$MaxStderrBytes = 1048576
    )
    if (-not (Test-Path -LiteralPath $Artifact -PathType Leaf) -or
        -not (Test-Path -LiteralPath $WorkingDirectory -PathType Container)) {
        throw 'JOB_ROUTE_INPUT_INVALID'
    }
    $artifactFull = [IO.Path]::GetFullPath($Artifact)
    $ps51 = Join-Path $env:WINDIR 'System32\WindowsPowerShell\v1.0\powershell.exe'
    $quoted = "'" + $artifactFull.Replace("'", "''") + "'"
    switch ($Kind) {
        'EXE' {
            return [A3JobObjectNative]::StartContained($artifactFull, $Arguments, $WorkingDirectory, $MaxStdoutBytes, $MaxStderrBytes)
        }
        'CMD' {
            if ([IO.Path]::GetExtension($artifactFull).ToLowerInvariant() -ne '.cmd') { throw 'JOB_ROUTE_KIND_MISMATCH' }
            $command = '& ' + $quoted + '; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }'
            return [A3JobObjectNative]::StartContained($ps51, @('-NoProfile','-NonInteractive','-Command',$command), $WorkingDirectory, $MaxStdoutBytes, $MaxStderrBytes)
        }
        'SHORTCUT' {
            if ([IO.Path]::GetExtension($artifactFull).ToLowerInvariant() -ne '.lnk') { throw 'JOB_ROUTE_KIND_MISMATCH' }
            $command = 'Start-Process -FilePath ' + $quoted + ' -ErrorAction Stop'
            return [A3JobObjectNative]::StartContained($ps51, @('-NoProfile','-NonInteractive','-Command',$command), $WorkingDirectory, $MaxStdoutBytes, $MaxStderrBytes)
        }
    }
}

function Get-A3JobProcessIds {
    param([A3ContainedSession]$Session)
    if ($null -eq $Session -or $Session.JobHandle -eq [IntPtr]::Zero) { throw 'JOB_SESSION_INVALID' }
    return [A3JobObjectNative]::ActiveProcessIds($Session.JobHandle)
}

function Get-A3JobActiveCount {
    param([A3ContainedSession]$Session)
    if ($null -eq $Session -or $Session.JobHandle -eq [IntPtr]::Zero) { throw 'JOB_SESSION_INVALID' }
    return [A3JobObjectNative]::ActiveCount($Session.JobHandle)
}

function Wait-A3ContainedRouteZero {
    param([A3ContainedSession]$Session, [int]$TimeoutMilliseconds = 10000, [int]$MinimumTotalProcesses = 1)
    if ($null -eq $Session -or $Session.JobHandle -eq [IntPtr]::Zero -or
        $Session.ProcessHandle -eq [IntPtr]::Zero -or $TimeoutMilliseconds -lt 1) {
        throw 'JOB_ROUTE_SESSION_INVALID'
    }
    $deadline = (Get-Date).AddMilliseconds($TimeoutMilliseconds)
    $observed = [Collections.Generic.HashSet[int]]::new()
    [void]$observed.Add($Session.ProcessId)
    do {
        foreach ($member in @(Get-A3JobProcessIds -Session $Session)) { [void]$observed.Add([int]$member) }
        $active = Get-A3JobActiveCount -Session $Session
        if ($active -eq 0) {
            $total = [A3JobObjectNative]::TotalProcessCount($Session.JobHandle)
            $exitCode = [uint32]0
            if (-not [A3JobObjectNative]::GetExitCodeProcess($Session.ProcessHandle, [ref]$exitCode)) {
                throw 'JOB_ROUTE_EXIT_UNREADABLE'
            }
            if ($exitCode -eq 259) { throw 'JOB_ROUTE_EXIT_STILL_ACTIVE' }
            $stdout=''; $stderr=''; $overflow=$false
            if ($Session.Capture) {
                $Session.Capture.Complete()
                $stdout=[Text.Encoding]::UTF8.GetString($Session.Capture.OutTask.Result)
                $stderr=[Text.Encoding]::UTF8.GetString($Session.Capture.ErrTask.Result)
                $overflow=$Session.Capture.Overflow
            }
            $result=[pscustomobject]@{
                launcher_pid=$Session.ProcessId
                observed_job_pids=@($observed)
                total_job_processes=$total
                active_after=0
                launcher_exit_code=$exitCode
                stdout=$stdout
                stderr=$stderr
                output_bound_exceeded=$overflow
            }
            $failure=if($overflow){'JOB_ROUTE_OUTPUT_BOUND_EXCEEDED'}elseif($exitCode -ne 0){"JOB_ROUTE_EXIT_NONZERO: $exitCode"}elseif($total -lt $MinimumTotalProcesses){'JOB_ROUTE_TARGET_NOT_PROVEN'}else{$null}
            if ($failure) {
                $errorResult=[InvalidOperationException]::new($failure)
                $errorResult.Data['route_result']=$result
                throw $errorResult
            }
            return $result
        }
        Start-Sleep -Milliseconds 25
    } while ((Get-Date) -lt $deadline)
    throw "JOB_ROUTE_ACTIVE_TIMEOUT: $active"
}

function Stop-A3ContainedProcess {
    param([A3ContainedSession]$Session)
    if ($null -eq $Session -or $Session.JobHandle -eq [IntPtr]::Zero) { throw 'JOB_SESSION_INVALID' }
    $before = Get-A3JobActiveCount -Session $Session
    if ($before -lt 1) { throw 'JOB_ACTIVE_PROCESS_COUNT_BEFORE_INVALID' }
    if (-not [A3JobObjectNative]::TerminateJobObject($Session.JobHandle, 0xA304)) {
        throw "TerminateJobObject failed: $([Runtime.InteropServices.Marshal]::GetLastWin32Error())"
    }
    $deadline = (Get-Date).AddSeconds(5)
    do {
        $after = Get-A3JobActiveCount -Session $Session
        if ($after -eq 0) { return [pscustomobject]@{ active_before = $before; active_after = 0 } }
        Start-Sleep -Milliseconds 25
    } while ((Get-Date) -lt $deadline)
    throw "JOB_ACTIVE_PROCESS_COUNT_AFTER_NOT_ZERO: $after"
}

function Close-A3ContainedProcess {
    param([A3ContainedSession]$Session)
    if ($null -eq $Session) { return }
    try {
        if ($Session.JobHandle -ne [IntPtr]::Zero) {
            try {
                if ((Get-A3JobActiveCount -Session $Session) -gt 0) {
                    [void][A3JobObjectNative]::TerminateJobObject($Session.JobHandle, 0xA304)
                }
            } catch {
                [void][A3JobObjectNative]::TerminateJobObject($Session.JobHandle, 0xA304)
            }
        }
    } finally {
        if ($Session.Capture) {
            try { $Session.Capture.Complete() } catch { } finally { $Session.Capture.Dispose() }
        }
        if ($Session.ProcessHandle -ne [IntPtr]::Zero) {
            [void][A3JobObjectNative]::CloseHandle($Session.ProcessHandle)
            $Session.ProcessHandle = [IntPtr]::Zero
        }
        if ($Session.JobHandle -ne [IntPtr]::Zero) {
            [void][A3JobObjectNative]::CloseHandle($Session.JobHandle)
            $Session.JobHandle = [IntPtr]::Zero
        }
    }
}

if ($JobHelperMode -eq 'Library') { return }

$job = [IntPtr]::Zero
$child = $null
$outerLock = $null
$lockPath = Join-Path ([IO.Path]::GetTempPath()) ("a3-f5-job-control-$([guid]::NewGuid().ToString('N')).lock")

try {
    $outerLock = [IO.File]::Open(
        $lockPath,
        [IO.FileMode]::OpenOrCreate,
        [IO.FileAccess]::ReadWrite,
        [IO.FileShare]::None)

    $shell = (Get-Command powershell.exe -ErrorAction SilentlyContinue).Source
    if (-not $shell) { $shell = (Get-Command pwsh -ErrorAction Stop).Source }
    $child = Start-Process -FilePath $shell -ArgumentList @(
        '-NoProfile', '-NonInteractive', '-ExecutionPolicy', 'Bypass',
        '-Command', 'Start-Sleep -Seconds 30'
    ) -WindowStyle Hidden -PassThru
    Start-Sleep -Milliseconds 250
    if ($child.HasExited) { throw 'child exited before job assignment' }

    $job = [A3JobObjectNative]::CreateJobObject([IntPtr]::Zero, $null)
    if ($job -eq [IntPtr]::Zero) {
        throw "CreateJobObject failed: $([Runtime.InteropServices.Marshal]::GetLastWin32Error())"
    }
    if (-not [A3JobObjectNative]::AssignProcessToJobObject($job, $child.Handle)) {
        throw "AssignProcessToJobObject failed: $([Runtime.InteropServices.Marshal]::GetLastWin32Error())"
    }

    $before = [A3JobObjectNative]::ActiveCount($job)
    if ($before -ne 1) { throw "expected one active job process, observed $before" }
    Write-Output "JOB_ACTIVE_COUNT_BEFORE=$before"

    if (-not [A3JobObjectNative]::TerminateJobObject($job, 0xA304)) {
        throw "TerminateJobObject failed: $([Runtime.InteropServices.Marshal]::GetLastWin32Error())"
    }
    if (-not $child.WaitForExit(5000)) { throw 'job child did not terminate within 5 seconds' }
    $after = [A3JobObjectNative]::ActiveCount($job)
    if ($after -ne 0) { throw "expected zero active job processes after termination, observed $after" }
    Write-Output "JOB_ACTIVE_COUNT_AFTER=$after"

    $outerAlive = [bool](Get-Process -Id $PID -ErrorAction SilentlyContinue)
    if (-not $outerAlive) { throw 'outer controller is not alive' }
    $outerLock.WriteByte(0x41)
    $outerLock.Flush()
    Write-Output 'OUTER_ALIVE=YES'
    Write-Output 'LOCK_SURVIVES_JOB_KILL=YES'
    exit 0
}
catch {
    Write-Output "JOB_OBJECT_POSITIVE_CONTROL_FAILED: $($_.Exception.Message)"
    exit 1
}
finally {
    if ($null -ne $outerLock) { $outerLock.Dispose() }
    if ($job -ne [IntPtr]::Zero) { [void][A3JobObjectNative]::CloseHandle($job) }
    if ($null -ne $child) {
        try {
            if (-not $child.HasExited) { Stop-Process -Id $child.Id -Force -ErrorAction SilentlyContinue }
            $child.Dispose()
        } catch { }
    }
    Remove-Item -LiteralPath $lockPath -Force -ErrorAction SilentlyContinue
}
