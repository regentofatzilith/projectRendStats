"""
Verify that we correctly distinguish:
- Actual Level: Current upgrade/research level
- Target Level: Maximum possible level

For Chrono Field, check both Ultimate Weapon and Labs data.
"""

import json
from pathlib import Path
from functions.data import ImportJSON

# Load JSON
json_path = Path(r"C:\Users\thors\AppData\Roaming\rendapp\userData.json")

with open(json_path, 'r', encoding='utf-8') as f:
    json_data = json.load(f)

print("="*80)
print("LEVEL VERIFICATION: Chrono Field")
print("="*80)

# =========================================================================
# Check Ultimate Weapon Data
# =========================================================================
print("\n" + "-"*80)
print("1. ULTIMATE WEAPON UPGRADES")
print("-"*80)

uw_df = ImportJSON.extract_ultimate_weapon_upgrades(json_data)
chrono_uw = uw_df[uw_df["Ultimate Weapon"] == "Chrono Field"]

print("\nChrono Field Ultimate Weapon Data:")
if not chrono_uw.empty:
    print(chrono_uw.to_string(index=False))
else:
    print("❌ No ultimate weapon data found")

# =========================================================================
# Check Labs Data
# =========================================================================
print("\n" + "-"*80)
print("2. LABS RESEARCH")
print("-"*80)

labs_df = ImportJSON.extract_relevant_labs_progress(json_data)
chrono_labs = labs_df[labs_df["Research Name"].str.contains("Chrono", case=False, na=False)]

print("\nChrono Field Labs Research Data:")
if not chrono_labs.empty:
    print(chrono_labs.to_string(index=False))
else:
    print("❌ No labs data found for Chrono Field")

# =========================================================================
# Check Combined Data
# =========================================================================
print("\n" + "-"*80)
print("3. COMBINED ULTIMATE WEAPONS DATA")
print("-"*80)

combined = ImportJSON.extract_combined_ultimate_weapons_data(json_data)
if "Chrono Field" in combined:
    chrono_combined = combined["Chrono Field"]
    print("\nChrono Field Combined Data:")
    print(chrono_combined.to_string(index=False))
    
    print("\n" + "="*80)
    print("DETAILED BREAKDOWN")
    print("="*80)
    
    for _, row in chrono_combined.iterrows():
        param = row.get("Parameter", "Unknown")
        print(f"\n{param}:")
        print(f"  Level (Actual): {row.get('Level', 'N/A')}")
        print(f"  Target Level: {row.get('Target Level', 'N/A')}")
        print(f"  Labs Level: {row.get('Labs Level', 'N/A')}")
        print(f"  Total Value: {row.get('Total Value', 'N/A')}")
else:
    print("❌ Chrono Field not found in combined data")

# =========================================================================
# Verify with Raw JSON
# =========================================================================
print("\n" + "-"*80)
print("4. RAW JSON DATA (For Reference)")
print("-"*80)

print("\nRaw Ultimate Weapons Section:")
uw_list = ImportJSON._find_first_list_by_key(json_data, "ultimateweapons") or []
chrono_raw_uw = [w for w in uw_list if any("chrono" in str(v).lower() for v in w.values())]
for weapon in chrono_raw_uw:
    print(f"  {json.dumps(weapon, indent=4)}")

print("\nRaw Labs Section (Chrono entries):")
labs_list = ImportJSON._find_first_list_by_key(json_data, "labs") or []
chrono_raw_labs = [lab for lab in labs_list if "chrono" in str(lab.get("name", "")).lower()]
for lab in chrono_raw_labs:
    print(f"  {json.dumps(lab, indent=4)}")

print("\n" + "="*80)
print("VERIFICATION COMPLETE")
print("="*80)

print("\n✅ Key Points to Verify:")
print("  1. Ultimate Weapon Level = current upgrade level")
print("  2. Target Level = max possible for ultimate weapon")
print("  3. Labs Level = current research level in labs")
print("  4. These should NOT be confused with each other")
