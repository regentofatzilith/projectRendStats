"""Debug trace for 50/50 uptime."""
import sys
sys.path.insert(0, r'\\mycloudex2ultra\Thorsten\_python\ProjectAtzi')
from functions.simulation import compute_multiplier_simulation

df, avg, components = compute_multiplier_simulation(
    duration_s=150,  # 3 full cycles (50+50+50)
    game_mode='tournament',
    generator_module='Black Hole Digestor',
    gt_cooldown_s=50.0,
    gt_duration_s=50.0,
    start_after_first_cooldown=False,  # Start active immediately
)

gt_series = components['golden_tower']
print("Golden Tower multipliers (first 120 seconds):")
for t in range(min(120, len(gt_series))):
    mult = gt_series[t]
    if mult != 1.0:
        print(f"t={t:3d}: {mult:.3f}×")

uptime = components['uptimes']['golden_tower']
print(f"\nUptime: {uptime:.1f}%")
print(f"Expected: 100% (CD=duration)")
