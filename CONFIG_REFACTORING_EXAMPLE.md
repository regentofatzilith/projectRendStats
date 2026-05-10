# Proposed config.py Structure Example

## Full Hierarchical Organization (Phase 1 + 2)

```python
"""
Configuration module for Ultimate Weapons lookup tables.

Hierarchical structure:
UW_NAME_LOOKUP = {
    "UW_LEVELS": {...},         # Workshop upgrades (base values)
    "UW_LABS": {...},           # Labs research bonuses
    "UW_RELIC": {...},          # Relic contributions (planned)
    "UW_MODULES": {...},        # Module submodule effects
    "UW_ASSIST_MODS": {...}     # Assist mod substats (planned)
}

Benefits:
- Single entry point for all lookups
- Easy completeness auditing
- Clear hierarchy for new sources
- Scalable structure for future mechanics
"""

# ============================================================================
# UNIFIED LOOKUP STRUCTURE
# ============================================================================

# ===== LEVELS LOOKUPS (Workshop Upgrades - Base Values) =====

GOLDEN_TOWER_BONUS_LOOKUP = {
    0: 5.0, 1: 5.8, 2: 6.6, 3: 7.4, 4: 8.2, 5: 9.0, 6: 9.8, 7: 10.6, 8: 11.4, 9: 12.2,
    10: 13.0, 11: 13.8, 12: 14.6, 13: 15.4, 14: 16.2, 15: 17.0, 16: 17.8, 17: 18.6,
    18: 19.4, 19: 20.2, 20: 21.0
}

GOLDEN_TOWER_DURATION_LOOKUP = {
    0: 15, 1: 16, 2: 17, 3: 18, 4: 19, 5: 20, 6: 21, 7: 22, 8: 23, 9: 24,
    10: 25, 11: 26, 12: 27, 13: 28, 14: 29, 15: 30, 16: 31, 17: 32, 18: 33, 19: 34,
    20: 35, 21: 36, 22: 37, 23: 38, 24: 39, 25: 40, 26: 41, 27: 42, 28: 43, 29: 44,
    30: 45, 31: 46, 32: 47, 33: 48, 34: 49, 35: 50, 36: 51, 37: 52, 38: 53
}

GOLDEN_TOWER_COOLDOWN_LOOKUP = {
    0: 300, 1: 290, 2: 280, 3: 270, 4: 260, 5: 250, 6: 240, 7: 230, 8: 220, 9: 210,
    10: 200, 11: 190, 12: 180, 13: 170, 14: 160, 15: 150, 16: 140, 17: 130, 18: 120,
    19: 110, 20: 100
}

# ... other lookups (abbreviated for space) ...

# ===== LABS LOOKUPS (Labs Research Bonuses) =====

GOLDEN_TOWER_DURATION_LABS_LOOKUP = {
    0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5, 6: 6, 7: 7, 8: 8, 9: 9, 10: 10,
    11: 11, 12: 12, 13: 13, 14: 14, 15: 15, 16: 16, 17: 17, 18: 18, 19: 19, 20: 20
}

GOLDEN_TOWER_BONUS_LABS_LOOKUP = {
    0: 0, 1: 0.15, 2: 0.30, 3: 0.45, 4: 0.60, 5: 0.75, 6: 0.90, 7: 1.05, 8: 1.20, 9: 1.35, 10: 1.50,
    11: 1.65, 12: 1.80, 13: 1.95, 14: 2.10, 15: 2.25, 16: 2.40, 17: 2.55, 18: 2.70, 19: 2.85, 20: 3.00,
    21: 3.15, 22: 3.30, 23: 3.45, 24: 3.60, 25: 3.75
}

# ... other labs lookups ... #

# ===== MODULES LOOKUPS (Module Submodule Effects by Rarity) =====

# Extracted from submodule_effects.json and structured by weapon
GOLDEN_TOWER_MODULES_LOOKUP = {
    "Bonus": {
        "Common": None,
        "Rare": None,
        "Epic": 1,
        "Legendary": 2,
        "Mythic": 3,
        "Ancestral": 4
    },
    "Duration": {
        "Common": None,
        "Rare": None,
        "Epic": None,
        "Legendary": 2,
        "Mythic": 4,
        "Ancestral": 7
    },
    "Cooldown": {
        "Common": None,
        "Rare": None,
        "Epic": None,
        "Legendary": -5,
        "Mythic": -8,
        "Ancestral": -12
    }
}

# ... other module lookups ...

# ============================================================================
# MASTER HIERARCHY: UW_NAME_LOOKUP
# ============================================================================

UW_NAME_LOOKUP = {
    "UW_LEVELS": {
        "GOLDEN_TOWER": {
            "Bonus": GOLDEN_TOWER_BONUS_LOOKUP,
            "Duration": GOLDEN_TOWER_DURATION_LOOKUP,
            "Cooldown": GOLDEN_TOWER_COOLDOWN_LOOKUP
        },
        "BLACK_HOLE": {
            "Size": BLACK_HOLE_SIZE_LOOKUP,
            "Duration": BLACK_HOLE_DURATION_LOOKUP,
            "Cooldown": BLACK_HOLE_COOLDOWN_LOOKUP,
            # "Bonus": BLACK_HOLE_BONUS_LOOKUP  # ⚠️ MISSING
        },
        "DEATH_WAVE": {
            "Damage": DEATH_WAVE_DAMAGE_LOOKUP,
            "Bonus": DEATH_WAVE_BONUS_LOOKUP,  # Alias
            "Quantity": DEATH_WAVE_QUANTITY_LOOKUP,
            "Cooldown": DEATH_WAVE_COOLDOWN_LOOKUP
        },
        "GOLDEN_BOT": {
            "Duration": GOLDEN_BOT_DURATION_LOOKUP,
            "Cooldown": GOLDEN_BOT_COOLDOWN_LOOKUP,
            "Bonus": GOLDEN_BOT_BONUS_LOOKUP,
            "Range": GOLDEN_BOT_RANGE_LOOKUP
            # "Health": GOLDEN_BOT_HEALTH_LOOKUP  # ⚠️ MISSING
        },
        "SPOTLIGHT": {
            "Bonus": SPOTLIGHT_DAMAGE_MULT_LOOKUP,
            "Angle": SPOTLIGHT_ANGLE_LOOKUP,
            "Quantity": SPOTLIGHT_QUANTITY_LOOKUP
        },
        "CHRONO_FIELD": {
            "Duration": CHRONO_FIELD_DURATION_LOOKUP,
            "Cooldown": CHRONO_FIELD_COOLDOWN_LOOKUP,
            "Slow %": CHRONO_FIELD_SLOW_LOOKUP
        },
        # ⚠️ MISSING: Summon Guardian, Smart Missiles, Inner Land Mines, Poison Swamp
    },
    
    "UW_LABS": {
        "GOLDEN_TOWER": {
            "Duration": GOLDEN_TOWER_DURATION_LABS_LOOKUP,
            "Bonus": GOLDEN_TOWER_BONUS_LABS_LOOKUP
        },
        "BLACK_HOLE": {
            "Bonus": BLACK_HOLE_BONUS_LABS_LOOKUP
        },
        "DEATH_WAVE": {
            "Bonus": DEATH_WAVE_BONUS_LABS_LOOKUP
        },
        "GOLDEN_BOT": {
            "Cooldown": GOLDEN_BOT_COOLDOWN_LABS_LOOKUP,
            "Duration": GOLDEN_BOT_DURATION_LABS_LOOKUP
        },
        "SPOTLIGHT": {
            "Bonus": SPOTLIGHT_BONUS_LABS_LOOKUP
        },
        "CHRONO_FIELD": {
            "Duration": CHRONO_FIELD_DURATION_LABS_LOOKUP
        },
        # ⚠️ MISSING: Summon Guardian, Smart Missiles, Inner Land Mines, Poison Swamp
    },
    
    "UW_MODULES": {
        "GOLDEN_TOWER": GOLDEN_TOWER_MODULES_LOOKUP,
        # ... other weapons ...
    },
    
    "UW_RELIC": {
        # Placeholder for future relic system
    },
    
    "UW_ASSIST_MODS": {
        # Placeholder for assist mod system
    }
}

# ============================================================================
# SOURCES AVAILABILITY MAP
# ============================================================================
# Map (weapon, parameter) -> frozenset of available sources
# Used by UI to determine: skip entry, mark as N/A, or show fields
# 
# A parameter with sources ("UW_LEVELS", "UW_LABS") means:
#   - Has base lookup in UW_LEVELS
#   - Has labs research bonus available in UW_LABS
#   - Should display both sections in UI
#
# A parameter with only ("UW_LEVELS",) means:
#   - No labs/module/relic effects support
#   - Should skip labs/module/relic display sections
#   - Mark those as "N/A" in uw_overview.py

UW_SOURCES_MAP = {
    # GOLDEN TOWER
    ("GOLDEN_TOWER", "Bonus"): frozenset(["UW_LEVELS", "UW_LABS", "UW_MODULES"]),
    ("GOLDEN_TOWER", "Duration"): frozenset(["UW_LEVELS", "UW_LABS", "UW_MODULES"]),
    ("GOLDEN_TOWER", "Cooldown"): frozenset(["UW_LEVELS"]),  # No labs available
    
    # BLACK HOLE
    ("BLACK_HOLE", "Size"): frozenset(["UW_LEVELS"]),
    ("BLACK_HOLE", "Duration"): frozenset(["UW_LEVELS"]),
    ("BLACK_HOLE", "Cooldown"): frozenset(["UW_LEVELS"]),
    ("BLACK_HOLE", "Bonus"): frozenset(["UW_LABS", "UW_MODULES"]),  # Labs only, no base level
    
    # DEATH WAVE
    ("DEATH_WAVE", "Damage"): frozenset(["UW_LEVELS", "UW_LABS"]),
    ("DEATH_WAVE", "Bonus"): frozenset(["UW_LEVELS", "UW_LABS"]),  # Alias to Damage
    ("DEATH_WAVE", "Quantity"): frozenset(["UW_LEVELS"]),
    ("DEATH_WAVE", "Cooldown"): frozenset(["UW_LEVELS"]),
    
    # GOLDEN BOT
    ("GOLDEN_BOT", "Duration"): frozenset(["UW_LEVELS", "UW_LABS"]),
    ("GOLDEN_BOT", "Cooldown"): frozenset(["UW_LEVELS", "UW_LABS"]),
    ("GOLDEN_BOT", "Bonus"): frozenset(["UW_LEVELS"]),
    ("GOLDEN_BOT", "Range"): frozenset(["UW_LEVELS"]),
    ("GOLDEN_BOT", "Health"): frozenset([]),  # ⚠️ Planned but not implemented
    
    # SPOTLIGHT
    ("SPOTLIGHT", "Bonus"): frozenset(["UW_LEVELS", "UW_LABS", "UW_MODULES"]),
    ("SPOTLIGHT", "Angle"): frozenset(["UW_LEVELS"]),
    ("SPOTLIGHT", "Quantity"): frozenset(["UW_LEVELS"]),
    
    # CHRONO FIELD
    ("CHRONO_FIELD", "Duration"): frozenset(["UW_LEVELS", "UW_LABS"]),
    ("CHRONO_FIELD", "Cooldown"): frozenset(["UW_LEVELS"]),
    ("CHRONO_FIELD", "Slow %"): frozenset(["UW_LEVELS"]),
}

# ============================================================================
# BACKWARD COMPATIBILITY LAYER (Optional)
# ============================================================================

# Keep old names pointing to new structure for gradual migration
GOLDEN_TOWER_LOOKUPS = UW_NAME_LOOKUP["UW_LEVELS"]["GOLDEN_TOWER"]
BLACK_HOLE_LOOKUPS = UW_NAME_LOOKUP["UW_LEVELS"]["BLACK_HOLE"]
DEATH_WAVE_LOOKUPS = UW_NAME_LOOKUP["UW_LEVELS"]["DEATH_WAVE"]
GOLDEN_BOT_LOOKUPS = UW_NAME_LOOKUP["UW_LEVELS"]["GOLDEN_BOT"]
SPOTLIGHT_LOOKUPS = UW_NAME_LOOKUP["UW_LEVELS"]["SPOTLIGHT"]
CHRONO_FIELD_LOOKUPS = UW_NAME_LOOKUP["UW_LEVELS"]["CHRONO_FIELD"]

# Old LABS_LOOKUPS pattern (for gradual migration)
LABS_LOOKUPS = {
    ("Golden Tower", "Duration"): UW_NAME_LOOKUP["UW_LABS"]["GOLDEN_TOWER"]["Duration"],
    ("Golden Tower", "Bonus"): UW_NAME_LOOKUP["UW_LABS"]["GOLDEN_TOWER"]["Bonus"],
    ("Black Hole", "Bonus"): UW_NAME_LOOKUP["UW_LABS"]["BLACK_HOLE"]["Bonus"],
    ("Death Wave", "Bonus"): UW_NAME_LOOKUP["UW_LABS"]["DEATH_WAVE"]["Bonus"],
    ("Golden Bot", "Cooldown"): UW_NAME_LOOKUP["UW_LABS"]["GOLDEN_BOT"]["Cooldown"],
    ("Golden Bot", "Duration"): UW_NAME_LOOKUP["UW_LABS"]["GOLDEN_BOT"]["Duration"],
    ("Spotlight", "Bonus"): UW_NAME_LOOKUP["UW_LABS"]["SPOTLIGHT"]["Bonus"],
    ("Chrono Field", "Duration"): UW_NAME_LOOKUP["UW_LABS"]["CHRONO_FIELD"]["Duration"],
}

# ============================================================================
# AUDIT & VALIDATION FUNCTIONS
# ============================================================================

def audit_uw_lookups(verbose: bool = True) -> dict:
    """
    Audit lookup completeness and consistency.
    
    Returns dict with audit results:
    {
        "missing_weapons": [...],
        "missing_parameters": {...},
        "level_range_issues": [...],
        "value_type_issues": [...],
        "total_checks": int,
        "passed": int,
        "failed": int
    }
    """
    
    # Define expected weapons and their parameters per source
    expected_params = {
        "GOLDEN_TOWER": {"Bonus", "Duration", "Cooldown"},
        "BLACK_HOLE": {"Size", "Duration", "Cooldown", "Bonus"},
        "DEATH_WAVE": {"Damage", "Bonus", "Quantity", "Cooldown"},
        "GOLDEN_BOT": {"Duration", "Cooldown", "Bonus", "Range", "Health"},
        "SPOTLIGHT": {"Bonus", "Angle", "Quantity"},
        "CHRONO_FIELD": {"Duration", "Cooldown", "Slow %"},
        "SUMMON_GUARDIAN": {"Duration", "Cooldown", "Bonus"},
        "SMART_MISSILES": {"Duration", "Cooldown", "Damage", "Quantity"},
        "INNER_LAND_MINES": {"Duration", "Cooldown", "Damage", "Quantity"},
        "POISON_SWAMP": {"Duration", "Cooldown", "Damage", "Slow %"},
    }
    
    issues = {
        "missing_weapons": [],
        "missing_parameters": {},
        "level_issues": [],
        "value_issues": [],
        "total_checks": 0,
        "passed": 0,
        "failed": 0
    }
    
    # Check UW_LEVELS completeness
    for weapon, expected_param_set in expected_params.items():
        issues["total_checks"] += 1
        
        if weapon not in UW_NAME_LOOKUP["UW_LEVELS"]:
            issues["missing_weapons"].append(weapon)
            issues["failed"] += 1
            continue
        
        existing_params = set(UW_NAME_LOOKUP["UW_LEVELS"][weapon].keys())
        missing = expected_param_set - existing_params
        
        if missing:
            issues["missing_parameters"][weapon] = list(missing)
            issues["failed"] += 1
        else:
            issues["passed"] += 1
            
        # Check level range consistency
        for param, lookup_dict in UW_NAME_LOOKUP["UW_LEVELS"][weapon].items():
            if not lookup_dict:
                continue
            
            levels = list(lookup_dict.keys())
            # Warn if levels are not sequential from 0 or 1
            if levels and (levels[0] not in [0, 1] or not all(isinstance(l, int) for l in levels)):
                issues["level_issues"].append(f"{weapon}.{param} has non-standard levels: {levels[:5]}...")
                issues["failed"] += 1
    
    if verbose:
        print("\n" + "="*70)
        print("ULTIMATE WEAPONS LOOKUP AUDIT REPORT")
        print("="*70)
        print(f"\nTotal Weapons Checked: {len(expected_params)}")
        print(f"Implemented: {len([w for w in expected_params if w in UW_NAME_LOOKUP['UW_LEVELS']])}")
        print(f"Missing: {len(issues['missing_weapons'])}")
        
        if issues["missing_weapons"]:
            print(f"\n⚠️  MISSING WEAPONS (UW_LEVELS):")
            for w in issues["missing_weapons"]:
                print(f"   - {w}")
        
        if issues["missing_parameters"]:
            print(f"\n⚠️  MISSING PARAMETERS (UW_LEVELS):")
            for weapon, params in issues["missing_parameters"].items():
                print(f"   - {weapon}: {', '.join(params)}")
        
        if issues["level_issues"]:
            print(f"\n⚠️  LEVEL RANGE ISSUES:")
            for issue in issues["level_issues"]:
                print(f"   - {issue}")
        
        print(f"\nAudit Score: {issues['passed']}/{issues['total_checks']}")
        print("="*70 + "\n")
    
    return issues


def get_uw_value(source: str, weapon: str, param: str, level: int, default=None):
    """
    Unified access function for all lookup sources.
    
    Usage:
        value = get_uw_value("UW_LEVELS", "GOLDEN_TOWER", "Bonus", 5)
        labs_bonus = get_uw_value("UW_LABS", "GOLDEN_TOWER", "Bonus", 10)
        module_val = get_uw_value("UW_MODULES", "GOLDEN_TOWER", "Bonus", "Epic")
    """
    try:
        lookup = UW_NAME_LOOKUP.get(source, {}).get(weapon, {}).get(param, {})
        return lookup.get(level, default)
    except (KeyError, TypeError):
        return default


def get_uw_weapon_params(source: str, weapon: str) -> dict:
    """Get all parameters available for a weapon in a given source."""
    return UW_NAME_LOOKUP.get(source, {}).get(weapon, {})


def list_all_weapons(source: str = "UW_LEVELS") -> list:
    """List all weapons available in a source."""
    return list(UW_NAME_LOOKUP.get(source, {}).keys())


def has_source(weapon: str, param: str, source: str) -> bool:
    """
    Check if a parameter has a specific source available.
    
    Usage:
        if has_source("GOLDEN_TOWER", "Bonus", "UW_LABS"):
            # This parameter has labs research available
            display_labs_section(...)
        else:
            # Skip labs section or mark as N/A
            display_na(...)
    """
    sources = UW_SOURCES_MAP.get((weapon, param), frozenset())
    return source in sources


def get_available_sources(weapon: str, param: str) -> frozenset:
    """
    Get all available sources for a weapon/parameter combination.
    
    Returns:
        frozenset of source names (e.g., {"UW_LEVELS", "UW_LABS", "UW_MODULES"})
    
    Usage:
        sources = get_available_sources("GOLDEN_TOWER", "Bonus")
        # Returns: frozenset(['UW_LEVELS', 'UW_LABS', 'UW_MODULES'])
        
        if "UW_LABS" in sources:
            # Show labs section
        if "UW_MODULES" in sources:
            # Show modules section (with rarity selector)
        if "UW_RELIC" not in sources:
            # Skip relics section (or mark N/A)
    """
    return UW_SOURCES_MAP.get((weapon, param), frozenset())


def count_supported_sources(weapon: str, param: str) -> int:
    """Count how many effect sources this parameter supports."""
    sources = get_available_sources(weapon, param)
    return len(sources)


def format_sources_for_display(weapon: str, param: str) -> str:
    """Format available sources as human-readable string for debugging/audits."""
    sources = get_available_sources(weapon, param)
    if not sources:
        return "None (no effects)"
    
    source_names = {
        "UW_LEVELS": "Base",
        "UW_LABS": "Labs",
        "UW_MODULES": "Modules",
        "UW_RELIC": "Relic",
        "UW_ASSIST_MODS": "Assist Mods"
    }
    
    labels = [source_names.get(s, s) for s in sorted(sources)]
    return " + ".join(labels)

```

---

## Usage Examples

### Old Way (Current)
```python
from functions.data import config

# Get base value
value = config.GOLDEN_TOWER_LOOKUPS["Bonus"].get(5)

# Get labs bonus
labs = config.LABS_LOOKUPS[("Golden Tower", "Bonus")].get(10)
```

### New Way (Proposed)
```python
from functions.data import config

# Get base value
value = config.get_uw_value("UW_LEVELS", "GOLDEN_TOWER", "Bonus", 5)

# Get labs bonus
labs = config.get_uw_value("UW_LABS", "GOLDEN_TOWER", "Bonus", 10)

# Get module effect by rarity
module = config.get_uw_value("UW_MODULES", "GOLDEN_TOWER", "Bonus", "Epic")

# List all weapons at bases
weapons = config.list_all_weapons("UW_LEVELS")

# ===== NEW: Check if a parameter has labs/modules/relics support =====
if config.has_source("GOLDEN_TOWER", "Bonus", "UW_LABS"):
    # Display labs section in UI
    pass
else:
    # Skip labs section or mark as "N/A"
    pass

# ===== NEW: Get all available sources for a parameter =====
sources = config.get_available_sources("GOLDEN_TOWER", "Duration")
# Returns: frozenset(['UW_LEVELS', 'UW_LABS', 'UW_MODULES'])

if "UW_LABS" in sources:
    # Labs research available
    pass
if "UW_MODULES" in sources:
    # Module effects available
    pass
if "UW_RELIC" not in sources:
    # Relics not available for this parameter
    pass

# Check completeness
audit = config.audit_uw_lookups(verbose=True)
```

---

## UI Integration: Using Sources Flags in uw_overview.py

### Problem Being Solved
- We don't know which effects the user has applied (modules, relics, etc.)
- Currently display shows `None` for missing sections, unclear if it's "not tracked" or "not supported"
- Need to distinguish: skip unsupported sections vs show disabled sections

### Solution: Modified Display Logic

**In `functions/computation/weapons.py` (format_single_parameter):**

```python
def format_single_parameter(param_name: str, param_data: dict) -> dict:
    """Format a single parameter with conditional display based on source availability."""
    
    from functions.data import config
    
    # Assume we have weapon_name available (from context or param_data)
    weapon_name = param_data.get("_weapon_name", "GOLDEN_TOWER")  # placeholder
    unit = param_data.get("unit", "")
    
    # Get which sources are available for this parameter
    available_sources = config.get_available_sources(weapon_name, param_name)
    
    # Format UW Level (always show if available)
    uw_level = param_data.get("uw_level", 0)
    uw_target = param_data.get("uw_target_level", 0)
    uw_value = param_data.get("uw_value", 0.0)
    uw_level_str = f"{uw_level}/{uw_target}" if uw_target > 0 else f"{uw_level}"
    uw_display = f"Lvl {uw_level_str}: {format_parameter_value(uw_value, unit)}"
    
    # ===== NEW: Labs Effect - Conditional Display =====
    if "UW_LABS" in available_sources:
        # Labs research is SUPPORTED for this parameter
        labs_level = param_data.get("labs_level", 0)
        labs_value = param_data.get("labs_value", 0.0)
        labs_level_str = f"{labs_level}" if labs_level > 0 else "0"
        labs_display = f"Lvl {labs_level_str}: {format_parameter_component(labs_value, unit=unit)}"
    else:
        # Labs research is NOT SUPPORTED - mark as N/A instead of showing
        labs_display = "N/A"
    
    # ===== NEW: Module Effects - Conditional Display =====
    if "UW_MODULES" in available_sources:
        # Modules are SUPPORTED for this parameter
        module_value = param_data.get("module_value", 0.0)
        module_display = format_parameter_component(module_value, unit=unit) if module_value != 0 else "None"
        show_module_rarity_selector = True
    else:
        # Modules are NOT SUPPORTED - skip section entirely
        module_display = "N/A"
        show_module_rarity_selector = False
    
    # ===== NEW: Relic Effects - Conditional Display =====
    if "UW_RELIC" in available_sources:
        relic_value = param_data.get("relic_value", 0.0)
        relic_display = format_parameter_component(relic_value, unit=unit) if relic_value != 0 else "None"
    else:
        relic_display = "N/A"  # Could also be hidden entirely
    
    # ===== NEW: Assist Mod Effects - Conditional Display =====
    if "UW_ASSIST_MODS" in available_sources:
        assist_value = param_data.get("assist_value", 0.0)
        assist_display = format_parameter_component(assist_value, unit=unit) if assist_value != 0 else "None"
    else:
        assist_display = "N/A"
    
    # Format Total
    total_value = param_data.get("total_value", 0.0)
    total_display = format_parameter_value(total_value, unit)
    
    return {
        "name": param_name,
        "uw_display": uw_display,
        "labs_display": labs_display,
        "labs_supported": "UW_LABS" in available_sources,  # ← Flag for UI
        "module_display": module_display,
        "module_supported": "UW_MODULES" in available_sources,  # ← Flag for UI
        "show_module_rarity_selector": show_module_rarity_selector,
        "relic_display": relic_display,
        "relic_supported": "UW_RELIC" in available_sources,  # ← Flag for UI
        "assist_display": assist_display,
        "assist_supported": "UW_ASSIST_MODS" in available_sources,  # ← Flag for UI
        "total_display": total_display,
    }
```

**In `pages/uw_overview.py` (render parameter card):**

```python
def render_parameter_card(param: dict) -> html.Div:
    """Render a single parameter's effects, skipping/hiding unsupported sections."""
    
    effects_rows = []
    
    # Always show Labs if supported
    if param.get("labs_supported", False):
        effects_rows.append(
            html.Div([
                html.Span("Labs:", className="label"),
                html.Span(param["labs_display"], className="value")
            ], className="effect-row")
        )
    
    # Show Module if supported
    if param.get("module_supported", False):
        effects_rows.append(
            html.Div([
                html.Span("Module:", className="label"),
                html.Span(param["module_display"], className="value"),
                # Optionally add rarity selector if module_supported
            ], className="effect-row")
        )
    
    # Show Relic if supported
    if param.get("relic_supported", False):
        effects_rows.append(
            html.Div([
                html.Span("Relic:", className="label"),
                html.Span(param["relic_display"], className="value")
            ], className="effect-row")
        )
    
    # Show Assist Mods if supported
    if param.get("assist_supported", False):
        effects_rows.append(
            html.Div([
                html.Span("Assist Mod:", className="label"),
                html.Span(param["assist_display"], className="value")
            ], className="effect-row")
        )
    
    # If NO effects are supported, show disclaimer
    if not effects_rows:
        effects_rows = [
            html.Div(
                html.Span("No effects available", className="na-text"),
                className="effect-row na"
            )
        ]
    
    return html.Div([
        html.Div([
            html.Span(param["name"], className="param-name"),
            html.Span(param["uw_display"], className="base-value")
        ], className="parameter-header"),
        html.Div(effects_rows, className="effects-section"),
        html.Div(
            param["total_display"],
            className="total-value"
        )
    ], className="parameter-card")
```

### Behavior Summary

| Scenario | Before | After |
|----------|--------|-------|
| Parameter has labs support | Show labs value or "Lvl 0: 0.00" | Show labs value or "Lvl 0: 0.00" |
| Parameter has NO labs support | Show "None" (confusing) | Show "N/A" or skip section (clear) |
| Parameter has module support | Show module value or "None" | Show with rarity selector if supported |
| Parameter has NO module support | Show "None" (may render UI for nothing) | Skip section entirely (less clutter) |
| Multiple unsupported effects | Shows many "None" rows (noisy) | Single "No effects available" (clean) |

### Benefits
- ✅ UI stays clean - don't show sections for unsupported effects
- ✅ Clear intent - "N/A" means "not supported", not "not tracked"
- ✅ Less cognitive load - user doesn't wonder why module selector doesn't work
- ✅ Extensible - adding new sources just updates `UW_SOURCES_MAP`
- ✅ Maintainable - sources are declared once, used everywhere
```

---

## Migration Path

### Step 1: Add Structure (Backward Compatible)
- Create `UW_NAME_LOOKUP` hierarchy
- Keep old names as aliases
- Tests pass, no code changes needed

### Step 2: Update Consumer Code Gradually
- Update `ImportJSON.py` → use `get_uw_value()`
- Update `UltimateWeapons.py` → use `get_uw_value()`
- Update `DataStore.py` → use `get_uw_value()`
- Tests pass at each step

### Step 3: Remove Old Names
- Delete aliases once all consumers updated
- Clean up config.py

---

## Completeness Matrix

### Current ✅ Implemented

| Weapon | Bonus/Damage | Duration | Cooldown | Size/Angle/Other |
|--------|:----:|:----:|:----:|:----:|
| Golden Tower | ✅ UW ✅ Labs | ✅ UW ✅ Labs | ✅ UW ❌ Labs | - |
| Black Hole | ❌ UW ✅ Labs | ✅ UW ❌ Labs | ✅ UW ❌ Labs | Size ✅ |
| Death Wave | ✅ UW ✅ Labs | ❌ UW ❌ Labs | ✅ UW ❌ Labs | Qty ✅ |
| Golden Bot | ✅ UW ❌ Labs | ✅ UW ✅ Labs | ✅ UW ✅ Labs | Range ✅, Health ❌ |
| Spotlight | ✅ UW ✅ Labs | ❌ UW ❌ Labs | ❌ UW ❌ Labs | Angle ✅, Qty ✅ |
| Chrono Field | ❌ UW ❌ Labs | ✅ UW ✅ Labs | ✅ UW ❌ Labs | Slow % ✅ |
| Summon Guardian | ❌ ❌ | ❌ ❌ | ❌ ❌ | - |
| Smart Missiles | ❌ ❌ | ❌ ❌ | ❌ ❌ | Dmg ❌, Qty ❌ |
| Inner Land Mines | ❌ ❌ | ❌ ❌ | ❌ ❌ | Dmg ❌, Qty ❌ |
| Poison Swamp | ❌ ❌ | ❌ ❌ | ❌ ❌ | Slow % ❌, Dmg ❌ |

**Summary:** 37% complete overall | 78% for implemented weapons | 0% for unimplemented weapons
