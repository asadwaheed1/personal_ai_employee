# Setup Windows Task Scheduler for AI Employee
# Run as Administrator: powershell -ExecutionPolicy Bypass -File setup_task_scheduler.ps1

$ErrorActionPreference = "Stop"

# Get paths
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectDir = Split-Path -Parent $scriptDir
$vaultPath = Join-Path $projectDir "ai_employee_vault"

Write-Host "Setting up AI Employee Windows Task Scheduler..." -ForegroundColor Cyan
Write-Host "Project directory: $projectDir" -ForegroundColor Gray
Write-Host "Vault path: $vaultPath" -ForegroundColor Gray
Write-Host ""

# Check if running as Administrator
if (-not ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole] "Administrator")) {
    Write-Host "Error: This script must be run as Administrator" -ForegroundColor Red
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    exit 1
}

# Create log directory
$logDir = Join-Path $vaultPath "Logs"
if (-not (Test-Path $logDir)) {
    New-Item -ItemType Directory -Path $logDir -Force | Out-Null
}

# Get Python path
$pythonPath = (Get-Command python3 -ErrorAction SilentlyContinue).Source
if (-not $pythonPath) {
    $pythonPath = (Get-Command python -ErrorAction SilentlyContinue).Source
}
if (-not $pythonPath) {
    Write-Host "Error: Python not found in PATH" -ForegroundColor Red
    exit 1
}

Write-Host "Python found at: $pythonPath" -ForegroundColor Green
Write-Host ""

# Define tasks
$tasks = @(
    @{
        Name = "AIEmployee_ContentCalendar_Check"
        Description = "Check content calendar for due posts (hourly)"
        Trigger = New-ScheduledTaskTrigger -Daily -At "00:00" -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration (New-TimeSpan -Days 1)
        Action = New-ScheduledTaskAction -Execute $pythonPath -Argument "-m src.orchestrator.skills.create_content_plan '{`"action`": `"check_calendar`"}'" -WorkingDirectory $projectDir
    },
    @{
        Name = "AIEmployee_Linkedin_Post"
        Description = "Daily LinkedIn post at 9:00 AM (weekdays only)"
        Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday -At "09:00"
        Action = New-ScheduledTaskAction -Execute $pythonPath -Argument "-m src.orchestrator.skills.post_linkedin '{`"action`": `"check_calendar`"}'" -WorkingDirectory $projectDir
    },
    @{
        Name = "AIEmployee_Weekly_Content_Plan"
        Description = "Weekly content planning (Sundays at 6:00 PM)"
        Trigger = New-ScheduledTaskTrigger -Weekly -DaysOfWeek Sunday -At "18:00"
        Action = New-ScheduledTaskAction -Execute $pythonPath -Argument "-m src.orchestrator.skills.create_content_plan '{`"num_posts`": 5}'" -WorkingDirectory $projectDir
    },
    @{
        Name = "AIEmployee_Process_Approved"
        Description = "Process approved actions (every 15 minutes)"
        Trigger = New-ScheduledTaskTrigger -Once -At "00:00" -RepetitionInterval (New-TimeSpan -Minutes 15) -RepetitionDuration (New-TimeSpan -Days 3650)
        Action = New-ScheduledTaskAction -Execute $pythonPath -Argument "-m src.orchestrator.skills.process_approved_actions '{`"vault_path`": `"$vaultPath`"}'" -WorkingDirectory $projectDir
    },
    @{
        Name = "AIEmployee_Dashboard_Update"
        Description = "Daily dashboard update at 8:00 AM"
        Trigger = New-ScheduledTaskTrigger -Daily -At "08:00"
        Action = New-ScheduledTaskAction -Execute $pythonPath -Argument "-c `"import sys; sys.path.insert(0, '$projectDir/src/orchestrator/skills'); from update_dashboard import UpdateDashboardSkill; skill = UpdateDashboardSkill('$vaultPath'); skill.execute({'summary': 'Morning dashboard update'})`"" -WorkingDirectory $projectDir
    }
)

# Remove existing AI Employee tasks
Write-Host "Removing existing AI Employee tasks..." -ForegroundColor Yellow
Get-ScheduledTask | Where-Object { $_.TaskName -like "AIEmployee_*" } | Unregister-ScheduledTask -Confirm:$false -ErrorAction SilentlyContinue

# Create new tasks
Write-Host "Creating AI Employee tasks..." -ForegroundColor Green
Write-Host ""

foreach ($task in $tasks) {
    try {
        Register-ScheduledTask `
            -TaskName $task.Name `
            -Description $task.Description `
            -Trigger $task.Trigger `
            -Action $task.Action `
            -Settings (New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable) `
            -Force | Out-Null

        Write-Host "✓ Created: $($task.Name)" -ForegroundColor Green
        Write-Host "  $($task.Description)" -ForegroundColor Gray
    }
    catch {
        Write-Host "✗ Failed: $($task.Name)" -ForegroundColor Red
        Write-Host "  Error: $_" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "Task Scheduler setup complete!" -ForegroundColor Green
Write-Host ""
Write-Host "To view tasks, open Task Scheduler and look for tasks starting with 'AIEmployee_'" -ForegroundColor Cyan
Write-Host "Or run: Get-ScheduledTask | Where-Object { `$_.TaskName -like 'AIEmployee_*' }" -ForegroundColor Gray
Write-Host ""
Write-Host "Logs will be written to: $logDir" -ForegroundColor Gray
