#!/usr/bin/env python
"""Verification script for refactored package structure."""

import sys
from pathlib import Path

# Ensure we're in the project root
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

print("=" * 60)
print("Package Refactoring Verification")
print("=" * 60)

tests_passed = 0
tests_failed = 0

def test_import(description, import_statement):
    """Test an import statement and report results."""
    global tests_passed, tests_failed
    try:
        exec(import_statement)
        print(f"✓ {description}")
        tests_passed += 1
        return True
    except Exception as e:
        print(f"✗ {description}: {e}")
        tests_failed += 1
        return False

# Test core package imports
print("\n1. Testing Core Package Imports")
print("-" * 60)
test_import("functions package", "import functions")
test_import("user_data_store singleton", "from functions import user_data_store")

# Test data subpackage
print("\n2. Testing Data Subpackage")
print("-" * 60)
test_import("DataStore module", "from functions.data import DataStore")
test_import("ImportJSON module", "from functions.data import ImportJSON")
test_import("ConvertNumbers module", "from functions.data import ConvertNumbers")
test_import("UserDataStore class", "from functions.data import UserDataStore")
test_import("Import_JSON_record function", "from functions.data import Import_JSON_record")
test_import("time_to_decimal_hours function", "from functions.data import time_to_decimal_hours")

# Test geometry subpackage
print("\n3. Testing Geometry Subpackage")
print("-" * 60)
test_import("TowerGeometry module", "from functions.geometry import TowerGeometry")
test_import("tower_layout_figure_with_kpis", "from functions.geometry import tower_layout_figure_with_kpis")
test_import("golden_bot_figure_with_kpis", "from functions.geometry import golden_bot_figure_with_kpis")

# Test graphs subpackage
print("\n4. Testing Graphs Subpackage")
print("-" * 60)
test_import("Graphs module", "from functions.graphs import Graphs")
test_import("Optimizer module", "from functions.graphs import Optimizer")
test_import("combined_metrics_figure", "from functions.graphs import combined_metrics_figure")
test_import("makeTable function", "from functions.graphs import makeTable")

# Test simulation subpackage
print("\n5. Testing Simulation Subpackage")
print("-" * 60)
test_import("Simulation module", "from functions.simulation import Simulation")
test_import("SimulationClass module", "from functions.simulation import SimulationClass")
test_import("compute_multiplier_simulation", "from functions.simulation import compute_multiplier_simulation")
test_import("UltimateWeaponSimulator", "from functions.simulation import UltimateWeaponSimulator")

# Test statistics subpackage
print("\n6. Testing Statistics Subpackage")
print("-" * 60)
test_import("Statistics module", "from functions.statistics import Statistics")
test_import("forecast_stats module", "from functions.statistics import forecast_stats")
test_import("TimeSeriesStats class", "from functions.statistics import TimeSeriesStats")
test_import("forecast_metric function", "from functions.statistics import forecast_metric")

# Test app module
print("\n7. Testing Application Module")
print("-" * 60)
test_import("app module", "import app")

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)
print(f"Tests Passed: {tests_passed}")
print(f"Tests Failed: {tests_failed}")
print(f"Success Rate: {tests_passed / (tests_passed + tests_failed) * 100:.1f}%")
print("=" * 60)

if tests_failed == 0:
    print("\n🎉 All tests passed! The refactoring is successful.")
    sys.exit(0)
else:
    print(f"\n⚠️  {tests_failed} test(s) failed. Please review the errors above.")
    sys.exit(1)
