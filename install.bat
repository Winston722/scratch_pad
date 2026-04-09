@echo off
:: ============================================================
::  Bluetti AC200L Price Monitor - Installer
::
::  This script will:
::    1. Check Python is installed
::    2. Download price_monitor.py from GitHub
::    3. Install required packages
::    4. Schedule it to run every day at 9 AM
::
::  BEFORE running this:
::    - Install Python from https://www.python.org/downloads/
::    - On the installer screen, CHECK "Add Python to PATH"
:: ============================================================

echo.
echo  Bluetti AC200L Price Monitor - Installer
echo  =========================================
echo.

:: --- Check Python is installed ---
python --version >nul 2>&1
if errorlevel 1 (
    echo  ERROR: Python not found.
    echo.
    echo  Please install Python first:
    echo    1. Go to https://www.python.org/downloads/
    echo    2. Click "Download Python"
    echo    3. Run the installer
    echo    4. IMPORTANT: Check the box that says "Add Python to PATH"
    echo    5. Then run this installer again.
    echo.
    pause
    exit /b 1
)

:: --- Create install folder ---
set INSTALL_DIR=%USERPROFILE%\PriceMonitor
echo  Installing to: %INSTALL_DIR%
mkdir "%INSTALL_DIR%" 2>nul

:: --- Download price_monitor.py from GitHub ---
echo.
echo  [1/3] Downloading price monitor script...
curl -L --fail -o "%INSTALL_DIR%\price_monitor.py" "https://raw.githubusercontent.com/Winston722/scratch_pad/main/price_monitor.py"
if errorlevel 1 (
    echo.
    echo  ERROR: Download failed. Check your internet connection and try again.
    pause
    exit /b 1
)
echo  Download complete.

:: --- Install Python packages ---
echo.
echo  [2/3] Installing required Python packages...
pip install requests beautifulsoup4
if errorlevel 1 (
    echo.
    echo  ERROR: Package install failed. Check your internet connection and try again.
    pause
    exit /b 1
)

:: --- Create scheduled task ---
echo.
echo  [3/3] Scheduling daily price check at 9:00 AM...
schtasks /create /tn "Bluetti Price Monitor" /tr "pythonw \"%INSTALL_DIR%\price_monitor.py\"" /sc daily /st 09:00 /f
if errorlevel 1 (
    echo.
    echo  ERROR: Could not create scheduled task.
    echo  Try right-clicking this file and choosing "Run as administrator".
    pause
    exit /b 1
)

echo.
echo  ============================================================
echo   All done!
echo.
echo   The price will be checked every day at 9:00 AM.
echo   A popup will appear if the price drops to $700 or less.
echo.
echo   To do a test run right now, open File Explorer and go to:
echo     %INSTALL_DIR%
echo   Then double-click price_monitor.py
echo.
echo   Logs are saved to:
echo     %INSTALL_DIR%\price_monitor.log
echo  ============================================================
echo.
pause
