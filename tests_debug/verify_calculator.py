"""Verify against calculator screenshot: 50s CD, 50s duration = 99% uptime."""
from functions.simulation import compute_multiplier_simulation

print("Calculator scenario: Black Hole 50s cooldown, 50s duration")
print("Expected: ~99% effective uptime")
print()

# Long simulation to get accurate steady-state percentage
df, avg, comp = compute_multiplier_simulation(
    duration_s=3600,
    game_mode='farming',
    armor_module='Primordial Collapse',
    generator_module='Galaxy Compressor',
    generator_rarity='Legendary',
    package_chance_pct=73.0,
    bh_cooldown_s=50.0,
    bh_duration_s=50.0,
    start_after_first_cooldown=False,  # Start immediately for steady-state
)

bh_uptime = comp['uptimes']['black_hole']
print(f"Simulated uptime: {bh_uptime:.1f}%")
print(f"Calculator shows: 99.0%")
print(f"Difference: {abs(bh_uptime - 99.0):.1f}%")
print()

if bh_uptime >= 98.5:
    print("✓ Match! Within acceptable tolerance")
else:
    print(f"⚠ Gap of {99.0 - bh_uptime:.1f}% - may need further investigation")
