# ──────────────────────────────────────────────────
# Meddash Daily Auto-Commit Script
# Runs via Windows Task Scheduler once per day.
# Commits all tracked changes and pushes to GitHub.
# ──────────────────────────────────────────────────

$RepoPath = "C:\Users\email\.gemini\antigravity"
$LogFile  = "$RepoPath\Meddash_organized_backend\07_DevOps_Observability\git_autocommit.log"

# Timestamp
$ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

# Navigate to repo
Set-Location $RepoPath

# Check if there are changes
$status = git status --porcelain
if ($status) {
    git add .
    $msg = "Auto-backup: $ts"
    git commit -m $msg
    git push origin main

    "$ts | COMMITTED | $msg" | Out-File -Append $LogFile
    Write-Output "[$ts] Changes committed and pushed."
} else {
    "$ts | NO CHANGES | Skipped" | Out-File -Append $LogFile
    Write-Output "[$ts] No changes detected. Skipping."
}
