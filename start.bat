@echo off
echo Starting Jim Discord Bot...
echo.

REM Check if Python 3.13 is available
python3.13 --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python 3.13 not found. Trying python3...
    python3 --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo Python 3 not found. Trying python...
        python --version >nul 2>&1
        if %errorlevel% neq 0 (
            echo ERROR: Python not found! Please install Python 3.13
            pause
            exit /b 1
        ) else (
            set PYTHON_CMD=python
        )
    ) else (
        set PYTHON_CMD=python3
    )
) else (
    set PYTHON_CMD=python3.13
)

echo Using %PYTHON_CMD%
echo.

REM Check if .env file exists
if not exist .env (
    echo ERROR: .env file not found!
    echo Please create a .env file with your API keys and database configuration.
    echo You can copy .env.example and fill in your values.
    pause
    exit /b 1
)

REM Install dependencies if needed
echo Installing dependencies...
%PYTHON_CMD% -m pip install --upgrade pip
%PYTHON_CMD% -m pip install -r requirements_download.txt

echo.
echo Starting Jim Bot...
echo Press Ctrl+C to stop the bot
echo.

REM Run the bot
%PYTHON_CMD% main.py

echo.
echo Bot stopped.
pause