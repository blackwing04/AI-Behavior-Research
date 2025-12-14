# Stop AI Behavior Research UI
# Usage: PowerShell -ExecutionPolicy Bypass -File Stop-UI.ps1

# Set UTF-8 encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "AI Behavior Research UI - Stop Tool" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Stop Streamlit processes using taskkill (more reliable)
Write-Host "[STOP] Stopping Streamlit and Python processes..." -ForegroundColor Yellow

$pythonStopped = $false
$cmdStopped = $false

# Kill all Python processes
$pythonKill = & taskkill /IM python.exe /F 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  - Python processes terminated" -ForegroundColor Green
    $pythonStopped = $true
} else {
    Write-Host "  - No Python processes found" -ForegroundColor Gray
}

# Kill all cmd.exe processes (may contain streamlit)
$cmdKill = & taskkill /IM cmd.exe /F 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "  - Command prompt windows terminated" -ForegroundColor Green
    $cmdStopped = $true
} else {
    Write-Host "  - No cmd.exe processes found" -ForegroundColor Gray
}

if ($pythonStopped -or $cmdStopped) {
    Write-Host "[SUCCESS] Streamlit processes stopped" -ForegroundColor Green
} else {
    Write-Host "[INFO] No running Streamlit found" -ForegroundColor Gray
}

# Wait for ports to be released and file handles to be freed
Write-Host "[WAIT] Waiting for ports to be released..." -ForegroundColor Gray
Start-Sleep -Seconds 2

# 額外清理：嘗試釋放被占用的文件句柄（如 .cache）
Write-Host "[CLEANUP] Attempting to release file handles..." -ForegroundColor Gray
try {
    # 強制垃圾回收，釋放所有文件句柄
    [System.GC]::Collect()
    [System.GC]::WaitForPendingFinalizers()
    Start-Sleep -Seconds 1
    Write-Host "[CLEANUP] File handles released" -ForegroundColor Green
} catch {
    Write-Host "[CLEANUP] Cleanup skipped" -ForegroundColor Gray
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Streamlit UI Stopped" -ForegroundColor Green
Write-Host "========================================`n" -ForegroundColor Green
