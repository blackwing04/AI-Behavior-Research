@echo off
chcp 65001 >nul

REM Get the script directory
set SCRIPT_DIR=%~dp0

REM Run PowerShell script
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%SCRIPT_DIR%powershell\02_install_dependencies.ps1"

pause
