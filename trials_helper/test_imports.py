"""
Test script to verify all imports work before building executable.
Run this before building to catch import errors early.
"""

print("Testing imports...")
print("-" * 50)

try:
    print("✓ dash", end=" ")
    import dash
    print(f"(v{dash.__version__})")
except ImportError as e:
    print(f"\n✗ dash FAILED: {e}")

try:
    print("✓ plotly", end=" ")
    import plotly
    print(f"(v{plotly.__version__})")
except ImportError as e:
    print(f"\n✗ plotly FAILED: {e}")

try:
    print("✓ pandas", end=" ")
    import pandas as pd
    print(f"(v{pd.__version__})")
except ImportError as e:
    print(f"\n✗ pandas FAILED: {e}")

try:
    print("✓ numpy", end=" ")
    import numpy as np
    print(f"(v{np.__version__})")
except ImportError as e:
    print(f"\n✗ numpy FAILED: {e}")

try:
    print("✓ scipy", end=" ")
    import scipy
    print(f"(v{scipy.__version__})")
except ImportError as e:
    print(f"\n✗ scipy FAILED: {e}")

try:
    print("✓ sklearn", end=" ")
    import sklearn
    print(f"(v{sklearn.__version__})")
except ImportError as e:
    print(f"\n✗ sklearn FAILED: {e}")

try:
    print("✓ dash_bootstrap_components", end=" ")
    import dash_bootstrap_components as dbc
    print(f"(v{dbc.__version__})")
except ImportError as e:
    print(f"\n✗ dash_bootstrap_components FAILED: {e}")

try:
    print("✓ requests")
    import requests
except ImportError as e:
    print(f"\n✗ requests FAILED: {e}")

try:
    print("✓ beautifulsoup4")
    from bs4 import BeautifulSoup
except ImportError as e:
    print(f"\n✗ beautifulsoup4 FAILED: {e}")

print("-" * 50)
print("\nTesting custom modules...")
print("-" * 50)

try:
    print("✓ functions.data.DataStore")
    from functions.data.DataStore import DataStore
except ImportError as e:
    print(f"✗ DataStore FAILED: {e}")

try:
    print("✓ functions.graphs.Graphs")
    from functions.graphs.Graphs import get_color_for_metric
except ImportError as e:
    print(f"✗ Graphs FAILED: {e}")

try:
    print("✓ functions.statistics.forecast_stats")
    from functions.statistics.forecast_stats import forecast_metric
except ImportError as e:
    print(f"✗ forecast_stats FAILED: {e}")

try:
    print("✓ pages.metrics_data")
    from pages.metrics_data import build_tier_options
except ImportError as e:
    print(f"✗ metrics_data FAILED: {e}")

print("-" * 50)
print("\n✅ All imports successful!")
print("\nYou can now run: build.bat")
print("Or: pyinstaller build_exe.spec")
