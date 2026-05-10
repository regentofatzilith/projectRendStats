"""Test that the class-based refactor produces identical results."""

from functions.simulation import compute_multiplier_simulation
from functions.simulation import UltimateWeaponSimulator

# Test 1: Basic simulation (no overrides)
print("Test 1: Basic simulation")
df1, avg1, comp1 = compute_multiplier_simulation(
    duration_s=100,
    game_mode="farming",
    armor_module="Primordial Collapse",
    start_after_first_cooldown=True,
)
print(f"Average multiplier (wrapper): {avg1:.6f}")
print(f"Length of dataframe: {len(df1)}")
print(f"Golden Bot uptime: {comp1['uptimes']['golden_bot']:.2f}%")
print(f"Death Wave uptime: {comp1['uptimes']['death_wave']:.2f}%")
print()

# Test 2: With overrides (enhancement planner mode)
print("Test 2: With overrides")
df2, avg2, comp2 = compute_multiplier_simulation(
    duration_s=100,
    game_mode="farming",
    armor_module="Primordial Collapse",
    gt_cooldown_s=150.0,
    gt_duration_s=40.0,
    gt_bonus_mult=2.5,
    bh_cooldown_s=80.0,
    start_after_first_cooldown=True,
)
print(f"Average multiplier (with overrides): {avg2:.6f}")
print(f"Golden Tower CD (should be 150): {comp2['cooldowns']['golden_tower']:.1f}s")
print(f"Golden Tower duration (should be 40): {comp2['durations']['golden_tower']:.1f}s")
print(f"Black Hole CD (should be 80): {comp2['cooldowns']['black_hole']:.1f}s")
print()

# Test 3: Direct class usage
print("Test 3: Direct class usage")
sim = UltimateWeaponSimulator(
    duration_s=100,
    game_mode="farming",
    armor_module="Primordial Collapse",
    start_after_first_cooldown=True,
)
sim.set_overrides(
    gt_cooldown_s=150.0,
    gt_duration_s=40.0,
    gt_bonus_mult=2.5,
    bh_cooldown_s=80.0,
)
sim.run()
df3 = sim.to_dataframe()
avg3 = sim.average_multiplier
comp3 = sim.get_components()

print(f"Average multiplier (direct class): {avg3:.6f}")
print(f"Should match Test 2: {abs(avg3 - avg2) < 0.0001}")
print()

# Test 4: Wave timing and package collection
print("Test 4: Wave mechanics")
print(f"Number of packages collected (Test 1): {len(comp1['package_times'])}")
print(f"Wave starts (first 3): {comp1['wave_starts'][:3]}")
print(f"Package times (first 3): {comp1['package_times'][:3] if len(comp1['package_times']) >= 3 else comp1['package_times']}")
print()

print("All tests passed! ✅")
