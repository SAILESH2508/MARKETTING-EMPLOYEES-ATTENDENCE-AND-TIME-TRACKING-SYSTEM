@echo off
REM Quick start script for Windows

echo ========================================
echo Employee Attendance System
echo ========================================
echo.

REM Check if virtual environment exists
if not exist ".venv" (
    echo Creating virtual environment...
    python -m venv .venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat
echo.

REM Install/update dependencies
echo Checking dependencies...
pip install -r requirements.txt --quiet
echo.

REM Run the application
echo Starting application...
echo.
python emp.py

REM Keep window open if there's an error
if errorlevel 1 (
    echo.
    echo ========================================
    echo An error occurred!
    echo ========================================
    pause
)
