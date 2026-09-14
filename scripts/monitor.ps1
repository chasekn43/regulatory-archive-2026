# Interactive Monitor for Continuous Search Loop
Clear-Host
$logPath = "c:\Users\Charwiz43\.gemini\antigravity\scratch\Affirm\regulatory-archive-2026\search_continuous.log"

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "   KINSLOW GRC SEARCH SIMULATOR LIVE MONITOR" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Log File: $logPath" -ForegroundColor Gray
Write-Host "Press Ctrl+C to exit.`n" -ForegroundColor DarkGray

if (-not (Test-Path $logPath)) {
    Write-Host "Error: Log file not found at $logPath" -ForegroundColor Red
    exit
}

# Live monitoring loop
try {
    # Check if python is running
    $processes = Get-Process -Name python -ErrorAction SilentlyContinue
    if ($processes) {
        Write-Host "Python Search Loop Process: RUNNING (PID: $($processes[0].Id))" -ForegroundColor Green
    } else {
        Write-Host "Python Search Loop Process: NOT RUNNING" -ForegroundColor Yellow
    }
    
    Write-Host "`nTailing last 15 entries (waiting for new entries)...`n" -ForegroundColor Gray
    
    # Tail the log file directly
    Get-Content -Path $logPath -Wait -Tail 15
}
catch {
    Write-Host "`nMonitoring stopped." -ForegroundColor Yellow
}
