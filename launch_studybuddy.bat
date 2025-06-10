@echo off
echo ===================================
echo StudyBuddy Launcher
echo ===================================
echo.

REM Check if Python is installed
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: Python not found in PATH
    echo Please install Python 3.8 or later and try again.
    echo.
    pause
    exit /b 1
)

REM Check if the virtual environment exists
if exist studybuddy_env\Scripts\activate.bat (
    echo Activating virtual environment...
    call studybuddy_env\Scripts\activate.bat
) else (
    echo WARNING: Virtual environment not found.
    echo Running with system Python installation.
    echo.
)

echo Starting StudyBuddy...
echo Press Ctrl+C to exit.
echo.

REM Run with error handling
python main.py
if %ERRORLEVEL% neq 0 (
    echo.
    echo Application exited with errors.
    echo Try running the diagnostic tool with:
    echo python audio_diagnostic.py
)

echo.
pause
