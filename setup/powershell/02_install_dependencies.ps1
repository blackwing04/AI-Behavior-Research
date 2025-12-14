$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "================================================================"
Write-Host "   AI Behavior Research - Install Dependencies"
Write-Host "================================================================"
Write-Host ""

# Check conda installation
$condaExists = $null -ne (Get-Command conda -ErrorAction SilentlyContinue)

if (-not $condaExists) {
    Write-Host "[ERROR] Conda not found"
    Write-Host "Please run 01_install_miniconda.bat first"
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "Checking conda installation..."
Write-Host "[OK] Conda found"
Write-Host ""

# Accept ToS
Write-Host "Accepting Anaconda Terms of Service..."
Write-Host "(This may take a moment, please wait...)"
Write-Host ""

conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main 2>$null
Write-Host "[OK] Accepted main repository terms"

conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r 2>$null
Write-Host "[OK] Accepted R repository terms"

conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/msys2 2>$null
Write-Host "[OK] Accepted MSYS2 repository terms"

Write-Host ""
Write-Host "Checking/Creating environment ai_behavior..."
Write-Host ""

# Create environment if it doesn't exist (Python 3.13 to match downloaded wheels)
conda create -n ai_behavior python=3.13 -y

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "[ERROR] Failed to create/access environment ai_behavior"
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "[OK] Environment ready"
Write-Host ""
Write-Host "Preparing to install all dependencies..."
Write-Host ""

# Step 1: Upgrade pip (using conda run to ensure environment is used)
Write-Host ""
Write-Host "[1/4] Upgrading pip..."
conda run -n ai_behavior python -m pip install --upgrade pip

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] pip upgrade failed"
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[OK] pip upgraded successfully"

# Step 2: Install PyTorch
Write-Host ""
Write-Host "[2/4] Installing PyTorch (CUDA 11.8)..."
Write-Host "This may take 5-10 minutes, please wait..."
Write-Host ""

conda run -n ai_behavior pip install torch==2.7.1 torchvision==0.22.1 torchaudio==2.7.1 --index-url https://download.pytorch.org/whl/cu118

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] PyTorch installation failed"
    Write-Host ""
    Write-Host "Possible reasons:"
    Write-Host "- Network connection issue"
    Write-Host "- Insufficient disk space"
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[OK] PyTorch installed successfully"

# Step 3: Install core dependencies
Write-Host ""
Write-Host "[3/4] Installing core dependencies..."
Write-Host ""

$packages = @(
    "transformers==4.57.1",
    "peft==0.18.0",
    "datasets==4.4.1",
    "accelerate==1.11.0",
    "bitsandbytes==0.48.2",
    "safetensors",
    "streamlit",
    "pandas",
    "openpyxl",
    "huggingface-hub[hf_xet]"
)

$failed_packages = @()

foreach ($pkg in $packages) {
    Write-Host "Installing $pkg..."
    conda run -n ai_behavior pip install "$pkg" --quiet
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[ERROR] Failed to install $pkg"
        $failed_packages += $pkg
    } else {
        Write-Host "[OK] Installed $pkg"
    }
}

if ($failed_packages.Count -gt 0) {
    Write-Host ""
    Write-Host "[ERROR] Failed to install these packages:"
    foreach ($pkg in $failed_packages) {
        Write-Host "  - $pkg"
    }
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host "[OK] All dependencies installed successfully"

# Step 4: Verify installation
Write-Host ""
Write-Host "[4/4] Verifying installation..."
Write-Host ""

python -c "import torch; print(f'PyTorch: {torch.__version__}'); print(f'CUDA available: {torch.cuda.is_available()}')"

if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Verification failed"
    Write-Host ""
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "[OK] All dependencies verified successfully"

# Completion message
Write-Host ""
Write-Host "================================================================"
Write-Host "   Installation Complete!"
Write-Host "================================================================"
Write-Host ""
Write-Host "Environment Information:"
Write-Host "- Environment Name: ai_behavior"
Write-Host "- Python Version: 3.10"
Write-Host "- PyTorch Version: 2.7.1"
Write-Host "- CUDA Version: 11.8"
Write-Host ""
Write-Host "Next Steps:"
Write-Host ""
Write-Host "1. Activate environment before each use:"
Write-Host "   conda activate ai_behavior"
Write-Host ""
Write-Host "2. Then run the UI:"
Write-Host "   cd H:\AI-Behavior-Research"
Write-Host "   python scripts/ui/ui_app.py"
Write-Host ""
Write-Host "3. Or use the quick launch script:"
Write-Host "   .\Start-UI.ps1"
Write-Host ""
Read-Host "Press Enter to exit"
