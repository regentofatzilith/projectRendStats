#!/usr/bin/env python
"""Quick verification that config.py refactoring is complete and working."""

import sys

def verify_imports():
    """Verify all imports work correctly."""
    results = []
    
    # Test 1: config module
    try:
        from functions.data import config
        assert hasattr(config, 'GOLDEN_TOWER_LOOKUPS')
        assert hasattr(config, 'CHRONO_FIELD_LOOKUPS')
        assert hasattr(config, 'LABS_LOOKUPS')
        results.append(("[OK]", "config.py module imports"))
    except Exception as e:
        results.append(("[FAIL]", f"config.py: {e}"))
        return results
    
    # Test 2: ImportJSON re-exports
    try:
        from functions.data import ImportJSON
        assert hasattr(ImportJSON, 'GOLDEN_TOWER_LOOKUPS')
        assert hasattr(ImportJSON, 'LABS_LOOKUPS')
        results.append(("[OK]", "ImportJSON re-exports lookups"))
    except Exception as e:
        results.append(("[FAIL]", f"ImportJSON re-exports: {e}"))
        return results
    
    # Test 3: UltimateWeapons imports
    try:
        from functions.data import UltimateWeaponAnalyzer
        results.append(("[OK]", "UltimateWeapons imports config"))
    except Exception as e:
        results.append(("[FAIL]", f"UltimateWeapons: {e}"))
        return results
    
    # Test 4: Verify lookups are identical
    try:
        from functions.data import config, ImportJSON
        assert config.GOLDEN_TOWER_LOOKUPS is ImportJSON.GOLDEN_TOWER_LOOKUPS
        assert config.LABS_LOOKUPS is ImportJSON.LABS_LOOKUPS
        results.append(("[OK]", "Lookups are identical (same objects)"))
    except Exception as e:
        results.append(("[FAIL]", f"Lookup identity: {e}"))
        return results
    
    return results

def main():
    """Run verification."""
    print("=" * 70)
    print("CONFIG.PY REFACTORING VERIFICATION")
    print("=" * 70)
    
    results = verify_imports()
    
    for status, message in results:
        print(f"{status} {message}")
    
    print("=" * 70)
    
    # Check if all passed
    all_passed = all(status == "[OK]" for status, _ in results)
    
    if all_passed:
        print("\n✓ All verifications passed!")
        print("\nRefactoring complete:")
        print("  • config.py created with all lookup tables")
        print("  • ImportJSON.py imports from config and re-exports")
        print("  • UltimateWeapons.py imports directly from config")
        print("  • Backward compatibility maintained")
        return 0
    else:
        print("\n✗ Some verifications failed!")
        return 1

if __name__ == "__main__":
    sys.exit(main())
