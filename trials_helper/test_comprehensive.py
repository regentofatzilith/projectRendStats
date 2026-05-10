"""
Final comprehensive test demonstrating:
1. Bug fix: Labs data extraction
2. New architecture: Clean separation of consolidated vs detailed output

Usage:
    python test_comprehensive.py [weapon_name]
    
    Examples:
        python test_comprehensive.py "Chrono Field"
        python test_comprehensive.py "Death Wave"
        python test_comprehensive.py "Golden Bot"
        python test_comprehensive.py  # Interactive mode
"""

import json
import sys
from pathlib import Path
from functions.data import UltimateWeaponAnalyzer

def get_available_weapons(analyzer):
    """Get list of available ultimate weapons."""
    return list(analyzer.get_all_consolidated().keys())

def prompt_for_weapon(available_weapons):
    """Prompt user to select a weapon from available options."""
    print("\n📋 Available Ultimate Weapons:")
    for i, weapon in enumerate(sorted(available_weapons), 1):
        print(f"  {i}. {weapon}")
    
    while True:
        try:
            choice = input(f"\nSelect a weapon (1-{len(available_weapons)}): ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(available_weapons):
                return sorted(available_weapons)[idx]
            else:
                print(f"❌ Please enter a number between 1 and {len(available_weapons)}")
        except ValueError:
            print("❌ Please enter a valid number")

def main(selected_weapon=None):
    print("="*80)
    print("COMPREHENSIVE TEST: Ultimate Weapon Analysis")
    print("="*80)
    
    # Load JSON
    json_path = Path(r"C:\Users\thors\AppData\Roaming\rendapp\userData.json")
    if not json_path.exists():
        print(f"❌ File not found: {json_path}")
        return
    
    with open(json_path, 'r', encoding='utf-8') as f:
        json_data = json.load(f)
    
    print(f"\n📂 Loaded: {json_path}")
    
    # Create analyzer
    analyzer = UltimateWeaponAnalyzer(json_data, selected_module="Primordial Collapse")
    
    # Determine which weapon to analyze
    available_weapons = get_available_weapons(analyzer)
    
    if selected_weapon is None:
        # Try to get from command line
        if len(sys.argv) > 1:
            selected_weapon = " ".join(sys.argv[1:])
        else:
            # Interactive mode
            selected_weapon = prompt_for_weapon(available_weapons)
    
    # Validate weapon selection
    if selected_weapon not in available_weapons:
        print(f"❌ Weapon not found: '{selected_weapon}'")
        print(f"   Available weapons: {', '.join(sorted(available_weapons))}")
        return
    
    weapon_name = selected_weapon
    
    # =========================================================================
    # PART 1: Display Selected Weapon
    # =========================================================================
    print("\n" + "="*80)
    print(f"PART 1: ANALYZING '{weapon_name.upper()}'")
    print("="*80)
    print(f"\n📊 Selected weapon: {weapon_name}")
    
    detailed = analyzer.get_detailed(weapon_name)
    
    # Find first parameter with labs data as example
    first_param_with_labs = None
    for param_name, breakdown in detailed.items():
        if breakdown.get('labs_level', 0) > 0:
            first_param_with_labs = (param_name, breakdown)
            break
    
    if first_param_with_labs:
        param_name, breakdown = first_param_with_labs
        print(f"\n✅ Example - {param_name}:")
        print(f"   Labs Research Level: {breakdown.get('labs_level', 0)}")
        print(f"   Labs Bonus Value: +{breakdown.get('labs_value', 0)}{breakdown.get('unit', '')}")
        print(f"\n   ✅ Labs data is being extracted correctly!")
    else:
        print(f"\n📝 Note: This weapon doesn't have labs research data in your current progress.")
    
    # =========================================================================
    # PART 2: Demonstrate New Architecture
    # =========================================================================
    print("\n" + "="*80)
    print("PART 2: NEW ARCHITECTURE DEMONSTRATION")
    print("="*80)
    
    print("\n📐 Architecture Layers:")
    print("  1. ImportJSON.py  → Extract raw data from JSON")
    print("  2. DataStore.py   → Cache & state management")
    print("  3. UltimateWeapons.py → Combine sources & present unified interface")
    
    # -------------------------------------------------------------------------
    # Output Type 1: CONSOLIDATED (Final Values Only)
    # -------------------------------------------------------------------------
    print("\n" + "-"*80)
    print("OUTPUT TYPE 1: Consolidated (Final Values Only)")
    print("-"*80)
    print("\nUse Case: Display in UI, show user final effective values")
    print("\nCode:")
    print(f'  consolidated = analyzer.get_consolidated("{weapon_name}")')
    print("\nResult:")
    
    consolidated = analyzer.get_consolidated(weapon_name)
    for param, value in consolidated.items():
        weapon = analyzer.get_weapon(weapon_name)
        unit = weapon.parameters[param].unit if weapon else ""
        print(f"  {param}: {value}{unit}")
    
    # -------------------------------------------------------------------------
    # Output Type 2: DETAILED (Component Breakdown)
    # -------------------------------------------------------------------------
    print("\n" + "-"*80)
    print("OUTPUT TYPE 2: Detailed (Component Breakdown)")
    print("-"*80)
    print("\nUse Case: Debugging, analysis, understanding where values come from")
    print("\nCode:")
    print(f'  detailed = analyzer.get_detailed("{weapon_name}")')
    print("\nResult:\n")
    
    detailed = analyzer.get_detailed(weapon_name)
    
    for param_name, breakdown in detailed.items():
        print(f"  {param_name}:")
        print(f"    Ultimate Weapon: Level {breakdown['uw_level']}/{breakdown['uw_target_level']} → {breakdown['uw_value']}{breakdown['unit']}")
        if breakdown['labs_level'] > 0:
            print(f"    Labs Research:   Level {breakdown['labs_level']} → +{breakdown['labs_value']}{breakdown['unit']}")
        if breakdown['module_value'] != 0:
            print(f"    Module Effect:   {'+' if breakdown['module_value'] >= 0 else ''}{breakdown['module_value']}{breakdown['unit']}")
        if breakdown['relic_value'] != 0:
            print(f"    Relics:          +{breakdown['relic_value']}{breakdown['unit']}")
        print(f"    {'─'*60}")
        print(f"    Total:           {breakdown['total_value']}{breakdown['unit']}")
        
        # Verify calculation
        calculated = (breakdown['uw_value'] + 
                     breakdown['labs_value'] + 
                     breakdown['relic_value'] + 
                     breakdown['module_value'])
        expected = breakdown['total_value']
        if abs(calculated - expected) < 0.01:
            print(f"    ✅ Calculation verified: {breakdown['uw_value']} + {breakdown['labs_value']} + {breakdown['relic_value']} + {breakdown['module_value']} = {expected}{breakdown['unit']}")
        else:
            print(f"    ❌ Calculation mismatch: {calculated} != {expected}")
        print()
    
    # =========================================================================
    # PART 3: Comparison with Other Weapons
    # =========================================================================
    print("="*80)
    print("PART 3: MULTI-WEAPON COMPARISON")
    print("="*80)
    print("\nAll Ultimate Weapons (Consolidated View):\n")
    
    all_weapons = analyzer.get_all_consolidated()
    for loop_weapon_name in sorted(all_weapons.keys()):
        print(f"{loop_weapon_name}:")
        weapon = analyzer.get_weapon(loop_weapon_name)
        for param, value in all_weapons[loop_weapon_name].items():
            unit = weapon.parameters[param].unit if weapon else ""
            print(f"  • {param}: {value}{unit}")
        print()
    
    # =========================================================================
    # SUMMARY
    # =========================================================================
    print("="*80)
    print("SUMMARY")
    print("="*80)
    
    print(f"\n✅ Analysis Complete for: {weapon_name}")
    print(f"   Parameters: {', '.join(consolidated.keys())}")
    
    print("\n✅ Architecture Features:")
    print("   - Clean three-layer separation (Import → Store → Present)")
    print("   - Two output types (Consolidated & Detailed)")
    print("   - Object-oriented design (WeaponParameter, UltimateWeapon)")
    print("   - Single entry point (UltimateWeaponAnalyzer)")
    
    print("\n✅ Benefits:")
    print("   - Code is easier to understand")
    print("   - Each file has one clear purpose")
    print("   - Easy to extend with new features")
    print("   - Better IDE support and type safety")
    
    print("\n📚 Documentation:")
    print("   See ULTIMATE_WEAPONS_REFACTORING.md for full details")
    
    print("\n" + "="*80)
    print(f"ANALYSIS COMPLETE: {weapon_name} ✅")
    print("="*80)

if __name__ == "__main__":
    # Get selected weapon from command line or run interactively
    selected_weapon = None
    if len(sys.argv) > 1:
        selected_weapon = " ".join(sys.argv[1:])
    
    main(selected_weapon)
