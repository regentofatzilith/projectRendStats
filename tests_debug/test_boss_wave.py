"""Test boss wave detection and lab package callback functionality."""

from functions.simulation import UltimateWeaponSimulator


def test_boss_wave_basic():
    """Test basic boss wave detection without lab package."""
    sim = UltimateWeaponSimulator(
        duration_s=600,  # 10 minutes
        game_mode="farming",
        boss_wave_interval=10,
        lab_package_after_boss=False,
    )
    sim.run()
    
    components = sim.get_components()
    
    # Should have boss_waves list in components
    assert "boss_waves" in components
    assert "boss_package_times" in components
    
    # Without lab enabled, no boss packages should be collected
    assert len(components["boss_package_times"]) == 0
    
    print("✓ Boss wave basic test passed")


def test_boss_wave_with_lab():
    """Test boss wave with lab package enabled."""
    sim = UltimateWeaponSimulator(
        duration_s=600,  # 10 minutes (~20 waves)
        game_mode="farming",
        boss_wave_interval=10,
        lab_package_after_boss=True,
    )
    sim.run()
    
    components = sim.get_components()
    
    # Should have detected boss waves and collected packages
    assert len(components["boss_waves"]) > 0
    assert len(components["boss_package_times"]) > 0
    
    # Boss waves should be at multiples of boss_wave_interval
    for boss_wave in components["boss_waves"]:
        assert boss_wave % 10 == 0, f"Boss wave {boss_wave} not at interval 10"
    
    print(f"✓ Boss waves detected: {components['boss_waves']}")
    print(f"✓ Boss packages collected at: {components['boss_package_times']}")
    print(f"✓ Total boss packages: {len(components['boss_package_times'])}")


def test_boss_wave_callback():
    """Test boss wave callback is triggered."""
    callback_calls = []
    
    def boss_callback(time_s: int, wave_idx: int):
        callback_calls.append((time_s, wave_idx))
        print(f"  📦 Boss package callback at t={time_s}s, wave={wave_idx}")
    
    sim = UltimateWeaponSimulator(
        duration_s=600,
        game_mode="farming",
        boss_wave_interval=10,
        lab_package_after_boss=True,
        on_boss_package_callback=boss_callback,
    )
    sim.run()
    
    # Callback should have been called for each boss package
    components = sim.get_components()
    assert len(callback_calls) == len(components["boss_package_times"])
    assert len(callback_calls) > 0
    
    print(f"✓ Callback triggered {len(callback_calls)} times")
    for time_s, wave_idx in callback_calls:
        print(f"  - t={time_s}s, wave={wave_idx}")


def test_boss_wave_intervals():
    """Test different boss wave intervals (4-10)."""
    for interval in [4, 5, 6, 8, 10]:
        sim = UltimateWeaponSimulator(
            duration_s=600,
            game_mode="farming",
            boss_wave_interval=interval,
            lab_package_after_boss=True,
        )
        sim.run()
        
        components = sim.get_components()
        
        # Verify all boss waves are at correct intervals
        for boss_wave in components["boss_waves"]:
            assert boss_wave % interval == 0, f"Interval {interval}: wave {boss_wave} invalid"
        
        print(f"✓ Interval {interval}: {len(components['boss_waves'])} boss waves detected")


def test_boss_package_cooldown_reduction():
    """Test that boss packages also trigger cooldown reduction."""
    sim_no_boss = UltimateWeaponSimulator(
        duration_s=600,
        game_mode="farming",
        generator_module="Galaxy Compressor",
        generator_rarity="Ancestral",
        package_chance_pct=0.0,  # No random packages
        lab_package_after_boss=False,
        boss_wave_interval=10,
    )
    sim_no_boss.run()
    
    sim_with_boss = UltimateWeaponSimulator(
        duration_s=600,
        game_mode="farming",
        generator_module="Galaxy Compressor",
        generator_rarity="Ancestral",
        package_chance_pct=0.0,  # No random packages
        lab_package_after_boss=True,
        boss_wave_interval=10,
    )
    sim_with_boss.run()
    
    # Boss packages should increase average multiplier through cooldown reduction
    avg_no_boss = sim_no_boss.average_multiplier
    avg_with_boss = sim_with_boss.average_multiplier
    
    print(f"✓ Avg mult without boss packages: {avg_no_boss:.3f}×")
    print(f"✓ Avg mult with boss packages: {avg_with_boss:.3f}×")
    
    # With boss packages reducing cooldowns, multiplier should be higher
    assert avg_with_boss >= avg_no_boss, "Boss packages should increase multiplier"
    
    if avg_with_boss > avg_no_boss:
        improvement_pct = ((avg_with_boss / avg_no_boss) - 1) * 100
        print(f"✓ Boss packages improved multiplier by {improvement_pct:.2f}%")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Boss Wave Detection & Lab Package Callback")
    print("=" * 60)
    
    test_boss_wave_basic()
    print()
    
    test_boss_wave_with_lab()
    print()
    
    test_boss_wave_callback()
    print()
    
    test_boss_wave_intervals()
    print()
    
    test_boss_package_cooldown_reduction()
    print()
    
    print("=" * 60)
    print("✅ All boss wave tests passed!")
    print("=" * 60)
