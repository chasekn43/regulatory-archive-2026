# Kinslow GRC & SEO Operations Dashboard
# Consolidated console interface for all integrated search visibility tools.

$archivePath = "c:\Users\Charwiz43\.gemini\antigravity\scratch\Affirm\regulatory-archive-2026"
$indexnowPath = "c:\Users\Charwiz43\.gemini\antigravity\scratch\Affirm\indexnow"
$logPath = "$archivePath\search_continuous.log"

function Show-Header {
    Clear-Host
    Write-Host "==========================================================" -ForegroundColor Cyan
    Write-Host "        KINSLOW GRC & SEO CAMPAIGN CONTROL PORTAL" -ForegroundColor Cyan
    Write-Host "==========================================================" -ForegroundColor Cyan
}

function Get-SimulatorProcess {
    # Query WMI to find the exact python process running the search simulator script
    $proc = Get-CimInstance -Query "SELECT * FROM Win32_Process WHERE Name = 'python.exe' AND CommandLine LIKE '%run_continuous_search.py%'" -ErrorAction SilentlyContinue
    return $proc
}

function Start-Simulator {
    $proc = Get-SimulatorProcess
    if ($proc) {
        Write-Host "Stopping existing simulator process (PID: $($proc.ProcessId))..." -ForegroundColor Yellow
        Stop-Process -Id $proc.ProcessId -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 1
    }
    
    Write-Host "Starting continuous search simulator in the background..." -ForegroundColor Green
    Start-Process -FilePath "python" -ArgumentList "run_continuous_search.py" -WorkingDirectory $archivePath -WindowStyle Hidden
    Start-Sleep -Seconds 2
    
    $newProc = Get-SimulatorProcess
    if ($newProc) {
        Write-Host "Simulator successfully launched! (PID: $($newProc.ProcessId))" -ForegroundColor Green
    } else {
        Write-Host "Warning: Process launched but could not verify running status. Check logs." -ForegroundColor Red
    }
    Read-Host "`nPress Enter to return to main menu"
}

function Stop-Simulator {
    $proc = Get-SimulatorProcess
    if ($proc) {
        Write-Host "Stopping simulator process (PID: $($proc.ProcessId))..." -ForegroundColor Yellow
        Stop-Process -Id $proc.ProcessId -Force
        Write-Host "Simulator stopped." -ForegroundColor Green
    } else {
        Write-Host "Simulator is not currently running." -ForegroundColor Gray
    }
    Read-Host "`nPress Enter to return to main menu"
}

function Tail-Logs {
    Show-Header
    Write-Host "Tailing simulator logs live. Press Ctrl+C to stop.`n" -ForegroundColor Gray
    if (Test-Path $logPath) {
        try {
            Get-Content -Path $logPath -Wait -Tail 20
        }
        catch {
            Write-Host "`nStopped log tail." -ForegroundColor Gray
        }
    } else {
        Write-Host "Error: Log file not found at $logPath" -ForegroundColor Red
        Read-Host "`nPress Enter to return to main menu"
    }
}

function Run-RankCheck {
    Show-Header
    Write-Host "Executing SEO Rank Check Audit across DuckDuckGo, Bing, Yahoo, and Google..." -ForegroundColor Green
    Write-Host "This will take about 60-90 seconds. Please wait...`n" -ForegroundColor Gray
    
    Push-Location $archivePath
    try {
        python check_rankings.py
        Write-Host "`nRank check complete! Running parser..." -ForegroundColor Green
        python analyze_audit.py
    }
    catch {
        Write-Host "Error running python scripts: $_" -ForegroundColor Red
    }
    Pop-Location
    Read-Host "`nPress Enter to return to main menu"
}

function Submit-IndexNow {
    Show-Header
    Write-Host "Executing sitemap diff parsing and dispatching IndexNow broadcast..." -ForegroundColor Green
    
    if (-not $env:INDEXNOW_KEY) {
        $env:INDEXNOW_KEY = "4366b539c9914619a970e53a2707ec41"
    }
    
    Push-Location $indexnowPath
    try {
        node scripts/indexnow-submit.mjs
    }
    catch {
        Write-Host "Error running Node submit script: $_" -ForegroundColor Red
    }
    Pop-Location
    Read-Host "`nPress Enter to return to main menu"
}

function View-Metrics {
    Show-Header
    Write-Host "Parsing latest search visibility metrics..." -ForegroundColor Green
    Push-Location $archivePath
    try {
        python analyze_audit.py
    }
    catch {
        Write-Host "Error parsing audit logs: $_" -ForegroundColor Red
    }
    Pop-Location
    Read-Host "`nPress Enter to return to main menu"
}

# Main Application Menu Loop
while ($true) {
    Show-Header
    $proc = Get-SimulatorProcess
    if ($proc) {
        Write-Host "Search Simulator: RUNNING (PID: $($proc.ProcessId))" -ForegroundColor Green
    } else {
        Write-Host "Search Simulator: STOPPED" -ForegroundColor Red
    }
    Write-Host "Key Location:     https://chasekn43.github.io/regulatory-archive-2026/4366b539c9914619a970e53a2707ec41.txt" -ForegroundColor Gray
    Write-Host "==========================================================" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "  [1] Start / Restart Search Simulator (Background Daemon)" -ForegroundColor Yellow
    Write-Host "  [2] Stop Search Simulator" -ForegroundColor Yellow
    Write-Host "  [3] View Search Simulator Logs (Live Stream)" -ForegroundColor Yellow
    Write-Host "  [4] Run Fresh Rank Audit & Analyze Results" -ForegroundColor Yellow
    Write-Host "  [5] Trigger IndexNow URL Broadcast" -ForegroundColor Yellow
    Write-Host "  [6] View Search Metrics & Stats Summary" -ForegroundColor Yellow
    Write-Host "  [7] Exit" -ForegroundColor White
    Write-Host ""
    
    $selection = Read-Host "Select operational task (1-7)"
    
    switch ($selection) {
        "1" { Start-Simulator }
        "2" { Stop-Simulator }
        "3" { Tail-Logs }
        "4" { Run-RankCheck }
        "5" { Submit-IndexNow }
        "6" { View-Metrics }
        "7" { Clear-Host; break }
        default { 
            Write-Host "Invalid option. Please choose 1 to 7." -ForegroundColor Red
            Start-Sleep -Seconds 1
        }
    }
}
