# Start AI Behavior Research UI
# Usage: PowerShell -ExecutionPolicy Bypass -File Start-UI.ps1

param(
    [switch]$OpenBrowser = $true,
    [int]$Port = 8501
)

# Set UTF-8 encoding
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "AI Behavior Research UI - Start Tool" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# Get project root directory
# $MyInvocation.MyCommand.Path = H:\AI-Behavior-Research\scripts\ui\Start-UI.ps1
# Split-Path -Parent twice gets to H:\AI-Behavior-Research
$scriptDir = Split-Path -Parent (Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path))

# Find conda automatically
Write-Host "[SEARCH] Looking for conda..." -ForegroundColor Yellow

$condaPath = $null
$condaPaths = @(
    "$env:USERPROFILE\miniconda3",
    "$env:USERPROFILE\anaconda3",
    "$env:USERPROFILE\anaconda",
    "C:\miniconda3",
    "C:\anaconda3",
    "C:\anaconda"
)

foreach ($path in $condaPaths) {
    if (Test-Path "$path\Scripts\activate.bat") {
        $condaPath = $path
        Write-Host "[FOUND] Conda location: $condaPath" -ForegroundColor Green
        break
    }
}

if (-not $condaPath) {
    Write-Host "[ERROR] Conda not found" -ForegroundColor Red
    Write-Host "`nSolutions:" -ForegroundColor Yellow
    Write-Host "1. Download and install Miniconda from:" -ForegroundColor Gray
    Write-Host "   https://docs.conda.io/projects/miniconda/en/latest/" -ForegroundColor Gray
    Write-Host "2. Restart PowerShell after installation" -ForegroundColor Gray
    Write-Host "3. Run this script again" -ForegroundColor Gray
    Start-Sleep -Seconds 5
    exit 1
}

# Add conda to PATH (no need for init)
Write-Host "[INIT] Setting up conda environment..." -ForegroundColor Yellow
$env:PATH = "$condaPath\Scripts;$condaPath;$env:PATH"
$env:CONDA_PREFIX = $condaPath

# Check if environment exists
Write-Host "[CHECK] Checking ai_behavior environment..." -ForegroundColor Yellow
$envs = & "$condaPath\Scripts\conda.exe" env list 2>$null | Select-String "ai_behavior"

if (-not $envs) {
    Write-Host "[ERROR] ai_behavior environment does not exist" -ForegroundColor Red
    Write-Host "`nPlease create it first:" -ForegroundColor Yellow
    Write-Host "  conda create -n ai_behavior python=3.10" -ForegroundColor Gray
    Start-Sleep -Seconds 5
    exit 1
}

Write-Host "[FOUND] ai_behavior environment" -ForegroundColor Green

# Function to check if port is available
function Is-PortAvailable {
    param([int]$Port)
    try {
        $connection = Test-NetConnection -ComputerName 127.0.0.1 -Port $Port -WarningAction SilentlyContinue
        return -not $connection.TcpTestSucceeded
    } catch {
        return $true
    }
}

# Function to find available port
function Find-AvailablePort {
    param([int]$StartPort = 8501, [int]$EndPort = 8510)
    
    Write-Host "[CHECK] Searching for available port (8501-8510)..." -ForegroundColor Yellow
    
    for ($port = $StartPort; $port -le $EndPort; $port++) {
        if (Is-PortAvailable -Port $port) {
            Write-Host "[FOUND] Port $port is available" -ForegroundColor Green
            return $port
        } else {
            Write-Host "  - Port $port in use" -ForegroundColor Gray
        }
    }
    
    # All ports in range are in use, force kill and use default port
    Write-Host "[WARN] All ports 8501-8510 in use, forcing cleanup..." -ForegroundColor Yellow
    return $EndPort
}

# 先強制清理現有的 Python/Streamlit 進程（重要！要在檢查埠之前）
Write-Host "[CHECK] Cleaning up any existing Streamlit processes..." -ForegroundColor Yellow

# Use taskkill for more reliable termination
$pythonKill = & taskkill /IM python.exe /F 2>&1 | Out-Null
$cmdKill = & taskkill /IM cmd.exe /F 2>&1 | Out-Null

Write-Host "[WAIT] Waiting for port to be released..." -ForegroundColor Gray
Start-Sleep -Seconds 3

# 再檢查可用埠（此時舊進程已被清理）
$AvailablePort = Find-AvailablePort -StartPort 8501 -EndPort 8510

# 額外等待，確保端口完全釋放
Start-Sleep -Seconds 1

# If no port available, use default and force it
$Port = $AvailablePort
if ($Port -eq 8510) {
    Write-Host "[FORCE] Forcing cleanup of port 8510..." -ForegroundColor Yellow
    $process = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue | Where-Object {$_.State -eq "Listen"}
    if ($process) {
        Stop-Process -Id $process.OwningProcess -Force -ErrorAction SilentlyContinue
        Write-Host "[FORCE] Killed process on port $Port (PID: $($process.OwningProcess))" -ForegroundColor Yellow
        Start-Sleep -Seconds 2
    }
}

# Start UI
Write-Host "[START] Starting Streamlit UI..." -ForegroundColor Green
Write-Host "Project directory: $scriptDir" -ForegroundColor Gray
Write-Host ""
Write-Host "[NOTE] First-time startup note:" -ForegroundColor Yellow
Write-Host "   The UI may take 30-60 seconds to load on first launch." -ForegroundColor Yellow
Write-Host "   Please be patient. Subsequent launches will be faster." -ForegroundColor Yellow
Write-Host ""

try {
    # Set environment variables
    $env:STREAMLIT_SERVER_PORT = $AvailablePort
    $env:STREAMLIT_LOGGER_LEVEL = "warning"
    $env:STREAMLIT_SERVER_HEADLESS = "false"
    
    # Activate environment and start Streamlit
    Write-Host "[START] Starting Streamlit in separate window on port $AvailablePort..." -ForegroundColor Green
    
    # Start Streamlit in a new window that stays open
    # Use absolute path to ui_app.py to avoid path issues
    $uiAppPath = "$scriptDir\scripts\ui\ui_app.py"
    $streamlitCmd = "cd /d `"$scriptDir`" && $condaPath\Scripts\conda.exe run -n ai_behavior python -m streamlit run `"$uiAppPath`" --server.port $AvailablePort --logger.level=warning --client.showErrorDetails=false"
    
    # Append browser open command inside cmd so only one browser opens
    if ($OpenBrowser) {
        $streamlitCmd += " && start http://localhost:$Port"
    }
    
    $processArgs = @(
        "/k",
        $streamlitCmd
    )
    
    Start-Process -FilePath "cmd.exe" -ArgumentList $processArgs -WindowStyle Normal
    
    Write-Host "[SUCCESS] Streamlit started in new window" -ForegroundColor Green
    Write-Host ""
    
    # Wait for startup
    Write-Host "[WAIT] Initializing Streamlit..." -ForegroundColor Gray
    Start-Sleep -Seconds 3
    
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "UI Started Successfully" -ForegroundColor Green
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Browser: http://localhost:$AvailablePort" -ForegroundColor Cyan
    Write-Host "Using Port: $AvailablePort" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "[STOP METHODS]" -ForegroundColor Yellow
    Write-Host "1. Run: scripts\ui\Stop-UI.ps1" -ForegroundColor Yellow
    Write-Host "2. Run: Stop-UI.bat (in root)" -ForegroundColor Yellow
    Write-Host "3. Task Manager: End python.exe process" -ForegroundColor Yellow
    Write-Host ""
    
} catch {
    Write-Host "[ERROR] Failed to start: $_" -ForegroundColor Red
    exit 1
}
