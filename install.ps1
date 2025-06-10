# PowerShell script for StudyBuddy dependency installation on Windows

Write-Host "Installing StudyBuddy dependencies..." -ForegroundColor Cyan

# Check if Python is installed
try {
    $pythonVersion = python --version
    Write-Host "Found Python: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Python not found. Please install Python 3.8 or newer." -ForegroundColor Red
    Write-Host "Download from: https://www.python.org/downloads/" -ForegroundColor Yellow
    exit
}

# Create a virtual environment (optional but recommended)
Write-Host "Creating virtual environment..." -ForegroundColor Cyan
python -m venv studybuddy_env

# Activate the environment
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
.\studybuddy_env\Scripts\Activate.ps1

# Install dependencies
Write-Host "Installing Python packages..." -ForegroundColor Cyan
pip install --upgrade pip
pip install -r requirements.txt

# Check for audio-related packages specifically
Write-Host "Verifying audio dependencies..." -ForegroundColor Cyan
$audioPackages = @("sounddevice", "webrtcvad", "scipy", "numpy")

foreach ($package in $audioPackages) {
    try {
        $importTest = python -c "import $package; print(f'$package is installed')"
        Write-Host $importTest -ForegroundColor Green
    } catch {
        Write-Host "Warning: $package may not be installed correctly." -ForegroundColor Yellow
        Write-Host "Attempting to reinstall $package..." -ForegroundColor Cyan
        pip uninstall -y $package
        pip install $package
    }
}

# Verify installation with diagnostic script
Write-Host "Running audio diagnostic test..." -ForegroundColor Cyan
python audio_diagnostic.py

Write-Host "Installation complete." -ForegroundColor Green
Write-Host "To run StudyBuddy:" -ForegroundColor Cyan
Write-Host "1. Activate the environment: .\studybuddy_env\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "2. Run the application: python main.py" -ForegroundColor White
Write-Host "3. Or use the launcher: .\launch_studybuddy.bat" -ForegroundColor White

Write-Host "If you encounter audio issues:" -ForegroundColor Yellow
Write-Host "1. Run the diagnostic tool: python audio_diagnostic.py" -ForegroundColor White
Write-Host "2. Check your microphone and speaker settings" -ForegroundColor White
Write-Host "3. Ensure your Windows user account has permission to write to the temp directory" -ForegroundColor White

# Keep the window open
Write-Host "Press any key to exit..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
