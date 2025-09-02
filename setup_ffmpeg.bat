@echo off
echo Setting up FFmpeg for voice support...
echo.

REM Check if FFmpeg is already available
ffmpeg -version >nul 2>&1
if %errorlevel% == 0 (
    echo FFmpeg is already installed and available!
    echo.
    goto :end
)

echo FFmpeg not found in PATH. You need to install FFmpeg for voice features.
echo.
echo Please follow these steps:
echo 1. Go to https://ffmpeg.org/download.html
echo 2. Download FFmpeg for Windows
echo 3. Extract it to a folder (e.g., C:\ffmpeg)
echo 4. Add the bin folder to your system PATH (e.g., C:\ffmpeg\bin)
echo 5. Restart your command prompt/PowerShell
echo.
echo Alternative: Use chocolatey (if installed):
echo   choco install ffmpeg
echo.
echo Or use winget:
echo   winget install ffmpeg
echo.

:end
pause
