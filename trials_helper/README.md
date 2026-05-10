# trials_helper

This folder contains helper scripts, utilities, and legacy code that are **not required** to run the main application (`app.py`).

## Contents

### Utility Scripts
These are helper scripts for various development tasks:

- **analyze_json.py** - Analyzes userData.json and generates CSV reports
- **clean_lab_and_workshop.py** - Data cleanup utility
- **generate_active_manifest.py** - Generates manifest file
- **merge_lab_overrides.py** - Merges lab override data
- **merge_workshop_partial.py** - Merges workshop data
- **scrape_lab_upgrades.py** - Web scraper for lab upgrade data
- **scrape_workshop_enhancements.py** - Web scraper for workshop enhancements
- **scrape_workshop_upgrades.py** - Web scraper for workshop upgrades
- **scrape_workshop_upgrade_tables.py** - Web scraper for workshop tables
- **verify_refactoring.py** - Tests the package refactoring
- **write_app_file.py** - Generates app.py (legacy)
- **write_graphs_file.py** - Generates graph code (legacy)
- **reorg_app_layout.py** - Layout reorganization script

### Alternative Runners
- **run_app.py** - Alternative app runner (legacy, superseded by app.py)
- **run_app.bat** - Windows batch file to run the app
- **run_app.ps1** - PowerShell script to run the app

### Legacy Code
- **myproject/** - Old package structure (superseded by `functions/`)
- **PermaCalc.py** - Old PermaCalc implementation (superseded by perma_calc_core.py)
- **perma_calc.py** - Disabled page (superseded by pages/perma_calc_new.py)

### Documentation
- **BOSS_WAVE_FEATURE.md** - Boss wave feature documentation
- **BOSS_WAVE_UI_GUIDE.md** - Boss wave UI guide
- **PERMA_CALC_STANDALONE.md** - PermaCalc standalone deployment guide
- **QUICK_REFERENCE.md** - Package refactoring quick reference
- **REFACTORING_SUMMARY.md** - Detailed refactoring summary
- **SIMULATION_REFACTORING.md** - Simulation refactoring documentation

## Usage

These files are kept for reference and development purposes. They can be:
- Used as reference when developing new features
- Run standalone for data processing tasks
- Archived or deleted if no longer needed

## Note

**None of these files are required to run the main application.** The application only needs:
- `app.py`
- `requirements.txt`
- `perma_calc_core.py` (imported by pages/perma_calc_new.py)
- `functions/` package
- `pages/` package
- `assets/` folder
