"""
Computation Layer - Quick Reference Guide
===========================================

Fast lookup for common computation tasks in Phase 3 (page migrations).
"""

## Import Patterns

### Pattern 1: Import Specific Functions
```python
from functions.computation import get_weapon_cards, calculate_uw_uptime
```

### Pattern 2: Import Modules
```python
from functions.computation import weapons, simulation, formatting
result = weapons.get_weapon_cards(data)
```

### Pattern 3: Mixed Imports
```python
from functions.computation.weapons import get_weapon_cards
from functions.computation import simulation, formatting
```

---

## Common Tasks

### Task 1: Format Ultimate Weapons for Display Card

**Before (Current)**:
```python
for weapon_name in weapon_names:
    weapon_data = analyzer.get_detailed(weapon_name)
    # ... manual formatting
```

**After (Phase 3)**:
```python
from functions.computation import get_weapon_cards
from functions.data import DataManager

dm = DataManager.get_instance()
all_weapons = dm.get_all_weapons(detailed=True)
cards = get_weapon_cards(all_weapons)

# cards[weapon_name] → ready for UI display
```

---

### Task 2: Simulate Ultimate Weapon Uptime

**Before (Current)**:
```python
# Long function inline in perma_calc_hybrid.py
timeline = np.arange(total_time)
# ... 50+ lines of simulation code
```

**After (Phase 3)**:
```python
from functions.computation import calculate_uw_uptime

result = calculate_uw_uptime(
    uw_cooldown=53,      # Golden Core cooldown
    uw_duration=41,      # Duration stays active
    total_time=3600      # 1 hour simulation
)

permanence = result['perma_result']
uptime_timeline = result['perma_active']
```

**For Detailed Analysis**:
```python
from functions.computation import calculate_uw_uptime, calculate_uptime_stats

df = calculate_uw_uptime(
    uw_cooldown=53,
    uw_duration=41,
    total_time=3600,
    return_df=True  # Get full DataFrame
)

stats = calculate_uptime_stats(df)
print(f"Uptime: {stats['uptime_pct']:.1f}%")
print(f"Avg activation interval: {stats['avg_activation_interval']}s")
```

---

### Task 3: Format Time Values

**Before (Current)**:
```python
# Manual string formatting scattered across code
time_str = f"{hours}h {minutes}m {seconds}s"
```

**After (Phase 3)**:
```python
from functions.computation import format_time

# Compact form
time_str = format_time(3661)  # "1h 1m 1s"

# Full form
time_str = format_time(3661, compact=False)  # "1 hour, 1 minute, 1 second"

# Without seconds
time_str = format_time(3661, include_seconds=False)  # "1h 1m"
```

---

### Task 4: Format Numbers

**Before (Current)**:
```python
# Manual formatting
num_str = f"{value:,.1f}"
```

**After (Phase 3)**:
```python
from functions.computation import format_number, format_percentage

# With thousands separator
num_str = format_number(1234567)  # "1,234,567.0"

# As percentage
pct_str = format_percentage(0.45)  # "45.0%"
pct_str = format_percentage(0.45, include_sign=True)  # "+45.0%"
```

---

### Task 5: Calculate Efficiency Metrics

**Before (Current)**:
```python
# Manual calculation
uptime_pct = (active_time / total_time) * 100
efficiency = uptime_pct / 100
```

**After (Phase 3)**:
```python
from functions.computation import calculate_uptime_efficiency, calculate_efficiency_score

# Single metric
efficiency = calculate_uptime_efficiency(3000, 3600)  # 0.833

# Multi-metric score
metrics = {'dmg': 0.8, 'uptime': 0.9, 'speed': 0.7}
weights = {'dmg': 0.4, 'uptime': 0.4, 'speed': 0.2}
score = calculate_efficiency_score(metrics, weights)  # 0.82
```

---

### Task 6: Tier Configuration Lookup

**Before (Current)**:
```python
tier_row = Tier_DF[Tier_DF['name'] == tier_name]
if not tier_row.empty:
    wave_time = tier_row.iloc[0]['wave_time']
```

**After (Phase 3)**:
```python
from functions.computation import get_tier_config

config = get_tier_config("Tier 14")
wave_time = config['wave_time']
boss_waves = config['boss_waves']
```

---

### Task 7: Ultimate Weapon Configuration Lookup

**Before (Current)**:
```python
uw_row = UW_CONFIG_DF[UW_CONFIG_DF['name'] == weapon_name]
base_cooldown = uw_row.iloc[0]['base_cooldown']
```

**After (Phase 3)**:
```python
from functions.computation import get_uw_config

config = get_uw_config("Golden Bot")
base_cooldown = config['base_cooldown']
base_duration = config['base_duration']
can_queue = config['can_queue']
```

---

### Task 8: Downsample Data for Plotting

**Before (Current)**:
```python
# Manual downsampling logic
n = len(df)
if n > max_points:
    # ... complex sampling logic
```

**After (Phase 3)**:
```python
from functions.computation import downsample_simulation_df

df = calculate_uw_uptime(53, 41, total_time=3600, return_df=True)
df_plot = downsample_simulation_df(df, max_points=800)

# df_plot now safe for plotting (preserves important events)
```

---

### Task 9: Statistical Aggregation

**Before (Current)**:
```python
# Manual stats calculation
min_val = min(values)
max_val = max(values)
avg_val = sum(values) / len(values)
```

**After (Phase 3)**:
```python
from functions.computation import calculate_min_max_avg, calculate_percentiles

stats = calculate_min_max_avg([10, 20, 30, 40, 50])
# {'min': 10, 'max': 50, 'avg': 30}

percentiles = calculate_percentiles([1, 2, ..., 100], [25, 50, 75])
# {'p25': 25, 'p50': 50, 'p75': 75}
```

---

### Task 10: Value Categorization

**Before (Current)**:
```python
# Manual if-else chains
if value < 50:
    category = "Low"
elif value < 80:
    category = "Medium"
else:
    category = "High"
```

**After (Phase 3)**:
```python
from functions.computation import categorize_value

category = categorize_value(
    value=75,
    thresholds=[50, 80],
    categories=['Low', 'Medium', 'High']
)  # "Medium"
```

---

## Data Flow Examples

### Example 1: uw_overview.py Refactoring

**Before**:
```python
# Current uw_overview.py
import json
with open('assets/userData.json') as f:
    user_data = json.load(f)

analyzer = UltimateWeaponAnalyzer(user_data)
all_weapons = analyzer.get_all_weapons_dict()

for weapon_name, weapon_data in all_weapons.items():
    detailed = analyzer.get_detailed(weapon_name)
    # ... manual formatting (50 lines)
    cards[weapon_name] = formatted_data
```

**After (Phase 3)**:
```python
# Refactored uw_overview.py
from functions.data import DataManager
from functions.computation import get_weapon_cards

@callback(...)
def display_weapons():
    dm = DataManager.get_instance()
    all_weapons = dm.get_all_weapons(detailed=True)
    cards = get_weapon_cards(all_weapons)
    
    # Use cards directly in UI
    return [create_card_component(name, data) for name, data in cards.items()]
```

**Benefits**:
- Removes 50+ lines of formatting code
- All weapons loaded once in DataManager (cached)
- Formatting reusable by other pages

---

### Example 2: perma_calc_hybrid.py Refactoring

**Before**:
```python
# Current perma_calc_hybrid.py
def calculate_uw_uptime(...):  # 100+ lines
    timeline = np.arange(...)
    # ... complex simulation logic

Package_reduction_series, is_boss_package = simulate_package_reductions(...)
# ... more code

@callback(...)
def update_figure(selected_uw, ...):
    df = calculate_uw_uptime(...)
    # ... plotting code
```

**After (Phase 3)**:
```python
# Refactored perma_calc_hybrid.py
from functions.computation import (
    get_uw_config,
    calculate_uw_uptime,
    downsample_simulation_df,
)

@callback(...)
def update_figure(selected_uw, ...):
    config = get_uw_config(selected_uw)
    df = calculate_uw_uptime(
        config['base_cooldown'],
        config['base_duration'],
        return_df=True
    )
    df_plot = downsample_simulation_df(df, max_points=800)
    # ... create figure from df_plot
```

**Benefits**:
- Removes 100+ lines from page
- Simulation logic centralized and testable
- Configuration lookups simplified

---

### Example 3: metrics_data.py Refactoring

**Before**:
```python
# Current metrics_data.py
uptime_pct = (active_seconds / total_seconds) * 100
min_val = min(values)
max_val = max(values)
avg_val = sum(values) / len(values)
# ... more manual calculations
```

**After (Phase 3)**:
```python
# Refactored metrics_data.py
from functions.computation import (
    calculate_uptime_efficiency,
    calculate_min_max_avg,
    calculate_percentiles,
    emphasize_value,
)

efficiency = calculate_uptime_efficiency(active_seconds, total_seconds)
stats = calculate_min_max_avg(values)
percentiles = calculate_percentiles(values)

# Get color-coded emphasis
emphasized = emphasize_value(efficiency * 100, 70, 90)
color = emphasized['color']  # "success", "warning", or "danger"
```

**Benefits**:
- Consistent calculations across app
- Color/emphasis logic centralized
- Easier to adjust thresholds

---

## Common Patterns

### Pattern 1: Get Data + Transform + Display

```python
from functions.data import DataManager
from functions.computation import get_weapon_cards

dm = DataManager.get_instance()
weapons_detailed = dm.get_all_weapons(detailed=True)
cards = get_weapon_cards(weapons_detailed)
return html.Div([create_card(name, data) for name, data in cards.items()])
```

### Pattern 2: Simulate + Analyze + Display

```python
from functions.computation import (
    calculate_uw_uptime,
    calculate_uptime_stats,
    downsample_simulation_df,
)

df = calculate_uw_uptime(53, 41, return_df=True)
stats = calculate_uptime_stats(df)
df_plot = downsample_simulation_df(df)
# Use df_plot for plotting, stats for display
```

### Pattern 3: Format for Display

```python
from functions.computation import (
    format_time,
    format_percentage,
    format_unit_value,
)

duration_str = format_time(3661, compact=True)  # "1h 1m 1s"
uptime_str = format_percentage(0.833, include_sign=False)  # "83.3%"
cooldown_str = format_unit_value(53, "s")  # "53.0s"
```

---

## Testing Helpers

### Test Simulation Function

```python
from functions.computation import calculate_uw_uptime

# Test permanence case
result = calculate_uw_uptime(53, 41, total_time=3600)
assert result['perma_result'] == True, "Should be permanent"

# Test non-permanent case
result = calculate_uw_uptime(100, 30, total_time=3600)
assert result['perma_result'] == False, "Should not be permanent"

# Test DataFrame output
df = calculate_uw_uptime(53, 41, return_df=True)
assert len(df) == 3600, "Should have 3600 rows"
assert 'is_active' in df.columns, "Should have is_active column"
```

### Test Formatting Functions

```python
from functions.computation import format_time, format_number

assert format_time(3661) == "1h 1m 1s"
assert format_number(1234567) == "1,234,567.0"
assert format_number(1234567, decimal_places=0) == "1,234,567"
```

---

## Troubleshooting

**Issue**: ImportError on computation modules
**Solution**: Ensure `functions/computation/__init__.py` exists with proper imports

**Issue**: Functions return None
**Solution**: Check that required parameters are provided (no defaults for critical params)

**Issue**: Simulation looks different from old code
**Solution**: Verify tier config and package settings match original values

**Issue**: Performance degradation
**Solution**: DataManager caches data; ensure you're using single instance via `get_instance()`

---

## Migration Checklist

For each page migration:

- [ ] Identify all local data loading
- [ ] Replace with DataManager calls
- [ ] Identify all formatting code
- [ ] Replace with computation.formatting functions
- [ ] Identify all calculations
- [ ] Replace with computation.metrics functions
- [ ] Test with same inputs as original
- [ ] Verify output format matches UI expectations
- [ ] Remove now-unused imports
- [ ] Remove now-unused local functions
- [ ] Update docstrings with new dependencies
