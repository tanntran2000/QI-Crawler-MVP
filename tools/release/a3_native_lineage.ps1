if (-not ('A3NativeLineage' -as [type])) {
    Add-Type -TypeDefinition @'
using System;
using System.Collections.Generic;
using System.ComponentModel;
using System.Runtime.InteropServices;

public sealed class A3NativeProcessRecord {
    public int pid;
    public int ppid;
    public string native_snapshot_status;
    public string evidence_source;
    public string snapshot_timestamp;
    public string metadata_status;
}

public static class A3NativeLineage {
    private const uint TH32CS_SNAPPROCESS = 0x00000002;
    private const int ERROR_NO_MORE_FILES = 18;

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    private struct ProcessEntry {
        public uint dwSize;
        public uint cntUsage;
        public uint th32ProcessID;
        public UIntPtr th32DefaultHeapID;
        public uint th32ModuleID;
        public uint cntThreads;
        public uint th32ParentProcessID;
        public int pcPriClassBase;
        public uint dwFlags;
        [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 260)]
        public string szExeFile;
    }

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern IntPtr CreateToolhelp32Snapshot(uint flags, uint processId);

    [DllImport("kernel32.dll", EntryPoint = "Process32FirstW", CharSet = CharSet.Unicode, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool Process32First(IntPtr snapshot, ref ProcessEntry entry);

    [DllImport("kernel32.dll", EntryPoint = "Process32NextW", CharSet = CharSet.Unicode, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool Process32Next(IntPtr snapshot, ref ProcessEntry entry);

    [DllImport("kernel32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool CloseHandle(IntPtr handle);

    public static A3NativeProcessRecord[] Capture() {
        IntPtr snapshot = CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0);
        if (snapshot == new IntPtr(-1))
            throw new Win32Exception(Marshal.GetLastWin32Error(), "TOOLHELP32_SNAPSHOT_FAILED");
        try {
            ProcessEntry entry = new ProcessEntry();
            entry.dwSize = (uint)Marshal.SizeOf(typeof(ProcessEntry));
            if (!Process32First(snapshot, ref entry))
                throw new Win32Exception(Marshal.GetLastWin32Error(), "TOOLHELP32_FIRST_FAILED");
            string capturedAt = DateTime.UtcNow.ToString("o");
            List<A3NativeProcessRecord> records = new List<A3NativeProcessRecord>();
            do {
                if (entry.th32ProcessID > int.MaxValue || entry.th32ParentProcessID > int.MaxValue)
                    throw new InvalidOperationException("TOOLHELP32_PID_OUT_OF_RANGE");
                records.Add(new A3NativeProcessRecord {
                    pid = checked((int)entry.th32ProcessID),
                    ppid = checked((int)entry.th32ParentProcessID),
                    native_snapshot_status = "SUCCESS",
                    evidence_source = "TOOLHELP32",
                    snapshot_timestamp = capturedAt,
                    metadata_status = "UNKNOWN"
                });
                if (records.Count > 65536)
                    throw new InvalidOperationException("TOOLHELP32_PROCESS_COUNT_EXCEEDED");
                entry.dwSize = (uint)Marshal.SizeOf(typeof(ProcessEntry));
            } while (Process32Next(snapshot, ref entry));
            int endError = Marshal.GetLastWin32Error();
            if (endError != ERROR_NO_MORE_FILES)
                throw new Win32Exception(endError, "TOOLHELP32_ENUMERATION_FAILED");
            return records.ToArray();
        } finally {
            if (!CloseHandle(snapshot))
                throw new Win32Exception(Marshal.GetLastWin32Error(), "TOOLHELP32_CLOSE_FAILED");
        }
    }
}
'@
}

function Get-A3NativeProcessSnapshot {
    $records = [A3NativeLineage]::Capture()
    if (@($records).Count -eq 0) { throw 'TOOLHELP32_EMPTY_SYSTEM_SNAPSHOT' }
    return [pscustomobject]@{
        status = 'SUCCESS'
        evidence_source = 'TOOLHELP32'
        snapshot_timestamp = $records[0].snapshot_timestamp
        processes = @($records)
    }
}
