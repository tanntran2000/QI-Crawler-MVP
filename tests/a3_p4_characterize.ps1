param([Parameter(Mandatory)][string]$Root)

$ErrorActionPreference='Stop'
$repo=(Resolve-Path -LiteralPath (Join-Path $PSScriptRoot '..')).Path
. (Join-Path $repo 'tools\release\a3_job_object.ps1') -Mode Library
. (Join-Path $repo 'tools\release\a3_native_lineage.ps1')
$probeSource=Get-Content -Raw -LiteralPath (Join-Path $repo 'tools\release\a3_probe_windows.ps1')
$tokens=$null;$parseErrors=$null
$probeAst=[Management.Automation.Language.Parser]::ParseInput($probeSource,[ref]$tokens,[ref]$parseErrors)
if(@($parseErrors).Count -ne 0){throw 'P4_CHARACTERIZATION_PROBE_PARSE_FAILED'}
$treeFunction=@($probeAst.FindAll({param($n) $n -is [Management.Automation.Language.FunctionDefinitionAst] -and $n.Name -eq 'Get-ProcessTreeEvidence'},$true))
if($treeFunction.Count -ne 1){throw 'P4_CHARACTERIZATION_TREE_FUNCTION_MISSING'}
. ([scriptblock]::Create($treeFunction[0].Extent.Text))
$python=(Resolve-Path -LiteralPath (Join-Path $repo '.venv\Scripts\python.exe')).Path
$target=(Resolve-Path -LiteralPath (Join-Path $repo 'tests\a3_p4_route_target.py')).Path
$ps51='C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe'
$Root=[IO.Path]::GetFullPath($Root)
New-Item -ItemType Directory -Path $Root -Force | Out-Null

function Wait-PidFile([string]$Path) {
    $deadline=(Get-Date).AddSeconds(10)
    while((Get-Date) -lt $deadline) {
        if(Test-Path -LiteralPath $Path -PathType Leaf) { return [int](Get-Content -LiteralPath $Path -Raw) }
        Start-Sleep -Milliseconds 50
    }
    throw "PID_FILE_TIMEOUT: $Path"
}

function Run-Case([string]$Kind) {
    $caseRoot=Join-Path $Root $Kind
    New-Item -ItemType Directory -Path $caseRoot -Force | Out-Null
    $pidFile=Join-Path $caseRoot 'child.pid'
    $session=$null
    if($Kind -eq 'EXE' -or $Kind -eq 'GRANDCHILD') {
        $mode=if($Kind -eq 'GRANDCHILD'){'chain'}else{'spawn'}
        $session=Start-A3ContainedRoute -Kind EXE -Artifact $python -Arguments @($target,'--mode',$mode,'--pid-out',$pidFile) -WorkingDirectory $caseRoot
    } elseif($Kind -eq 'CMD') {
        $cmd=Join-Path $caseRoot 'route with spaces.cmd'
        $line='@echo off' + "`r`n" + 'start "" "' + $python + '" "' + $target + '" --mode spawn --pid-out "' + $pidFile + '"' + "`r`n"
        [IO.File]::WriteAllText($cmd,$line)
        $session=Start-A3ContainedRoute -Kind CMD -Artifact $cmd -WorkingDirectory $caseRoot
    } else {
        $lnk=Join-Path $caseRoot 'route shortcut.lnk'
        $shell=New-Object -ComObject WScript.Shell
        $shortcut=$shell.CreateShortcut($lnk)
        $shortcut.TargetPath=$python
        $shortcut.Arguments='"' + $target + '" --mode spawn --pid-out "' + $pidFile + '"'
        $shortcut.WorkingDirectory=$caseRoot
        $shortcut.Save()
        $session=Start-A3ContainedRoute -Kind SHORTCUT -Artifact $lnk -WorkingDirectory $caseRoot
    }
    try {
        $child=Wait-PidFile $pidFile
        Start-Sleep -Milliseconds 200
        $members=@(Get-A3JobProcessIds -Session $session)
        $nativeLineage=Get-ProcessTreeEvidence @($session.ProcessId)
        $active=Get-A3JobActiveCount -Session $session
        $parentFile=$pidFile.Replace('.pid','.parent')
        $parentPid=if(Test-Path -LiteralPath $parentFile){[int](Get-Content -LiteralPath $parentFile -Raw)}else{$null}
        $result=[ordered]@{
            route=$Kind
            launcher_pid=$session.ProcessId
            target_parent_pid=$parentPid
            surviving_child_pid=$child
            child_alive=[bool](Get-Process -Id $child -ErrorAction SilentlyContinue)
            job_active_after_parent_exit=$active
            job_members=$members
            child_in_job=($child -in $members)
            native_lineage_contains_child=($child -in @($nativeLineage.ids))
            native_snapshot_status=$nativeLineage.snapshot_status
            native_tree=$nativeLineage
            breakaway_ok_enabled=$false
            silent_breakaway_ok_enabled=$false
        }
        $falseZeroRejected=$false
        try { [void](Wait-A3ContainedRouteZero -Session $session -TimeoutMilliseconds 100 -MinimumTotalProcesses 2) }
        catch { $falseZeroRejected=($_.Exception.Message -like 'JOB_ROUTE_ACTIVE_TIMEOUT*') }
        $result.false_zero_rejected_while_child_alive=$falseZeroRejected
        if($active -gt 0) {
            $terminated=Stop-A3ContainedProcess -Session $session
            $result.job_zero_after_termination=($terminated.active_after -eq 0)
        } else { $result.job_zero_after_termination=$true }
        return [pscustomobject]$result
    } finally {
        if($session) { Close-A3ContainedProcess -Session $session }
    }
}

$all=@()
foreach($kind in @('EXE','CMD','SHORTCUT','GRANDCHILD')) {
    try { $all += Run-Case $kind }
    catch { $all += [pscustomobject]@{route=$kind;error=$_.Exception.Message;child_in_job=$false;job_zero_after_termination=$false} }
}
$all | ConvertTo-Json -Depth 8
