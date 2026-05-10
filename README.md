# ProjectAtzi — Ultimate Weapons + Labs Dashboard

A Dash app to analyze and visualize ultimate weapon upgrades, labs bonuses, and module abilities for your rendapp profile. It includes robust data extraction, combined lookup-driven tables, and an at-a-glance schematic for Black Holes and Golden Bot with module effects and rarities.

## Highlights

- Complete lookup tables for ultimate weapons (Black Hole, Death Wave, Golden Bot, Spotlight) including:
  - Upgrade contributions
  - Labs-only bonuses (separated where appropriate)
  - Normalized parameters and fixed cooldown arithmetic
- Module abilities with rarity support:
  - Armor: Primordial Collapse, Multiverse Nexus
  - Generator: Galaxy Compressor, Black Hole Digestor
  - Rarity-aware multipliers and special effects integrated into calculations and UI
- Combined ultimate weapons table enhanced with module + rarity effects:
  - Cooldown synchronization (Multiverse Nexus)
  - Black Hole total count and damage reduction clarifications (Primordial Collapse)
  - Per-package cooldown reduction (Galaxy Compressor)
  - Coins/kill per free upgrade (Black Hole Digestor)
- Black Hole schematic integration:
  - Primordial Collapse now explicitly sets Total Black Holes to 3
  - KPI card shows the effective BH total
- Golden Bot layout improvements forming a 2×3 grid:
  - Graph, KPI panel, and a standalone "Cooldown Reduction / Package" panel for Galaxy Compressor

## Files of interest

- `app.py` — Dash app layout and callbacks (UI, selections, figures, tables)
- `myproject/ImportJSON.py` — Data extraction, upgrade & labs lookups, combined computations
- `myproject/TowerGeometry.py` — Combined table assembly and module effect rows
- `test_todos_extraction.py` — Quick script to validate that workshop/labs todos load correctly
- `run_app.ps1` / `run_app.bat` / `run_app.py` — Options to start the app on Windows

## How to run (Windows)

You can start the app any of these ways:

- PowerShell: run `run_app.ps1`
- Command Prompt: run `run_app.bat`
- Python: `python run_app.py`

The app auto-locates your `userData.json` from common locations (including `%APPDATA%\rendapp`). If it can’t find it, place the file in the repository root or update the search logic in `app.py` accordingly.

## Quick validation

- Import check: `python -c "import app; print('OK')"` should print without errors
- Todo extraction: `python test_todos_extraction.py` prints a summary of workshop and labs todos

## Notes & assumptions

- Rarity dropdowns control the strength of module abilities in both the combined table and UI panels
- Primordial Collapse sets BH total to 3 by design (base 1 + 2 via module effect)
- Labs-only bonus rows are separated where it improves clarity (e.g., Spotlight Damage Mult vs Labs Bonus)
- Time-series and score debug prints shown on import are expected and useful for diagnostics

## Next steps (optional)

- Add explanatory tooltips that break down the BH total (base + module + synergy)
- Add small unit tests for module-specific UI panels
- Wire a linter/formatter (e.g., ruff/black) and a lightweight type check
