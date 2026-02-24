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
set "MEDIAINFO_LOCAL_DIR=%CD%\tools\mediainfo"
set "MEDIAINFO_LOCAL_EXE=%MEDIAINFO_LOCAL_DIR%\MediaInfo.exe"
where mediainfo >nul 2>&1
if %errorlevel% neq 0 (
    if exist "%MEDIAINFO_LOCAL_EXE%" (
        echo MediaInfo not found in PATH, using local dev copy at tools\mediainfo.
        set "PATH=%MEDIAINFO_LOCAL_DIR%;%PATH%"
    ) else (
        echo MediaInfo not found in PATH. Downloading local dev copy...
        if not exist "%MEDIAINFO_LOCAL_DIR%" mkdir "%MEDIAINFO_LOCAL_DIR%"
        powershell -NoProfile -ExecutionPolicy Bypass -Command "try { $zipPath = Join-Path $env:TEMP 'MediaInfo_CLI_23.11_Windows_x64.zip'; Invoke-WebRequest -Uri 'https://mediaarea.net/download/binary/mediainfo/23.11/MediaInfo_CLI_23.11_Windows_x64.zip' -OutFile $zipPath; Expand-Archive -LiteralPath $zipPath -DestinationPath '%MEDIAINFO_LOCAL_DIR%' -Force; Remove-Item -LiteralPath $zipPath -Force; exit 0 } catch { Write-Host $_.Exception.Message; exit 1 }"
        if exist "%MEDIAINFO_LOCAL_EXE%" (
            echo Downloaded MediaInfo to tools\mediainfo.
            set "PATH=%MEDIAINFO_LOCAL_DIR%;%PATH%"
        ) else (
            echo WARNING: Could not download MediaInfo. Video metadata extraction may be limited.
            echo To install MediaInfo on Windows: Download from https://mediaarea.net/en/MediaInfo/Download/Windows
            timeout /t 2 >nul
        )
    )
)

:: Run the application
python main.py

:: Deactivate virtual environment
call deactivate
pause 