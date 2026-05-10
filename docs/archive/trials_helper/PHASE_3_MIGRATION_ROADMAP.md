"""
Phase 3 - Page Migration Roadmap
=================================

Status: NOT STARTED (Ready to begin)
Estimated Timeline: 4-6 hours
Dependencies: Phase 1 (DataManager) ✓ and Phase 2 (Computation) ✓

This document outlines the migration plan for moving pages to use the new
3-layer architecture (Data → Computation → Display).

## Phase 3 Overview

Goal: Eliminate code duplication by migrating pages to use centralized layers

Approach: One page at a time, keeping old code runnable during transition

Strategy: 
1. Create new page version alongside old
2. Test new version thoroughly
3. Swap to new version once validated
4. Remove old code

## Pages to Migrate (Recommended Order)

Priority 1 (Direct dependencies on computation):
1. uw_overview.py - Weapon display + formatting
2. perma_calc_hybrid.py - Simulation + plotting

Priority 2 (Use metrics + formatting):
3. metrics_data.py - Metric calculations
4. forecast.py - Time series + statistics

Priority 3 (Configuration + formatting):
5. tower_layout.py - Formatting + lookups
6. guardian_performance.py - Metrics + formatting
7. optimizer.py - Metrics + graphs
8. chance_calculators.py - Metrics + formatting
9. settings.py - Minimal changes (mostly UI state)

## Detailed Migration Plans

### MIGRATION 1: uw_overview.py
Current Status: Working but duplicates formatting logic
Target: Use DataManager + get_weapon_cards()
Estimated Effort: 1-2 hours

Current Implementation:
```python
# Lines 1-182 (simplified structure)
import json
from functions.data import UltimateWeaponAnalyzer

def update_uw_cards(selected_uw):
    # Load JSON
    with open('assets/userData.json') as f:
        data = json.load(f)
    
    # Create analyzer
    analyzer = UltimateWeaponAnalyzer(data)
    all_weapons = analyzer.get_all_weapons_dict()
    
    # Manual formatting (50+ lines)
    for weapon_name, weapon in all_weapons.items():
        detailed = analyzer.get_detailed(weapon_name)
        # ... build card_data row by row
    
    return card_data
```

Refactored Implementation:
```python
# New uw_overview.py
from functions.data import DataManager
from functions.computation import get_weapon_cards

def update_uw_cards(selected_uw):
    dm = DataManager.get_instance()
    all_weapons = dm.get_all_weapons(detailed=True)
    cards = get_weapon_cards(all_weapons)
    
    # Use cards directly in UI
    return [create_card_component(...) for ...]
```

### Migration Steps:

1. **Update imports**:
   ```python
   # Remove
   import json
   from functions.data import UltimateWeaponAnalyzer
   
   # Add
   from functions.data import DataManager
   from functions.computation import get_weapon_cards
   ```

2. **Replace callback logic**:
   - Remove JSON loading code (5-10 lines)
   - Remove analyzer instantiation
   - Replace manual formatting with get_weapon_cards()
   - Keep UI component creation as-is

3. **Testing**:
   - Compare card output format with current implementation
   - Verify all weapons display correctly
   - Check dark mode text colors (should be unchanged)

4. **Cleanup**:
   - Remove unused imports
   - Remove formatting functions (now in computation layer)

Expected Result: Page reduced from 182 lines to ~80 lines

---

### MIGRATION 2: perma_calc_hybrid.py
Current Status: Complex with inline simulation code
Target: Use DataManager + computation functions
Estimated Effort: 2-3 hours

Focus Areas:
1. Simulation (calculate_uw_uptime)
2. Data loading (DataManager)
3. Plotting (downsample_simulation_df)

Current Key Functions:
- calculate_uw_uptime() - 60+ lines → Replace with computation.calculate_uw_uptime()
- simulate_package_reductions() - 30+ lines → Replace with computation.simulate_package_reductions()
- _calculate_uptime_downtime_stats() - 40+ lines → Replace with computation.calculate_uptime_stats()
- _downsample_for_plot() - 30+ lines → Replace with computation.downsample_simulation_df()

### Migration Steps:

1. **Remove constants** (move to simulation.py):
   - WA_Card, Wave_Basetime, Farming_Perks
   - GC_EFFECTS, MVN_EFFECTS
   - Tier_DF, UW_CONFIG_DF
   - All use get_tier_config() and get_uw_config() instead

2. **Replace simulation code**:
   ```python
   # Old
   df = calculate_uw_uptime(cd, duration, return_df=True)
   stats = _calculate_uptime_downtime_stats(df)
   
   # New
   from functions.computation import (
       calculate_uw_uptime,
       calculate_uptime_stats,
   )
   df = calculate_uw_uptime(cd, duration, return_df=True)
   stats = calculate_uptime_stats(df)
   ```

3. **Replace plotting helpers**:
   ```python
   # Old
   df_plot = _downsample_for_plot(df, max_points=800)
   
   # New
   from functions.computation import downsample_simulation_df
   df_plot = downsample_simulation_df(df, max_points=800)
   ```

4. **Update data loading**:
   - Remove JSON loading from callbacks
   - Use DataManager for tier/weapon configs
   - Remove uptime calculations from page (now in computation layer)

5. **Testing**:
   - Run same tier/weapon combinations as current
   - Compare uptime % results
   - Compare plot output visually
   - Verify boss wave handling

Expected Result: Page reduced from 1023 lines to ~400 lines

---

### MIGRATION 3: metrics_data.py
Current Status: Manual metric calculations
Target: Use computation.metrics functions
Estimated Effort: 1.5 hours

Replacements:
- Manual min/max/avg → calculate_min_max_avg()
- Manual percentile → calculate_percentiles()
- Manual efficiency → calculate_uptime_efficiency()
- Manual categorization → categorize_value()

### Migration Steps:

1. **Replace calculation code**:
   ```python
   from functions.computation import (
       calculate_min_max_avg,
       calculate_percentiles,
       emphasize_value,
   )
   
   # Old
   min_val = min(values)
   max_val = max(values)
   avg = sum(values)/len(values)
   
   # New
   stats = calculate_min_max_avg(values)
   min_val, max_val, avg = stats['min'], stats['max'], stats['avg']
   ```

2. **Add color/emphasis logic**:
   ```python
   result = emphasize_value(
       value=efficiency*100,
       threshold_low=70,
       threshold_high=90
   )
   color = result['color']  # 'danger', 'warning', 'success'
   ```

3. **Testing**:
   - Compare metric values with current calculations
   - Verify color coding matches thresholds

---

### MIGRATION 4: forecast.py
Current Status: Uses time series stats scattered
Target: Use computation.metrics + statistics functions
Estimated Effort: 1.5 hours

Replacements:
- forecast_stats functions → computation functions
- Time series calculations → metrics module
- Rolling averages → calculate_rolling_average()

---

### MIGRATION 5-9: Remaining Pages
Current Status: Various
Target: Centralize formatting + metric calculations
Estimated Effort: 1.5 hours total

For each page:
1. Replace format_number/format_time with computation functions
2. Replace local metric calculations with computation functions
3. Update data loading to use DataManager where applicable
4. Test and cleanup

---

## Testing Strategy for Phase 3

### Functional Testing
```python
# For each migrated page:
# 1. Load page with same inputs as before
# 2. Compare numeric results
# 3. Verify UI rendering

# Specific test cases:
- uw_overview: All 9 weapons display correctly
- perma_calc_hybrid: Uptime % matches old code for 10+ weapon configs
- metrics_data: Min/max/avg values computed identically
- formatting: Numbers, times, percentages format identically
```

### Performance Testing
```python
# Measure before/after:
# - Initial page load time
# - Callback execution time
# - Memory usage
# - DataManager cache hit rate

# Expected improvements:
# - 30-50% faster due to DataManager caching
# - 10-20% less memory due to shared data
```

### Integration Testing
```python
# Test across page boundaries:
# - Switch between pages (DataManager shared)
# - Update one page, check if others reflect changes
# - Test with invalid tier/weapon names
# - Test with edge case values
```

## Rollback Strategy

If issues found during migration:

**Option 1: Parallel Versions**
- Keep old page file as page_old.py
- Create new page_v2.py with new implementation
- Switch via environment variable or config
- Easy A/B testing and rollback

**Option 2: Version Control**
- Commit at each migration step
- Use git branches: page/migrating-xyz
- Roll back specific page via git revert

**Option 3: Feature Flags**
- Use @disable_callback or similar to toggle
- Use environment variable for layer selection

## Success Criteria

Phase 3 is complete when:

✓ All pages refactored to use new layers
✓ No duplicate data loading across pages
✓ No duplicate formatting code
✓ All metrics calculated via computation layer
✓ Performance metrics show 20%+ improvement
✓ All UI output identical to current implementation
✓ Removed 500+ lines of duplicate code
✓ Code passing linting and type checking

## Dependencies and Blockers

**Required Before Phase 3**:
- ✓ Phase 1: DataManager must be working
- ✓ Phase 2: All computation modules must be tested

**Potential Blockers**:
- Page-specific logic that doesn't fit the layers (handle case-by-case)
- Circular dependencies between pages (unlikely given architecture)
- Missing computation functions (identify and add to Phase 2)

## Estimated Timeline

Migration 1 (uw_overview): 1-2 hours
Migration 2 (perma_calc_hybrid): 2-3 hours
Migration 3-5: 1-2 hours each (5-8 total)
Testing & Cleanup: 1-2 hours

**Total: 10-16 hours** (or ~2-3 full days of focused work)

## Phase 3 Verification Checklist

After all page migrations complete:

- [ ] All pages load without errors
- [ ] All pages display correct output
- [ ] DataManager cache working (check via get_load_info())
- [ ] No JSON files loaded from individual pages
- [ ] All formatting uses computation.formatting functions
- [ ] All metrics use computation.metrics functions
- [ ] All simulations use computation.simulation functions
- [ ] Performance profiling shows improvement
- [ ] Code coverage >80% for computation layer
- [ ] Type checking passes (pylance)
- [ ] Linting passes (no warnings)
- [ ] Removed duplicate functions from pages

## Next Steps

After Phase 3 is complete → Phase 4: Cleanup & Optimization

Phase 4 will:
- Profile performance
- Optimize hot paths
- Add caching where beneficial
- Clean up any remaining tech debt
- Documentation of final architecture
"""

# Next Migration: Start with uw_overview.py
# Command to begin: "Migrate uw_overview.py to use DataManager + get_weapon_cards()"
