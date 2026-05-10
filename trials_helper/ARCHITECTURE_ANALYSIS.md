# Architecture Analysis: Current State vs. Proposed 3-Layer Model

## Current State Analysis

### What Exists Today

**Layer 1: Data Extraction (ImportJSON.py)**
```
extract_ultimate_weapon_upgrades() → DataFrame
extract_golden_bot_info() → DataFrame
extract_relevant_module_upgrades() → DataFrame
extract_relevant_labs_progress() → DataFrame
extract_combined_ultimate_weapons_data() → Dict[str, DataFrame]
```

**Layer 2: Business Logic (UltimateWeapons.py) ✓ GOOD**
```
WeaponParameter dataclass
UltimateWeapon dataclass
UltimateWeaponAnalyzer (main interface)
  ├─ get_consolidated() → Dict[str, float]
  ├─ get_detailed() → Dict[str, Dict]
  ├─ get_all_weapons() → Dict[str, UltimateWeapon]
```

**Layer 3: Caching (DataStore.py)**
```
UserDataStore (global singleton)
  ├─ _combined_weapons_cache
  ├─ get_combined_weapons_data(module)
  ├─ Thread locks for safety
```

**Layer 4: Display (pages/*.py)**
```
uw_overview.py
  ├─ Loads JSON from file (assets/active_manifest.json or userData.json)
  ├─ Creates UltimateWeaponAnalyzer instance
  ├─ Calls get_detailed() in callback
  ├─ Renders cards

perma_calc_hybrid.py
  ├─ Loads JSON from file (same pattern)
  ├─ Creates UltimateWeaponAnalyzer instance
  ├─ Calls get_detailed() in callback
  ├─ Renders simulation
```

---

## Problems Identified

### 1. **JSON Loading is Duplicated**
- ❌ Each page independently loads JSON from file
- ❌ No single source of truth for data
- ❌ Different pages might load different versions
- ❌ I/O happens in display layer (should be data layer)

### 2. **Analyzer is Recreated Per Request**
- ❌ New analyzer created each time a user navigates to a page
- ❌ Expensive computation happens every page view
- ❌ DataStore exists but isn't used for UltimateWeaponAnalyzer
- ❌ No caching of analyzer results

### 3. **DataStore Exists But is Underutilized**
- ❌ Only caches combined_weapons_data (raw DataFrames)
- ❌ Doesn't cache the high-level analyzer
- ❌ Not integrated with UltimateWeapons layer
- ❌ Never called from display pages

### 4. **Display Logic Mixed with Computation**
- ❌ Pages directly handle JSON I/O
- ❌ Each page has its own error handling
- ❌ Computation happens inline in callbacks
- ❌ Hard to reuse computation logic across pages

### 5. **No Single Entry Point for Data Access**
- ❌ Pages directly import ImportJSON
- ❌ Pages directly load JSON files
- ❌ SimulationClass imports ImportJSON directly
- ❌ No consistent way to access data across the app

### 6. **Repeated Computation**
See examples:
- `uw_overview.py`: Line 59-175 - iterates weapons to build cards
- `perma_calc_hybrid.py`: Line 550+ - processes the same analyzer data
- Both do similar filtering, formatting, display logic

---

## Proposed 3-Layer Architecture

### Layer 1: DATA LAYER (`functions/data/DataManager.py`) ⭐ NEW

**Responsibility:** Single source of truth for all data access

```python
class DataManager:
    """Global data manager - singleton pattern"""
    
    _instance = None
    
    def __init__(self):
        self.json_path = self._find_json_path()  # userData or assets/active_manifest
        self.json_data = self._load_json()
        self.analyzer = None  # Created lazily
        self._lock = threading.Lock()
    
    @staticmethod
    def get_instance():
        """Get or create singleton instance"""
        if DataManager._instance is None:
            DataManager._instance = DataManager()
        return DataManager._instance
    
    def _find_json_path(self) -> Path:
        """Find JSON: check userData first, fall back to assets"""
        # Try user's AppData
        # Fall back to assets/active_manifest.json
        
    def _load_json(self) -> Dict[str, Any]:
        """Load and cache JSON data"""
        
    def get_analyzer(self, module: str = "Primordial Collapse") -> UltimateWeaponAnalyzer:
        """Get or create analyzer (cached)"""
        with self._lock:
            if self.analyzer is None:
                self.analyzer = UltimateWeaponAnalyzer(self.json_data, module)
            return self.analyzer
    
    def get_weapon_data(self, weapon_name: str, detailed: bool = False):
        """Get data for single weapon - preferred API"""
        analyzer = self.get_analyzer()
        if detailed:
            return analyzer.get_detailed(weapon_name)
        return analyzer.get_consolidated(weapon_name)
    
    def get_all_weapons(self, detailed: bool = False):
        """Get all weapons - preferred API"""
        analyzer = self.get_analyzer()
        if detailed:
            return analyzer.get_all_detailed()
        return analyzer.get_all_consolidated()
    
    def reload_data(self):
        """Force reload of JSON and analyzer (for dev/testing)"""
        self.json_data = self._load_json()
        self.analyzer = None
```

**Usage:**
```python
data_mgr = DataManager.get_instance()
chrono = data_mgr.get_weapon_data("Chrono Field", detailed=True)
all_weapons = data_mgr.get_all_weapons(detailed=False)
```

---

### Layer 2: COMPUTATION LAYER (`functions/computation/`) ⭐ NEW

**Responsibility:** Stateless functions that transform data

```
functions/computation/
├── __init__.py
├── weapons.py         # UW-specific computations
├── stats.py           # Statistical computations
├── simulation.py      # Simulation computations
└── aggregation.py     # Multi-weapon aggregations
```

**Example: `functions/computation/weapons.py`**
```python
def get_weapon_cards(weapons_detailed: Dict) -> Dict[str, Card]:
    """Transform detailed weapon data into card format for display"""
    cards = {}
    for weapon_name, params in weapons_detailed.items():
        cards[weapon_name] = {
            "name": weapon_name,
            "parameters": [
                {
                    "name": param_name,
                    "uw_effect": param["uw_value"],
                    "lab_effect": param["labs_value"],
                    "module_effect": param["module_value"],
                    "relic_effect": param["relic_value"],
                    "total": param["total_value"],
                    "unit": param["unit"]
                }
                for param_name, param in params.items()
            ]
        }
    return cards

def get_weapon_summary(weapon_detailed: Dict) -> Dict:
    """Get summary stats for a weapon"""
    # Aggregate all parameters
    # Calculate totals, averages, etc.
```

**Usage:**
```python
data_mgr = DataManager.get_instance()
detailed_data = data_mgr.get_all_weapons(detailed=True)
cards = get_weapon_cards(detailed_data)
# Pass cards to display layer
```

---

### Layer 3: DISPLAY LAYER (pages/*.py)

**Responsibility:** Pure Dash UI - no data loading, no computation

```python
# pages/uw_overview.py (SIMPLIFIED)

@callback(
    Output("uw-overview-content", "children"),
    Input("uw-overview-loading", "children"),
)
def update_uw_overview(_: Any) -> Any:
    """Generate the UW overview cards."""
    try:
        # Layer 1: Get data (single source of truth)
        data_mgr = DataManager.get_instance()
        weapons_detailed = data_mgr.get_all_weapons(detailed=True)
        
        # Layer 2: Transform data
        cards_data = get_weapon_cards(weapons_detailed)
        
        # Layer 3: Render UI
        return render_weapon_cards(cards_data)
        
    except Exception as e:
        return dbc.Alert(f"Error: {e}", color="danger")
```

**Benefits:**
- No JSON loading
- No business logic
- No repeated computation
- Pure presentation logic
- Testable (mock data_mgr and compute functions)

---

## Migration Path: Incremental (Recommended)

### Why NOT a clean slate:
- UltimateWeapons refactoring is already good (Layer 2 ✓)
- Existing pages work (just inefficient)
- Can verify each migration works
- Lower risk than full rewrite

### Steps:

**Phase 1: Create DataManager (Day 1)**
```
- Create functions/data/DataManager.py
- Integrate with existing UltimateWeaponAnalyzer
- Add tests for DataManager
- No changes needed to existing pages yet
```

**Phase 2: Create Computation Layer (Day 2-3)**
```
- Create functions/computation/weapons.py
- Create stateless functions for card rendering
- Create tests for each computation function
- No changes needed to existing pages yet
```

**Phase 3: Migrate Pages One by One (Day 4+)**
```
- UW Overview page → simplify, use DataManager + compute functions
- PermaCalc Hybrid page → simplify, remove duplicate logic
- Other pages as needed
```

**Phase 4: Cleanup (Day 5+)**
```
- Remove deprecated functions
- Consolidate error handling
- Add global result caching if needed
```

---

## Benefits of Proposed Architecture

| Aspect | Current | Proposed |
|--------|---------|----------|
| **Data Loading** | Duplicated in each page | Single DataManager |
| **Analyzer Caching** | Not cached | Global cached instance |
| **Code Reuse** | Difficult, duplicated logic | Stateless computation functions |
| **Testing** | Hard to test pages | Easy to test computation functions |
| **Performance** | JSON loaded per request | Loaded once at startup |
| **Maintainability** | Scattered logic | Clear separation of concerns |
| **Debugging** | Trace through pages | Trace through layers |

---

## Comparison: Clean Slate vs. Incremental

### Clean Slate Approach
**Pros:**
- Start completely fresh
- No legacy constraints
- Optimal architecture from day 1

**Cons:**
- More work (rewrite all pages)
- Higher risk (might break things)
- Longer development time
- Need to migrate existing features

### Incremental Refactoring (RECOMMENDED)
**Pros:**
- Build on existing good work (UltimateWeapons ✓)
- Lower risk (test each phase)
- Can deploy incrementally
- Verify migrations work

**Cons:**
- Might have temporary duplication
- Requires discipline to avoid old patterns
- Phase 3 has some messy transition time

## Recommendation

**✅ INCREMENTAL REFACTORING**

Reasons:
1. UltimateWeapons layer is already solid
2. Lower risk - can verify each step
3. Can deploy changes incrementally
4. Existing features keep working during transition
5. Learn what works before committing to full rewrite
6. 80/20 rule: Get most benefits with less effort

---

## Estimated Effort

- **DataManager + Tests**: 2-3 hours
- **Computation Layer + Tests**: 3-4 hours  
- **Migrate uw_overview.py**: 1-2 hours
- **Migrate perma_calc_hybrid.py**: 1-2 hours
- **Other migrations**: 2-3 hours
- **Testing & cleanup**: 2-3 hours

**Total: 12-18 hours** → Could be done over a few days

---

## Next Steps

If you agree with this approach:

1. ✅ Create `functions/data/DataManager.py` (single source of truth)
2. ✅ Create `functions/computation/weapons.py` (stateless rendering)
3. ✅ Migrate `uw_overview.py` first (simplest page)
4. ✅ Verify it works
5. ✅ Migrate other pages
6. ✅ Remove duplicates and clean up

Would you like me to start with Phase 1 (DataManager)?
