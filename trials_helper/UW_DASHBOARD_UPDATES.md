# UW Dashboard Updates - PermaCalc and Overview Pages

## Summary
Updated the UW PermaCalc Hybrid page and created a new UW Overview page to display detailed breakdown of Ultimate Weapon statistics powered by the newly configured UltimateWeapons analyzer.

## Changes Made

### 1. Updated `pages/perma_calc_hybrid.py`

#### New Imports
- Added `import json` for loading game data
- Added `from functions.data import UltimateWeaponAnalyzer` for detailed stat breakdown

#### Modified Callback: `update_all_outputs()`
The stat card callback now displays detailed breakdown information:

**What's displayed in each weapon card:**
```
[Breakdown of key parameters]
Duration: UW(9/20)=12s + Lab(29)=+29s + Mod=0s + Rel=0s = 41s
Cooldown: UW(7/12)=110s + Lab(7)=-7s + Mod=+10s + Rel=0s = 113s

CD: 53s → 113s | Dur: 41s → 41s
Uptime: 99.5%
Downtime: Avg: 0.5s
Activation Interval: 113.5s
```

**Component breakdown display:**
- **UW Effect**: Base value from Ultimate Weapon upgrade level
- **Lab Effect**: Bonus from Labs research level
- **Module Effect**: Contribution from equipped module
- **Relic Effect**: Contribution from relics (e.g., Bot Range Bonus)
- **Total**: Final effective value used in simulation

#### Key Improvements
1. **Component Transparency**: Users can now see exactly how each source contributes to final values
2. **Labs & Relics Integration**: Previously hidden values are now visible on the main dashboard
3. **Graceful Degradation**: If UltimateWeaponAnalyzer fails, displays fall back to simulation data only
4. **Clean UI**: Breakdown displayed in compact monospace format above the efficiency metrics

---

### 2. Created New Page: `pages/uw_overview.py`

#### Purpose
Dedicated page for viewing detailed breakdown of all Ultimate Weapons in structured card format.

#### Page Structure
- **Path**: `/uw-overview`
- **Page Name**: "UW Overview"
- **Order**: 9 (appears after PermaCalc Hybrid)

#### Display Format
Each weapon shows a card with:

```
WEAPON_NAME
├─ Duration
│  ├─ UW Effect: Lvl 9/20: 12s
│  ├─ Lab Effect: Lvl 29: +29s
│  ├─ Module Effect: None
│  ├─ Relic Effect: None
│  └─ Total: 41s
│
├─ Cooldown
│  ├─ UW Effect: Lvl 7/12: 110s
│  ├─ Lab Effect: Lvl 7: -7s
│  ├─ Module Effect: +10s (from Primordial Collapse)
│  ├─ Relic Effect: None
│  └─ Total: 113s
│
├─ [Additional Parameters]
```

#### Features
1. **Color-coded sections**: Different colors for each effect type
2. **Hover information**: Compact layout expands on different screen sizes
3. **Responsive grid**: 1 card mobile, 2 cards tablet, 3 cards desktop
4. **Error handling**: Displays helpful messages if data can't be loaded
5. **Loading state**: Shows loading indicator while data is being fetched

---

## Data Flow Architecture

```
userData.json / active_manifest.json
    ↓
UltimateWeaponAnalyzer
    ├─ Extracts UW upgrade levels
    ├─ Extracts Labs research levels
    ├─ Extracts Module effects
    ├─ Extracts Relic bonuses
    └─ Combines into component breakdown
        │
        ├─→ perma_calc_hybrid.py (stat cards)
        │   └─ Shows breakdown + simulation metrics
        │
        └─→ uw_overview.py (detailed view)
            └─ Shows full breakdown for each weapon
```

---

## Component Values Displayed

### Ultimate Weapon Effect
- Shows upgrade level (actual/target)
- Displays base value from lookup table
- Example: "Lvl 7/12: 110s"

### Lab Effect
- Shows research level
- Displays bonus/penalty value
- Example: "Lvl 29: +29s" or "Lvl 7: -7s"

### Module Effect
- Shows contribution from selected module
- Example: "+10s (from Primordial Collapse)"

### Relic Effect
- Shows relic bonuses (if applicable)
- Example: "+6.0m (Bot Range Bonus)" for Golden Bot Range

### Total
- Sum of all components: UW + Lab + Module + Relic
- Final value used in simulation

---

## Files Modified

1. **pages/perma_calc_hybrid.py** (965 lines)
   - Added imports: json, UltimateWeaponAnalyzer
   - Modified: `update_all_outputs()` callback (stats card generation)
   - Enhanced breakdown display in stat cards

2. **pages/uw_overview.py** (NEW - 188 lines)
   - New Flask/Dash page for detailed weapon overview
   - Callback: `update_uw_overview()` - generates detailed cards
   - Integrated with UltimateWeaponAnalyzer

---

## Browser Behavior

### PermaCalc Hybrid Page (`/perma-calc-hybrid`)
- Stat cards now show component breakdown
- Breakdown appears above efficiency metrics
- Example: "Duration: UW(9/20)=12s + Lab(29)=+29s + ... = 41s"

### New UW Overview Page (`/uw-overview`)
- Click "UW Overview" in sidebar to navigate
- Shows all weapons with detailed breakdown
- Each weapon on its own card
- Responsive layout (mobile-friendly)

---

## Testing Recommendations

1. **PermaCalc Hybrid**:
   - Open page and verify stat cards display breakdown
   - Compare breakdown values with detailed view in UW Overview
   - Change tier/modules and confirm values update

2. **UW Overview**:
   - Load page and verify all weapons display
   - Check that breakdown values match those in PermaCalc
   - Test on mobile to verify responsive layout

---

## Future Enhancements

Potential improvements (not implemented in this update):
1. Add export functionality (CSV/JSON) of breakdown values
2. Add comparison view (side-by-side weapons)
3. Add historical tracking of stats changes
4. Add searchable/filterable weapon list
5. Add "suggested upgrades" based on perma requirements
