# publish-cleanup.ps1
# One-shot cleanup for kinslow-regulatory-archive.org.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File .\publish-cleanup.ps1           # dry-run
#   powershell -ExecutionPolicy Bypass -File .\publish-cleanup.ps1 -Apply    # actually run

[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [switch]$Apply
)

$ErrorActionPreference = 'Stop'

# --- locate git ---
$gitRoot = "C:\Users\Charwiz43\AppData\Local\github-copilot-git-2.53.0-4"
$git = Join-Path $gitRoot "mingw64\bin\git.exe"
if (-not (Test-Path $git)) {
    throw "git.exe not found at $git. Edit this script and set `$gitRoot to your git install path."
}
$env:PATH = (Join-Path $gitRoot "mingw64\bin") + ";" + $env:PATH

# Helper: run git with a single argument string (avoids PS splat issues).
# Usage: Invoke-Git "rev-parse --abbrev-ref HEAD"
function Invoke-Git([string]$ArgString) {
    $output = & $git $ArgString.Split(' ', [System.StringSplitOptions]::RemoveEmptyEntries) 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "git $ArgString failed (exit $LASTEXITCODE):`n" + (($output -join "`n").Substring(0, [Math]::Min(2000, ($output -join "`n").Length)))
    }
    return $output
}

# --- paths to un-track (cached only; files stay on disk) ---
$dirs = @(
    'logs'
    'scratch'
    'downloads_review'
    'new_batch_review'
    '.search_safety'
    '860e342df2f84581f5f630b9f6c4cab1-b965310ab13d3a5295ea0d158e6a8349e0f0df1d'
)
$files = @(
    '.aider.chat.history.md'
    '.aider.input.history'
    '16dcac3abadb4ac695eb0c2fde338139.txt'
    '4366b539c9914619a970e53a2707ec41.txt'
    'fa481ca42fd54303a95cc9e0bb6ec542.txt'
    'BingSiteAuth (2).xml'
    'BingSiteAuth (4).xml'
)
$trackedFilesToAdd = @(
    '.gitignore'
    'robots.txt'
    'index.html'
)

# Helper: count tracked files matching a path
function Count-Tracked([string]$Path) {
    $out = Invoke-Git "ls-files $Path"
    if (-not $out) { return 0 }
    return @($out).Count
}

# --- start ---
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $repoRoot
Write-Host "Repo: $repoRoot" -ForegroundColor Cyan
Write-Host "git : $git" -ForegroundColor Cyan
Write-Host ""

$branch = (Invoke-Git "rev-parse --abbrev-ref HEAD" | Select-Object -First 1).Trim()
Write-Host "On branch: $branch" -ForegroundColor Cyan

$status = Invoke-Git "status --porcelain"
$expectedModified = @(
    ' M .gitignore',
    ' M index.html',
    ' M robots.txt'
) | Sort-Object

$actualModified = @($status | Where-Object { $_ -match '^\s*M\s' }) | Sort-Object
$extra = $actualModified | Where-Object { $expectedModified -notcontains $_ }
$missing = $expectedModified | Where-Object { $actualModified -notcontains $_ }

if ($extra -or $missing) {
    Write-Host ""
    Write-Host "WARNING: uncommitted changes differ from expected." -ForegroundColor Yellow
    if ($extra)   { Write-Host "  Unexpected modified files:" -ForegroundColor Yellow; $extra | ForEach-Object { Write-Host "    $_" } }
    if ($missing) { Write-Host "  Expected-but-missing modified files:" -ForegroundColor Yellow; $missing | ForEach-Object { Write-Host "    $_" } }
    Write-Host ""
    if (-not $Apply) {
        Write-Host "[DRY-RUN] would stop here. Re-run with -Apply to continue anyway." -ForegroundColor Magenta
    } else {
        $ans = Read-Host "Continue anyway? [y/N]"
        if ($ans -ne 'y') { Write-Host "Aborted."; exit 1 }
    }
}

Write-Host ""
Write-Host "=== Will un-track (cached only, files stay on disk) ===" -ForegroundColor Cyan
foreach ($d in $dirs) {
    $n = Count-Tracked $d
    if ($n -gt 0) { Write-Host "  dir : $d  ($n files)" }
    else          { Write-Host "  dir : $d  (none tracked, skip)" }
}
foreach ($f in $files) {
    $n = Count-Tracked $f
    if ($n -gt 0) { Write-Host "  file: $f" }
    else          { Write-Host "  file: $f  (not tracked, skip)" }
}

Write-Host ""
Write-Host "=== Will stage for commit ===" -ForegroundColor Cyan
foreach ($f in $trackedFilesToAdd) { Write-Host "  + $f" }
if ($status | Where-Object { $_ -match '^\s*M\s+sitemap\.xml' }) {
    Write-Host "  + sitemap.xml (modified)"
}

if (-not $Apply) {
    Write-Host ""
    Write-Host "[DRY-RUN] No changes made. Re-run with -Apply to execute." -ForegroundColor Magenta
    Write-Host ""
    Write-Host "After this script pushes, do the following manually:" -ForegroundColor Cyan
    Write-Host "  A. Wait ~5 minutes, then visit in a browser:"
    Write-Host "       https://kinslow-regulatory-archive.org/logs/"
    Write-Host "     (should 404)"
    Write-Host ""
    Write-Host "  B. Google Search Console:"
    Write-Host "       Removals -> New Request -> 'Remove all URLs with this prefix' for each:"
    Write-Host "         https://kinslow-regulatory-archive.org/logs/"
    Write-Host "         https://kinslow-regulatory-archive.org/scratch/"
    Write-Host "         https://kinslow-regulatory-archive.org/bin/"
    Write-Host "         https://kinslow-regulatory-archive.org/bing_test.html"
    Write-Host "         https://kinslow-regulatory-archive.org/ddg_test.html"
    Write-Host "         https://kinslow-regulatory-archive.org/google_test.html"
    Write-Host "         https://kinslow-regulatory-archive.org/google169507de43bc15cc.html"
    Write-Host "       Sitemaps -> resubmit: sitemap.xml"
    Write-Host ""
    Write-Host "  C. Bing Webmaster Tools:"
    Write-Host "       Block URLs -> add each path/URL above"
    Write-Host "       Sitemaps -> resubmit: https://kinslow-regulatory-archive.org/sitemap.xml"
    exit 0
}

Write-Host ""
Write-Host "=== Un-tracking cached files ===" -ForegroundColor Green
foreach ($d in $dirs) {
    if ((Count-Tracked $d) -gt 0) {
        Invoke-Git "rm -r --cached $d" | Out-Null
        Write-Host "  un-tracked dir : $d"
    }
}
foreach ($f in $files) {
    if ((Count-Tracked $f) -gt 0) {
        Invoke-Git "rm --cached `"$f`"" | Out-Null
        Write-Host "  un-tracked file: $f"
    }
}

Write-Host ""
Write-Host "=== Staging tracked files ===" -ForegroundColor Green
foreach ($f in $trackedFilesToAdd) {
    if (Test-Path $f) {
        Invoke-Git "add $f" | Out-Null
        Write-Host "  + $f"
    }
}
if ($status | Where-Object { $_ -match '^\s*M\s+sitemap\.xml' }) {
    Invoke-Git "add sitemap.xml" | Out-Null
    Write-Host "  + sitemap.xml"
}

Write-Host ""
Write-Host "=== Committing ===" -ForegroundColor Green
$msg = "Stop publishing /logs and other internal artifacts; tighten robots.txt; canonicalize home page meta"
Invoke-Git "commit -m `"$msg`"" | Out-Null
Write-Host "  committed: $msg"

Write-Host ""
Write-Host "=== Pushing to origin/$branch ===" -ForegroundColor Green
Invoke-Git "push origin $branch"
Write-Host "  pushed."

Write-Host ""
Write-Host "=== Done. ===" -ForegroundColor Green
Write-Host ""
Write-Host "Now manually:" -ForegroundColor Cyan
Write-Host "  1. Wait 3-5 min, then check https://kinslow-regulatory-archive.org/logs/ in a browser (expect 404)."
Write-Host "  2. Google Search Console -> Removals -> submit prefix removals for /logs/, /scratch/, /bin/, *test.html"
Write-Host "  3. Google Search Console -> Sitemaps -> re-submit sitemap.xml"
Write-Host "  4. Bing Webmaster -> Block URLs -> same paths"
Write-Host "  5. Bing Webmaster -> Sitemaps -> re-submit sitemap.xml"