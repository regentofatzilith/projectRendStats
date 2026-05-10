import math
from functions.simulation import compute_multiplier_simulation

def test_farming_black_hole_uptime():
    # Farming mode should add +12s to black hole uptime compared to tournament (defaults)
    df_farm, avg_farm, comp_farm = compute_multiplier_simulation(duration_s=60, game_mode='farming')
    df_tourn, avg_tourn, comp_tourn = compute_multiplier_simulation(duration_s=60, game_mode='tournament')
    bh_farm = comp_farm['durations']['black_hole']
    bh_tourn = comp_tourn['durations']['black_hole']
    assert math.isclose(bh_farm, bh_tourn + 12.0, rel_tol=1e-6), f"Expected farming BH uptime = tournament + 12 (got {bh_farm} vs {bh_tourn})"


def test_farming_spotlight_damage():
    # Spotlight damage perk is x1.5, but effective multiplier scales by coverage.
    # Therefore (sp_farm - 1) should be 1.5x (sp_tourn - 1) for the same coverage.
    df_farm, avg_farm, comp_farm = compute_multiplier_simulation(duration_s=10, game_mode='farming')
    df_tourn, avg_tourn, comp_tourn = compute_multiplier_simulation(duration_s=10, game_mode='tournament')
    sp_farm = float(comp_farm['spotlight'][0])
    sp_tourn = float(comp_tourn['spotlight'][0])
    # If tournament has no boost (often 1.0×), then farming should be > 1.0× due to coverage*0.5
    if abs(sp_tourn - 1.0) < 1e-9:
        assert sp_farm > 1.0, f"Expected farming spotlight > 1.0 due to x1.5 damage and coverage (got {sp_farm})"
    else:
        import math
        assert math.isclose(sp_farm - 1.0, 1.5 * (sp_tourn - 1.0), rel_tol=1e-6), (
            f"Expected (farming-1) = 1.5×(tournament-1), got {sp_farm-1:.6f} vs {1.5*(sp_tourn-1):.6f}")

if __name__ == '__main__':
    test_farming_black_hole_uptime()
    test_farming_spotlight_damage()
    print('Farming perks tests passed.')
