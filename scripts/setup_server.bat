@echo off
REM Server Setup Script for Windows
REM This script helps set up the server-side components

echo ==========================================
echo Monitoring System - Server Setup
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
pip install -r requirements.txt
echo [OK] Dependencies installed

REM Check config file
if not exist "config.yaml" (
    echo.
    echo [WARNING] config.yaml not found!
    echo Please create config.yaml with your database settings
    echo See README.md for configuration details
) else (
    echo [OK] config.yaml found
)

REM Check templates
if not exist "templates" (
    echo.
    echo [WARNING] templates\ directory not found!
    echo Creating templates directory...
    mkdir templates
    echo [OK] templates\ directory created
    echo Please copy template files to templates\
) else (
    echo [OK] templates\ directory found
)

echo.
echo ==========================================
echo Database Setup
echo ==========================================
echo.
set /p SETUP_DB="Do you want to set up the database tables now? (y/n): "
if /i "%SETUP_DB%"=="y" (
    echo Running database setup...
    python setup_database.py
)

echo.
echo ==========================================
echo Setup Complete!
echo ==========================================
echo.
echo Next steps:
echo 1. Ensure config.yaml is configured correctly
echo 2. Set up database tables: python setup_database.py
echo 3. Create user account: python setup_user.py admin password
echo 4. Start server: python app_new.py
echo.

pause

