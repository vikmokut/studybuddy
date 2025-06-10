@echo off
echo Running StudyBuddy Temp Directory Fixer...
echo.

:: Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo Running with Administrator privileges - Good!
) else (
    echo WARNING: Not running as administrator.
    echo Some fixes might not work. Consider right-clicking this file
    echo and selecting "Run as administrator".
    echo.
    pause
)

:: Run the PowerShell script
powershell -ExecutionPolicy Bypass -File "fix_temp_dir.ps1"

echo.
echo Press any key to exit...
pause > nul
