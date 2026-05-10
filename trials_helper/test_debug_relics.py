"""Debug script to verify relic extraction."""

import json
from pathlib import Path
from functions.data import UltimateWeaponAnalyzer

json_path = Path(r"C:\Users\thors\AppData\Roaming\rendapp\userData.json")

with open(json_path, 'r', encoding='utf-8') as f:
    json_data = json.load(f)

analyzer = UltimateWeaponAnalyzer(json_data)

# Debug: extract relics
relics = analyzer._extract_relics_data()
print("Extracted Relics:")
for name, value in relics.items():
    print(f"  {name}: {value}")

# Get Golden Bot detailed data
print("\nGolden Bot - Range Detailed:")
detailed = analyzer.get_detailed("Golden Bot")
if "Range" in detailed:
    print(json.dumps(detailed["Range"], indent=2))
else:
    print("Range parameter not found")
