"""
Test script demonstrating the new UltimateWeapons unified interface.

This shows how much cleaner the code is now with the three-layer architecture:
1. ImportJSON.py - Raw extraction
2. DataStore.py - Caching
3. UltimateWeapons.py - Business logic (THIS FILE DEMONSTRATES IT)
"""

import json
from pathlib import Path
from functions.data.UltimateWeapons import UltimateWeaponAnalyzer

def main():
    print("🚀 Testing New UltimateWeapons Interface\n")
    
    # Load JSON data
    json_path = Path(r"C:\Users\thors\AppData\Roaming\rendapp\userData.json")
    
    if not json_path.exists():
        print(f"❌ JSON file not found: {json_path}")
        return
    
    print(f"📂 Loading: {json_path}\n")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    # Create analyzer
    analyzer = UltimateWeaponAnalyzer(json_data, selected_module="Primordial Collapse")
    
    print("="*80)
    print("EXAMPLE 1: Consolidated Output (Final Values Only)")
    print("="*80)
    print("\nChrono Field - Consolidated:")
    consolidated = analyzer.get_consolidated("Chrono Field")
    for param, value in consolidated.items():
        print(f"  {param}: {value}")
    
    print("\n" + "="*80)
    print("EXAMPLE 2: Detailed Output (Full Breakdown)")
    print("="*80)
    print("\nChrono Field - Detailed:")
    detailed = analyzer.get_detailed("Chrono Field")
    for param, breakdown in detailed.items():
        print(f"\n  {param}:")
        print(f"    UW Level: {breakdown['uw_level']}/{breakdown['uw_target_level']}")
        print(f"    UW Value: {breakdown['uw_value']}{breakdown['unit']}")
        print(f"    Labs Level: {breakdown['labs_level']}")
        print(f"    Labs Value: +{breakdown['labs_value']}{breakdown['unit']}")
        print(f"    Relic Value: +{breakdown['relic_value']}{breakdown['unit']}")
        print(f"    Module Value: {breakdown['module_value']}{breakdown['unit']}")
        print(f"    ──────────────────────────")
        print(f"    💎 TOTAL: {breakdown['total_value']}{breakdown['unit']}")
    
    print("\n" + "="*80)
    print("EXAMPLE 3: Pretty Print (Built-in Formatter)")
    print("="*80)
    analyzer.print_weapon("Chrono Field", show_detailed=True)
    
    print("\n" + "="*80)
    print("EXAMPLE 4: All Weapons - Consolidated Summary")
    print("="*80)
    all_consolidated = analyzer.get_all_consolidated()
    for weapon_name, params in all_consolidated.items():
        print(f"\n{weapon_name}:")
        for param, value in params.items():
            print(f"  {param}: {value}")
    
    print("\n" + "="*80)
    print("EXAMPLE 5: Compare Multiple Weapons")
    print("="*80)
    weapons_to_compare = ["Death Wave", "Golden Tower", "Chrono Field"]
    for weapon_name in weapons_to_compare:
        print(f"\n{weapon_name}:")
        data = analyzer.get_consolidated(weapon_name)
        for param, value in data.items():
            weapon = analyzer.get_weapon(weapon_name)
            if weapon and param in weapon.parameters:
                unit = weapon.parameters[param].unit
                print(f"  {param}: {value}{unit}")
    
    print("\n✅ Done! The new interface is much cleaner:")
    print("   - Consolidated output: Just the final values")
    print("   - Detailed output: Full breakdown of sources")
    print("   - Object-oriented: Clean WeaponParameter and UltimateWeapon classes")
    print("   - Single entry point: UltimateWeaponAnalyzer")

if __name__ == "__main__":
    main()
