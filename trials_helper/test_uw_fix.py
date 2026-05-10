import json
from functions.data import UltimateWeaponAnalyzer

# Test the fix
data = json.load(open('assets/active_manifest.json'))
analyzer = UltimateWeaponAnalyzer(data)
all_weapons = analyzer.get_all_weapons()

print(f"✓ Loaded {len(all_weapons)} weapons")

# Test iteration (this was failing before)
weapons_list = list(all_weapons.values())
if weapons_list:
    first_weapon = weapons_list[0]
    print(f"✓ First weapon: {first_weapon.name}")
    print(f"✓ Iteration works - accessing .name attribute: SUCCESS")
else:
    print("✗ No weapons loaded")
