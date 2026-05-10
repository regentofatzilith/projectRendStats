# PowerShell build script for creating standalone executable
# Run this from the project root directory

Write-Host "========================================"
Write-Host "Tower Conquest Analytics - Build Script"
Write-Host "========================================"
Write-Host ""

# Use full Python path
$python = "C:/Users/thors/AppData/Local/Programs/Python/Python313/python.exe"

# Check if PyInstaller is installed
Write-Host "Checking for PyInstaller..."
& $python -c "import PyInstaller" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "PyInstaller not found. Installing..."
    & $python -m pip install pyinstaller
    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "========================================"
        Write-Host "Build FAILED!"
        Write-Host "========================================"
        Read-Host "Press Enter to exit"
        exit 1
    }
}

# Clean previous builds
Write-Host "Cleaning previous builds..."
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "__pycache__") { Remove-Item -Recurse -Force "__pycache__" }

# Build the executable
Write-Host ""
Write-Host "Building executable..."
Write-Host "This may take 5-10 minutes..."
Write-Host ""

& $python -m PyInstaller build_exe.spec

if ($LASTEXITCODE -ne 0) {
    Write-Host ""
    Write-Host "========================================"
    Write-Host "Build FAILED!"
    Write-Host "========================================"
    Read-Host "Press Enter to exit"
    exit 1
}

Write-Host ""
Write-Host "========================================"
Write-Host "Build SUCCESSFUL!"
Write-Host "========================================"
Write-Host ""
Write-Host "Executable location: dist\TowerConquestAnalytics.exe"
Write-Host "Size: "
Get-ChildItem "dist\TowerConquestAnalytics.exe" | Format-Table Name, Length
Write-Host ""
Write-Host "To run: double-click dist\TowerConquestAnalytics.exe"
Write-Host "The app will open in your browser at http://localhost:8050"
Write-Host ""
Read-Host "Press Enter to exit"
