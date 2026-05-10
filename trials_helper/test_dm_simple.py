#!/usr/bin/env python
"""Quick test of DataManager import and basic functionality."""

print("Starting test...")

try:
    print("1. Importing DataManager...")
    from functions.data import DataManager
    print("   ✓ Import successful")
    
    print("2. Getting singleton instance...")
    mgr = DataManager.get_instance()
    print(f"   ✓ Got instance: {mgr}")
    
    print("3. Getting weapons list (first call - will load JSON)...")
    weapons = mgr.get_weapons_list()
    print(f"   ✓ Got {len(weapons)} weapons: {weapons}")
    
    print("4. Getting single weapon data...")
    chrono = mgr.get_weapon_data("Chrono Field", detailed=False)
    print(f"   ✓ Got data: {chrono}")
    
    print("\n✅ SUCCESS! DataManager is working!")
    
except Exception as e:
    print(f"\n❌ ERROR: {e}")
    import traceback
    traceback.print_exc()
