@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo ================================================================
echo            Batch Installer
echo ================================================================
echo.
echo [WARNING] This will install multiple packages silently.
echo           Please run as Administrator.
echo.
echo Press Ctrl+C to cancel, or press any key to continue...
pause >nul

python main.py

echo.
echo Done. Check logs folder for installation log.
pause