<#
schedule_cycle.ps1 — make the loop turn without a human (AN-CYCLE-SCHEDULE, s097)

THE PROBLEM THIS CLOSES. The analysis cycle runs every algorithm in dependency order, and
it runs only when somebody remembers to type the command. "On demand" is a euphemism for
"never" once a session ends — which is the exact hole the cycle itself was built to close,
left open one level up.

WHY THESE CADENCES. They are not preferences; each is set by what decays:

  DAILY 06:00   accumulate_logs.py
                the system PURGES audit, job, dump and syslog history in 7-120 days. A day
                not captured is gone permanently and cannot be back-filled at any price.
                This is the only task here whose value is DESTROYED BY DELAY.

  WEEKLY Sun    run_analysis_cycle.py
                the algorithms are cheap against the pre-aggregate (~15 min) and their
                inputs move weekly at most. Running it daily would burn I/O to re-derive
                the same answer; running it monthly lets the frontier drift unwatched.

  MONTHLY 1st   extract_write_channel_logs.py
                APQI sessions are purged, so batch-input evidence has a shelf life. The
                HTTP surface barely moves and rides along.

WHAT THIS SCRIPT DOES NOT DO. It does not extract from SAP on a schedule beyond the log
accumulator: extraction depends on a VPN and on someone deciding it is time, and a
scheduled task that silently fails to connect would be worse than no task, because the
absence of new rows reads as "nothing happened".

REGISTERING A SCHEDULED TASK CHANGES SYSTEM CONFIGURATION, so this script is not run
automatically. Run it yourself, from an elevated PowerShell:

    powershell -ExecutionPolicy Bypass -File scripts\schedule_cycle.ps1

Remove them again with:  Unregister-ScheduledTask -TaskName "SAP-Brain-*" -Confirm:$false
#>

$repo = Split-Path -Parent $PSScriptRoot
$py = (Get-Command python).Source
if (-not $py) { Write-Error "python not on PATH"; exit 1 }

function New-BrainTask {
    param($Name, $Script, $Trigger, $Why)
    $action = New-ScheduledTaskAction -Execute $py -Argument $Script -WorkingDirectory $repo
    # RunOnlyIfNetworkAvailable is deliberately NOT set: these read local files, and a task
    # that skips itself quietly is how a loop stops turning without anyone deciding it should.
    $settings = New-ScheduledTaskSettingsSet -StartWhenAvailable `
        -DontStopIfGoingOnBatteries -AllowStartIfOnBatteries `
        -ExecutionTimeLimit (New-TimeSpan -Hours 4)
    Register-ScheduledTask -TaskName $Name -Action $action -Trigger $Trigger `
        -Settings $settings -Description $Why -Force | Out-Null
    Write-Host "  registered  $Name"
    Write-Host "              $Why"
}

Write-Host "Registering the loop against $repo`n"

New-BrainTask -Name "SAP-Brain-Accumulate-Logs" `
    -Script "Zagentexecution\sap_data_extraction\scripts\accumulate_logs.py" `
    -Trigger (New-ScheduledTaskTrigger -Daily -At 6am) `
    -Why "DAILY. The system purges audit/job/dump history in 7-120 days. A day not captured is gone permanently - the only task here whose value is destroyed by delay."

New-BrainTask -Name "SAP-Brain-Analysis-Cycle" `
    -Script "brain_v2\methods\run_analysis_cycle.py" `
    -Trigger (New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At 3am) `
    -Why "WEEKLY. Every algorithm in dependency order against the pre-aggregate (~15 min). Inputs move weekly at most; daily would re-derive the same answer, monthly lets the frontier drift unwatched."

New-BrainTask -Name "SAP-Brain-Write-Channels" `
    -Script "Zagentexecution\sap_data_extraction\scripts\extract_write_channel_logs.py" `
    -Trigger (New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday -At 4am) `
    -Why "MONTHLY in effect. APQI batch-input sessions are purged, so that evidence has a shelf life. Needs the SAP connection - check its history if the row counts stop moving."

Write-Host "`nDone. Verify with:  Get-ScheduledTask -TaskName 'SAP-Brain-*' | Format-Table TaskName,State"
Write-Host "A scheduled task that FAILS SILENTLY is worse than none: check LastTaskResult"
Write-Host "with  Get-ScheduledTaskInfo -TaskName 'SAP-Brain-Analysis-Cycle'"
