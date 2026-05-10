"""Debug script to find where Bot Range Bonus is located in JSON."""

import json
from pathlib import Path

json_path = Path(r"C:\Users\thors\AppData\Roaming\rendapp\userData.json")

with open(json_path, 'r', encoding='utf-8') as f:
    json_data = json.load(f)

def find_bot_range_bonus(obj, path=""):
    """Recursively search for Bot Range Bonus in the JSON structure."""
    results = []
    
    if isinstance(obj, dict):
        for key, value in obj.items():
            new_path = f"{path}.{key}" if path else key
            if isinstance(value, dict) and value.get("name") == "Bot Range Bonus":
                results.append((new_path, value))
            results.extend(find_bot_range_bonus(value, new_path))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            new_path = f"{path}[{i}]"
            if isinstance(item, dict) and item.get("name") == "Bot Range Bonus":
                results.append((new_path, item))
            results.extend(find_bot_range_bonus(item, new_path))
    
    return results

results = find_bot_range_bonus(json_data)

print("Bot Range Bonus locations:")
if results:
    for path, value in results:
        print(f"\n  Path: {path}")
        print(f"  Value: {json.dumps(value, indent=4)}")
else:
    print("  NOT FOUND!")

# Also check for any relics section
print("\n\nSearching for 'relics' or 'relic' keys:")
def find_relics_keys(obj, path=""):
    """Find any keys containing 'relic'."""
    results = []
    
    if isinstance(obj, dict):
        for key, value in obj.items():
            new_path = f"{path}.{key}" if path else key
            if "relic" in key.lower():
                results.append((new_path, type(value).__name__))
            results.extend(find_relics_keys(value, new_path))
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            new_path = f"{path}[{i}]"
            results.extend(find_relics_keys(item, new_path))
    
    return results

relic_keys = find_relics_keys(json_data)
if relic_keys:
    for path, type_name in relic_keys:
        print(f"  {path}: {type_name}")
else:
    print("  No 'relic' keys found")
