# ProjectAtzi — Ultimate Weapons + Labs Dashboard

A Dash app to analyze your ProjectRend data even further. Applies statistical methods (weighted averages) to historical data.

## Contents

- Analyze your historical data:
  - Metrics & Overview: Daily income charts (total, per hour), Tier Analysis, Last 7 days Deep Dive.
  - Dissonance Tracker: Current boosts & model future improvements like Lab Upgrades or completing easier Dissonance Runs.
  - Guardian Performance: Track income from Guardians. Optimize your Fetch Guardian.
- Prediction:
  - Optimizer (Weekly): Optimize your week with or without sleep. Is based on average Tier income.
  - Forecast: Projects your historical income and shows potential income in the future.
  - UW PermaCalc (Hybrid): Visualizes UW Sync and allows for testing different cooldown, duration & module combinations.
- Helper Tools:
  - Tower Layout: Review the coverage of your tower range by Black Hole and Golden Bot.
  - Chance Calculators: Simple calculator showing you Reroll Shards or Gems needed to gain a target sub-module stat / module.
  - UW Overview: Work in Progress showing the effective UW substats extracted from userData.json (Modules, Levels, Labs, Relics, Sub-Module Effects).
- Settings:
  - Settings: Allows the import of a userData.json which is not located in the %appdata% folder.
  - Info: Landing page with short descriptions and links to all pages above

## Files of interest

Main File:
- `app.py` — Dash app layout and callbacks (UI, selections, figures, tables)
Statistics:
  - `functions/statistics/weighted_stats.py` — Compute time weighted mean, variance, and confidence intervals.
  - `functions/statistics/score_utils.py` — Reworked score function to be based on 24h income
Other Function Collections:  
  - `functions/geometry/TowerGeometry.py` — Verify why ProjectRend displays BH diameter wrongly
  - `functions/analysis/dissonance.py` — All computations regarding Dissonance

## How to run (Windows)

You can start the app any of these ways:

Navigate to `dist/ProjectRendStats.exe`, download and execute the exe-File.

From Files:
- PowerShell: run `run_app.ps1`
- Command Prompt: run `run_app.bat`
- Python: `python run_app.py`

The app auto-locates your `userData.json` from common locations (including `%APPDATA%\rendapp`). If it can’t find it, place the file in the repository root or update the search logic in `app.py` accordingly.
It will spool up a local server at `http://127.0.0.1:8050/` which you can simply open in your browser.

## Road Map

- Guardian-Performance: Review income Spikes after v28, fix broken Fetch Reroll Shards after v28
- Forecast: Statistics working, but no continuity due to actual dissonance runs and coin income spike
- UW PermaCalc Hybrid: Identify way to identify effective UW and wire in stats accordingly. Allow for assist mods.
- Chance Calculators: List of wanted items. Use of Monte Carlo or math to determine chain of successes and cost to do so.
- UW Overview: For information only. Not specifically wired to anything.
- Time Booster: Include Wave Skip / Intro Sprint calculator including costs associated for their masteries.
