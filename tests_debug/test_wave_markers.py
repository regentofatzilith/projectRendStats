"""Test that wave markers and package times are properly returned from simulation."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from functions.simulation import compute_multiplier_simulation

# Run a short simulation to check markers
df, avg_mult, components = compute_multiplier_simulation(
    game_mode="farming",
    duration_s=120,  # 2 minutes
    package_chance_pct=73.0
)

print(f"\n=== Wave Timing Test (Farming Mode) ===")
print(f"WAVE_DURATION: 30.14s")
print(f"Expected waves in 120s: {120 / 30.14:.1f} ≈ 4 waves")
print(f"\nWave starts returned: {components.get('wave_starts', [])}")
print(f"Package times returned: {components.get('package_times', [])}")
print(f"\nTotal waves: {len(components.get('wave_starts', []))}")
print(f"Total packages: {len(components.get('package_times', []))}")
print(f"Package rate: {len(components.get('package_times', [])) / len(components.get('wave_starts', [])):.1%} (expected ~73%)")
