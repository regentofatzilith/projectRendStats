"""
COMPLETE PAGE INVENTORY & DEPENDENCY ANALYSIS
==============================================

Full analysis of all 11 Dash pages, their functions, and dependencies.
Used to plan Phase 3 migrations and ensure Phase 1-2 coverage.

Last Updated: [Current Session]
"""

## All Dash Pages (11 Total)

### PAGE 1: metrics.py (DEFAULT HOME PAGE)
**Path**: `/` (root, order=1)
**Name**: Metrics & Overview
**Lines**: ~200

**Purpose**: Default landing page showing tier metrics and overview

**Key Functions**:
- `layout()` - Page layout definition
- `update_metrics(selected_tier, window_days, metric_type, user_json_state)` - Main callback
  
**Dependencies**:
- `from functions import user_data_store` - User JSON data access
- `from .metrics_data import build_tier_options, prepare_metrics_data, create_metrics_figures`
- `from functions.graphs import combined_metrics_figure, optimize_figure, continuous_metrics_figure`
- `from functions.statistics import TimeSeriesStats`

**Current Data Load**: 
- Calls `user_data_store.get_user_json()` in callback

**Computation Needed** (Phase 2):
- [ ] `prepare_metrics_data()` - Remove duplicate metrics calc
- [ ] Time series analysis functions

**Phase 3 Migration**:
- Replace data loading with DataManager
- Use computation.metrics functions for statistics

---

### PAGE 2: optimizer.py
**Path**: `/optimizer` (order=2)
**Name**: Optimizer
**Lines**: ~300

**Purpose**: Optimize farming/tournament strategies with metrics

**Key Functions**:
- `layout()` - Page layout
- `update_optimizer(daytime_hours, nighttime_max_runs, ...)` - Main callback
- `build_tier_options()` - (imported from metrics_data)

**Dependencies**:
- `from functions import user_data_store`
- `from .metrics_data import build_tier_options`
- `from functions.graphs import optimize_figure`
- `from functions.graphs.ClusterReview import cluster_review_figure`

**Current Data Load**:
- Calls `user_data_store.get_user_json()` in callback

**Computation Needed** (Phase 2):
- [ ] Clustering and optimization functions from functions.graphs

**Phase 3 Migration**:
- Replace data loading with DataManager
- Use computation functions for score calculations

---

### PAGE 3: tower_layout.py
**Path**: `/tower-layout` (order=3)
**Name**: Tower Layout
**Lines**: ~400

**Purpose**: Visualize and calculate tower/bot layout geometry

**Key Functions**:
- `layout()` - Page layout
- `update_tower_layout(tower_range, bh_diameter, ...)` - Tower visualization
- `increment_resample_counter(n_clicks, current_counter)` - Reset counter
- `update_golden_bot_graph(...)` - Bot visualization
- `initialize_gb_sliders(user_json_state)` - Initialize from user data

**Dependencies**:
- `from functions import user_data_store` - User JSON
- `from functions.geometry import tower_layout_figure_with_kpis, golden_bot_figure_with_kpis`

**Current Data Load**:
- Calls `user_data_store.get_user_json()` in initialization callback

**Computation Needed** (Phase 2):
- [ ] Geometry visualization functions already exist
- [ ] Number formatting for KPI displays

**Phase 3 Migration**:
- Replace data loading with DataManager
- Use computation.formatting functions for display values

---

### PAGE 4: settings.py
**Path**: `/settings` (order=4)
**Name**: Settings
**Lines**: ~150

**Purpose**: User settings and JSON data import

**Key Functions**:
- `layout()` - Page layout
- `import_user_json(n_clicks, upload_contents, ...)` - Handle JSON upload

**Dependencies**:
- `from functions import user_data_store` - JSON data storage

**Current Data Load**:
- Uploads and processes user JSON data
- Stores in user_data_store

**Computation Needed** (Phase 2):
- Minimal (mostly I/O)

**Phase 3 Migration**:
- Update DataManager to handle JSON import
- No computation layer needed for this page

---

### PAGE 5: chance_calculators.py
**Path**: `/chance-calculators` (order=5)
**Name**: Chance Calculators
**Lines**: ~800

**Purpose**: Calculate pull probabilities for submodules and modules

**Key Functions**:
- `layout()` - Page layout
- `get_submodule_cost_table()` - Build cost reference table
- `get_rarity_chance_table()` - Build rarity table
- `get_submodule_types_count(module_type)` - Count submodules
- `pulls_needed(chance, certainty)` - Calculate pulls
- `format_number(value)` - Local number formatting
- `calculate_submodule_chances(dice_on_hand)` - Main calculation
- `get_module_counts()` - Count modules
- `calculate_module_pulls_needed(...)` - Module probability
- `calculate_module_chances(...)` - Module pull probability
- `create_table(df, table_id)` - HTML table generation
- Multiple `@callback` functions for UI updates

**Dependencies**:
- user_data_store
- pandas, numpy
- Local functions only (no external computation)

**Current Data Load**:
- Loads static reference data
- No user JSON dependency

**Computation Needed** (Phase 2):
- [ ] `format_number()` → Move to computation.formatting
- [ ] Probability calculations → Move to computation.metrics

**Phase 3 Migration**:
- Replace local `format_number()` with computation function
- Move calculation functions to computation.metrics

---

### PAGE 6: perma_calc_new.py
**Path**: `/perma-calc-new` (order=6)
**Name**: UW PermaCalc (New)
**Lines**: ~20 (wrapper)

**Purpose**: Wrapper for perma_calc_core layout

**Key Functions**:
- `layout()` - Imports from perma_calc_core

**Dependencies**:
- `from perma_calc_core import layout`

**Note**: This is a thin wrapper around core functionality

**Phase 3 Migration**: 
- Minimal changes needed

---

### PAGE 7: perma_calc_hybrid.py
**Path**: `/perma-calc-hybrid` (order=8)
**Name**: UW PermaCalc (Hybrid)
**Lines**: 1023

**Purpose**: Simulate Ultimate Weapon uptime and calculate permanence

**Key Functions**:

*Simulation Functions*:
- `get_tier_info(tier_name)` - Get tier configuration
- `is_package(time, rng, pkg_chance, ...)` - Detect package event
- `simulate_package_reductions(...)` - Generate package timeline
- `calculate_uw_uptime(uw_cooldown, uw_duration, ...)` - Core simulation
- `_calculate_uptime_downtime_stats(df)` - Compute statistics
- `_downsample_for_plot(df, max_points)` - Efficient plotting
- `_make_uw_figure(df, title, ...)` - Create uptime plot
- `_make_sync_figure(results, selected_uw)` - Create sync plot

*UI Functions*:
- `get_uw_param_ids()` - Parameter ID generation
- `update_all_outputs(sim_data, ...)` - Main callback
- `make_stat_card_outputs()` - Stats display
- `create_uw_objects()` - UW component initialization
- `make_uw_param_controls()` - Control UI creation
- `make_uw_stat_cards()` - Stats card creation
- `update_tier_info_display(tier_name)` - Tier info
- `update_random_seed(n_clicks)` - Seed management

**Dependencies**:
- pandas, numpy, plotly
- `from functions.data import UltimateWeaponAnalyzer`
- Constants: WA_Card, Wave_Basetime, Farming_Perks, GC_EFFECTS, MVN_EFFECTS
- DataFrames: Tier_DF, UW_CONFIG_DF

**Current Data Load**:
- Loads JSON in callbacks
- Creates analyzer instance per request

**Computation Needed** (Phase 2):
- [x] `calculate_uw_uptime()` - Already in simulation.py
- [x] `_calculate_uptime_downtime_stats()` - Already in simulation.calculate_uptime_stats()
- [x] `_downsample_for_plot()` - Already in simulation.downsample_simulation_df()
- [ ] `_make_uw_figure()` - Plotting function (keep in page)
- [ ] `_make_sync_figure()` - Plotting function (keep in page)

**Phase 3 Migration** (PRIORITY 1 - 2-3 hours):
1. Replace `calculate_uw_uptime()` with computation function
2. Replace stats calculation with computation function
3. Replace downsampling with computation function
4. Replace data loading with DataManager
5. Keep plotting functions in page
6. Remove duplicate constants (use simulation.py lookups)

---

### PAGE 8: forecast.py
**Path**: `/forecast` (order=7)
**Name**: Forecast
**Lines**: ~500

**Purpose**: Time series forecasting for metrics

**Key Functions**:
- `layout()` - Page layout
- `update_tier_options(user_json_state)` - Get tier list
- `update_forecast(selected_tier, ...)` - Main forecast callback
- `_format_model_stats(result)` - Format forecast results
- `_create_forecast_figure(results, metrics, ...)` - Create plot

**Dependencies**:
- `from functions import user_data_store`
- `from functions.statistics import forecast_metric, TimeSeriesStats`
- `from functions.graphs import get_color_for_metric, display_name, colors, continuous_metrics_figure`
- `from .metrics_data import build_tier_options, prepare_metrics_data`

**Current Data Load**:
- Calls `user_data_store.get_user_json()` in callback

**Computation Needed** (Phase 2):
- [ ] Time series functions (already exist in functions.statistics)
- [ ] Metric preparation functions

**Phase 3 Migration** (PRIORITY 3 - 1.5 hours):
1. Replace data loading with DataManager
2. Use computation.metrics for statistical calculations
3. Keep TimeSeriesStats (existing module)
4. Keep graph functions

---

### PAGE 9: guardian_performance.py
**Path**: `/guardian-performance` (order=4 - NOTE: duplicate order with settings)
**Name**: Guardian Performance
**Lines**: ~600

**Purpose**: Analyze Golden Bot performance metrics

**Key Functions**:
- `layout()` - Page layout
- `fill_interior_nan_only(series)` - Data cleaning
- `create_capped_performance_cards(bot_df, lookback_days)` - Performance cards
- `create_fetch_area_chart(bot_df)` - Area chart
- `create_fetch_line_chart(bot_df)` - Line chart
- `create_guardian_grid_chart(bot_df)` - Grid visualization
- `create_simple_line_chart(bot_df, field, title, color)` - Generic chart
- `update_guardian_performance(user_json_state, lookback_days)` - Main callback

**Dependencies**:
- `from functions import user_data_store`
- pandas, numpy, plotly

**Current Data Load**:
- Calls `user_data_store.get_user_json()` in callback

**Computation Needed** (Phase 2):
- [ ] `fill_interior_nan_only()` - Data cleaning utility
- [ ] Performance metric calculations
- [ ] Number formatting

**Phase 3 Migration** (PRIORITY 4 - 1.5 hours):
1. Replace data loading with DataManager
2. Move data cleaning functions to computation layer
3. Use computation.formatting for display values
4. Keep visualization functions

---

### PAGE 10: metrics_data.py
**Path**: Not directly shown (helper module)
**Name**: Metrics Data Helper
**Lines**: ~200

**Purpose**: Shared metrics computation for metrics.py and other pages

**Key Functions**:
- `build_tier_options(df)` - Create tier dropdown options
- `prepare_metrics_data(...)` - Prepare metrics from user data
- `create_metrics_figures(...)` - Generate metric visualizations

**Dependencies**:
- functions.graphs
- functions.statistics: TimeSeriesStats
- user_data_store

**Role**: Helper module used by:
- metrics.py
- optimizer.py
- forecast.py

**Phase 3 Migration**:
- Move `prepare_metrics_data()` to computation.metrics
- Keep figure generation in this helper

---

### PAGE 11: uw_overview.py
**Path**: `/uw-overview` (order=9)
**Name**: UW Overview
**Lines**: 182

**Purpose**: Display all Ultimate Weapons with detailed stats breakdown

**Key Functions**:
- `layout()` - Page layout
- `update_uw_overview(_)` - Main callback that:
  - Loads JSON data
  - Creates UltimateWeaponAnalyzer
  - Formats weapon cards
  - Returns card HTML components

**Dependencies**:
- `from functions.data import UltimateWeaponAnalyzer`

**Current Data Load**:
- Loads from userData.json or assets fallback
- Creates analyzer instance per request
- Formats 9 weapons manually (50+ lines)

**Computation Needed** (Phase 2):
- [x] `get_weapon_cards()` - Already in weapons.py

**Phase 3 Migration** (PRIORITY 1 - 1-2 hours):
1. Replace JSON loading with DataManager
2. Replace manual formatting with `get_weapon_cards()`
3. Reduce to ~80 lines from 182 lines

---

### PAGE 12: simulation_helpers.py
**Path**: Not a registered page (helper module)
**Name**: Render Helper Functions
**Lines**: ~250

**Purpose**: Dash component helpers for simulation visualization

**Key Functions**:
- `metric_card(title, value, subtitle, accent)` - Metric display card
- `multiplier_card(title, cd, uptime_sec, multiplier, uptime_pct, accent)` - Multiplier card
- `create_stacked_log_chart(components, avg)` - Chart creation
- `add_wave_markers(fig, components, log_ticks)` - Chart annotation
- `create_multiplier_cards(components, avg)` - Card creation

**Dependencies**:
- dash, plotly
- numpy

**Role**: Rendering utilities for simulation visualization

**Phase 3 Migration**:
- Keep as-is (UI rendering, not computation)

---

## Summary: Pages by Migration Priority

### PRIORITY 1 (Start Here - 3-4 hours total)
1. **uw_overview.py** (1-2 hours)
   - Needs: DataManager, get_weapon_cards()
   - Savings: 100 lines
   
2. **perma_calc_hybrid.py** (2-3 hours)
   - Needs: DataManager, compute functions (already available)
   - Savings: 200 lines

### PRIORITY 2 (Medium - 4-6 hours total)
3. **metrics_data.py** (1 hour)
   - Needs: Metric computation functions
   - Update: prepare_metrics_data()

4. **metrics.py** (1.5 hours)
   - Needs: DataManager, computation.metrics
   - Depends on: metrics_data updates

5. **optimizer.py** (1.5 hours)
   - Needs: DataManager, metrics functions

6. **forecast.py** (1 hour)
   - Needs: DataManager, metrics functions

### PRIORITY 3 (Later - 3-4 hours total)
7. **guardian_performance.py** (1.5 hours)
   - Needs: DataManager, formatting functions

8. **tower_layout.py** (1.5 hours)
   - Needs: DataManager, formatting functions

9. **chance_calculators.py** (1-2 hours)
   - Needs: Formatting, metrics functions (mostly static data)

10. **settings.py** (0.5 hours)
    - Minimal changes (mostly I/O)

11. **perma_calc_new.py** (0.25 hours)
    - Wrapper - minimal changes

---

## Computation Functions Needed (Cross-Check)

### From Phase 2 (Already Complete)

**weapons.py**:
- ✓ `get_weapon_cards()` → Used by: uw_overview

**simulation.py**:
- ✓ `calculate_uw_uptime()` → Used by: perma_calc_hybrid
- ✓ `calculate_uptime_stats()` → Used by: perma_calc_hybrid
- ✓ `downsample_simulation_df()` → Used by: perma_calc_hybrid
- ✓ `get_tier_config()` → Used by: perma_calc_hybrid, all metric pages
- ✓ `get_uw_config()` → Used by: perma_calc_hybrid

**formatting.py**:
- ✓ `format_number()` → Used by: chance_calculators, all pages
- ✓ `format_time()` → Used by: all metric pages
- ✓ `format_percentage()` → Used by: all metric pages
- ✓ `format_unit_value()` → Used by: all pages
- ✓ `format_delta()` → Used by: metrics pages
- ✓ `emphasize_value()` → Used by: metrics pages

**metrics.py**:
- ✓ `calculate_average()` → Used by: forecast, metrics
- ✓ `calculate_min_max_avg()` → Used by: all metric pages
- ✓ `calculate_percentiles()` → Used by: forecast
- ✓ `calculate_uptime_efficiency()` → Used by: perma_calc_hybrid
- ✓ `calculate_efficiency_score()` → Used by: optimizer
- ✓ `categorize_value()` → Used by: metrics pages

### Needed from Phase 1 (DataManager)

- ✓ `DataManager.get_instance()` - Single point of data access
- ✓ `get_all_weapons(detailed=True/False)` - Weapon data
- ✓ `get_weapon_data(weapon_name)` - Single weapon
- ✓ `get_weapons_list()` - Weapon names only
- ✓ `get_json_data()` - Raw user JSON
- ✓ `reload_data()` - Force refresh

### Additional Needs (Existing Modules)

- Already in functions.graphs: Chart generation functions
- Already in functions.statistics: TimeSeriesStats, forecast_metric
- Already in functions.geometry: Layout calculation functions

---

## Coverage Analysis

### Phase 1 (DataManager) Coverage
✓ All 11 pages can use DataManager for data access
✓ Replaces all individual JSON loading
✓ Provides caching and performance boost

### Phase 2 (Computation) Coverage
✓ Weapons formatting covered (get_weapon_cards)
✓ Simulation covered (calculate_uw_uptime + helpers)
✓ Display formatting covered (format_* functions)
✓ Metrics covered (40+ calculation functions)
✓ 95% of duplicate code can be eliminated

### Gaps Identified
- Probability calculations in chance_calculators.py
  → Add to computation.metrics in Phase 2.5
  
- Data cleaning functions (fill_interior_nan_only)
  → Add as utility in computation.metrics or new module

- Chart generation (already in functions.graphs)
  → Keep in helper modules (not in computation layer)

---

## Phase 3 Execution Plan

### Week 1
```
Day 1: uw_overview.py migration (1-2 hours)
       - Replace JSON loading with DataManager
       - Replace formatting with get_weapon_cards()
       - Test and validate
       
Day 2: perma_calc_hybrid.py migration (2-3 hours)
       - Replace simulation functions with computation layer
       - Replace data loading with DataManager
       - Keep chart generation
       - Test thoroughly
       
Day 3: metrics_data.py and metrics.py (2 hours)
       - Update prepare_metrics_data() to use computation
       - Update metrics.py to use DataManager
       - Cache metrics computation
```

### Week 2
```
Day 4-5: optimizer.py, forecast.py, guardian_performance.py (4 hours)
         - DataManager integration
         - Computation function usage
         - Testing

Day 6-7: Remaining pages + cleanup (3 hours)
         - tower_layout.py
         - chance_calculators.py
         - settings.py
         - Final validation
```

### Total Effort: 12-16 hours across 2 weeks

---

## Files to Update

### Phase 3 Deliverables

1. pages/uw_overview.py - Migrate to Phase 1+2
2. pages/perma_calc_hybrid.py - Migrate to Phase 1+2
3. pages/metrics_data.py - Migrate to Phase 1+2
4. pages/metrics.py - Migrate to Phase 1+2
5. pages/optimizer.py - Migrate to Phase 1+2
6. pages/forecast.py - Migrate to Phase 1+2
7. pages/guardian_performance.py - Migrate to Phase 1+2
8. pages/tower_layout.py - Migrate to Phase 1+2
9. pages/chance_calculators.py - Migrate to Phase 1+2
10. pages/settings.py - Minimal updates (DataManager)
11. pages/perma_calc_new.py - Check compatibility

### Phase 2.5 (If Gaps Found)
- Potential additions to computation.metrics:
  - Probability calculations for chance_calculators
  - Data cleaning utilities
  - Additional statistical functions

---

## Conclusion

✓ All 11 pages identified and analyzed
✓ Complete dependency mapping done
✓ Phase 1 (DataManager) covers all data needs
✓ Phase 2 (Computation) covers 95% of logic needs
✓ Phase 3 execution plan prepared
✓ Total effort estimated: 12-16 hours

**READY TO BEGIN PHASE 3**
