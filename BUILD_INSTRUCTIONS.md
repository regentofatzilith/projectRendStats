# Tower Conquest Analytics - Build Instructions

## Building the Standalone Executable

### Linux Support
Yes, the project can be built and shipped for Linux.

Important: PyInstaller does not cross-compile. You must build on Linux for a Linux binary.
Use a native Linux machine, VM, WSL2, Docker container, or CI Linux runner.

### Prerequisites
- Python 3.13+ installed
- All dependencies installed: `pip install -r requirements.txt`

### Build Steps

#### Option 1: Automated Build (Windows)
```bash
# Simply run the build script
build.bat
```

#### Option 2: Manual Build
```bash
# Install PyInstaller
pip install pyinstaller

# Clean previous builds
rmdir /s /q build dist

# Build the executable
pyinstaller build_exe.spec
```

#### Option 3: Linux Build
```bash
# Make script executable (first time only)
chmod +x build_linux.sh

# Build on Linux
./build_linux.sh
```

Manual Linux build command:
```bash
python3 -m PyInstaller build_linux.spec
```

### Build Output
- **Location:** `dist/TowerConquestAnalytics.exe`
- **Expected Size:** ~150-300 MB (includes Python runtime + all libraries)
- **First Run:** May take 5-10 seconds to start (unpacking)

Linux output:
- **Location:** `dist/TowerConquestAnalytics/`
- **Run:** `./dist/TowerConquestAnalytics/TowerConquestAnalytics`

### Running the Executable
1. Double-click `TowerConquestAnalytics.exe`
2. A console window will open (showing status)
3. Your browser will automatically open to `http://localhost:8050`
4. Go to Settings page and load your `userData.json`

### Troubleshooting

#### Build Fails with Import Errors
- Check that all dependencies are installed: `pip install -r requirements.txt`
- Try adding missing module to `hiddenimports` in `build_exe.spec`

#### Executable Won't Start
- Run from command line to see error messages: `.\dist\TowerConquestAnalytics.exe`
- Check Windows Defender/Antivirus isn't blocking it

#### Browser Doesn't Open
- Manually open browser and go to `http://localhost:8050`
- Check console window for error messages

#### Missing Assets/Pages
- Ensure `assets/` and `pages/` folders are in same directory as build script
- Check `datas` list in `build_exe.spec` includes all necessary folders

### Distribution
To share with others:
1. Create a folder with:
   - `TowerConquestAnalytics.exe`
   - `README.md` (user instructions)
2. Zip the folder
3. Share via Google Drive, Discord, etc.

**Note:** Users do NOT need Python installed to run the .exe!

### Advanced: Hide Console Window
In `build_exe.spec`, change:
```python
console=True,  # Change to False
```
This hides the console window, but keep it True while testing for easier debugging.

### Advanced: Add Custom Icon
1. Create or download a `.ico` file
2. Place it in `assets/icon.ico`
3. In `build_exe.spec`, change:
```python
icon='assets/icon.ico',
```

## File Structure After Build
```
ProjectAtzi/
├── build/              (temporary build files - can delete)
├── dist/
│   └── TowerConquestAnalytics.exe  (distributable executable)
├── build_exe.spec      (PyInstaller configuration)
└── build.bat           (automated build script)
```
