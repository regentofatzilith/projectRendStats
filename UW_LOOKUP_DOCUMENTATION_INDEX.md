# Ultimate Weapons Lookup Structure - Complete Documentation

## 📚 Documentation Map

Five documents work together to solve the lookup structure problem:

### 1. **[UW_QUICK_START.md](UW_QUICK_START.md)** ⭐ START HERE
   - 4 practical steps (5-15 min each)
   - Copy-paste code for each step  
   - Testing section with examples
   - Before/after comparison
   - ~30-45 minutes to complete
   
   **Best for:** Getting started NOW, implementing Phase 1 quickly

---

### 2. **[LOOKUP_STRUCTURE_PROPOSAL.md](LOOKUP_STRUCTURE_PROPOSAL.md)** - Strategy & Analysis
   - Current state problems
   - Full hierarchical structure design
   - Completeness checklist (what's implemented vs missing)
   - Implementation phases & migration strategy
   - Risk assessment & backward compatibility options
   
   **Best for:** Understanding the big picture, planning phases, identifying gaps

---

### 3. **[CONFIG_REFACTORING_EXAMPLE.md](CONFIG_REFACTORING_EXAMPLE.md)** - Implementation Details
   - Working Python code you can copy/paste
   - `UW_NAME_LOOKUP` hierarchy with all weapons
   - `UW_SOURCES_MAP` for flagging capabilities
   - Helper functions (`get_uw_value()`, `audit_uw_lookups()`, etc.)
   - Integration examples with uw_overview.py
   - Usage examples: old vs new patterns
   
   **Best for:** Actually implementing the changes, understanding code patterns

---

### 4. **[UW_SOURCES_FLAGGING_GUIDE.md](UW_SOURCES_FLAGGING_GUIDE.md)** - UI Integration ⭐
   - Solves your specific concern: "we don't know user's module/relic inputs"
   - `UW_SOURCES_MAP` structure (which sources support which parameters)
   - Helper functions for checking capability
   - How uw_overview.py uses flags to skip/mark unsupported sections
   - Before/after UI behavior comparison
   - Edge cases and completeness status
   
   **Best for:** Understanding how to fix uw_overview.py display issues

---

### 5. **[UW_PARAMETERS_SOURCES_MATRIX.md](UW_PARAMETERS_SOURCES_MATRIX.md)** - Reference
   - Quick lookup table for all weapons & parameters
   - Shows which sources (UW_LEVELS, UW_LABS, UW_MODULES) are available
   - Completeness statistics (50% overall)
   - UW_SOURCES_MAP template (ready to copy-paste)
   - Quick query script
   
   **Best for:** Quick reference while implementing, auditing completeness

---

## 🎯 Quick Answer to Your Specific Issue

**Your Problem:**
> "We do not know the user's input regarding modules and assist modules => we cannot know the effects here. However, i want a flag, so we can indicate if a certain value actually has a lab/submodule effect assigned to it."

**The Solution:**
Create `UW_SOURCES_MAP` mapping each **(weapon, parameter)** to its available sources:

```python
UW_SOURCES_MAP = {
    ("GOLDEN_TOWER", "Bonus"): frozenset(["UW_LEVELS", "UW_LABS", "UW_MODULES"]),
    ("GOLDEN_TOWER", "Cooldown"): frozenset(["UW_LEVELS"]),  # No labs/modules
    ("SPOTLIGHT", "Angle"): frozenset(["UW_LEVELS"]),
    # ... etc
}
```

Then in `uw_overview.py`:
```python
sources = config.get_available_sources("GOLDEN_TOWER", "Bonus")

if "UW_LABS" in sources:
    show_labs_section()  # Parameter supports labs research
else:
    skip_or_mark_na()    # No labs for this parameter
```

**Result:** Clean UI - only show sections for parameters that support effects.

See [UW_SOURCES_FLAGGING_GUIDE.md](UW_SOURCES_FLAGGING_GUIDE.md) for full details.

---

## 🚀 Implementation Roadmap

### Phase 1: Foundation (Low Risk)
- [ ] Copy `UW_NAME_LOOKUP` structure from CONFIG_REFACTORING_EXAMPLE.md
- [ ] Copy `UW_SOURCES_MAP` from CONFIG_REFACTORING_EXAMPLE.md
- [ ] Add helper functions: `has_source()`, `get_available_sources()`, etc.
- [ ] Keep old names as aliases (backward compatible)
- [ ] Tests pass without code changes

**Files affected:** `functions/data/config.py` only

---

### Phase 2: Display Logic (Medium Risk)
- [ ] Update `functions/computation/weapons.py` format functions to check sources
- [ ] Add `*_supported` flags to parameter dict (labs_supported, module_supported, etc.)
- [ ] Return flags alongside values

**Files affected:** `functions/computation/weapons.py`

---

### Phase 3: UI Integration (Medium Risk)
- [ ] Update `pages/uw_overview.py` to use `*_supported` flags
- [ ] Skip rendering for unsupported sections
- [ ] Mark as "N/A" instead of "None" where appropriate
- [ ] Show module rarity selector only if supported

**Files affected:** `pages/uw_overview.py`

---

### Phase 4: Consumer Migration (Medium Risk)
- [ ] Update `ImportJSON.py` to use new structure
- [ ] Update `UltimateWeapons.py` to use new structure
- [ ] Update `DataStore.py` to use new structure
- [ ] Tests pass with new patterns

**Files affected:** `functions/data/ImportJSON.py`, `UltimateWeapons.py`, `DataStore.py`

---

### Phase 5: Completion (Optional, Low Risk)
- [ ] Extract missing weapons (Summon Guardian, etc.) from JSON
- [ ] Remove backward compatibility aliases
- [ ] Document final structure

**Files affected:** `functions/data/config.py`

---

## 💡 Key Design Decisions

| Decision | Rationale | Alternatives Considered |
|----------|-----------|------------------------|
| **Use `frozenset` for sources** | Immutable, hashable, efficient membership tests | lists (mutable), tuples (less clear) |
| **Flag per (weapon, param)** | Each parameter can have different effect support | Global per-weapon (less flexible) |
| **Mark unsupported as "N/A"** | Clear UI—"N/A" vs "None" means different things | Hide entirely (harder to debug) |
| **Centralize in config.py** | Single source of truth for all declarations | Distributed across files (maintenance nightmare) |
| **Backward compatible phase 1** | Gradual migration, lower risk | Big bang refactor (higher risk, faster) |

---

## 📊 Completeness Status

### Currently Tracked ✅
- Golden Tower: 100% (Bonus, Duration, Cooldown)
- Black Hole: 75% (Size, Duration, Cooldown present; Bonus missing from base)
- Death Wave: 100% (Damage, Quantity, Cooldown)
- Golden Bot: 80% (Duration, Cooldown, Bonus, Range present; Health missing)
- Spotlight: 100% (Bonus, Angle, Quantity)
- Chrono Field: 100% (Duration, Cooldown, Slow %)

### Not Yet Tracked ❌
- Summon Guardian: 0% (needs extraction from workshop JSON)
- Smart Missiles: 0% (needs extraction)
- Inner Land Mines: 0% (needs extraction)
- Poison Swamp: 0% (needs extraction)

---

## 🔗 Cross-References

| Topic | Document | Section |
|-------|----------|---------|
| **Quick start (30 min)** | UW_QUICK_START.md | All sections |
| Hierarchical structure overview | LOOKUP_STRUCTURE_PROPOSAL.md | Proposed Hierarchical Structure |
| How to implement in config.py | CONFIG_REFACTORING_EXAMPLE.md | Full Hierarchical Organization |
| Sources flagging (your issue) | UW_SOURCES_FLAGGING_GUIDE.md | All sections |
| Reference table (all weapons) | UW_PARAMETERS_SOURCES_MATRIX.md | All sections |
| Helper function examples | CONFIG_REFACTORING_EXAMPLE.md | Audit & Validation Functions |
| uw_overview.py integration | CONFIG_REFACTORING_EXAMPLE.md + UW_SOURCES_FLAGGING_GUIDE.md | UI Integration sections |
| Backward compatibility | LOOKUP_STRUCTURE_PROPOSAL.md + CONFIG_REFACTORING_EXAMPLE.md | Backward Compatibility sections |
| Completeness tracking | All docs | Completeness sections |
| 4-step implementation guide | UW_QUICK_START.md | Steps 1-4 |

---

## ❓ FAQ

**Q: Do we need all sources (UW_LEVELS, UW_LABS, UW_MODULES, UW_RELIC, UW_ASSIST_MODS)?**  
A: No, start with what exists. Phases 1-3 use UW_LEVELS + UW_LABS + UW_MODULES. UW_RELIC and UW_ASSIST_MODS are placeholders for future expansion.

**Q: Should I migrate all code at once or gradually?**  
A: Gradually. Phase 1 keeps backward compatibility (old names still work), so you can migrate consumers one file at a time.

**Q: What if a weapon has no lookups at all?**  
A: Use empty frozenset: `("SUMMON_GUARDIAN", "Duration"): frozenset([])`. uw_overview.py marks as "N/A".

**Q: Can I add new sources later?**  
A: Yes, just add to UW_SOURCES_MAP. The `*_supported` flags automatically adapt.

**Q: Should I show "N/A" or skip the section entirely?**  
A: Recommendation: skip unsupported sources. If all sources unsupported, show "No effects available" message.

---

## 📝 Next Steps

1. **Review** these three documents (start with this index, then PROPOSAL → EXAMPLE → GUIDE)
2. **Decide** which phases to implement (suggest: Phase 1 + 2 to fix your UI issue)
3. **Prioritize** Phase 1 if you want clean UI quickly
4. **Plan** timeline for other phases

Once you decide, the CONFIG_REFACTORING_EXAMPLE.md has copy-paste-ready code to implement.

---

## 📞 Support References

- **Original user concern:** "We do not know the user's input regarding modules and assist modules"  
  → Addressed in [UW_SOURCES_FLAGGING_GUIDE.md](UW_SOURCES_FLAGGING_GUIDE.md)

- **How to check completeness:**  
  → `config.audit_uw_lookups()` in [CONFIG_REFACTORING_EXAMPLE.md](CONFIG_REFACTORING_EXAMPLE.md)

- **How to display conditionally:**  
  → Integration examples in [CONFIG_REFACTORING_EXAMPLE.md](CONFIG_REFACTORING_EXAMPLE.md) + [UW_SOURCES_FLAGGING_GUIDE.md](UW_SOURCES_FLAGGING_GUIDE.md)

---

**Last Updated:** March 22, 2026  
**Status:** Ready for implementation  
**Risk Level:** Low-Medium (modular phases, backward compatible)
