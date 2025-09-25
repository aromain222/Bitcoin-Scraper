@echo off
rem ============================================================================
rem  Wall Street Financial-Models – One-Click Startup Script (Windows)
rem ----------------------------------------------------------------------------
rem  1) Creates a Python venv (venv\) if missing
rem  2) Installs / upgrades dependencies
rem  3) Kills any processes on ports 5001 (backend) and 8080 (UI)
rem  4) Starts backend on 5001 and frontend (static) on 8080
rem  5) Opens default browser
rem ----------------------------------------------------------------------------
rem  Usage:  double-click start.bat  (or run in cmd / PowerShell)
rem ============================================================================

SETLOCAL ENABLEDELAYEDEXPANSION

:: Detect script location
SET SCRIPT_DIR=%~dp0
SET PROJECT_ROOT=%SCRIPT_DIR%financial-models-app
SET BACKEND_DIR=%PROJECT_ROOT%\backend
SET FRONTEND_DIR=%PROJECT_ROOT%\frontend

IF NOT EXIST "%BACKEND_DIR%" (
    echo [ERROR] Backend directory not found: %BACKEND_DIR%
    pause
    exit /b 1
)
IF NOT EXIST "%FRONTEND_DIR%" (
    echo [ERROR] Frontend directory not found: %FRONTEND_DIR%
    pause
    exit /b 1
)

:: 1. Create venv if missing
IF NOT EXIST "%PROJECT_ROOT%\venv" (
    echo Creating Python virtual-env…
    python -m venv "%PROJECT_ROOT%\venv"
)

CALL "%PROJECT_ROOT%\venv\Scripts\activate.bat"

:: 2. Install / update deps
IF EXIST "%BACKEND_DIR%\requirements.txt" (
    echo Installing / updating Python dependencies…
    python -m pip install --upgrade pip >nul
    python -m pip install -r "%BACKEND_DIR%\requirements.txt" >nul
) ELSE (
    echo WARNING: requirements.txt not found – skipping pip install
)

:: 3. Kill ports 5001 & 8080 (silent if none)
FOR %%P IN (5001 8080) DO (
    FOR /F "usebackq tokens=5" %%i IN (`netstat -ano ^| findstr :%%P`) DO (
        echo Killing PID %%i on port %%P…
        taskkill /PID %%i /F >nul
    )
)

:: 4. Start backend & frontend
start "Backend" cmd /k "cd /d %BACKEND_DIR% && python app.py"
start "Frontend" cmd /k "cd /d %FRONTEND_DIR% && python -m http.server 8080"

:: 5. Open browser after short delay
ping 127.0.0.1 -n 3 >nul
start http://localhost:8080

echo --------------------------------------------------------------------------------
echo Backend running on http://localhost:5001  (logs in new cmd window)
echo Frontend running on http://localhost:8080 (logs in new cmd window)
echo Close the windows or press CTRL+C in them to stop the servers.
echo --------------------------------------------------------------------------------

ENDLOCAL
pause 