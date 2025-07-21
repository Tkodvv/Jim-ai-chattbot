@echo off
echo Starting Jim Discord Bot with PostgreSQL...
echo.

REM Check if Python 3.13.2 is available
python3.13.2 --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python 3.13.2 not found. Trying python3.13...
    python3.13 --version >nul 2>&1
    if %errorlevel% neq 0 (
        echo Python 3.13 not found. Trying python3...
        python3 --version >nul 2>&1
        if %errorlevel% neq 0 (
            echo Python 3 not found. Trying python...
            python --version >nul 2>&1
            if %errorlevel% neq 0 (
                echo ERROR: Python not found! Please install Python 3.13.2
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
) else (
    set PYTHON_CMD=python3.13.2
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

REM Start PostgreSQL service
echo Starting PostgreSQL service...
net start postgresql-x64-16 >nul 2>&1
if %errorlevel% neq 0 (
    echo Trying alternative PostgreSQL service names...
    net start postgresql-16 >nul 2>&1
    if %errorlevel% neq 0 (
        net start postgresql >nul 2>&1
        if %errorlevel% neq 0 (
            echo WARNING: Could not start PostgreSQL service automatically.
            echo Please ensure PostgreSQL is running manually.
            echo Common service names: postgresql-x64-16, postgresql-16, postgresql
            echo.
        ) else (
            echo PostgreSQL service started successfully.
        )
    ) else (
        echo PostgreSQL service started successfully.
    )
) else (
    echo PostgreSQL service started successfully.
)

REM Wait a moment for PostgreSQL to fully start
timeout /t 3 /nobreak >nul

REM Setup database and test connection
echo Setting up database...
%PYTHON_CMD% setup_database.py

if %errorlevel% neq 0 (
    echo.
    echo Database setup failed. Continuing anyway...
    echo Make sure PostgreSQL is running and DATABASE_URL is correct.
    echo.
)

REM Install dependencies if needed
echo Installing dependencies...
%PYTHON_CMD% -m pip install --upgrade pip
%PYTHON_CMD% -m pip install -r requirements_download.txt

echo.
echo Starting Jim Bot...
echo Press Ctrl+C to stop the bot
echo PostgreSQL and bot will both stop when you close this window
echo.

REM Run the bot
%PYTHON_CMD% main.py

echo.
echo Bot stopped.
echo Stopping PostgreSQL service...
net stop postgresql-x64-16 >nul 2>&1
net stop postgresql-16 >nul 2>&1
net stop postgresql >nul 2>&1

pause