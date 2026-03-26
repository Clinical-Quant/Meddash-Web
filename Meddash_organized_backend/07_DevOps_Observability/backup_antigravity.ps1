$source = "C:\Users\email\.gemini\antigravity"
$destinationFolder = "G:\My Drive\Meddash_Backups" 
$tempFolder = Join-Path $env:TEMP "Antigravity_Backup_Temp"
$notifierScript = "C:\Users\email\.gemini\antigravity\Meddash_organized_backend\07_DevOps_Observability\telegram_notifier.py"

if (-not (Test-Path $destinationFolder)) {
    New-Item -ItemType Directory -Force -Path $destinationFolder | Out-Null
}

$dateStamp = Get-Date -Format "yyyy-MM-dd_HH-mm"
$destinationArchive = Join-Path -Path $destinationFolder -ChildPath "Antigravity_Backup_$dateStamp.zip"

try {
    Write-Host "Creating robust snapshot... (bypassing active file locks)"
    if (Test-Path $tempFolder) { Remove-Item -Recurse -Force $tempFolder }

    # Use robust copy to bypass any SQLite files or text logs that are actively locked by AI agents
    $robocopyArgs = @($source, $tempFolder, "/E", "/COPY:DAT", "/R:0", "/W:0", "/NFL", "/NDL", "/NJH", "/NJS", "/nc", "/ns", "/np")
    & robocopy @robocopyArgs | Out-Null

    Write-Host "Compressing snapshot: $destinationArchive"
    Compress-Archive -Path $tempFolder -DestinationPath $destinationArchive -Force

    Write-Host "Cleaning up temporary snapshot files..."
    Remove-Item -Recurse -Force $tempFolder

    Write-Host "Backup complete. Cleaning up old backups..."
    $backups = Get-ChildItem -Path $destinationFolder -Filter "Antigravity_Backup_*.zip" | Sort-Object CreationTime -Descending
    if ($backups.Count -gt 3) {
        $backups[3..($backups.Count - 1)] | Remove-Item -Force
        Write-Host "Cleaned up old backups. Retained the latest 3."
    }
    else {
        Write-Host "Total backups is $($backups.Count), no cleanup needed."
    }

    # Get the final ZIP file size for the success message
    $sizeInMB = [math]::Round((Get-Item $destinationArchive).Length / 1MB, 1)
    $fileName = Split-Path $destinationArchive -Leaf

    # Send SUCCESS alert to Telegram
    $msg = "Backup Complete%0A%0AFile: ${fileName}%0ASize: ${sizeInMB} MB%0AVault: Google Drive (Meddash_Backups)%0A%0AEcosystem is safe."
    python $notifierScript --message $msg --level success

}
catch {
    # Send FAILURE alert to Telegram
    $errMsg = "BACKUP FAILED%0A%0AError: $($_.Exception.Message)%0A%0AManual intervention required."
    python $notifierScript --message $errMsg --level error
    Write-Host "ERROR: Backup failed. $($_.Exception.Message)"
}
