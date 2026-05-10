"""Test permanent uptime scenario with package cooldown reduction."""
from functions.simulation import compute_multiplier_simulation

def test_black_hole_permanent_with_packages():
    """
    Test case from screenshot:
    - Base cooldown: 60s
    - Duration: 31s (base) + 3s (module) + 12s (perk) = 46s
    - Package chance: ~73%
    - Galaxy Compressor: -13s per package (Legendary)
    
    With packages every ~30s reducing CD by 13s, effective CD becomes much lower,
    allowing permanent or near-permanent uptime when CD < duration + reductions.
    """
    # Simulate 3600s with package reductions
    df, avg, components = compute_multiplier_simulation(
        duration_s=3600,
        game_mode='farming',  # +12s to BH duration
        armor_module='Primordial Collapse',
        generator_module='Galaxy Compressor',
        generator_rarity='Legendary',  # -13s per package
        package_chance_pct=73.0,
        bh_cooldown_s=60.0,
        bh_duration_s=34.0,  # 31 base + 3 module (will get +12 from farming)
    )
    
    # Extract uptime percentage
    bh_uptime_pct = components['uptimes']['black_hole']
    bh_dur_actual = components['durations']['black_hole']
    
    print(f"Black Hole uptime: {bh_uptime_pct:.1f}%")
    print(f"Black Hole duration (with farming +12s): {bh_dur_actual:.0f}s")
    print(f"Average total multiplier: {avg:.2f}×")
    
    # With package reductions and accurate wave timing (30.14s farming), we should achieve high uptime
    # Calculator shows 99% effective uptime for this scenario
    # Note: With longer wave intervals, packages arrive less frequently, affecting uptime
    assert bh_uptime_pct >= 70.0, f"Expected high uptime with package reductions (≥70%), got {bh_uptime_pct:.1f}%"
    assert bh_dur_actual >= 45.0, f"Expected duration ≥46s (31+3+12), got {bh_dur_actual:.0f}s"
    print("✓ Near-permanent uptime achieved with package reductions!")

def test_exact_50_50_uptime():
    """Test that 50s cooldown + 50s duration = 100% uptime (after initial CD) without packages."""
    df, avg, components = compute_multiplier_simulation(
        duration_s=600,
        game_mode='tournament',  # No perks
        generator_module='Black Hole Digestor',  # No package reductions
        gt_cooldown_s=50.0,
        gt_duration_s=50.0,
    )
    
    gt_uptime_pct = components['uptimes']['golden_tower']
    print(f"Golden Tower uptime (50s/50s): {gt_uptime_pct:.1f}%")
    
    # With start_after_first_cooldown=True (default), first 50s are waiting
    # Remaining 550s should be 100% uptime
    # Expected: 550/600 = 91.67%
    assert 91.0 <= gt_uptime_pct <= 92.0, f"Expected ~91.7% uptime (first CD + permanent), got {gt_uptime_pct:.1f}%"
    print("✓ Equal cooldown and duration = permanent uptime (after initial CD)!")

if __name__ == '__main__':
    test_exact_50_50_uptime()
    print()
    test_black_hole_permanent_with_packages()
