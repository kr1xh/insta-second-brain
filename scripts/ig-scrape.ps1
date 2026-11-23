# Run, pause and reschedule the scheduled captures (Windows tasks named "insta-second-brain <name>").
# ponytail: Task Scheduler already does scheduling, enabling and run-now; this only names the steps.
#   upgrade path: a Python CLI if the runs ever need to work on macOS/Linux (cron/launchd).
#
#   ig-scrape.ps1 status                  what is on, at what times, next run
#   ig-scrape.ps1 run [name]              run now (default: daily); works while the schedule is off
#   ig-scrape.ps1 stop [name]             stop a run in progress (default: all); progress is kept
#   ig-scrape.ps1 on|off [name]           turn schedules on or off (default: all); "unschedule" = off
#   ig-scrape.ps1 schedule <name> HH:MM [HH:MM ...]   new daily time(s); turns the schedule on
param(
    [Parameter(Position = 0)][string]$Action = 'status',
    [Parameter(Position = 1)][string]$Which = '',
    [Parameter(ValueFromRemainingArguments = $true)][string[]]$Rest = @()
)
trap { Write-Host $_.Exception.Message; exit 1 }

$Prefix = 'insta-second-brain '
$Tasks = [ordered]@{}
Get-ScheduledTask -TaskName "$Prefix*" -ErrorAction SilentlyContinue |
    Sort-Object TaskName | ForEach-Object { $Tasks[$_.TaskName.Substring($Prefix.Length)] = $_.TaskName }
if (-not $Tasks.Count) { throw "No scheduled tasks named '$Prefix<name>'. See docs/sweep.md to create one." }

function Get-Targets([string]$name, [string]$default) {
    if (-not $name) { $name = $default }
    if ($name -eq 'all') { return @($Tasks.Keys) }
    if (-not $Tasks.Contains($name)) { throw "Unknown run '$name'. Known: $(@($Tasks.Keys) -join ', '), all." }
    return @($name)
}

# A disabled task reports State 'Disabled' even mid-run; 0x41301 is Task Scheduler's "currently running".
function Test-Running([string]$k) {
    (Get-ScheduledTask -TaskName $Tasks[$k]).State -eq 'Running' -or
    (Get-ScheduledTaskInfo -TaskName $Tasks[$k]).LastTaskResult -eq 0x41301
}

# Stop-ScheduledTask ends only the process the task started, not the capture/analyse/browser children,
# so find that process by the task's command line and end its whole tree.
function Stop-Tree([string]$k) {
    $a = @((Get-ScheduledTask -TaskName $Tasks[$k]).Actions)[0]
    if ($a.Arguments) {
        Get-CimInstance Win32_Process |
            Where-Object { $_.CommandLine -and $_.CommandLine.Contains($a.Arguments) -and
                           $_.CommandLine.Contains([IO.Path]::GetFileName($a.Execute)) } |
            ForEach-Object { taskkill /PID $_.ProcessId /T /F 2>&1 | Out-Null }
    }
    Stop-ScheduledTask -TaskName $Tasks[$k]
}

function Show-Status {
    foreach ($k in $Tasks.Keys) {
        $t = Get-ScheduledTask -TaskName $Tasks[$k]
        $i = Get-ScheduledTaskInfo -TaskName $Tasks[$k]
        $times = ($t.Triggers | ForEach-Object {
            $fmt = if ($_.CimClass.CimClassName -match 'Weekly') { 'ddd HH:mm' } else { 'HH:mm' }
            ([datetime]$_.StartBoundary).ToString($fmt)
        }) -join ', '
        if (-not $times) { $times = 'none' }
        $next = if (-not $t.Settings.Enabled -or -not $i.NextRunTime) { '-' } else { $i.NextRunTime.ToString('ddd HH:mm') }
        $state = if ($t.Settings.Enabled) { 'ON' } else { 'OFF' }
        if (Test-Running $k) { $state += ' (running now)' }
        '{0,-8} {1,-16} times: {2,-20} next: {3}' -f $k, $state, $times, $next
    }
}

switch ($Action.ToLower()) {
    'status' { }
    { $_ -in 'on', 'off', 'unschedule' } {
        foreach ($k in Get-Targets $Which 'all') {
            if ($Action -eq 'on') { Enable-ScheduledTask -TaskName $Tasks[$k] | Out-Null }
            else { Disable-ScheduledTask -TaskName $Tasks[$k] | Out-Null }
            "${k}: $($Action.ToLower())"
        }
    }
    'run' {
        foreach ($k in Get-Targets $Which 'daily') {
            if (Test-Running $k) { "${k}: already running"; continue }
            # one Instagram run at a time (docs/risk-controls.md)
            $busy = @($Tasks.Keys | Where-Object { $_ -ne $k -and (Test-Running $_) })
            if ($busy) { "${k}: not started, $($busy -join ', ') is running. Wait, or: ig-scrape stop $($busy[0])"; continue }
            $wasOff = -not (Get-ScheduledTask -TaskName $Tasks[$k]).Settings.Enabled
            if ($wasOff) { Enable-ScheduledTask -TaskName $Tasks[$k] | Out-Null }
            Start-ScheduledTask -TaskName $Tasks[$k]
            # the start is asynchronous: wait for it, because disabling a queued start can cancel it
            $deadline = (Get-Date).AddSeconds(15)
            while (-not (Test-Running $k) -and (Get-Date) -lt $deadline) { Start-Sleep -Milliseconds 250 }
            $started = Test-Running $k
            # disabling does not stop a run that has started, so an OFF schedule stays OFF
            if ($wasOff) { Disable-ScheduledTask -TaskName $Tasks[$k] | Out-Null }
            if ($started) { "${k}: started" } else { "${k}: did not start within 15 s; check Task Scheduler" }
        }
    }
    'stop' {
        foreach ($k in Get-Targets $Which 'all') {
            Stop-Tree $k
            "${k}: stopped"
        }
    }
    'schedule' {
        if (-not $Which -or $Which -eq 'all' -or -not $Rest) { throw 'Usage: ig-scrape schedule <name> HH:MM [HH:MM ...]' }
        $k = @(Get-Targets $Which '')[0]
        $triggers = foreach ($at in $Rest) {
            if ($at -notmatch '^([01]?\d|2[0-3]):[0-5]\d$') { throw "Bad time '$at'. Use 24-hour HH:MM, e.g. 08:30 or 21:00." }
            New-ScheduledTaskTrigger -Daily -At $at
        }
        Set-ScheduledTask -TaskName $Tasks[$k] -Trigger $triggers | Out-Null
        Enable-ScheduledTask -TaskName $Tasks[$k] | Out-Null
        "${k}: every day at $($Rest -join ', ')"
    }
    default {
        Get-Content $PSCommandPath | Select-Object -Skip 4 -First 5 | ForEach-Object { $_.TrimStart('# ') }
        exit 1
    }
}
''
Show-Status
