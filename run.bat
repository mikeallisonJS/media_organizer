@echo off
echo Running Archimedius...

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH. Please install Python 3 to run this application.
    pause
    exit /b 1
)

:: Check if virtual environment exists, create if not
if not exist archimedius_venv (
    echo Creating virtual environment...
    python -m venv archimedius_venv
)

:: Activate virtual environment and install dependencies
echo Activating virtual environment and installing dependencies...
call archimedius_venv\Scripts\activate.bat
pip install -r requirements.txt

:: Check if Tkinter is installed
python -c "import tkinter" >nul 2>&1
if %errorlevel% neq 0 (
    echo Tkinter is not installed. Please install it with your Python distribution.
    pause
    exit /b 1
)

:: Check if MediaInfo is installed (optional)
where mediainfo >nul 2>&1
if %errorlevel% neq 0 (
    echo WARNING: MediaInfo is not installed. Video metadata extraction will be limited.
    echo To install MediaInfo on Windows: Download from https://mediaarea.net/en/MediaInfo/Download/Windows
    echo.
    echo Continuing without MediaInfo...
    timeout /t 2 >nul
)

:: Run the application
python main.py

:: Deactivate virtual environment
call deactivate
pause 