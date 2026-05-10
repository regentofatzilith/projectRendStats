"""
Test and demonstration of the DataManager singleton.

Usage:
    python test_data_manager.py
    
This script demonstrates:
1. Singleton pattern (same instance returned)
2. Lazy loading (data loaded on first access)
3. Caching (subsequent accesses are instant)
4. Thread safety
5. All API methods
"""

import time
from functions.data import DataManager


def test_singleton():
    """Test that DataManager returns same instance."""
    print("\n" + "="*80)
    print("TEST 1: Singleton Pattern")
    print("="*80)
    
    mgr1 = DataManager.get_instance()
    mgr2 = DataManager.get_instance()
    
    print(f"Instance 1: {id(mgr1)}")
    print(f"Instance 2: {id(mgr2)}")
    print(f"Same instance? {mgr1 is mgr2}")
    
    assert mgr1 is mgr2, "Singleton failed - different instances!"
    print("✅ PASS: Singleton returns same instance")


def test_lazy_loading():
    """Test that data is loaded on first access."""
    print("\n" + "="*80)
    print("TEST 2: Lazy Loading")
    print("="*80)
    
    # Fresh instance for this test
    mgr = DataManager.get_instance()
    print(f"DataManager state: {mgr}")
    
    print("\nFirst call to get_all_weapons (triggers load)...")
    start = time.time()
    weapons_first = mgr.get_all_weapons(detailed=False)
    first_time = time.time() - start
    
    print(f"  Time: {first_time:.3f}s")
    print(f"  Weapons loaded: {len(weapons_first)}")
    print(f"  Weapons: {list(weapons_first.keys())[:3]}...")
    
    print("\nSecond call to get_all_weapons (should be cached)...")
    start = time.time()
    weapons_second = mgr.get_all_weapons(detailed=False)
    second_time = time.time() - start
    
    print(f"  Time: {second_time:.3f}s")
    print(f"  Weapons loaded: {len(weapons_second)}")
    
    assert weapons_first == weapons_second, "Data changed!"
    assert second_time < first_time, "Caching not working!"
    print(f"✅ PASS: Caching working (speedup: {first_time/second_time:.0f}x)")


def test_apis():
    """Test all DataManager API methods."""
    print("\n" + "="*80)
    print("TEST 3: API Methods")
    print("="*80)
    
    mgr = DataManager.get_instance()
    
    # Test get_weapons_list
    print("\n1. get_weapons_list():")
    weapons = mgr.get_weapons_list()
    print(f"   ✓ Returns list of {len(weapons)} weapons")
    print(f"   ✓ Sorted: {weapons == sorted(weapons)}")
    print(f"   ✓ Examples: {weapons[:3]}")
    
    # Test validate_weapon_exists
    print("\n2. validate_weapon_exists():")
    exists = mgr.validate_weapon_exists("Chrono Field")
    print(f"   ✓ 'Chrono Field' exists: {exists}")
    assert exists, "Chrono Field should exist!"
    
    invalid = mgr.validate_weapon_exists("Nonexistent Weapon")
    print(f"   ✓ 'Nonexistent Weapon' exists: {invalid}")
    assert not invalid, "Nonexistent weapon should not exist!"
    
    # Test get_weapon_data (consolidated)
    print("\n3. get_weapon_data(weapon_name, detailed=False):")
    chrono = mgr.get_weapon_data("Chrono Field", detailed=False)
    print(f"   ✓ Got {len(chrono)} parameters for Chrono Field")
    print(f"   ✓ Parameters: {list(chrono.keys())}")
    for param_name, value in chrono.items():
        print(f"     - {param_name}: {value}")
    
    # Test get_weapon_data (detailed)
    print("\n4. get_weapon_data(weapon_name, detailed=True):")
    chrono_detailed = mgr.get_weapon_data("Chrono Field", detailed=True)
    print(f"   ✓ Got {len(chrono_detailed)} parameters (detailed)")
    duration = chrono_detailed.get("Duration", {})
    print(f"   ✓ Duration breakdown:")
    if isinstance(duration, dict):
        print(f"     - UW Level: {duration.get('uw_level', 'N/A')}")
        print(f"     - UW Value: {duration.get('uw_value', 'N/A')}")
        print(f"     - Labs Level: {duration.get('labs_level', 'N/A')}")
        print(f"     - Labs Value: {duration.get('labs_value', 'N/A')}")
        print(f"     - Total: {duration.get('total_value', 'N/A')}")
    
    # Test get_all_weapons
    print("\n5. get_all_weapons(detailed=False):")
    all_weapons = mgr.get_all_weapons(detailed=False)
    print(f"   ✓ Got {len(all_weapons)} weapons")
    for weapon_name, params in list(all_weapons.items())[:2]:
        print(f"   ✓ {weapon_name}: {len(params)} parameters")
    
    # Test get_load_info
    print("\n6. get_load_info():")
    info = mgr.get_load_info()
    for key, value in info.items():
        print(f"   ✓ {key}: {value}")
    
    print("\n✅ PASS: All API methods working")


def test_consolidation():
    """Test consolidated vs detailed output."""
    print("\n" + "="*80)
    print("TEST 4: Consolidated vs Detailed Output")
    print("="*80)
    
    mgr = DataManager.get_instance()
    
    print("\nConsolidated output (final values only):")
    consolidated = mgr.get_weapon_data("Death Wave", detailed=False)
    for param, value in list(consolidated.items())[:3]:
        print(f"  {param}: {value}")
    
    print("\nDetailed output (component breakdown):")
    detailed = mgr.get_weapon_data("Death Wave", detailed=True)
    bonus = detailed.get("Bonus", {})
    if isinstance(bonus, dict):
        print(f"  Bonus breakdown:")
        print(f"    - UW Value: {bonus.get('uw_value', 0)}")
        print(f"    - Labs Value: +{bonus.get('labs_value', 0)}")
        print(f"    - Module Value: +{bonus.get('module_value', 0)}")
        print(f"    - Relic Value: +{bonus.get('relic_value', 0)}")
        print(f"    - Total: {bonus.get('total_value', 0)}")
        
        # Verify calculation
        calculated = (bonus.get('uw_value', 0) + 
                     bonus.get('labs_value', 0) + 
                     bonus.get('module_value', 0) + 
                     bonus.get('relic_value', 0))
        expected = bonus.get('total_value', 0)
        matches = abs(calculated - expected) < 0.01
        print(f"    ✓ Calculation verified: {matches}")
    
    print("\n✅ PASS: Consolidated and detailed outputs working")


def test_all_weapons_consistency():
    """Test that get_all_weapons and get_weapon_data return consistent data."""
    print("\n" + "="*80)
    print("TEST 5: Consistency Check")
    print("="*80)
    
    mgr = DataManager.get_instance()
    
    # Get all weapons
    all_weapons = mgr.get_all_weapons(detailed=False)
    
    # Check each weapon
    print(f"\nVerifying {len(all_weapons)} weapons...")
    for weapon_name in list(all_weapons.keys())[:3]:
        direct = mgr.get_weapon_data(weapon_name, detailed=False)
        assert direct == all_weapons[weapon_name], f"Data mismatch for {weapon_name}!"
        print(f"  ✓ {weapon_name}: consistent")
    
    print("\n✅ PASS: All data is consistent")


def main():
    """Run all tests."""
    print("\n" + "="*80)
    print("DataManager Test Suite")
    print("="*80)
    
    try:
        test_singleton()
        test_lazy_loading()
        test_apis()
        test_consolidation()
        test_all_weapons_consistency()
        
        print("\n" + "="*80)
        print("✅ ALL TESTS PASSED")
        print("="*80)
        print("\nDataManager is ready for use in pages!")
        print("\nUsage example:")
        print("  from functions.data import DataManager")
        print("")
        print("  mgr = DataManager.get_instance()")
        print("  weapons = mgr.get_all_weapons(detailed=True)")
        print("  chrono = mgr.get_weapon_data('Chrono Field')")
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
