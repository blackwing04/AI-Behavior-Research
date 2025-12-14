$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "================================================================"
Write-Host "   AI Behavior Research - Miniconda Installation Guide"
Write-Host "================================================================"
Write-Host ""
Write-Host "This script will help you install Miniconda"
Write-Host ""

# Check if conda is already installed
$condaExists = $null -ne (Get-Command conda -ErrorAction SilentlyContinue)

if ($condaExists) {
    Write-Host "[OK] Miniconda is already installed"
    conda --version
    Write-Host ""
    Write-Host "Next step: Run 02_install_dependencies.bat"
    Write-Host ""
    Read-Host "Press Enter to continue"
    exit 0
}

Write-Host "[ERROR] Miniconda not detected"
Write-Host "Opening Miniconda download page..."
Write-Host "Please download Miniconda3 (Python 3.10 or higher)"
Write-Host ""
Write-Host "Download page: https://docs.conda.io/projects/miniconda/en/latest/"
Write-Host ""

# Try to open browser
Start-Process "https://docs.conda.io/projects/miniconda/en/latest/"

Write-Host "Please wait for the page to open, then:"
Write-Host "1. Download Windows 64-bit version"
Write-Host "2. Run the installer"
Write-Host "3. Check 'Add Miniconda to PATH' during installation"
Write-Host "4. After installation, re-run this script"
Write-Host ""
Read-Host "Press Enter after installation is complete"

# Check again
Write-Host ""
Write-Host "Checking for conda..."
Write-Host ""

$condaExists = $null -ne (Get-Command conda -ErrorAction SilentlyContinue)

if ($condaExists) {
    Write-Host "[OK] Miniconda is now installed!"
    conda --version
    Write-Host ""
    Write-Host "Next step: Run 02_install_dependencies.bat"
    Write-Host ""
    Read-Host "Press Enter to continue"
    exit 0
} else {
    Write-Host "[ERROR] Miniconda still not detected"
    Write-Host "Please ensure it is properly installed and added to PATH"
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}
