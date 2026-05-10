import json
from functions.data import UltimateWeaponAnalyzer

# Load JSON
with open('assets/active_manifest.json', 'r') as f:
    json_data = json.load(f)

# Create analyzer
analyzer = UltimateWeaponAnalyzer(json_data)

# Check what weapons we get
all_weapons = analyzer.get_all_weapons()

print(f"\n{'='*80}")
print(f"WEAPONS FOUND: {len(all_weapons)}")
print(f"{'='*80}")

for weapon_name, weapon in all_weapons.items():
    print(f"\n{weapon_name}:")
    detailed = weapon.get_detailed()
    print(f"  Parameters: {list(detailed.keys())}")
    for param_name, param_data in detailed.items():
        total = param_data.get('total_value', 0)
        unit = param_data.get('unit', '')
        print(f"    - {param_name}: {total}{unit}")

print(f"\n{'='*80}")
print(f"EXPECTED WEAPONS (from UltimateWeapons.py WEAPON_DEFINITIONS):")
print(f"{'='*80}")
for weapon_name, params in analyzer.WEAPON_DEFINITIONS.items():
    found = "✓ FOUND" if weapon_name in all_weapons else "✗ MISSING"
    print(f"{weapon_name} {found}")
    print(f"  Expected parameters: {params}")
    if weapon_name in all_weapons:
        actual_params = list(all_weapons[weapon_name].parameters.keys())
        missing_params = [p for p in params if p not in actual_params]
        if missing_params:
            print(f"  ⚠️ Missing parameters: {missing_params}")
