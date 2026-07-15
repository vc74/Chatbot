@echo off
title ChatBot Server
echo.
echo ================================
echo        ChatBot Server
echo ================================
echo.

REM Check if Python is available
py --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    pause
    exit /b 1
)

REM Change to script directory
cd /d "%~dp0"

REM Check if .env file exists
if not exist ".env" (
    echo Error: .env file not found!
    echo Please create a .env file with your Groq API key.
    pause
    exit /b 1
)

echo Starting ChatBot Production Server...
echo Server will be available at: http://localhost:5000
echo Press Ctrl+C to stop the server
echo.

REM Run the production server
py server.py

pause