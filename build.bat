@echo off
REM Build script for creating standalone executable
REM Run this from the project root directory

echo ========================================
echo Tower Conquest Analytics - Build Script
echo ========================================
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
    if errorlevel 1 (
        echo Failed to install PyInstaller
        pause
        exit /b 1
    )
)

REM Clean previous builds
echo Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist __pycache__ rmdir /s /q __pycache__

REM Build the executable
echo.
echo Building executable...
echo This may take 5-10 minutes...
echo.

pyinstaller build_exe.spec

if errorlevel 1 (
    echo.
    echo ========================================
    echo Build FAILED!
    echo ========================================
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build SUCCESSFUL!
echo ========================================
echo.
echo Executable location: dist\TowerConquestAnalytics.exe
echo Size: 
dir dist\TowerConquestAnalytics.exe | find "TowerConquestAnalytics.exe"
echo.
echo To run: double-click dist\TowerConquestAnalytics.exe
echo The app will open in your browser at http://localhost:8050
echo.
pause
