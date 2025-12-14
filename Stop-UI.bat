@echo off
REM Stop AI Behavior Research UI
REM Uses PowerShell to stop processes

cd /d "%~dp0"

chcp 65001 >nul
powershell -NoProfile -ExecutionPolicy Bypass -File "scripts\ui\Stop-UI.ps1"

pause
