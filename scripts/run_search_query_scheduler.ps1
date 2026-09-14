param(
    [int]$QueriesPerRun = 10,
    [string]$PythonExe = "python",
    [string]$OutputDir = ".\logs\scheduled-runs"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$runner = Join-Path $repoRoot "multi_engine_search_suite.py"
if (-not (Test-Path $runner)) {
    throw "Runner not found: $runner"
}

if (-not (Test-Path $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir -Force | Out-Null
}

$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$outfile = Join-Path $OutputDir "multi-engine-$stamp.json"
$start = Get-Date
Write-Host "[$($start.ToString('s'))] Executing scheduled multi-engine query pass..."

& $PythonExe $runner --iterations 1 --output $outfile
$code = $LASTEXITCODE
$end = Get-Date

if ($code -eq 0) {
    Write-Host "[$($end.ToString('s'))] Success: Saved results to $outfile"
} else {
    Write-Host "[$($end.ToString('s'))] Runner failed with exit code $code"
    exit $code
}
