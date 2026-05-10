# UW Lookup Implementation - Quick Start

**Goal:** Fix uw_overview.py to skip unsupported sections instead of showing "None"

**Your Request:** "Mark entries as N/A when no labs/module effects are available"

**Solution:** Add `UW_SOURCES_MAP` + helper functions + conditional rendering

---

## ⏱️ Implementation Time: ~30-45 minutes

### Step 1: Add UW_SOURCES_MAP to config.py (5 minutes)

**File:** `functions/data/config.py`  
**After line:** ~280 (after LABS_LOOKUPS)

```python
# ============================================================================
# SOURCES AVAILABILITY MAP
# ============================================================================
# Map (weapon, parameter) -> frozenset of available sources
# Used by UI to determine: skip entry, mark as N/A, or show fields
# See UW_PARAMETERS_SOURCES_MATRIX.md for complete reference

UW_SOURCES_MAP = {
    # GOLDEN TOWER
    ("GOLDEN_TOWER", "Bonus"): frozenset(["UW_LEVELS", "UW_LABS", "UW_MODULES"]),
    ("GOLDEN_TOWER", "Duration"): frozenset(["UW_LEVELS", "UW_LABS", "UW_MODULES"]),
    ("GOLDEN_TOWER", "Cooldown"): frozenset(["UW_LEVELS"]),
    
    # BLACK HOLE
    ("BLACK_HOLE", "Size"): frozenset(["UW_LEVELS"]),
    ("BLACK_HOLE", "Duration"): frozenset(["UW_LEVELS"]),
    ("BLACK_HOLE", "Cooldown"): frozenset(["UW_LEVELS"]),
    ("BLACK_HOLE", "Bonus"): frozenset(["UW_LABS", "UW_MODULES"]),
    
    # DEATH WAVE
    ("DEATH_WAVE", "Damage"): frozenset(["UW_LEVELS", "UW_LABS"]),
    ("DEATH_WAVE", "Bonus"): frozenset(["UW_LEVELS", "UW_LABS"]),
    ("DEATH_WAVE", "Quantity"): frozenset(["UW_LEVELS"]),
    ("DEATH_WAVE", "Cooldown"): frozenset(["UW_LEVELS"]),
    
    # GOLDEN BOT
    ("GOLDEN_BOT", "Duration"): frozenset(["UW_LEVELS", "UW_LABS"]),
    ("GOLDEN_BOT", "Cooldown"): frozenset(["UW_LEVELS", "UW_LABS"]),
    ("GOLDEN_BOT", "Bonus"): frozenset(["UW_LEVELS"]),
    ("GOLDEN_BOT", "Range"): frozenset(["UW_LEVELS"]),
    
    # SPOTLIGHT
    ("SPOTLIGHT", "Bonus"): frozenset(["UW_LEVELS", "UW_LABS", "UW_MODULES"]),
    ("SPOTLIGHT", "Angle"): frozenset(["UW_LEVELS"]),
    ("SPOTLIGHT", "Quantity"): frozenset(["UW_LEVELS"]),
    
    # CHRONO FIELD
    ("CHRONO_FIELD", "Duration"): frozenset(["UW_LEVELS", "UW_LABS"]),
    ("CHRONO_FIELD", "Cooldown"): frozenset(["UW_LEVELS"]),
    ("CHRONO_FIELD", "Slow %"): frozenset(["UW_LEVELS"]),
}
```

---

### Step 2: Add Helper Functions to config.py (5 minutes)

**File:** `functions/data/config.py`  
**After:** UW_SOURCES_MAP definition

```python
def has_source(weapon: str, param: str, source: str) -> bool:
    """Check if a parameter supports a specific source."""
    sources = UW_SOURCES_MAP.get((weapon, param), frozenset())
    return source in sources


def get_available_sources(weapon: str, param: str) -> frozenset:
    """Get all available sources for a weapon/parameter combination."""
    return UW_SOURCES_MAP.get((weapon, param), frozenset())
```

---

### Step 3: Update weapons.py (10 minutes)

**File:** `functions/computation/weapons.py`  
**Find:** The `format_single_parameter` function (~line 100)  
**Update:** Add source checking before format strings

```python
def format_single_parameter(param_name: str, param_data: dict) -> dict:
    """Format a single parameter with conditional display based on source availability."""
    
    from functions.data import config
    
    weapon_name = param_data.get("_weapon_name", "")  # Assume this is available
    unit = param_data.get("unit", "")
    
    # Get which sources are available
    available_sources = config.get_available_sources(weapon_name, param_name)
    
    # ===== EXISTING CODE: Format UW Level =====
    uw_level = param_data.get("uw_level", 0)
    uw_target = param_data.get("uw_target_level", 0)
    uw_value = param_data.get("uw_value", 0.0)
    uw_level_str = f"{uw_level}/{uw_target}" if uw_target > 0 else f"{uw_level}"
    uw_display = f"Lvl {uw_level_str}: {format_parameter_value(uw_value, unit)}"
    
    # ===== NEW: Labs Effect - Check if supported =====
    if "UW_LABS" in available_sources:
        labs_level = param_data.get("labs_level", 0)
        labs_value = param_data.get("labs_value", 0.0)
        labs_level_str = f"{labs_level}" if labs_level > 0 else "0"
        labs_display = f"Lvl {labs_level_str}: {format_parameter_component(labs_value, unit=unit)}"
        labs_supported = True
    else:
        labs_display = "N/A"
        labs_supported = False
    
    # ===== NEW: Module Effect - Check if supported =====
    if "UW_MODULES" in available_sources:
        module_value = param_data.get("module_value", 0.0)
        module_display = format_parameter_component(module_value, unit=unit) if module_value != 0 else "None"
        module_supported = True
    else:
        module_display = "N/A"
        module_supported = False
    
    # ===== EXISTING CODE: Relic & Total (unchanged) =====
    relic_value = param_data.get("relic_value", 0.0)
    relic_display = format_parameter_component(relic_value, unit=unit) if relic_value != 0 else "None"
    
    total_value = param_data.get("total_value", 0.0)
    total_display = format_parameter_value(total_value, unit)
    
    # ===== NEW: Return flags for UI =====
    return {
        "name": param_name,
        "uw_display": uw_display,
        "labs_display": labs_display,
        "labs_supported": labs_supported,  # ← FLAG
        "module_display": module_display,
        "module_supported": module_supported,  # ← FLAG
        "relic_display": relic_display,
        "total_display": total_display,
    }
```

---

### Step 4: Update uw_overview.py Rendering (15 minutes)

**File:** `pages/uw_overview.py`  
**Find:** Where parameter details are rendered  
**Update:** Use `*_supported` flags to conditionally show sections

```python
# Example: If rendering parameter cards
def render_parameter_card(param: dict) -> html.Div:
    """Render parameter with conditional effect sections."""
    
    effects = []
    
    # Show Labs only if supported
    if param.get("labs_supported", False):
        effects.append(
            html.Div([
                html.Span("Labs: ", className="label"),
                html.Span(param["labs_display"], className="value")
            ], className="effect-row")
        )
    
    # Show Modules only if supported
    if param.get("module_supported", False):
        effects.append(
            html.Div([
                html.Span("Module: ", className="label"),
                html.Span(param["module_display"], className="value")
            ], className="effect-row")
        )
    
    # If NO effects supported, show message
    if not effects:
        effects.append(
            html.Div(
                html.Span("No effects available", className="na-text"),
                className="effect-row na"
            )
        )
    
    return html.Div([
        html.Div([
            html.Span(param["name"], className="param-name"),
            html.Span(param["uw_display"], className="base-value")
        ], className="parameter-header"),
        html.Div(effects, className="effects-section"),
        html.Div(param["total_display"], className="total-value")
    ], className="parameter-card")
```

---

## ✅ Testing

### Test 1: Check flags are computed
```python
from functions.data import config

# Verify map exists
assert hasattr(config, 'UW_SOURCES_MAP')

# Verify helper functions work
assert config.has_source("GOLDEN_TOWER", "Bonus", "UW_LABS") == True
assert config.has_source("GOLDEN_TOWER", "Cooldown", "UW_LABS") == False

# Verify sources
sources = config.get_available_sources("BLACK_HOLE", "Bonus")
assert "UW_LABS" in sources
assert "UW_MODULES" in sources
assert "UW_LEVELS" not in sources
```

### Test 2: Check display logic
```python
from functions.computation.weapons import format_single_parameter

param = {
    "_weapon_name": "GOLDEN_TOWER",
    "uw_level": 7,
    "uw_target_level": 16,
    "uw_value": 12.0,
    "labs_level": 3,
    "labs_value": 3.0,
    "module_value": 0,
    "relic_value": 0,
    "total_value": 15.0,
    "unit": "s"
}

result = format_single_parameter("Duration", param)
assert result["labs_supported"] == True  # Has labs
assert result["module_supported"] == True  # Has modules
```

### Test 3: Check unsupported parameter
```python
param = {
    "_weapon_name": "GOLDEN_TOWER",
    "uw_level": 5,
    "uw_target_level": 20,
    "uw_value": 8.5,
    "labs_level": 0,
    "labs_value": 0,
    "module_value": 0,
    "relic_value": 0,
    "total_value": 8.5,
}

result = format_single_parameter("Cooldown", param)
assert result["labs_supported"] == False  # No labs for cooldown
assert result["module_supported"] == False  # No modules for cooldown
assert result["labs_display"] == "N/A"
```

---

## 📋 Checklist

- [ ] Added UW_SOURCES_MAP to config.py
- [ ] Added has_source() and get_available_sources() functions
- [ ] Updated format_single_parameter() to check sources
- [ ] Updated uw_overview.py to use *_supported flags
- [ ] Tested with Golden Tower (has labs/modules) ✅
- [ ] Tested with cooldown (base only) ✅
- [ ] Verified "N/A" displays instead of "None" ✅
- [ ] Verified unsupported sections are skipped ✅

---

## 🎉 Result

**Before:**
```
Duration (Lvl 7/16: 12.0s)
├─ Labs: Lvl 3: 3.00
├─ Module: None     ← Confusing
├─ Relic: None      ← Why show this?
└─ Total: 15.0s

Cooldown (Lvl 5/20: 8.5s)
├─ Labs: None       ← Looks broken
├─ Module: None     ← Unused UI
├─ Relic: None      ← Unused UI
└─ Total: 8.5s
```

**After:**
```
Duration (Lvl 7/16: 12.0s)
├─ Labs: Lvl 3: 3.00
├─ Module: None
└─ Total: 15.0s

Cooldown (Lvl 5/20: 8.5s)
├─ No effects available
└─ Total: 8.5s
```

Clean, clear, and unambiguous. ✨

---

## 📚 See Also

- **Full details:** [UW_SOURCES_FLAGGING_GUIDE.md](UW_SOURCES_FLAGGING_GUIDE.md)
- **Reference table:** [UW_PARAMETERS_SOURCES_MATRIX.md](UW_PARAMETERS_SOURCES_MATRIX.md)
- **Implementation code:** [CONFIG_REFACTORING_EXAMPLE.md](CONFIG_REFACTORING_EXAMPLE.md)
- **Complete plan:** [LOOKUP_STRUCTURE_PROPOSAL.md](LOOKUP_STRUCTURE_PROPOSAL.md)
- **Documentation index:** [UW_LOOKUP_DOCUMENTATION_INDEX.md](UW_LOOKUP_DOCUMENTATION_INDEX.md)

---

**Status:** Ready to implement  
**Risk:** Low (only adds flags, doesn't change existing values)  
**Time to complete:** 30-45 minutes  
**Benefit:** Clean UI, solves the N/A vs None ambiguity
