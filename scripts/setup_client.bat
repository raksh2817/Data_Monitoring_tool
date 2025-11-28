@echo off
REM Client Setup Script for Windows
REM This script helps set up the client-side agent

echo ==========================================
echo Monitoring System - Client Setup
echo ==========================================
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    exit /b 1
)
echo [OK] Python found
python --version

REM Check pip
pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip is not installed
    exit /b 1
)
echo [OK] pip found

REM Create virtual environment if it doesn't exist
if not exist "..\.venv" (
    echo.
    echo Creating virtual environment...
    python -m venv ..\.venv
    echo [OK] Virtual environment created
)

REM Activate virtual environment
echo.
echo Activating virtual environment...
call ..\.venv\Scripts\activate.bat

REM Install dependencies
echo.
echo Installing Python dependencies...
pip install requests psutil
echo [OK] Dependencies installed

REM Check or create agent config
if not exist "agent_config.json" (
    echo.
    echo Creating agent_config.json from template...
    if exist "agent_config.json.template" (
        copy agent_config.json.template agent_config.json
        echo [OK] agent_config.json created
        echo.
        echo [WARNING] IMPORTANT: Edit agent_config.json with your settings:
        echo    - api_url: Your server's IP address and port
        echo    - host_key: Unique key (must match database)
    ) else (
        echo [ERROR] agent_config.json.template not found
    )
) else (
    echo [OK] agent_config.json found
)

echo.
echo ==========================================
echo Setup Complete!
echo ==========================================
echo.
echo Next steps:
echo 1. Edit agent_config.json with your server URL and host_key
echo 2. Ensure host is registered in database on server
echo 3. Test agent: python agent.py
echo 4. Set up Windows Task Scheduler for automatic runs
echo.

pause

