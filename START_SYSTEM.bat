@echo off
REM ============================================================================
REM Diabetic Retinopathy Detection System - Startup Script
REM ============================================================================
REM This script starts both the backend and frontend servers
REM ============================================================================

setlocal enabledelayedexpansion
cd /d "%~dp0"

echo.
echo ============================================================================
echo  🏥 Diabetic Retinopathy Detection System - Startup Launcher
echo ============================================================================
echo.

REM Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo ❌ ERROR: Virtual environment not found!
    echo Please run: python -m venv venv
    pause
    exit /b 1
)

REM Check if frontend node_modules exists
if not exist "frontend\node_modules" (
    echo ❌ ERROR: Frontend dependencies not installed!
    echo Installing frontend dependencies...
    cd frontend
    call npm install
    cd ..
)

echo ✅ All dependencies found!
echo.
echo Starting Backend Server...
echo.

REM Start backend in new window
start "DR Detection Backend" cmd /k ^
    "cd /d "%cd%" && ^
    call venv\Scripts\activate.bat && ^
    python -m uvicorn src.api:app --host localhost --port 8001"

timeout /t 3 /nobreak

echo.
echo Starting Frontend Server...
echo.

REM Start frontend in new window
start "DR Detection Frontend" cmd /k ^
    "cd /d "%cd%\frontend" && ^
    call npm start"

timeout /t 3 /nobreak

echo.
echo ============================================================================
echo  ✅ STARTUP COMPLETE
echo ============================================================================
echo.
echo 📊 Backend URL:  http://localhost:8001
echo 🖥️  Frontend URL: http://localhost:3000
echo.
echo Waiting for servers to initialize (15-30 seconds)...
echo Once servers are ready, your browser will open automatically.
echo.
echo If browser doesn't open, manually visit: http://localhost:3000
echo.
timeout /t 10 /nobreak

REM Try to open browser (Windows specific)
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" (
    start "" "%ProgramFiles%\Google\Chrome\Application\chrome.exe" http://localhost:3000
) else if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" (
    start "" "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" http://localhost:3000
) else (
    start http://localhost:3000
)

echo.
echo 🎉 System is running!
echo Press Ctrl+C in either terminal to stop servers
echo.
pause
