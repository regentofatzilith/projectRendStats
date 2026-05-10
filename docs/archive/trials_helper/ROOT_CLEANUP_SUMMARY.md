# Root Folder Cleanup - Summary

## Date: 2026-01-17

## Overview
Cleaned up the root folder to contain only **essential files needed to run the application**.

## Final Root Structure

```
ProjectAtzi/
├── app.py                      # Main application entry point ✓ REQUIRED
├── requirements.txt            # Python dependencies ✓ REQUIRED
├── perma_calc_core.py          # Core PermaCalc logic (imported by pages/perma_calc_new.py) ✓ REQUIRED
├── README.md                   # Project documentation
├── RENDER_DEPLOYMENT.md        # Deployment guide
├── render_requirements.txt     # Deployment-specific requirements
│
├── assets/                     # Static assets (CSS, JSON data) ✓ REQUIRED
├── functions/                  # Business logic package ✓ REQUIRED
├── pages/                      # Dash application pages ✓ REQUIRED
├── deploy_render/              # Deployment configurations
├── tests_debug/                # Test and debug scripts
├── trials_helper/              # Helper scripts and legacy code (NOT REQUIRED)
└── .venv/                      # Virtual environment
```

## Files Moved to trials_helper/

### Utility Scripts (18 files)
- analyze_json.py
- clean_lab_and_workshop.py
- generate_active_manifest.py
- merge_lab_overrides.py
- merge_workshop_partial.py
- reorg_app_layout.py
- scrape_lab_upgrades.py
- scrape_workshop_enhancements.py
- scrape_workshop_upgrades.py
- scrape_workshop_upgrade_tables.py
- write_app_file.py
- write_graphs_file.py
- verify_refactoring.py
- run_app.py
- run_app.bat
- run_app.ps1
- PermaCalc.py (legacy, superseded by perma_calc_core.py)
- perma_calc.py (disabled page, superseded by perma_calc_new.py)

### Documentation (6 files)
- BOSS_WAVE_FEATURE.md
- BOSS_WAVE_UI_GUIDE.md
- PERMA_CALC_STANDALONE.md
- QUICK_REFERENCE.md
- REFACTORING_SUMMARY.md
- SIMULATION_REFACTORING.md

### Legacy Code (1 folder)
- myproject/ (old package structure, superseded by functions/)

**Total: 25 files/folders moved**

## Files Remaining in Root

### Essential for Running App (3 files)
1. **app.py** - Main application entry point
2. **requirements.txt** - Python dependencies
3. **perma_calc_core.py** - Core PermaCalc functionality (imported by pages/perma_calc_new.py)

### Documentation (3 files)
1. **README.md** - Project overview and usage
2. **RENDER_DEPLOYMENT.md** - Deployment instructions
3. **render_requirements.txt** - Deployment-specific dependencies

### Essential Folders (4 folders)
1. **assets/** - Static resources (CSS, JSON configurations)
2. **functions/** - Business logic (data, geometry, graphs, simulation, statistics)
3. **pages/** - Dash application pages
4. **deploy_render/** - Deployment configurations

### Other Folders (2 folders)
1. **tests_debug/** - Test and debug scripts
2. **trials_helper/** - Helper scripts and legacy code (can be archived/deleted)

## Verification

✓ App tested and loads successfully with 8 pages registered:
- Metrics & Optimizer
- Simulation
- Tower Layout
- Guardian Performance
- Settings
- Chance Calculators
- UW PermaCalc (New)
- Forecast

## Benefits

1. **Cleaner Root** - Only essential files at the top level
2. **Clear Purpose** - Easy to see what's needed vs. what's helper code
3. **Easier Deployment** - Less confusion about what to include
4. **Maintainability** - Helper scripts organized and documented
5. **Reduced Clutter** - 25 items moved out of root folder

## Next Steps

Consider:
1. Archive `trials_helper/` to a separate repository or zip file
2. Update deployment scripts to exclude `trials_helper/`
3. Add `trials_helper/` to `.gitignore` if desired
