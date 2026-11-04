@echo off
rem Double-click launcher. The real work is in start.ps1 (kept separate so Chinese text displays correctly).
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1"
if errorlevel 1 pause
