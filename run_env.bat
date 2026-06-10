@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo ================================================================
echo            Environment Variables Setup
echo ================================================================
echo.

python set_env.py

echo.
pause