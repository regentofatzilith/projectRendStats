# UW Sources Flagging: Quick Reference

## Problem
You can't know which modules/assist mods the user has applied—that's user input. But the **UI needs to know** whether each parameter **supports** labs/module effects at all, so it can:
- Skip rendering unsupported sections (clean UI)
- Mark unsupported fields as "N/A" (clear intent)  
- Show rarity selectors only for parameters that support modules

## Solution: UW_SOURCES_MAP

A simple map of **(weapon, parameter) → available sources**:

```python
UW_SOURCES_MAP = {
    # GOLDEN TOWER - fully featured
    ("GOLDEN_TOWER", "Bonus"): frozenset(["UW_LEVELS", "UW_LABS", "UW_MODULES"]),
    ("GOLDEN_TOWER", "Duration"): frozenset(["UW_LEVELS", "UW_LABS", "UW_MODULES"]),
    ("GOLDEN_TOWER", "Cooldown"): frozenset(["UW_LEVELS"]),  # No labs/modules
    
    # BLACK HOLE - mixed support
    ("BLACK_HOLE", "Size"): frozenset(["UW_LEVELS"]),
    ("BLACK_HOLE", "Bonus"): frozenset(["UW_LABS", "UW_MODULES"]),  # Labs only
    
    # ... all other weapons/params
}
```

**Key insight:** Each parameter lists which sources have data for it. That's our **capability flag**.

---

## Reading the Flags

| frozenset Value | Meaning | UI Action |
|---|---|---|
| `{"UW_LEVELS"}` | Base value only, no effects | Show only base level; skip Labs/Module/Relic sections |
| `{"UW_LEVELS", "UW_LABS"}` | Base + labs possible | Show base level; show labs section |
| `{"UW_LEVELS", "UW_LABS", "UW_MODULES"}` | Base + labs + modules possible | Show all three with full UI |
| `{"UW_LABS"}` | Labs only (unusual) | Skip base; show labs section only |
| `{}` | Empty (not implemented) | Mark as "N/A" or skip entirely |

---

## Helper Functions

```python
from functions.data import config

# Check if single source available
if config.has_source("GOLDEN_TOWER", "Bonus", "UW_LABS"):
    show_labs_input()

# Get all available sources
sources = config.get_available_sources("GOLDEN_TOWER", "Bonus")
# Returns: frozenset(['UW_LEVELS', 'UW_LABS', 'UW_MODULES'])

# Use in conditional rendering
if "UW_MODULES" in sources:
    show_rarity_selector()
else:
    hide_or_skip_rarity_selector()

# Format for display/debugging
labels = config.format_sources_for_display("GOLDEN_TOWER", "Bonus")
# Returns: "Base + Labs + Modules"
```

---

## Integration with uw_overview.py

### Current Problem
```python
# Old way - shows "None" for everything unclear
module_display = format_parameter_component(0.0) if 0.0 != 0 else "None"
# Result: "None" shown regardless of whether modules are supported
```

### New Solution
```python
# New way - check capability first
available_sources = config.get_available_sources(weapon, param)

if "UW_MODULES" in available_sources:
    # Render module section with rarity selector
    module_display = show_module_section_with_selector()
else:
    # Skip module section entirely (or show "N/A")
    module_display = "N/A"  # or: pass/skip
```

### Result
**Before:**
```
Duration (Lvl 7/16: 12.0s)
├─ Labs: Lvl 3: 3.00
├─ Module: None          ← Renders but doesn't work
├─ Relic: None           ← Confusing - why show these?
└─ Total: 15.0s
```

**After:**
```
Duration (Lvl 7/16: 12.0s)
├─ Labs: Lvl 3: 3.00
└─ Total: 15.0s
```
Much cleaner—only shows what's actually supported.

---

## Implementation Checklist

### Step 1: Add UW_SOURCES_MAP to config.py ✅
```python
UW_SOURCES_MAP = {
    ("GOLDEN_TOWER", "Bonus"): frozenset(["UW_LEVELS", "UW_LABS", "UW_MODULES"]),
    # ... etc for all weapons/params
}
```

### Step 2: Add helper functions to config.py ✅
```python
def has_source(weapon, param, source) -> bool
def get_available_sources(weapon, param) -> frozenset
def format_sources_for_display(weapon, param) -> str
```

### Step 3: Update weapons.py display logic
```python
# In format_single_parameter():
available_sources = config.get_available_sources(weapon, param)
labs_supported = "UW_LABS" in available_sources
module_supported = "UW_MODULES" in available_sources
# ... return flags in dict
```

### Step 4: Update uw_overview.py rendering
```python
# In render_parameter_card():
if param.get("labs_supported"):
    render_labs_section()
else:
    skip_labs_section()
# ... same for modules, relics, etc
```

---

## Complete Mapping Status

### ✅ Fully Flaggable
- Golden Tower: Bonus, Duration, Cooldown
- Black Hole: Size, Duration, Cooldown, Bonus
- Death Wave: All parameters
- Golden Bot: Duration, Cooldown, Bonus, Range
- Spotlight: Bonus, Angle, Quantity
- Chrono Field: Duration, Cooldown, Slow %

### ⚠️ Partially Flaggable
- Golden Bot: Health (not implemented)
- Black Hole: Bonus (labs-only, no base level)

### ❌ Not Implemented
- Summon Guardian: All parameters
- Smart Missiles: All parameters
- Inner Land Mines: All parameters
- Poison Swamp: All parameters

---

## Edge Cases Handled

### Case 1: Labs-Only Parameter
```python
("BLACK_HOLE", "Bonus"): frozenset(["UW_LABS", "UW_MODULES"])
# No UW_LEVELS - means user can't level this base in workshop
# But labs research and modules CAN affect it
# UI: Show labs/modules sections, but skip "Base Level" section
```

### Case 2: Base-Only Parameter
```python
("GOLDEN_TOWER", "Cooldown"): frozenset(["UW_LEVELS"])
# Only workshop levels matter, no labs/modules
# UI: Show base level only, hide labs/module/relic sections
```

### Case 3: Unimplemented Parameter
```python
("SUMMON_GUARDIAN", "Duration"): frozenset([])
# Empty frozenset - parameter exists but no lookups
# UI: Mark as "N/A" or skip entirely
```

---

## Testing Completeness

```python
from functions.data import config

# Run audit to check what's flagged vs missing
issues = config.audit_uw_lookups(verbose=True)

# Output:
# ULTIMATE WEAPONS LOOKUP AUDIT REPORT
# =====================================
# Total Weapons Checked: 10
# Implemented: 6
# Missing: 4
# 
# ⚠️  MISSING WEAPONS (UW_LEVELS):
#    - SUMMON_GUARDIAN
#    - SMART_MISSILES
#    ...
# 
# Audit Score: 23/30
```

---

## Summary

| Aspect | Solution |
|---|---|
| **Problem** | Can't know user's module/relic inputs, but UI needs to know what's *possible* |
| **Approach** | Maintain `UW_SOURCES_MAP` listing which sources support each parameter |
| **Benefits** | Clean UI, no confusing "None" values, extensible for new sources |
| **Implementation** | 4 simple steps: add map, add helpers, update display logic, flag rendering |
| **Maintenance** | Single source of truth; update map when adding new parameters/sources |
