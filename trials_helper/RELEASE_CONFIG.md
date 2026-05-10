# Release Configuration Summary

## Build Date
January 17, 2026

## Included Pages
✅ **Metrics** - Daily Results and performance tracking
✅ **Forecast** - Predictive analytics with multiple models (exponential, sigmoidal, ensemble, etc.)
✅ **Settings** - User data import configuration
✅ **Tower Layout** - Tower configuration visualization
✅ **Guardian Performance** - Guardian effectiveness analysis
✅ **Chance Calculators** - Game mechanic probability calculators
✅ **Perma Calc (New)** - Permanent upgrade calculations

## Excluded from Build
❌ **Simulation** - Moved to `trials_helper/simulation.py.excluded`
❌ **Perma Calc (Old)** - Already in `trials_helper/`, using perma_calc_new instead

## Default userData.json Path

**Dynamic Path (works for any Windows user):**
```
%APPDATA%\rendapp\userData.json
```

**Resolves to:**
```
C:\Users\<CurrentWindowsUser>\AppData\Roaming\rendapp\userData.json
```

This is automatically detected using:
- `os.getenv("APPDATA")` environment variable
- Fallback: `Path.home() / "AppData" / "Roaming"`

**Note:** The game stores userData.json in:
```
C:\Users\<User>\AppData\LocalLow\Boolba Games\Tower Conquest\userData.json
```

If users have their data there instead, they can use "Custom Path" option in Settings.

## Build Configuration

### PyInstaller Settings
- **Single File:** Yes (`--onefile`)
- **Console Window:** Visible (for status/debugging)
- **Icon:** None (can be added later)
- **UPX Compression:** Enabled

### Dependencies Bundled
- Python 3.13 runtime
- dash 3.2.0
- plotly 6.3.1
- pandas 2.3.3
- numpy 2.3.3
- scipy 1.16.2
- scikit-learn 1.8.0
- dash-bootstrap-components 2.0.4
- All project modules (functions/, pages/, assets/)

### Excluded from Bundle
- matplotlib (unused)
- tkinter, PyQt5, PySide2 (GUI toolkits)
- pages.simulation
- pages.perma_calc (old version)

## File Size Estimate
**Expected:** 150-300 MB (single .exe file)

## Distribution Structure
```
TowerConquestAnalytics/
├── TowerConquestAnalytics.exe  (standalone executable)
└── README.md                   (user instructions)
```

**Optional additions for distribution:**
- Quick Start Guide
- Sample userData.json
- Changelog
- License

## Auto-start Behavior
1. Executable starts embedded Python + Dash server
2. Opens default browser to `http://localhost:8050`
3. Console window shows server status
4. Ready to use immediately

## User Instructions
1. Download and extract
2. Double-click `TowerConquestAnalytics.exe`
3. Wait for browser to open (~5-10 seconds first run)
4. Go to Settings → Import userData.json
5. Browse to game data location or use default path

## Testing Checklist
Before distribution:
- [ ] Build completes without errors
- [ ] .exe starts successfully
- [ ] Browser opens automatically
- [ ] Settings page loads userData.json from default path
- [ ] All included pages render correctly
- [ ] Metrics charts display properly
- [ ] Forecast models work with all types
- [ ] No console errors during normal usage
- [ ] Can close and restart without issues

## Version
**Release:** 1.0.0
**Build Type:** Standalone Windows Executable
**Target OS:** Windows 10/11 (64-bit)
