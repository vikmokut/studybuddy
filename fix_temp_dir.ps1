# PowerShell script to fix common temp directory permission issues
# This addresses the "Error processing audio: [WinError 2] The system cannot find the file specified" error

Write-Host "StudyBuddy Temporary Directory Fixer" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host ""

# Get current user
$currentUser = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
Write-Host "Current user: $currentUser" -ForegroundColor Green

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "WARNING: This script is not running as Administrator." -ForegroundColor Yellow
    Write-Host "Some fixes may not work. Consider rerunning as Administrator." -ForegroundColor Yellow
    Write-Host ""
}

# Get temp directory path
$tempDir = [System.IO.Path]::GetTempPath()
Write-Host "Temp directory: $tempDir" -ForegroundColor Green

# Check if temp directory exists
if (-not (Test-Path $tempDir)) {
    Write-Host "Temp directory does not exist! Creating it..." -ForegroundColor Red
    try {
        New-Item -ItemType Directory -Path $tempDir -Force
        Write-Host "Created temp directory successfully." -ForegroundColor Green
    } catch {
        Write-Host "Failed to create temp directory: $_" -ForegroundColor Red
    }
}

# Check write permissions
Write-Host "Testing write permissions to temp directory..." -ForegroundColor Cyan
$testFile = Join-Path $tempDir "studybuddy_test.txt"
try {
    "Test content" | Out-File -FilePath $testFile
    Write-Host "Successfully wrote to temp directory!" -ForegroundColor Green
    Remove-Item -Path $testFile -Force
} catch {
    Write-Host "Failed to write to temp directory: $_" -ForegroundColor Red
    
    # Try to fix permissions
    Write-Host "Attempting to fix permissions..." -ForegroundColor Cyan
    if ($isAdmin) {
        try {
            # Grant full control to the current user
            $acl = Get-Acl $tempDir
            $rule = New-Object System.Security.AccessControl.FileSystemAccessRule(
                $currentUser, 
                "FullControl", 
                "ContainerInherit,ObjectInherit", 
                "None", 
                "Allow"
            )
            $acl.SetAccessRule($rule)
            Set-Acl $tempDir $acl
            
            Write-Host "Permissions updated. Testing again..." -ForegroundColor Cyan
            "Test content" | Out-File -FilePath $testFile
            Write-Host "Success! Permissions fixed." -ForegroundColor Green
            Remove-Item -Path $testFile -Force
        } catch {
            Write-Host "Failed to update permissions: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "To fix permissions, please run this script as Administrator." -ForegroundColor Yellow
    }
}

# Create alternative directory in Documents
Write-Host "Creating alternative audio directory in Documents..." -ForegroundColor Cyan
$docsDir = [Environment]::GetFolderPath("MyDocuments")
$altDir = Join-Path $docsDir "StudyBuddy"

try {
    if (-not (Test-Path $altDir)) {
        New-Item -ItemType Directory -Path $altDir -Force
    }
    
    $altTestFile = Join-Path $altDir "audio_test.txt"
    "Test content" | Out-File -FilePath $altTestFile
    Write-Host "Successfully created and wrote to alternative directory:" -ForegroundColor Green
    Write-Host $altDir -ForegroundColor Green
    Remove-Item -Path $altTestFile -Force
} catch {
    Write-Host "Failed to create alternative directory: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "Troubleshooting completed." -ForegroundColor Cyan
Write-Host "If issues persist, try the following:" -ForegroundColor Yellow
Write-Host "1. Run StudyBuddy as Administrator" -ForegroundColor White
Write-Host "2. Check antivirus settings for file blocking" -ForegroundColor White
Write-Host "3. Run 'python audio_diagnostic.py' for more detailed diagnostics" -ForegroundColor White

Read-Host -Prompt "Press Enter to exit"
