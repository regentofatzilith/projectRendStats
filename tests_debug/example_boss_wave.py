"""Example usage of boss wave detection and lab package functionality.

This demonstrates how to use the new boss wave features in the simulation.
"""

from functions.simulation import UltimateWeaponSimulator


def example_basic_boss_waves():
    """Basic usage: Enable lab package after boss."""
    print("=" * 60)
    print("Example 1: Basic Boss Wave Detection")
    print("=" * 60)
    
    sim = UltimateWeaponSimulator(
        duration_s=1800,  # 30 minutes
        game_mode="farming",
        generator_module="Galaxy Compressor",
        generator_rarity="Ancestral",
        boss_wave_interval=10,  # Boss every 10 waves (default)
        lab_package_after_boss=True,  # Enable lab upgrade
    )
    sim.run()
    
    components = sim.get_components()
    
    print(f"Boss waves detected: {components['boss_waves']}")
    print(f"Boss packages collected: {len(components['boss_package_times'])}")
    print(f"Average multiplier: {sim.average_multiplier:.4f}×")
    print()


def example_with_callback():
    """Use callback to track boss packages in real-time."""
    print("=" * 60)
    print("Example 2: Boss Wave with Callback")
    print("=" * 60)
    
    def log_boss_package(time_s, wave_idx):
        """Callback function triggered when boss package is collected."""
        print(f"  📦 Boss defeated! Package received at wave {wave_idx} (t={time_s}s)")
    
    sim = UltimateWeaponSimulator(
        duration_s=900,
        game_mode="farming",
        boss_wave_interval=5,  # More frequent for demo
        lab_package_after_boss=True,
        on_boss_package_callback=log_boss_package,
    )
    
    print("Running simulation with boss wave callback...\n")
    sim.run()
    
    print(f"\nTotal boss packages: {len(sim.boss_package_times)}")
    print(f"Average multiplier: {sim.average_multiplier:.4f}×")
    print()


def example_compare_intervals():
    """Compare different boss wave intervals."""
    print("=" * 60)
    print("Example 3: Comparing Boss Wave Intervals")
    print("=" * 60)
    
    intervals = [4, 5, 6, 8, 10]
    
    for interval in intervals:
        sim = UltimateWeaponSimulator(
            duration_s=1200,  # 20 minutes
            game_mode="farming",
            generator_module="Galaxy Compressor",
            generator_rarity="Ancestral",
            package_chance_pct=0.0,  # Disable random packages for fair comparison
            boss_wave_interval=interval,
            lab_package_after_boss=True,
        )
        sim.run()
        
        num_packages = len(sim.boss_package_times)
        avg_mult = sim.average_multiplier
        
        print(f"  Interval {interval:2d}: {num_packages:2d} packages → {avg_mult:.4f}× avg multiplier")
    
    print()


def example_impact_analysis():
    """Analyze the impact of boss packages on performance."""
    print("=" * 60)
    print("Example 4: Impact Analysis")
    print("=" * 60)
    
    duration = 1800
    
    # Without boss packages
    sim_without = UltimateWeaponSimulator(
        duration_s=duration,
        game_mode="farming",
        generator_module="Galaxy Compressor",
        generator_rarity="Ancestral",
        package_chance_pct=50.0,  # Normal random packages
        lab_package_after_boss=False,
    )
    sim_without.run()
    
    # With boss packages
    sim_with = UltimateWeaponSimulator(
        duration_s=duration,
        game_mode="farming",
        generator_module="Galaxy Compressor",
        generator_rarity="Ancestral",
        package_chance_pct=50.0,
        boss_wave_interval=10,
        lab_package_after_boss=True,
    )
    sim_with.run()
    
    mult_without = sim_without.average_multiplier
    mult_with = sim_with.average_multiplier
    improvement = ((mult_with / mult_without) - 1) * 100
    
    print(f"Without 'Package After Boss' lab:")
    print(f"  Random packages: {len(sim_without.package_times)}")
    print(f"  Average multiplier: {mult_without:.4f}×")
    print()
    print(f"With 'Package After Boss' lab:")
    print(f"  Random packages: {len(sim_with.package_times)}")
    print(f"  Boss packages: {len(sim_with.boss_package_times)}")
    print(f"  Total packages: {len(sim_with.package_times) + len(sim_with.boss_package_times)}")
    print(f"  Average multiplier: {mult_with:.4f}×")
    print()
    print(f"Performance improvement: +{improvement:.2f}%")
    print()


if __name__ == "__main__":
    example_basic_boss_waves()
    example_with_callback()
    example_compare_intervals()
    example_impact_analysis()
    
    print("=" * 60)
    print("✅ All examples completed!")
    print("=" * 60)
