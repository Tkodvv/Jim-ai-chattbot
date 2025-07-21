@echo off
echo Testing Python Installation...
echo.

echo Checking 'python' command:
python --version 2>nul
if %errorlevel% equ 0 (
    echo ✓ 'python' command works
) else (
    echo ✗ 'python' command not found
)

echo.
echo Checking 'py' command (Python Launcher):
py --version 2>nul
if %errorlevel% equ 0 (
    echo ✓ 'py' command works
) else (
    echo ✗ 'py' command not found
)

echo.
echo Checking pip installation:
python -m pip --version 2>nul
if %errorlevel% equ 0 (
    echo ✓ pip works with 'python' command
) else (
    py -m pip --version 2>nul
    if %errorlevel% equ 0 (
        echo ✓ pip works with 'py' command
    ) else (
        echo ✗ pip not working with either command
    )
)

echo.
echo If no Python commands work, please:
echo 1. Install Python 3.13.2 from https://www.python.org/downloads/
echo 2. Make sure to check "Add Python to PATH" during installation
echo 3. Restart your command prompt after installation

pause