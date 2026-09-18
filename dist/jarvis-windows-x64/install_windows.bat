@echo off
title J.A.R.V.I.S. Windows Installer
color 0b

echo ===============================================================
echo          J.A.R.V.I.S. AUTOMATED INSTALLER FOR WINDOWS
echo ===============================================================
echo.

REM 1. Check Python
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [!] ERROR: Python 3.10+ was not found in your PATH.
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation.
    echo.
    pause
    exit /b 1
)

echo [+] Python found:
python --version

REM 2. Check Java
where java >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [!] WARNING: Java 21+ was not found in your PATH.
    echo The HUD interface requires OpenJDK 21 or higher.
    echo You can download it from: https://adoptium.net/
    echo.
) else (
    echo [+] Java found:
    java --version
)
echo.

REM 3. Create Python Virtual Environment
echo [*] Setting up Python virtual environment in backend\.venv ...
cd /d "%~dp0"
python -m venv backend\.venv
if %ERRORLEVEL% neq 0 (
    echo [!] Warning: Failed to create venv. Falling back to global pip...
    pip install -r backend\requirements.txt
) else (
    echo [*] Installing required Python packages...
    backend\.venv\Scripts\python -m pip install --upgrade pip
    backend\.venv\Scripts\pip install -r backend\requirements.txt
)

echo.
echo ===============================================================
echo          INSTALLATION FINISHED SUCCESSFULLY!
echo ===============================================================
echo.
echo  -> Double-click "jarvis.exe" to launch J.A.R.V.I.S.
echo  -> Double-click "jarvis-config.exe" to configure AI providers & keys.
echo.
pause
