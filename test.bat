@echo off
setlocal

echo Running Archimedius tests...

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python is not installed or not in PATH. Please install Python 3.
    exit /b 1
)

:: Check if virtual environment exists, create if not
if not exist archimedius_venv (
    echo Creating virtual environment...
    python -m venv archimedius_venv
    if %errorlevel% neq 0 (
        echo Failed to create virtual environment.
        exit /b 1
    )
)

:: Activate virtual environment
call archimedius_venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo Failed to activate virtual environment.
    exit /b 1
)

:: Use a repo-local temp directory to avoid system TEMP permission issues
if not exist .tmp mkdir .tmp
set "TMP=%CD%\.tmp"
set "TEMP=%CD%\.tmp"

:: Install project dependencies
echo Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Failed to install requirements.
    call deactivate
    exit /b 1
)

:: Ensure pytest is available (install it if missing)
python -m pytest --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Pytest not found, installing...
    python -m pip install pytest
    if %errorlevel% neq 0 (
        echo Failed to install pytest automatically.
        echo Try manually: python -m pip install pytest
        call deactivate
        exit /b 1
    )
)

:: Run tests
if "%~1"=="" (
    python -m pytest tests -v -p no:cacheprovider --basetemp=tests\.pytest_tmp
) else (
    python -m pytest %*
)
set TEST_EXIT_CODE=%errorlevel%

:: Deactivate virtual environment and return original test exit code
call deactivate
exit /b %TEST_EXIT_CODE%
