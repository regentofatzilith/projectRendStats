"""Multiplier simulation for ultimate weapons with dropdown overrides.

This file provides backward-compatible wrapper around the new class-based
SimulationClass.UltimateWeaponSimulator. The original function signature is
preserved for existing code, but internally uses the cleaner class design.
"""

import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple, Optional

from .SimulationClass import UltimateWeaponSimulator
from functions.data import ImportJSON
from functions import user_data_store


def compute_multiplier_simulation(
    duration_s: int = 3600,
    game_mode: str = "farming",
    armor_module: str = "Primordial Collapse",
    armor_rarity: str = "Ancestral",
    generator_module: str = "Galaxy Compressor",
    generator_rarity: str = "Legendary",
    package_chance_pct: float = 73.0,
    # Golden Bot overrides
    gb_cooldown_s: Optional[float] = None,
    gb_uptime_s: Optional[float] = None,
    gb_bonus_mult: Optional[float] = None,
    gb_range_override: Optional[float] = None,
    # Death Wave overrides
    dw_cooldown_s: Optional[float] = None,
    dw_waves_count: Optional[float] = None,
    dw_bonus_mult: Optional[float] = None,
    # Golden Tower overrides
    gt_cooldown_s: Optional[float] = None,
    gt_duration_s: Optional[float] = None,
    gt_bonus_mult: Optional[float] = None,
    # Black Hole overrides
    bh_cooldown_s: Optional[float] = None,
    bh_duration_s: Optional[float] = None,
    bh_bonus_mult: Optional[float] = None,
    bh_size_override: Optional[float] = None,
    # Spotlight overrides
    sp_damage_mult: Optional[float] = None,
    sp_angle_deg: Optional[float] = None,
    sp_quantity_override: Optional[float] = None,
    # Chrono Field overrides
    cf_cooldown_s: Optional[float] = None,
    cf_duration_s: Optional[float] = None,
    # Geometry inputs
    tower_range: Optional[float] = None,
    bot_range: Optional[float] = None,
    bh_diameter: Optional[float] = None,
    bh_count: Optional[int] = None,
    start_after_first_cooldown: bool = True,
    # Boss wave configuration
    boss_wave_interval: int = 10,
    lab_package_after_boss: bool = False,
    on_boss_package_callback: Optional[Any] = None,
    # Predefined package times
    predefined_package_times: Optional[list] = None,
) -> Tuple[pd.DataFrame, float, Dict[str, np.ndarray]]:
    """Simulate second-by-second multipliers for ultimate weapons.
    
    Backward-compatible wrapper around UltimateWeaponSimulator class.
    Returns (timeline dataframe, average total multiplier, components dict).
    All overrides are optional; if provided they replace parsed base values
    before perks are applied.
    """
    # Create simulator instance with base configuration
    sim = UltimateWeaponSimulator(
        duration_s=duration_s,
        game_mode=game_mode,
        armor_module=armor_module,
        armor_rarity=armor_rarity,
        generator_module=generator_module,
        generator_rarity=generator_rarity,
        package_chance_pct=package_chance_pct,
        tower_range=tower_range,
        bot_range=bot_range,
        bh_diameter=bh_diameter,
        bh_count=bh_count,
        start_after_first_cooldown=start_after_first_cooldown,
        boss_wave_interval=boss_wave_interval,
        lab_package_after_boss=lab_package_after_boss,
        on_boss_package_callback=on_boss_package_callback,
        predefined_package_times=predefined_package_times,
    )
    
    # Apply overrides (enhancement planner mode)
    sim.set_overrides(
        gb_cooldown_s=gb_cooldown_s,
        gb_uptime_s=gb_uptime_s,
        gb_bonus_mult=gb_bonus_mult,
        gb_range_override=gb_range_override,
        dw_cooldown_s=dw_cooldown_s,
        dw_waves_count=dw_waves_count,
        dw_bonus_mult=dw_bonus_mult,
        gt_cooldown_s=gt_cooldown_s,
        gt_duration_s=gt_duration_s,
        gt_bonus_mult=gt_bonus_mult,
        bh_cooldown_s=bh_cooldown_s,
        bh_duration_s=bh_duration_s,
        bh_bonus_mult=bh_bonus_mult,
        bh_size_override=bh_size_override,
        sp_damage_mult=sp_damage_mult,
        sp_angle_deg=sp_angle_deg,
        sp_quantity_override=sp_quantity_override,
        cf_cooldown_s=cf_cooldown_s,
        cf_duration_s=cf_duration_s,
    )
    
    # Run simulation
    sim.run()
    
    # Return in original format
    df = sim.to_dataframe()
    avg_total = sim.average_multiplier
    components = sim.get_components()
    
    return df, avg_total, components
