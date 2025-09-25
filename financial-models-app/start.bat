@echo off
echo 🚀 Starting Financial Models App...
echo ==================================

REM Check Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python is not installed. Please install Python 3.
    pause
    exit /b 1
)

echo ✅ Python found

REM Start backend
echo 🐍 Starting Python backend...
cd backend

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
)

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Install requirements
echo 📦 Installing Python dependencies...
pip install -r requirements.txt >nul 2>&1

REM Start Flask app in background
echo 🚀 Starting Flask backend on http://localhost:5000
start /b python app.py

REM Wait for backend to start
timeout /t 3 /nobreak >nul

REM Start frontend
cd ..\frontend
echo 🌐 Starting frontend on http://localhost:8000
echo 📱 Opening in your default browser...

REM Open browser
start http://localhost:8000

REM Start Python HTTP server
python -m http.server 8000

pause 