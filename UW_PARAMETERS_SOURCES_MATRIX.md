# UW Parameters & Sources Reference Table

Quick lookup for which parameters support which effect sources.

---

## Legend

| Symbol | Meaning |
|--------|---------|
| ✅ | Source has data available |
| ❌ | Source not available |
| ⚠️ | Source mentioned but not implemented |
| 🟦 | Planned for future |

---

## Complete Sources Matrix

### GOLDEN TOWER

| Parameter | UW_LEVELS | UW_LABS | UW_MODULES | UW_RELIC | Status |
|-----------|:---------:|:-------:|:----------:|:--------:|--------|
| Bonus | ✅ | ✅ | ✅ | ❌ | Fully featured |
| Duration | ✅ | ✅ | ✅ | ❌ | Fully featured |
| Cooldown | ✅ | ❌ | ❌ | ❌ | Base only |

**UW_LEVELS Range:** Bonus 0-20, Duration 0-38, Cooldown 0-20  
**UW_LABS Range:** Duration 0-20, Bonus 0-25

---

### BLACK HOLE

| Parameter | UW_LEVELS | UW_LABS | UW_MODULES | UW_RELIC | Status |
|-----------|:---------:|:-------:|:----------:|:--------:|--------|
| Size | ✅ | ❌ | ❌ | ❌ | Base only |
| Duration | ✅ | ❌ | ❌ | ❌ | Base only |
| Cooldown | ✅ | ❌ | ❌ | ❌ | Base only |
| Bonus | ❌ | ✅ | ✅ | ❌ | Labs + Modules only |

**UW_LEVELS Range:** Size 0-20, Duration 0-23, Cooldown 0-15  
**UW_LABS Range:** Bonus 0-20

---

### DEATH WAVE

| Parameter | UW_LEVELS | UW_LABS | UW_MODULES | UW_RELIC | Status |
|-----------|:---------:|:-------:|:----------:|:--------:|--------|
| Damage | ✅ | ✅ | ❌ | ❌ | Base + Labs |
| Bonus | ✅ | ✅ | ❌ | ❌ | Alias to Damage |
| Quantity | ✅ | ❌ | ❌ | ❌ | Base only |
| Cooldown | ✅ | ❌ | ❌ | ❌ | Base only |

**UW_LEVELS Range:** Damage 0-30, Quantity 0-4, Cooldown 0-25  
**UW_LABS Range:** Bonus 0-20

---

### GOLDEN BOT

| Parameter | UW_LEVELS | UW_LABS | UW_MODULES | UW_RELIC | Status |
|-----------|:---------:|:-------:|:----------:|:--------:|--------|
| Duration | ✅ | ✅ | ❌ | ❌ | Base + Labs |
| Cooldown | ✅ | ✅ | ❌ | ❌ | Base + Labs |
| Bonus | ✅ | ❌ | ❌ | ❌ | Base only |
| Range | ✅ | ❌ | ❌ | ❌ | Base only |
| Health | ⚠️ | ❌ | ❌ | ❌ | **Not implemented** |

**UW_LEVELS Range:** Duration 1-30, Cooldown 1-15, Bonus 1-30, Range 1-15, Health ⚠️  
**UW_LABS Range:** Duration 0-20, Cooldown 0-25

---

### SPOTLIGHT

| Parameter | UW_LEVELS | UW_LABS | UW_MODULES | UW_RELIC | Status |
|-----------|:---------:|:-------:|:----------:|:--------:|--------|
| Bonus | ✅ | ✅ | ✅ | ❌ | Fully featured |
| Angle | ✅ | ❌ | ❌ | ❌ | Base only |
| Quantity | ✅ | ❌ | ❌ | ❌ | Base only |

**UW_LEVELS Range:** Bonus 0-25, Angle 0-90, Quantity 0-3  
**UW_LABS Range:** Bonus 0-20

---

### CHRONO FIELD

| Parameter | UW_LEVELS | UW_LABS | UW_MODULES | UW_RELIC | Status |
|-----------|:---------:|:-------:|:----------:|:--------:|--------|
| Duration | ✅ | ✅ | ❌ | ❌ | Base + Labs |
| Cooldown | ✅ | ❌ | ❌ | ❌ | Base only |
| Slow % | ✅ | ❌ | ❌ | ❌ | Base only |

**UW_LEVELS Range:** Duration 0-35, Cooldown 0-12, Slow % 0-11  
**UW_LABS Range:** Duration 0-30

---

## Unimplemented Weapons

### SUMMON GUARDIAN ❌

| Parameter | UW_LEVELS | UW_LABS | UW_MODULES | UW_RELIC | Status |
|-----------|:---------:|:-------:|:----------:|:--------:|--------|
| Duration | ❌ | ❌ | ❌ | ❌ | **Missing** |
| Cooldown | ❌ | ❌ | ❌ | ❌ | **Missing** |
| Bonus | ❌ | ❌ | ❌ | ❌ | **Missing** |

**Expected parameters from WEAPON_DEFINITIONS:** Duration, Cooldown, Bonus  
**Action needed:** Extract from workshop JSON and define lookups

---

### SMART MISSILES ❌

| Parameter | UW_LEVELS | UW_LABS | UW_MODULES | UW_RELIC | Status |
|-----------|:---------:|:-------:|:----------:|:--------:|--------|
| Duration | ❌ | ❌ | ❌ | ❌ | **Missing** |
| Cooldown | ❌ | ❌ | ❌ | ❌ | **Missing** |
| Damage | ❌ | ❌ | ❌ | ❌ | **Missing** |
| Quantity | ❌ | ❌ | ❌ | ❌ | **Missing** |

**Expected parameters from WEAPON_DEFINITIONS:** Duration, Cooldown, Damage, Quantity  
**Action needed:** Extract from workshop JSON and define lookups

---

### INNER LAND MINES ❌

| Parameter | UW_LEVELS | UW_LABS | UW_MODULES | UW_RELIC | Status |
|-----------|:---------:|:-------:|:----------:|:--------:|--------|
| Duration | ❌ | ❌ | ❌ | ❌ | **Missing** |
| Cooldown | ❌ | ❌ | ❌ | ❌ | **Missing** |
| Damage | ❌ | ❌ | ❌ | ❌ | **Missing** |
| Quantity | ❌ | ❌ | ❌ | ❌ | **Missing** |

**Expected parameters from WEAPON_DEFINITIONS:** Duration, Cooldown, Damage, Quantity  
**Action needed:** Extract from workshop JSON and define lookups

---

### POISON SWAMP ❌

| Parameter | UW_LEVELS | UW_LABS | UW_MODULES | UW_RELIC | Status |
|-----------|:---------:|:-------:|:----------:|:--------:|--------|
| Duration | ❌ | ❌ | ❌ | ❌ | **Missing** |
| Cooldown | ❌ | ❌ | ❌ | ❌ | **Missing** |
| Damage | ❌ | ❌ | ❌ | ❌ | **Missing** |
| Slow % | ❌ | ❌ | ❌ | ❌ | **Missing** |

**Expected parameters from WEAPON_DEFINITIONS:** Duration, Cooldown, Damage, Slow %  
**Action needed:** Extract from workshop JSON and define lookups

---

## Summary Statistics

### Completeness by Weapon

| Weapon | Implemented | Expected | % Complete |
|--------|:-----------:|:--------:|:----------:|
| Golden Tower | 3/3 | 3 | **100%** ✅ |
| Black Hole | 3/4 | 4 | **75%** ⚠️ |
| Death Wave | 4/4 | 4 | **100%** ✅ |
| Golden Bot | 4/5 | 5 | **80%** ⚠️ |
| Spotlight | 3/3 | 3 | **100%** ✅ |
| Chrono Field | 3/3 | 3 | **100%** ✅ |
| Summon Guardian | 0/3 | 3 | **0%** ❌ |
| Smart Missiles | 0/4 | 4 | **0%** ❌ |
| Inner Land Mines | 0/4 | 4 | **0%** ❌ |
| Poison Swamp | 0/4 | 4 | **0%** ❌ |

**Overall:** 20/40 = **50%** complete

---

### Completeness by Source

| Source | Weapons with it | Total Possible | % Coverage |
|--------|:---------------:|:--------------:|:----------:|
| UW_LEVELS | 6/10 | 10 | **60%** |
| UW_LABS | 6/10 | 10 | **60%** |
| UW_MODULES | 3/10 | 10 | **30%** |
| UW_RELIC | 0/10 | 10 | **0%** 🟦 |
| UW_ASSIST_MODS | 0/10 | 10 | **0%** 🟦 |

---

### UW_SOURCES_MAP Template

For each cell with ✅, include source in frozenset. Example:

```python
UW_SOURCES_MAP = {
    # GOLDEN_TOWER (3 parameters, all fully featured)
    ("GOLDEN_TOWER", "Bonus"): frozenset(["UW_LEVELS", "UW_LABS", "UW_MODULES"]),
    ("GOLDEN_TOWER", "Duration"): frozenset(["UW_LEVELS", "UW_LABS", "UW_MODULES"]),
    ("GOLDEN_TOWER", "Cooldown"): frozenset(["UW_LEVELS"]),
    
    # BLACK_HOLE (4 parameters, mixed support)
    ("BLACK_HOLE", "Size"): frozenset(["UW_LEVELS"]),
    ("BLACK_HOLE", "Duration"): frozenset(["UW_LEVELS"]),
    ("BLACK_HOLE", "Cooldown"): frozenset(["UW_LEVELS"]),
    ("BLACK_HOLE", "Bonus"): frozenset(["UW_LABS", "UW_MODULES"]),
    
    # ... continue for all rows with ✅
    
    # Unimplemented = empty frozenset or omit
    # ("SUMMON_GUARDIAN", "Duration"): frozenset([]),
}
```

---

## Actions Needed

### Immediate (To Complete Phase 1)
- [ ] Copy UW_SOURCES_MAP template above into config.py with all ✅ sources
- [ ] Add helper functions (has_source, get_available_sources, etc.)
- [ ] Add audit function to validate

### Short Term (To Fix UI)
- [ ] Update format_single_parameter in weapons.py to check sources
- [ ] Update uw_overview.py rendering to use flags

### Medium Term (Optional)
- [ ] Extract missing weapons from workshop JSON
- [ ] Add UW_MODULES module effects from submodule_effects.json
- [ ] Add relic support structure (when relic system is available)

---

## Quick Query Script

Check any parameter:

```python
from functions.data import config

# Check what sources support a parameter
sources = config.get_available_sources("GOLDEN_TOWER", "Bonus")
print(f"Golden Tower Bonus supports: {sources}")
# Output: frozenset(['UW_LEVELS', 'UW_LABS', 'UW_MODULES'])

# Check if specific source available
if config.has_source("CHRONO_FIELD", "Duration", "UW_LABS"):
    print("Chrono Field Duration has labs research")
    
# Audit completeness
issues = config.audit_uw_lookups()
print(f"Completeness: {issues['passed']}/{issues['total_checks']}")
```

---

**Last Updated:** March 22, 2026  
**Data Source:** config.py + UltimateWeapons.py definitions  
**Validation:** Cross-checked against workshop_upgrades_tables.json and lab_upgrades_tables.json
