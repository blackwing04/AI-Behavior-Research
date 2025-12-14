@echo off
REM Start AI Behavior Research UI
REM Uses PowerShell to avoid encoding issues

cd /d "%~dp0"

chcp 65001 >nul
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\ui\Start-UI.ps1"
pause
