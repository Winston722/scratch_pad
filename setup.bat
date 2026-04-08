@echo off
:: ============================================================
:: Bluetti AC200L Price Monitor - One-Time Setup
:: ============================================================
:: BEFORE running this:
::   1. Install Python from https://www.python.org/downloads/
::   2. On the installer, check "Add Python to PATH"
::   3. Then double-click this file
:: ============================================================

echo.
echo  Bluetti AC200L Price Monitor Setup
echo  ===================================
echo.

:: Check Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python not found.
    echo.
    echo  Please install Python first:
    echo    1. Go to https://www.python.org/downloads/
    echo    2. Download and run the installer
    echo    3. CHECK the box "Add Python to PATH"
    echo    4. Then run this setup again.
    echo.
    pause
    exit /b 1
)

echo  [1/2] Installing required Python packages...
pip install requests beautifulsoup4
if errorlevel 1 (
    echo.
    echo  ERROR: pip install failed. Check your internet connection and try again.
    pause
    exit /b 1
)

echo.
echo  [2/2] Creating daily scheduled task (runs at 9:00 AM every day)...

:: Use the folder this .bat file lives in to find price_monitor.py
set SCRIPT_PATH=%~dp0price_monitor.py

:: Create (or overwrite) the scheduled task
schtasks /create /tn "Bluetti Price Monitor" /tr "pythonw \"%SCRIPT_PATH%\"" /sc daily /st 09:00 /f
if errorlevel 1 (
    echo.
    echo  ERROR: Could not create scheduled task.
    echo  Try running this file as Administrator (right-click -> Run as administrator).
    pause
    exit /b 1
)

echo.
echo  ============================================================
echo   Setup complete!
echo.
echo   The price will be checked every day at 9:00 AM.
echo   A popup will appear if the price drops to $700 or less.
echo.
echo   To test it now, double-click price_monitor.py
echo   To change the time: open Task Scheduler, find
echo     "Bluetti Price Monitor", and edit the trigger.
echo  ============================================================
echo.
pause
