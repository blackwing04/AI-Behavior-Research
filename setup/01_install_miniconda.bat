@echo off
chcp 65001 >nul

REM Get the script directory
set SCRIPT_DIR=%~dp0

REM Run PowerShell script
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%powershell\01_install_miniconda.ps1"

pause
