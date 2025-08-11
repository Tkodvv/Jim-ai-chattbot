@echo off
title Jim Discord Bot Debug Launcher
echo DEBUG: Starting Jim Discord Bot...
echo.

echo DEBUG: Step 1 - Checking Python installation
python --version
if %errorlevel% equ 0 (
    echo DEBUG: Found 'python' command
    set PYTHON_CMD=python
    goto python_found
)

echo DEBUG: 'python' not found, trying 'py'
py --version
if %errorlevel% equ 0 (
    echo DEBUG: Found 'py' command  
    set PYTHON_CMD=py
    goto python_found
)

echo DEBUG: ERROR - No Python found
echo Please install Python and make sure it's in your PATH
pause
exit /b 1

:python_found
echo DEBUG: Using %PYTHON_CMD%
echo.

echo DEBUG: Step 2 - Checking for .env file
if not exist .env (
    echo DEBUG: .env file not found
    echo Creating a basic .env file for you...
    echo DATABASE_URL=postgresql://postgres:1136@localhost:5432/jimbot > .env
    echo DISCORD_TOKEN=your_discord_token_here >> .env
    echo OPENAI_API_KEY=your_openai_api_key_here >> .env
    echo GOOGLE_API_KEY=your_google_api_key_here >> .env
    echo GOOGLE_CSE_ID=your_google_cse_id_here >> .env
    echo FLASK_SECRET_KEY=your_secret_key_here >> .env
    echo.
    echo DEBUG: Created .env file. Please edit it with your actual API keys.
    echo DEBUG: Press any key to continue...
    pause
)

echo DEBUG: Step 3 - Installing dependencies
%PYTHON_CMD% -m pip install --upgrade pip
%PYTHON_CMD% -m pip install discord.py openai aiohttp python-dotenv langchain faiss-cpu flask flask-sqlalchemy

REM If using JSON instead of PostgreSQL, you can safely ignore psycopg2-binary and database setup





echo.
echo DEBUG: Step 4 - Starting bot (uses JSON storage now)
echo DEBUG: Press Ctrl+C to stop the bot
echo.

%PYTHON_CMD% main.py

echo.
echo DEBUG: Bot stopped
echo DEBUG: Press any key to exit...
pause
