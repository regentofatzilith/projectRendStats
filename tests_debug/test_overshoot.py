"""Test overshoot credit scenario."""
from functions.simulation import compute_multiplier_simulation

print("Scenario: 100s cooldown, package at t=90 with -13s reduction")
print("Expected: instant activation, new cooldown = 97s")
print()

# Simulate with guaranteed package every 30s
df, avg, comp = compute_multiplier_simulation(
    duration_s=300,
    game_mode='tournament',
    generator_module='Galaxy Compressor',
    generator_rarity='Legendary',  # -13s per package
    package_chance_pct=100.0,  # Guarantee packages every wave
    gt_cooldown_s=100.0,
    gt_duration_s=10.0,
)

gt_series = comp['golden_tower']
pkg_times = comp.get('package_times', [])

print("Package collection times:", pkg_times)
print()
print("Golden Tower activations (first 150s):")
prev_active = False
for t in range(min(150, len(gt_series))):
    active = gt_series[t] != 1.0
    if active and not prev_active:
        pkg_info = " [PACKAGE]" if t in pkg_times else ""
        print(f"  Activated at t={t:3d}{pkg_info}")
    prev_active = active

print()
print(f"Overall uptime: {comp['uptimes']['golden_tower']:.1f}%")
print()
print("Analysis:")
print("- First package at t=30 (timer at ~70s) → timer becomes 57s")
print("- Second package at t=60 (timer at ~27s) → timer becomes 14s")  
print("- Third package at t=90 (timer at ~11s → 0 with 2s credit)")
print("  → Instant activation, new cooldown = 100 - 2 = 98s")
print("- If overshoot credit works: activations become more frequent over time")
