# UW Sources Flagging - Visual Guide

## The Problem → Solution Flow

```
╔═══════════════════════════════════════════════════════════════════════╗
║                   CURRENT STATE - AMBIGUOUS                           ║
╚═══════════════════════════════════════════════════════════════════════╝

Duration (lvl 7/16)
├─ Labs: Lvl 3: 3.00 seconds
├─ Module: None                 ⟵ Does this mean:
├─ Relic: None                     a) Not supported?
└─ Total: 12.0s                    b) Supported but user has none?
                                   c) Something else?
                                
Cooldown (lvl 5/20)                ⟵ Why show these if not supported?
├─ Labs: None
├─ Module: None
├─ Relic: None
└─ Total: 8.5s


╔═══════════════════════════════════════════════════════════════════════╗
║                 SOLUTION - CAPABILITY FLAGGING                         ║
╚═══════════════════════════════════════════════════════════════════════╝

UW_SOURCES_MAP = {
    ("GOLDEN_TOWER", "Duration"): {
        "UW_LEVELS" ✅,    ← User can level in workshops
        "UW_LABS" ✅,      ← User can research labs
        "UW_MODULES" ✅    ← User can equip modules
    }
    
    ("GOLDEN_TOWER", "Cooldown"): {
        "UW_LEVELS" ✅,    ← User can level in workshops
        "UW_LABS" ❌,      ← NO labs research available
        "UW_MODULES" ❌    ← NO modules affect this
    }
}


╔═══════════════════════════════════════════════════════════════════════╗
║                   RESULT - CLEAR UI                                    ║
╚═══════════════════════════════════════════════════════════════════════╝

Duration (Lvl 7/16)
├─ Labs: Lvl 3: 3.00 seconds    ⟵ Shows because UW_LABS ✅
├─ Module: None                 ⟵ Shows because UW_MODULES ✅
└─ Total: 12.0s

Cooldown (Lvl 5/20)
└─ Total: 8.5s                  ⟵ No effects section (clean!)
```

---

## Data Flow Diagram

```
   USER'S UNKNOWN INPUTS
   ┌──────────────────┐
   │ • Module chosen  │
   │ • Module rarity  │
   │ • Lab levels     │
   │ • Relic equipped │
   └────────┬─────────┘
            │ (unknown to us)
            ▼
   ┌────────────────────────────┐
   │   UW_SOURCES_MAP           │
   │   (what CAN affect param)   │
   │                            │
   │ ("Golden Tower", "Bonus")  │
   │ → ["UW_LEVELS",            │
   │    "UW_LABS", 
   │    "UW_MODULES"]           │
   └────────┬────────────────────┘
            │
            ▼
   ┌────────────────────────────┐
   │  Helper Functions          │
   │                            │
   │ has_source(w, p, s)        │
   │ get_available_sources()    │
   │ format_sources_for_display │
   └────────┬────────────────────┘
            │
            ▼
   ┌────────────────────────────┐
   │  format_single_parameter   │
   │                            │
   │  Return flags:             │
   │  • labs_supported: True    │
   │  • module_supported: True  │
   │  • relic_supported: False  │
   └────────┬────────────────────┘
            │
            ▼
   ┌────────────────────────────┐
   │  uw_overview.py render     │
   │  (conditional based on     │
   │   *_supported flags)       │
   │                            │
   │  if labs_supported:        │
   │    show_labs_section()     │
   │  else:                     │
   │    skip_section()          │
   └────────┬────────────────────┘
            │
            ▼
   ┌────────────────────────────┐
   │   CLEAN UI                 │
   │                            │
   │ Only supported sections    │
   │ shown, others hidden       │
   └────────────────────────────┘
```

---

## UW Sources Capability Matrix

### Golden Tower
```
                  UW_LEVELS  UW_LABS  UW_MODULES  UW_RELIC
Bonus                ✅        ✅        ✅          ❌
Duration             ✅        ✅        ✅          ❌
Cooldown             ✅        ❌        ❌          ❌
                 
→ Action: Show all 3 sections for Bonus only
```

### Black Hole
```
                  UW_LEVELS  UW_LABS  UW_MODULES  UW_RELIC
Size                 ✅        ❌        ❌          ❌
Duration             ✅        ❌        ❌          ❌
Cooldown             ✅        ❌        ❌          ❌
Bonus                ❌        ✅        ✅          ❌
                 
→ Action: Skip labs/modules for Size/Duration/Cooldown
         Show labs + modules for Bonus
```

---

## Code Structure

```python
# CONFIG.PY
UW_SOURCES_MAP = {
    ("GOLDEN_TOWER", "Bonus"): frozenset(["UW_LEVELS", "UW_LABS", "UW_MODULES"]),
    ("GOLDEN_TOWER", "Cooldown"): frozenset(["UW_LEVELS"]),
    # ... all weapons/params
}

def has_source(weapon, param, source) -> bool:
    return source in UW_SOURCES_MAP.get((weapon, param), frozenset())

def get_available_sources(weapon, param) -> frozenset:
    return UW_SOURCES_MAP.get((weapon, param), frozenset())


# WEAPONS.PY
def format_single_parameter(param_name, param_data) -> dict:
    sources = config.get_available_sources(weapon, param_name)
    
    # Check capability before showing section
    labs_supported = "UW_LABS" in sources
    module_supported = "UW_MODULES" in sources
    
    return {
        # ... existing fields ...
        "labs_supported": labs_supported,      # ← FLAG
        "module_supported": module_supported,  # ← FLAG
    }


# UW_OVERVIEW.PY
def render_parameter_card(param) -> html.Div:
    effects = []
    
    # Only render if capability is flagged
    if param.get("labs_supported"):
        effects.append(render_labs_section(param))
    
    if param.get("module_supported"):
        effects.append(render_module_section(param))
    
    # If no effects possible, show message
    if not effects:
        effects.append(html.Span("No effects available"))
    
    return html.Div([
        render_base_level(param),
        html.Div(effects),
        render_total(param)
    ])
```

---

## User Journey

### 1. Config declares capability once
```
UW_SOURCES_MAP = {
    ("GOLDEN_TOWER", "Bonus"): {"UW_LEVELS", "UW_LABS", "UW_MODULES"},
    ("GOLDEN_TOWER", "Cooldown"): {"UW_LEVELS"},
    ...
}
↓
This is the SINGLE SOURCE OF TRUTH
```

### 2. UI checks capability
```
sources = get_available_sources("GOLDEN_TOWER", "Cooldown")
→ frozenset(["UW_LEVELS"])

"UW_LABS" in sources? NO → Skip labs section
"UW_MODULES" in sources? NO → Skip modules section
↓
Show only what's supported
```

### 3. User sees clean UI
```
Cooldown
├─ Base: Lvl 5/20: 8.5s
└─ Total: 8.5s

Bonus
├─ Base: Lvl 5/20: 8.5
├─ Labs: Lvl 3: 1.5
├─ Module: ×1.2
└─ Total: 10.2
```

---

## Testing Checklist

```
✅ haas_source("GOLDEN_TOWER", "Bonus", "UW_LABS") == True
✅ has_source("GOLDEN_TOWER", "Cooldown", "UW_LABS") == False
✅ get_available_sources("GOLDEN_BOT", "Duration") == {"UW_LEVELS", "UW_LABS"}
✅ UI shows labs section for Bonus
✅ UI hides labs section for Cooldown
✅ No "None" rows displayed
✅ "No effects available" shown only when truly nothing supported
```

---

## Quick Lookup: Is Feature Supported?

```
Golden Tower Bonus:
  Can user level it? YES (UW_LEVELS) → Show Base Level ✅
  Can labs affect it? YES (UW_LABS) → Show Labs ✅
  Can modules affect it? YES (UW_MODULES) → Show Modules ✅
  Can relics affect it? NO (not in map) → Skip Relics ✅

Golden Tower Cooldown:
  Can user level it? YES (UW_LEVELS) → Show Base Level ✅
  Can labs affect it? NO (not in map) → Skip Labs ✅
  Can modules affect it? NO (not in map) → Skip Modules ✅
  Can relics affect it? NO (not in map) → Skip Relics ✅
```

---

## Error States Handled

```
❌ Parameter has empty frozenset
   → UI shows "No effects available"
   → No "None" rows

❌ Parameter not in map at all
   → Defaults to empty frozenset
   → UI shows "No effects available"
   → Safe fallback

❌ User has 0 level in available source
   → Section shown but displays "Lvl 0: 0"
   → Clear it's available but unused

✅ All cases handled gracefully
```

---

## Before vs After

### BEFORE: Confusing
```
Bonus: ✅ Lvl 5/20: 8.5
Labs: Lvl 0: 0.00
Module: None          ← Is this broken?
Relic: None           ← Should be here?
Total: 8.5
```

### AFTER: Clear
```
Bonus: ✅ Lvl 5/20: 8.5 (UW_LEVELS + UW_LABS + UW_MODULES)
├─ Labs: Lvl 0: 0.00
├─ Module: None
└─ Total: 8.5

Cooldown: ✅ Lvl 5/20: 8.5 (UW_LEVELS only)
└─ Total: 8.5
```

---

## Summary

| Element | Purpose |
|---------|---------|
| **UW_SOURCES_MAP** | Declares which sources support which parameters |
| **has_source()** | Check if single source available |
| **get_available_sources()** | Get all sources for parameter |
| **Flag in return dict** | Tell UI what to render |
| **Conditional rendering** | Only show supported sections |

**Result:** Clean, unambiguous UI that matches actual capabilities ✨
