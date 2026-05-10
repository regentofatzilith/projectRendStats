# Ultimate Weapons Lookup Structure Proposal

## Current State Analysis

### Current Structure Issues
- **Flat namespace**: Individual lookups scattered (e.g., `GOLDEN_TOWER_BONUS_LOOKUP`, `GOLDEN_TOWER_DURATION_LOOKUP`)
- **No single entry point**: No unified way to check completeness across all weapons/parameters
- **Labs lookup fragmentation**: Separate `LABS_LOOKUPS` dict with tuple keys `("Weapon", "Parameter")`
- **Difficult to audit**: Hard to verify all weapons have all expected parameter sources
- **Growth problem**: New sources (Relics, Modules, Assist Mods) hard to track systematically

---

## Proposed Hierarchical Structure

### Top-Level Organization
```python
UW_NAME_LOOKUP = {
    "UW_LEVELS": { ... },      # Workshop upgrades (base/intrinsic values)
    "UW_LABS": { ... },        # Labs research bonuses
    "UW_RELIC": { ... },       # Relic contributions
    "UW_MODULES": { ... },     # Module submodule effects
    "UW_ASSIST_MODS": { ... }  # Assist mod substats
}
```

---

## Detailed Proposed Structure (With All Weapons)

### 1. UW_LEVELS (Workshop Upgrades Base Values)

**Golden Tower**
```python
"GOLDEN_TOWER": {
    "Bonus": GOLDEN_TOWER_BONUS_LOOKUP,     # 0-20, values: 5.0 to 21.0
    "Duration": GOLDEN_TOWER_DURATION_LOOKUP,  # 0-38, values: 15 to 53
    "Cooldown": GOLDEN_TOWER_COOLDOWN_LOOKUP   # 0-20, values: 300 to 100
}
```

**Black Hole**
```python
"BLACK_HOLE": {
    "Size": BLACK_HOLE_SIZE_LOOKUP,        # 0-20, values: 30 to 70
    "Duration": BLACK_HOLE_DURATION_LOOKUP,    # 0-23, values: 15 to 38
    "Cooldown": BLACK_HOLE_COOLDOWN_LOOKUP,    # 0-15, values: 200 to 50
    "Bonus": BLACK_HOLE_BONUS_LOOKUP  # *** MISSING - needs implementation
}
```

**Death Wave**
```python
"DEATH_WAVE": {
    "Damage": DEATH_WAVE_DAMAGE_LOOKUP,    # 0-30, values: 2 to 9119
    "Bonus": DEATH_WAVE_BONUS_LOOKUP,      # 0-30, alias to Damage
    "Quantity": DEATH_WAVE_QUANTITY_LOOKUP,  # 0-4, values: 1 to 5
    "Cooldown": DEATH_WAVE_COOLDOWN_LOOKUP   # 0-25, values: 300 to 50
}
```

**Golden Bot**
```python
"GOLDEN_BOT": {
    "Duration": GOLDEN_BOT_DURATION_LOOKUP,    # 1-30, values: 20.5 to 35.0
    "Cooldown": GOLDEN_BOT_COOLDOWN_LOOKUP,    # 1-15, values: 117 to 75
    "Bonus": GOLDEN_BOT_BONUS_LOOKUP,          # 1-30, values: 2.2 to 8.0
    "Range": GOLDEN_BOT_RANGE_LOOKUP           # 1-15, values: 22 to 50
    # *** MISSING: Health, possibly other parameters
}
```

**Spotlight**
```python
"SPOTLIGHT": {
    "Bonus": SPOTLIGHT_DAMAGE_MULT_LOOKUP,  # 0-25, values: 8.0 to 43.0
    "Angle": SPOTLIGHT_ANGLE_LOOKUP,           # 0-90, values: 30 to 90
    "Quantity": SPOTLIGHT_QUANTITY_LOOKUP      # 0-3, values: 1 to 4
    # *** MISSING: Other parameters if they exist
}
```

**Chrono Field**
```python
"CHRONO_FIELD": {
    "Duration": CHRONO_FIELD_DURATION_LOOKUP,  # 0-35, values: 5 to 40
    "Cooldown": CHRONO_FIELD_COOLDOWN_LOOKUP,  # 0-12, values: 180 to 60
    "Slow %": CHRONO_FIELD_SLOW_LOOKUP         # 0-11, values: 20 to 75
}
```

**Summon Guardian** ⚠️ MISSING LOOKUPS
```python
"SUMMON_GUARDIAN": {
    "Duration": SUMMON_GUARDIAN_DURATION_LOOKUP,
    "Cooldown": SUMMON_GUARDIAN_COOLDOWN_LOOKUP,
    "Bonus": SUMMON_GUARDIAN_BONUS_LOOKUP
}
```

**Smart Missiles** ⚠️ MISSING LOOKUPS
```python
"SMART_MISSILES": {
    "Duration": SMART_MISSILES_DURATION_LOOKUP,
    "Cooldown": SMART_MISSILES_COOLDOWN_LOOKUP,
    "Damage": SMART_MISSILES_DAMAGE_LOOKUP,
    "Quantity": SMART_MISSILES_QUANTITY_LOOKUP
}
```

**Inner Land Mines** ⚠️ MISSING LOOKUPS
```python
"INNER_LAND_MINES": {
    "Duration": INNER_LAND_MINES_DURATION_LOOKUP,
    "Cooldown": INNER_LAND_MINES_COOLDOWN_LOOKUP,
    "Damage": INNER_LAND_MINES_DAMAGE_LOOKUP,
    "Quantity": INNER_LAND_MINES_QUANTITY_LOOKUP
}
```

**Poison Swamp** ⚠️ MISSING LOOKUPS
```python
"POISON_SWAMP": {
    "Duration": POISON_SWAMP_DURATION_LOOKUP,
    "Cooldown": POISON_SWAMP_COOLDOWN_LOOKUP,
    "Damage": POISON_SWAMP_DAMAGE_LOOKUP,
    "Slow %": POISON_SWAMP_SLOW_LOOKUP
}
```

---

### 2. UW_LABS (Labs Research Bonuses)

```python
"GOLDEN_TOWER": {
    "Duration": GOLDEN_TOWER_DURATION_LABS_LOOKUP,     # 0-20, values: 0 to 20
    "Bonus": GOLDEN_TOWER_BONUS_LABS_LOOKUP            # 0-25, values: 0 to 3.75
}
"BLACK_HOLE": {
    "Bonus": BLACK_HOLE_BONUS_LABS_LOOKUP              # 0-20, values: 0 to 11.00
}
"DEATH_WAVE": {
    "Bonus": DEATH_WAVE_BONUS_LABS_LOOKUP              # 0-20, values: 0 to 2.45
}
"GOLDEN_BOT": {
    "Cooldown": GOLDEN_BOT_COOLDOWN_LABS_LOOKUP,       # 0-25, values: 0 to -25
    "Duration": GOLDEN_BOT_DURATION_LABS_LOOKUP        # 0-20, values: 0 to 10.00
}
"SPOTLIGHT": {
    "Bonus": SPOTLIGHT_BONUS_LABS_LOOKUP               # 0-20, values: 0 to 3.00
}
"CHRONO_FIELD": {
    "Duration": CHRONO_FIELD_DURATION_LABS_LOOKUP      # 0-30, values: 0 to 30
}
```

**Missing Labs Research:**
- Summon Guardian (all parameters)
- Smart Missiles (all parameters)
- Inner Land Mines (all parameters)
- Poison Swamp (all parameters)

---

### 3. UW_RELIC (Relic Contributions)

**Status: Currently unused/planned**

Placeholder structure for future relic system:
```python
"GOLDEN_TOWER": {
    "Bonus": {},
    "Duration": {}
}
# ... etc for all weapons
```

---

### 4. UW_MODULES (Module Submodule Effects)

From `submodule_effects.json`:

**Golden Tower** (from file):
```python
"GOLDEN_TOWER": {
    "Bonus": {"Common": None, "Rare": None, "Epic": 1, "Legendary": 2, "Mythic": 3, "Ancestral": 4},
    "Duration": {"Common": None, "Rare": None, "Epic": None, "Legendary": 2, "Mythic": 4, "Ancestral": 7},
    "Cooldown": {"Common": None, "Rare": None, "Epic": None, "Legendary": -5, "Mythic": -8, "Ancestral": -12}
}
```

**Other modules:** Need to extract from `submodule_effects.json`

---

### 5. UW_ASSIST_MODS (Assist Mod Substats)

**Status: Tracked but not yet structured**

---

## Completeness Checklist

### ✅ Implemented & Complete
- [x] Golden Tower: Bonus, Duration, Cooldown (UW_LEVELS)
- [x] Golden Tower: Duration, Bonus (UW_LABS)
- [x] Black Hole: Size, Duration, Cooldown (UW_LEVELS)
- [x] Black Hole: Bonus (UW_LABS)
- [x] Death Wave: Damage, Quantity, Cooldown (UW_LEVELS)
- [x] Death Wave: Bonus (UW_LABS)
- [x] Golden Bot: Duration, Cooldown, Bonus, Range (UW_LEVELS)
- [x] Golden Bot: Cooldown, Duration (UW_LABS)
- [x] Spotlight: Bonus (Damage Mult), Angle, Quantity (UW_LEVELS)
- [x] Spotlight: Bonus (UW_LABS)
- [x] Chrono Field: Duration, Cooldown, Slow % (UW_LEVELS)
- [x] Chrono Field: Duration (UW_LABS)

### ⚠️ Partially Implemented
- [ ] Black Hole: Bonus (UW_LEVELS) - **MISSING**
- [ ] Golden Bot: Health (UW_LEVELS) - **MISSING**
- [ ] Golden Tower: Modules - **Need to structure from JSON**
- [ ] Black Hole: Modules - **Need to structure from JSON**
- [ ] Other weapon modules - **Need to structure from JSON**

### ❌ Not Implemented (Weapons Exist But No Lookups)
- [ ] Summon Guardian: All UW_LEVELS parameters
- [ ] Summon Guardian: All UW_LABS parameters
- [ ] Smart Missiles: All UW_LEVELS parameters
- [ ] Smart Missiles: All UW_LABS parameters
- [ ] Inner Land Mines: All UW_LEVELS parameters
- [ ] Inner Land Mines: All UW_LABS parameters
- [ ] Poison Swamp: All UW_LEVELS parameters
- [ ] Poison Swamp: All UW_LABS parameters

### 📋 Planned/Future
- [ ] UW_RELIC: All weapons (awaiting relic system)
- [ ] UW_ASSIST_MODS: Full structuring (exists informally)

---

## Implementation Steps

### Phase 1: Create Hierarchical Structure (Refactoring Existing)
1. Rename `GOLDEN_TOWER_LOOKUPS` → `UW_LEVELS["GOLDEN_TOWER"]`
2. Consolidate `LABS_LOOKUPS` → `UW_LABS` grouped by weapon
3. Move module effects from JSON to `UW_MODULES` structure
4. Add `UW_RELIC` and `UW_ASSIST_MODS` placeholders
5. **⭐ Add `UW_SOURCES_MAP` to flag which sources are available per parameter** (See [UW_SOURCES_FLAGGING_GUIDE.md](UW_SOURCES_FLAGGING_GUIDE.md))

### Phase 2: Add Validation & Audit Functions
```python
def audit_uw_lookups():
    """Verify completeness and consistency."""
    expected_weapons = {
        "GOLDEN_TOWER": {"Bonus", "Duration", "Cooldown"},
        "BLACK_HOLE": {"Size", "Duration", "Cooldown", "Bonus"},
        # ... etc
    }
    
    for weapon, params in expected_weapons.items():
        # Check UW_LEVELS
        # Check UW_LABS
        # Check consistency (level ranges, value types)
        # Report gaps

# NEW: Helper functions for sources checking (for uw_overview.py)
def has_source(weapon, param, source) -> bool
def get_available_sources(weapon, param) -> frozenset
def format_sources_for_display(weapon, param) -> str
```

### Phase 3: Add Missing Lookups
1. Extract Summon Guardian, Smart Missiles, Inner Land Mines, Poison Swamp from workshop JSON
2. Add missing labs research if available
3. Validate level ranges and value types

### Phase 4: Update Consumer Code
1. Update `ImportJSON.py` to use new structure
2. Update `UltimateWeapons.py` to use new structure
3. Update `DataStore.py` to use new structure
4. Verify all lookup access patterns still work

---

## Usage Comparison

### Current
```python
from functions.data import config
lookup = config.GOLDEN_TOWER_LOOKUPS["Bonus"].get(level)

# Labs lookup (separate)
labs_lookup = config.LABS_LOOKUPS[("Golden Tower", "Bonus")].get(labs_level)
```

### Proposed
```python
from functions.data import config
lookup = config.UW_NAME_LOOKUP["UW_LEVELS"]["GOLDEN_TOWER"]["Bonus"].get(level)

# Labs lookup (same place)
labs_lookup = config.UW_NAME_LOOKUP["UW_LABS"]["GOLDEN_TOWER"]["Bonus"].get(labs_level)

# With helper function (recommended)
def get_uw_value(source, weapon, param, level):
    """source: "UW_LEVELS", "UW_LABS", "UW_RELIC", etc."""
    return config.UW_NAME_LOOKUP.get(source, {}).get(weapon, {}).get(param, {}).get(level)
```

---

## Risk Assessment

### Low Risk Changes
- Reorganizing existing lookups into hierarchy
- Adding structure for future sources
- Audit functions (read-only)

### Medium Risk Changes
- Updating consumer code (multiple files)
- Need comprehensive test coverage

### High Risk Changes
- None identified if done with backward compatibility layer

---

## Backward Compatibility Strategy

### Option 1: Keep Old Names as Aliases
```python
GOLDEN_TOWER_LOOKUPS = UW_NAME_LOOKUP["UW_LEVELS"]["GOLDEN_TOWER"]
LABS_LOOKUPS = {
    ("Golden Tower", "Bonus"): UW_NAME_LOOKUP["UW_LABS"]["GOLDEN_TOWER"]["Bonus"],
    # ... etc
}
```

### Option 2: Update All Consumer Code
- Requires updating 5+ files
- More maintainable long-term
- Clearer intent with new naming

---

## Files Affected

### Direct Changes
- `functions/data/config.py` - Reorganize structure + add validation
- `functions/data/ImportJSON.py` - Update lookup access (medium change)
- `functions/data/UltimateWeapons.py` - Update lookup access
- `functions/data/DataStore.py` - Update lookup access

### Indirect Changes
- Any page/geometry using lookups via ImportJSON

### No Changes Needed
- JSON asset files (if using same structure keys)
- Pages/graphs unless they directly import lookups

---

## Next Steps

1. **Confirm proposal** - Does this structure match your vision?
2. **Identify priority** - Start with existing lookups (low risk) or full restructuring?
3. **Set scope** - Include modules/assist-mods or keep phase 1 focused?
4. **Assign ownership** - Who validates completeness across sources?
5. **Plan migration** - Backward compatibility needed, or big bang refactor?
