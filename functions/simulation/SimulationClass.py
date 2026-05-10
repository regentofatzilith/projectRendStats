"""Class-based ultimate weapon simulator.

Replaces the monolithic compute_multiplier_simulation() function with a cleaner
object-oriented design that separates configuration, simulation, and results.
"""

import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List, Callable
from functions.data import ImportJSON
from functions import user_data_store


class UltimateWeaponSimulator:
    """Simulates ultimate weapon multipliers with configurable parameters.
    
    Usage:
        # Basic simulation with defaults
        sim = UltimateWeaponSimulator(duration_s=3600, game_mode="farming")
        sim.run()
        avg_multiplier = sim.average_multiplier
        
        # With overrides for enhancement planner
        sim = UltimateWeaponSimulator(duration_s=3600, game_mode="farming")
        sim.set_overrides(gt_cooldown_s=150, gt_duration_s=40, gt_bonus_mult=2.5)
        sim.run()
        
        # Access results
        df = sim.to_dataframe()
        components = sim.get_components()
    """
    
    def __init__(
        self,
        duration_s: int = 3600,
        game_mode: str = "farming",
        armor_module: str = "Primordial Collapse",
        armor_rarity: str = "Ancestral",
        generator_module: str = "Galaxy Compressor",
        generator_rarity: str = "Legendary",
        package_chance_pct: float = 73.0,
        tower_range: Optional[float] = None,
        bot_range: Optional[float] = None,
        bh_diameter: Optional[float] = None,
        bh_count: Optional[int] = None,
        start_after_first_cooldown: bool = False,
        boss_wave_interval: int = 10,
        lab_package_after_boss: bool = False,
        on_boss_package_callback: Optional[Callable[[int, int], None]] = None,
        predefined_package_times: Optional[List[int]] = None,
    ):
        """Initialize simulator with base configuration.
        
        Parameters are loaded from JSON data; overrides can be applied separately
        via set_overrides() before calling run().
        """
        self.duration_s = int(max(1, duration_s))
        self.game_mode = game_mode
        self.armor_module = armor_module
        self.armor_rarity = armor_rarity
        self.generator_module = generator_module
        self.generator_rarity = generator_rarity
        self.package_chance_pct = package_chance_pct
        self.start_after_first_cooldown = start_after_first_cooldown
        
        # Geometry inputs
        self.tower_range = tower_range
        self.bot_range = bot_range
        self.bh_diameter = bh_diameter
        self.bh_count = bh_count
        
        # Boss wave configuration
        self.boss_wave_interval = max(4, min(10, boss_wave_interval))  # Clamp to [4, 10]
        self.lab_package_after_boss = lab_package_after_boss
        self.on_boss_package_callback = on_boss_package_callback
        
        # Predefined package times (for re-roll functionality)
        self.predefined_package_times = predefined_package_times
        
        # Override storage (applied before perks)
        self.overrides: Dict[str, Any] = {}
        
        # Results (populated by run())
        self.timeline_seconds: Optional[np.ndarray] = None
        self.gb_series: Optional[np.ndarray] = None
        self.dw_series: Optional[np.ndarray] = None
        self.gt_series: Optional[np.ndarray] = None
        self.bh_series: Optional[np.ndarray] = None
        self.sp_series: Optional[np.ndarray] = None
        self.cf_series: Optional[np.ndarray] = None
        self.total_series: Optional[np.ndarray] = None
        self.uptime_counters: Dict[str, float] = {}
        self.package_times: List[int] = []
        self.wave_starts_exact: List[float] = []
        self.boss_waves: List[int] = []
        self.boss_package_times: List[int] = []
        
        # Effective parameters after overrides + perks
        self.effective_params: Dict[str, float] = {}
        
    def set_overrides(
        self,
        # Golden Bot
        gb_cooldown_s: Optional[float] = None,
        gb_uptime_s: Optional[float] = None,
        gb_bonus_mult: Optional[float] = None,
        gb_range_override: Optional[float] = None,
        # Death Wave
        dw_cooldown_s: Optional[float] = None,
        dw_waves_count: Optional[float] = None,
        dw_bonus_mult: Optional[float] = None,
        # Golden Tower
        gt_cooldown_s: Optional[float] = None,
        gt_duration_s: Optional[float] = None,
        gt_bonus_mult: Optional[float] = None,
        # Black Hole
        bh_cooldown_s: Optional[float] = None,
        bh_duration_s: Optional[float] = None,
        bh_bonus_mult: Optional[float] = None,
        bh_size_override: Optional[float] = None,
        # Spotlight
        sp_damage_mult: Optional[float] = None,
        sp_angle_deg: Optional[float] = None,
        sp_quantity_override: Optional[float] = None,
        # Chrono Field
        cf_cooldown_s: Optional[float] = None,
        cf_duration_s: Optional[float] = None,
    ):
        """Set parameter overrides for enhancement planner mode.
        
        Any non-None values will override the base JSON values before perks are applied.
        """
        self.overrides.update({
            'gb_cooldown_s': gb_cooldown_s,
            'gb_uptime_s': gb_uptime_s,
            'gb_bonus_mult': gb_bonus_mult,
            'gb_range_override': gb_range_override,
            'dw_cooldown_s': dw_cooldown_s,
            'dw_waves_count': dw_waves_count,
            'dw_bonus_mult': dw_bonus_mult,
            'gt_cooldown_s': gt_cooldown_s,
            'gt_duration_s': gt_duration_s,
            'gt_bonus_mult': gt_bonus_mult,
            'bh_cooldown_s': bh_cooldown_s,
            'bh_duration_s': bh_duration_s,
            'bh_bonus_mult': bh_bonus_mult,
            'bh_size_override': bh_size_override,
            'sp_damage_mult': sp_damage_mult,
            'sp_angle_deg': sp_angle_deg,
            'sp_quantity_override': sp_quantity_override,
            'cf_cooldown_s': cf_cooldown_s,
            'cf_duration_s': cf_duration_s,
        })
        
    def _parse_number(self, val: Any, default: float = 0.0) -> float:
        """Parse a number from various formats."""
        try:
            if isinstance(val, (int, float)):
                return float(val)
            s = str(val)
            import re
            m = re.search(r"([\-+]?\d+(?:\.\d+)?)", s)
            return float(m.group(1)) if m else default
        except Exception:
            return default
            
    def _get_param(self, df: pd.DataFrame, param_keyword: str) -> str:
        """Extract parameter value from dataframe."""
        if df is None or df.empty:
            return ""
        mask = df["Parameter"].astype(str).str.contains(param_keyword, case=False, na=False)
        if mask.any():
            return str(df.loc[mask, "Total Value"].iloc[0])
        return ""
        
    def _extract_combined(self) -> Dict[str, pd.DataFrame]:
        """Extract combined data from JSON store."""
        if user_data_store.full_json is None:
            return {}
        return ImportJSON.extract_combined_ultimate_weapons_data(
            user_data_store.full_json, 
            selected_module=self.armor_module
        )
        
    def _apply_farming_perks(self, values: Dict[str, float]) -> Dict[str, float]:
        """Apply farming mode perks to values."""
        if self.game_mode != "farming":
            return values
        values["death_wave_waves"] = values.get("death_wave_waves", 0.0) + 1.0
        values["spotlight_damage"] = values.get("spotlight_damage", 1.0) * 1.5
        values["golden_tower_bonus"] = values.get("golden_tower_bonus", 1.0) * 1.5
        values["black_hole_uptime"] = values.get("black_hole_uptime", 0.0) + 12.0
        return values
        
    def _load_base_parameters(self):
        """Load base parameters from JSON and apply overrides."""
        combined = self._extract_combined()
        
        # Golden Bot
        gb_df = combined.get("Golden Bot", pd.DataFrame())
        gb_bonus = self._parse_number(self._get_param(gb_df, "Bonus"), 1.0)
        gb_cd = self._parse_number(self._get_param(gb_df, "Cooldown"), 100.0)
        gb_up = self._parse_number(self._get_param(gb_df, "Duration"), 22.0)
        gb_rng = self._parse_number(self._get_param(gb_df, "Range"), 40.0)
        # Inject relics: Bot Range Bonus (absolute meters)
        try:
            bot_range_bonus = float(user_data_store.relics_data.get('Bot Range Bonus', 0.0) or 0.0)
            gb_rng = max(0.0, gb_rng + bot_range_bonus)
        except Exception:
            pass
        
        # Death Wave
        dw_df = combined.get("Death Wave", pd.DataFrame())
        dw_bonus = self._parse_number(self._get_param(dw_df, "Bonus"), 1.0)
        dw_cd = self._parse_number(self._get_param(dw_df, "Cooldown"), 300.0)
        dw_waves = max(1.0, self._parse_number(self._get_param(dw_df, "Quantity"), 1.0))
        
        # Golden Tower
        gt_df = combined.get("Golden Tower", pd.DataFrame())
        gt_bonus = self._parse_number(self._get_param(gt_df, "Bonus"), 1.0)
        gt_cd = self._parse_number(self._get_param(gt_df, "Cooldown"), 200.0)
        gt_up = self._parse_number(self._get_param(gt_df, "Duration"), 30.0)
        
        # Black Hole
        bh_df = combined.get("Black Hole", pd.DataFrame())
        bh_cd = self._parse_number(self._get_param(bh_df, "Cooldown"), 100.0)
        bh_up = self._parse_number(self._get_param(bh_df, "Duration"), 25.0)
        bh_size = self._parse_number(self._get_param(bh_df, "Size"), 48.0)
        bh_bonus = self._parse_number(self._get_param(bh_df, "Bonus"), 1.0)
        
        # Spotlight
        sp_df = combined.get("Spotlight", pd.DataFrame())
        sp_damage = self._parse_number(self._get_param(sp_df, "Damage Mult"), 1.0)
        sp_angle = self._parse_number(self._get_param(sp_df, "Angle"), 60.0)
        sp_quantity = self._parse_number(self._get_param(sp_df, "Quantity"), 1.0)
        
        # Chrono Field
        cf_df = combined.get("Chrono Field", pd.DataFrame())
        cf_cd = self._parse_number(self._get_param(cf_df, "Cooldown"), 100.0)
        cf_up = self._parse_number(self._get_param(cf_df, "Duration"), 25.0)

        # --- Multiverse Nexus cooldown synchronization (mirror table logic) ---
        # If armor module is Multiverse Nexus, synchronize Death Wave, Golden Tower, Black Hole, Chrono Field cooldowns
        # to their average plus rarity-specific offset before any overrides/perks.
        if self.armor_module == "Multiverse Nexus":
            nexus_offsets = {"Epic": 20, "Legendary": 10, "Mythic": 1, "Ancestral": -10}
            offset = nexus_offsets.get(self.armor_rarity, 0)
            # Collect existing cooldown numeric values (already parsed above)
            cds = [dw_cd, gt_cd, bh_cd, cf_cd]
            if all(c > 0 for c in cds):
                avg_cd = (sum(cds) / len(cds)) + offset
                # Apply synchronized cooldown (must remain >= 1)
                dw_cd = max(1.0, avg_cd)
                gt_cd = max(1.0, avg_cd)
                bh_cd = max(1.0, avg_cd)
                cf_cd = max(1.0, avg_cd)
        
        # Apply overrides BEFORE perks
        if self.overrides.get('gb_bonus_mult') is not None:
            gb_bonus = self.overrides['gb_bonus_mult']
        if self.overrides.get('gb_cooldown_s') is not None and self.overrides['gb_cooldown_s'] > 0:
            gb_cd = self.overrides['gb_cooldown_s']
        if self.overrides.get('gb_uptime_s') is not None and self.overrides['gb_uptime_s'] > 0:
            gb_up = self.overrides['gb_uptime_s']
        if self.overrides.get('gb_range_override') is not None and self.overrides['gb_range_override'] > 0:
            gb_rng = self.overrides['gb_range_override']
            
        if self.overrides.get('dw_cooldown_s') is not None and self.overrides['dw_cooldown_s'] > 0:
            dw_cd = self.overrides['dw_cooldown_s']
        if self.overrides.get('dw_waves_count') is not None and self.overrides['dw_waves_count'] > 0:
            dw_waves = self.overrides['dw_waves_count']
        if self.overrides.get('dw_bonus_mult') is not None:
            dw_bonus = self.overrides['dw_bonus_mult']
            
        if self.overrides.get('gt_cooldown_s') is not None and self.overrides['gt_cooldown_s'] > 0:
            gt_cd = self.overrides['gt_cooldown_s']
        if self.overrides.get('gt_duration_s') is not None and self.overrides['gt_duration_s'] > 0:
            gt_up = self.overrides['gt_duration_s']
        if self.overrides.get('gt_bonus_mult') is not None:
            gt_bonus = self.overrides['gt_bonus_mult']
            
        if self.overrides.get('bh_cooldown_s') is not None and self.overrides['bh_cooldown_s'] > 0:
            bh_cd = self.overrides['bh_cooldown_s']
        if self.overrides.get('bh_duration_s') is not None and self.overrides['bh_duration_s'] > 0:
            bh_up = self.overrides['bh_duration_s']
        if self.overrides.get('bh_bonus_mult') is not None:
            bh_bonus = self.overrides['bh_bonus_mult']
        if self.overrides.get('bh_size_override') is not None and self.overrides['bh_size_override'] > 0:
            bh_size = self.overrides['bh_size_override']
            
        if self.overrides.get('sp_damage_mult') is not None:
            sp_damage = self.overrides['sp_damage_mult']
        if self.overrides.get('sp_angle_deg') is not None and self.overrides['sp_angle_deg'] > 0:
            sp_angle = self.overrides['sp_angle_deg']
        if self.overrides.get('sp_quantity_override') is not None and self.overrides['sp_quantity_override'] > 0:
            sp_quantity = self.overrides['sp_quantity_override']
            
        if self.overrides.get('cf_cooldown_s') is not None and self.overrides['cf_cooldown_s'] > 0:
            cf_cd = self.overrides['cf_cooldown_s']
        if self.overrides.get('cf_duration_s') is not None and self.overrides['cf_duration_s'] > 0:
            cf_up = self.overrides['cf_duration_s']
            
        # Apply farming perks (after overrides)
        perk_values = {
            "golden_tower_bonus": gt_bonus,
            "death_wave_waves": dw_waves,
            "spotlight_damage": sp_damage,
            "black_hole_uptime": bh_up,
        }
        perk_values = self._apply_farming_perks(perk_values)
        gt_bonus = perk_values["golden_tower_bonus"]
        dw_waves = perk_values["death_wave_waves"]
        sp_damage = perk_values["spotlight_damage"]
        bh_up = perk_values["black_hole_uptime"]
        
        # Derived uptimes
        dw_up = dw_waves * 4.0
        
        # Clamp cooldowns
        gb_cd = max(1.0, gb_cd)
        dw_cd = max(1.0, dw_cd)
        gt_cd = max(1.0, gt_cd)
        bh_cd = max(1.0, bh_cd)
        cf_cd = max(1.0, cf_cd)
        
        # Store effective parameters
        self.effective_params = {
            'gb_bonus': gb_bonus,
            'gb_cd': gb_cd,
            'gb_up': gb_up,
            'gb_rng': gb_rng,
            'dw_bonus': dw_bonus,
            'dw_cd': dw_cd,
            'dw_up': dw_up,
            'dw_waves': dw_waves,
            'gt_bonus': gt_bonus,
            'gt_cd': gt_cd,
            'gt_up': gt_up,
            'bh_bonus': bh_bonus,
            'bh_cd': bh_cd,
            'bh_up': bh_up,
            'bh_size': bh_size,
            'sp_damage': sp_damage,
            'sp_angle': sp_angle,
            'sp_quantity': sp_quantity,
            'cf_cd': cf_cd,
            'cf_up': cf_up,
        }
        
    def _calculate_coverage_fractions(self):
        """Calculate coverage fractions for each weapon based on geometry."""
        params = self.effective_params
        
        # Geometry defaults
        tr = self.tower_range if self.tower_range and self.tower_range > 0 else 69.5
        br = self.bot_range if self.bot_range and self.bot_range > 0 else params['gb_rng']
        bh_diam = self.bh_diameter if self.bh_diameter and self.bh_diameter > 0 else params['bh_size']
        bh_cnt = self.bh_count if self.bh_count and self.bh_count > 0 else (3 if self.armor_module == "Primordial Collapse" else 2)
        
        # Golden Bot coverage - use sampling to match tower layout calculation
        # Sample 30 random bot positions and calculate average tower range coverage
        gb_coverage_frac = self._sample_golden_bot_coverage(tr, br, samples=30)
        
        # Black Hole coverage
        tower_r = tr / 2.0
        bh_orbit_r = 0.85 * tr / 2.0
        bh_radius = (bh_diam / 2.0) * 1.33 * np.sqrt(tr / 69.5)
        num = tower_r**2 + bh_orbit_r**2 - bh_radius**2
        den = 2 * tower_r * bh_orbit_r if tower_r > 0 and bh_orbit_r > 0 else 1.0
        cos_val = np.clip(num / den, -1.0, 1.0)
        angle_per_bh = 2 * np.arccos(cos_val) * 180 / np.pi
        bh_coverage_frac = float(max(0.0, min(1.0, (angle_per_bh * bh_cnt) / 360.0)))
        
        # Spotlight coverage
        sp_coverage_frac = min(1.0, (params['sp_quantity'] * params['sp_angle']) / 360.0)
        
        # Effective bonuses
        sp_effective = 1.0 + (params['sp_damage'] - 1.0) * sp_coverage_frac
        gb_effective_bonus = 1.0 + (params['gb_bonus'] - 1.0) * gb_coverage_frac
        bh_effective_bonus = 1.0 + (params['bh_bonus'] - 1.0) * bh_coverage_frac
        
        return gb_effective_bonus, bh_effective_bonus, sp_effective, sp_coverage_frac
    
    def _sample_golden_bot_coverage(self, tower_range: float, bot_range: float, samples: int = 30) -> float:
        """Calculate Golden Bot tower range coverage using random position sampling.
        
        This matches the tower layout visualization's calculation method.
        
        Args:
            tower_range: Tower range radius in meters
            bot_range: Golden Bot range in meters (base value)
            samples: Number of random positions to sample
            
        Returns:
            Average coverage fraction (0.0 to 1.0)
        """
        rng = np.random.default_rng(42)  # Fixed seed for reproducibility
        tower_r = tower_range / 2.0
        wall_fraction = 0.40
        wall_r = (tower_range * wall_fraction) / 2.0
        
        # Bot radius scaled in data units (meters) - matching TowerGeometry.py formula
        bot_radius = (bot_range / 2.0) * 1.33 * (tower_range / 69.5)
        
        # Bot can move up to 1.5× tower range radius
        max_r = 1.5 * tower_r
        
        # Sample angles uniformly and radii from clipped normal centered at 0.5*tower_r
        angles = rng.uniform(0, 2 * np.pi, size=samples)
        radii = rng.normal(loc=0.5 * tower_r, scale=0.4 * tower_r, size=samples)
        radii = np.clip(radii, 0.0, max_r)
        
        xs = radii * np.cos(angles)
        ys = radii * np.sin(angles)
        
        # Helper function: calculate arc length where bot circle intersects target circle's circumference
        def calc_circumference_coverage(bot_x: float, bot_y: float, bot_r: float, target_r: float) -> float:
            """Calculate percentage of target circle's circumference covered by bot circle."""
            d = np.sqrt(bot_x**2 + bot_y**2)  # Distance from origin to bot center
            
            # If bot doesn't reach the target circumference, return 0
            if d > target_r + bot_r or d + bot_r < target_r:
                return 0.0
            
            # If bot contains the entire target circle, return 100
            if d + target_r <= bot_r:
                return 100.0
            
            # Calculate intersection points using circle-circle intersection formula
            if abs(d - target_r) < bot_r < d + target_r:
                cos_half_angle = (target_r**2 + d**2 - bot_r**2) / (2.0 * target_r * d)
                cos_half_angle = np.clip(cos_half_angle, -1.0, 1.0)
                half_angle = np.arccos(cos_half_angle)
                arc_angle = 2.0 * half_angle
                return (arc_angle / (2.0 * np.pi)) * 100.0
            
            return 0.0
        
        # Calculate coverage for each sample position
        total_coverage = 0.0
        for i in range(samples):
            bot_x, bot_y = float(xs[i]), float(ys[i])
            coverage = calc_circumference_coverage(bot_x, bot_y, bot_radius, tower_r)
            total_coverage += coverage
        
        # Return average coverage as a fraction (0.0 to 1.0)
        avg_coverage_pct = total_coverage / samples if samples > 0 else 0.0
        return avg_coverage_pct / 100.0
        
    def _setup_wave_timing(self):
        """Setup wave timing and package collection RNG."""
        WAVE_DURATION = 30.140 if self.game_mode == "farming" else 28.070
        num_waves = int(np.ceil(self.duration_s / WAVE_DURATION))
        wave_starts_exact = [w * WAVE_DURATION for w in range(num_waves)]
        wave_starts_int = [int(round(ws)) for ws in wave_starts_exact]
        
        # Determine which waves get packages
        if self.predefined_package_times is not None:
            # Use predefined package times - map them to wave indices
            waves_with_packages = set()
            for pkg_time in self.predefined_package_times:
                # Find which wave this time belongs to
                for wave_idx, wave_start in enumerate(wave_starts_int):
                    if wave_start == pkg_time:
                        waves_with_packages.add(wave_idx)
                        break
        else:
            # Generate random packages based on package_chance_pct
            rng = np.random.default_rng()
            waves_with_packages = {w for w in range(num_waves) if rng.random() < (self.package_chance_pct / 100.0)}
        
        return wave_starts_exact, wave_starts_int, waves_with_packages
        
    def _gc_effect_per_pkg(self) -> float:
        """Get cooldown reduction per package based on generator rarity."""
        mapping = {"Epic": 10.0, "Legendary": 13.0, "Mythic": 17.0, "Ancestral": 20.0}
        return mapping.get(self.generator_rarity, 0.0)
        
    def run(self):
        """Run the simulation and populate result arrays.
        
        Call this after initialization (and optionally set_overrides()) to execute
        the simulation. Results are accessible via properties and get_components().
        """
        # Load parameters
        self._load_base_parameters()
        params = self.effective_params
        
        # Calculate coverage
        gb_effective_bonus, bh_effective_bonus, sp_effective, sp_coverage_frac = self._calculate_coverage_fractions()
        
        # Setup wave timing
        wave_starts_exact, wave_starts_int, waves_with_packages = self._setup_wave_timing()
        self.wave_starts_exact = wave_starts_exact
        
        # Package reduction
        per_pkg_reduction = self._gc_effect_per_pkg() if self.generator_module == "Galaxy Compressor" else 0.0
        
        # Initialize timers (seconds until next activation)
        timer_gb = params['gb_cd'] if self.start_after_first_cooldown else 0.0
        timer_dw = params['dw_cd'] if self.start_after_first_cooldown else 0.0
        timer_gt = params['gt_cd'] if self.start_after_first_cooldown else 0.0
        timer_bh = params['bh_cd'] if self.start_after_first_cooldown else 0.0
        timer_cf = params['cf_cd'] if self.start_after_first_cooldown else 0.0
        
        # Active remaining time
        active_gb = 0.0
        active_dw = 0.0
        active_gt = 0.0
        active_bh = 0.0
        active_cf = 0.0
        
        # Result arrays
        T = self.duration_s
        self.gb_series = np.ones(T)
        self.dw_series = np.ones(T)
        self.gt_series = np.ones(T)
        self.bh_series = np.ones(T)
        self.sp_series = np.full(T, sp_effective)
        self.cf_series = np.ones(T)  # 1.0 = inactive, will be set to 0.0 when active
        
        # Uptime counters
        up_gb = up_dw = up_gt = up_bh = up_cf = 0
        self.package_times = []
        
        # Simulation loop
        for t in range(T):
            # Boss wave detection (boss appears every N waves, package arrives after boss wave ends)
            boss_package_collected = False
            if self.lab_package_after_boss:
                for wave_idx in range(len(wave_starts_int)):
                    # Check if this is a boss wave (every boss_wave_interval waves: 10, 20, 30...)
                    # Boss appears at wave 10, 20, 30... (not wave 0)
                    if wave_idx > 0 and wave_idx % self.boss_wave_interval == 0:
                        # Package arrives after boss wave completes (at the start of next wave)
                        if t == wave_starts_int[wave_idx]:
                            boss_package_collected = True
                            self.boss_package_times.append(t)
                            if wave_idx not in self.boss_waves:
                                self.boss_waves.append(wave_idx)
                            # Trigger callback if provided
                            if self.on_boss_package_callback:
                                try:
                                    self.on_boss_package_callback(t, wave_idx)
                                except Exception:
                                    pass  # Silently ignore callback errors
                            break
            
            # Package collection check
            package_collected = False
            for wave_idx in range(len(wave_starts_int)):
                if t == wave_starts_int[wave_idx] and wave_idx in waves_with_packages:
                    package_collected = True
                    self.package_times.append(t)
                    break
                    
            # Apply active multipliers
            if active_gb > 0:
                self.gb_series[t] = gb_effective_bonus
                active_gb -= 1
                up_gb += 1
            if active_dw > 0:
                self.dw_series[t] = params['dw_bonus']
                active_dw -= 1
                up_dw += 1
            if active_gt > 0:
                self.gt_series[t] = params['gt_bonus']
                active_gt -= 1
                up_gt += 1
            if active_bh > 0:
                self.bh_series[t] = bh_effective_bonus
                active_bh -= 1
                up_bh += 1
            if active_cf > 0:
                self.cf_series[t] = 0.0  # 0.0 = active (reduces enemy speed/damage)
                active_cf -= 1
                up_cf += 1
                
            # Decrement timers
            timer_gb -= 1
            timer_dw -= 1
            timer_gt -= 1
            timer_bh -= 1
            timer_cf -= 1
            
            # Apply package reductions (exclude Golden Bot)
            # Regular packages OR boss packages both trigger cooldown reduction
            if (package_collected or boss_package_collected) and per_pkg_reduction > 0:
                dw_overshoot = max(0.0, per_pkg_reduction - timer_dw) if timer_dw > 0 else 0.0
                gt_overshoot = max(0.0, per_pkg_reduction - timer_gt) if timer_gt > 0 else 0.0
                bh_overshoot = max(0.0, per_pkg_reduction - timer_bh) if timer_bh > 0 else 0.0
                cf_overshoot = max(0.0, per_pkg_reduction - timer_cf) if timer_cf > 0 else 0.0
                
                timer_dw = max(0.0, timer_dw - per_pkg_reduction)
                timer_gt = max(0.0, timer_gt - per_pkg_reduction)
                timer_bh = max(0.0, timer_bh - per_pkg_reduction)
                timer_cf = max(0.0, timer_cf - per_pkg_reduction)
            else:
                dw_overshoot = gt_overshoot = bh_overshoot = cf_overshoot = 0.0
                
            # Activate if timers hit 0
            if timer_gb <= 0:
                timer_gb = params['gb_cd']
                if active_gb <= 0:
                    active_gb = params['gb_up']
                else:
                    active_gb += params['gb_up']
            if timer_dw <= 0:
                timer_dw = params['dw_cd'] - dw_overshoot
                if active_dw <= 0:
                    active_dw = params['dw_up']
                else:
                    active_dw += params['dw_up']
            if timer_gt <= 0:
                timer_gt = params['gt_cd'] - gt_overshoot
                if active_gt <= 0:
                    active_gt = params['gt_up']
                else:
                    active_gt += params['gt_up']
            if timer_bh <= 0:
                timer_bh = params['bh_cd'] - bh_overshoot
                if active_bh <= 0:
                    active_bh = params['bh_up']
                else:
                    active_bh += params['bh_up']
            if timer_cf <= 0:
                timer_cf = params['cf_cd'] - cf_overshoot
                if active_cf <= 0:
                    active_cf = params['cf_up']
                else:
                    active_cf += params['cf_up']
                    
        # Calculate total multiplier
        self.total_series = self.gb_series * self.dw_series * self.gt_series * self.bh_series * self.sp_series
        
        # Store uptime statistics
        pct = lambda x: (x / T * 100.0) if T > 0 else 0.0
        self.uptime_counters = {
            'golden_bot': pct(up_gb),
            'death_wave': pct(up_dw),
            'golden_tower': pct(up_gt),
            'black_hole': pct(up_bh),
            'chrono_field': pct(up_cf),
            'spotlight': 100.0,
        }
        
        # Store timeline
        self.timeline_seconds = np.arange(T)
        
    @property
    def average_multiplier(self) -> float:
        """Get the time-averaged total multiplier."""
        if self.total_series is None:
            return 0.0
        return float(np.mean(self.total_series))
        
    def to_dataframe(self) -> pd.DataFrame:
        """Convert results to formatted dataframe (matching original table format)."""
        if self.timeline_seconds is None:
            return pd.DataFrame()
        # Safeguard: ensure series are populated
        if any(
            a is None
            for a in (
                self.gb_series,
                self.dw_series,
                self.gt_series,
                self.bh_series,
                self.sp_series,
                self.total_series,
            )
        ):
            return pd.DataFrame()
        # Type guards for static analyzers
        assert self.gb_series is not None
        assert self.dw_series is not None
        assert self.gt_series is not None
        assert self.bh_series is not None
        assert self.sp_series is not None
        assert self.total_series is not None
            
        def fmt_mult(v: float) -> str:
            try:
                return f"{v:.3f}×"
            except Exception:
                return ""
                
        mask = lambda arr: arr != 1.0
        return pd.DataFrame({
            "t (s)": self.timeline_seconds,
            "Golden Bot": np.where(mask(self.gb_series), [fmt_mult(v) for v in self.gb_series], ""),
            "Death Wave": np.where(mask(self.dw_series), [fmt_mult(v) for v in self.dw_series], ""),
            "Golden Tower": np.where(mask(self.gt_series), [fmt_mult(v) for v in self.gt_series], ""),
            "Black Hole (eff.)": np.where(mask(self.bh_series), [fmt_mult(v) for v in self.bh_series], ""),
            "Spotlight (eff.)": [fmt_mult(v) for v in self.sp_series],
            "Total Mult": [fmt_mult(v) for v in self.total_series],
        })
        
    def get_components(self) -> Dict[str, Any]:
        """Get component arrays and metadata (matching original return format)."""
        if self.timeline_seconds is None:
            return {}
        # Safeguard: ensure series are populated
        if any(
            a is None
            for a in (
                self.gb_series,
                self.dw_series,
                self.gt_series,
                self.bh_series,
                self.sp_series,
                self.cf_series,
                self.total_series,
            )
        ):
            return {}
        # Type guards for static analyzers
        assert self.gb_series is not None
        assert self.dw_series is not None
        assert self.gt_series is not None
        assert self.bh_series is not None
        assert self.sp_series is not None
        assert self.cf_series is not None
        assert self.total_series is not None
            
        def uw_permanence_stats(series: np.ndarray) -> dict:
            # Consider value > 1.0 as active, <= 1.0 as downtime
            is_active = series > 1.0
            downtime_mask = ~is_active
            uptime_pct = np.sum(is_active) / len(series) * 100.0 if len(series) > 0 else 0.0
            # Find lengths of consecutive downtime periods
            from itertools import groupby
            downtime_lengths = [sum(1 for _ in group) for val, group in groupby(downtime_mask) if val]
            num_downtime_events = len(downtime_lengths)  # Count number of separate downtime events
            max_downtime = max(downtime_lengths) if downtime_lengths else 0
            avg_downtime = float(np.mean(downtime_lengths)) if downtime_lengths else 0.0
            median_downtime = float(np.median(downtime_lengths)) if downtime_lengths else 0.0
            total_downtime_seconds = sum(downtime_lengths)  # Total seconds of downtime
            return {
                'num_downtime': int(num_downtime_events),  # Number of separate downtime events
                'total_downtime_seconds': int(total_downtime_seconds),  # Total seconds
                'uptime_pct': uptime_pct,
                'downtime_stats': {
                    'max': max_downtime,
                    'avg': avg_downtime,
                    'median': median_downtime,
                }
            }

        # For permanence stats, cf_series uses 0.0 for active, 1.0 for inactive
        # We need to invert it so the > 1.0 logic in uw_permanence_stats works correctly
        # When CF is active: cf_series = 0.0, we want > 1.0, so use 2.0
        # When CF is inactive: cf_series = 1.0, we want <= 1.0, so use 1.0
        cf_series_for_stats = np.where(self.cf_series == 0.0, 2.0, 1.0)
        
        uw_series_map = {
            'black_hole': self.bh_series,
            'golden_tower': self.gt_series,
            'chrono_field': cf_series_for_stats,
            'death_wave': self.dw_series,
        }

        uw_permanence = {k: uw_permanence_stats(v) for k, v in uw_series_map.items()}

        params = self.effective_params
        _, _, sp_effective, sp_coverage_frac = self._calculate_coverage_fractions()
        
        return {
            "golden_bot": self.gb_series,
            "death_wave": self.dw_series,
            "golden_tower": self.gt_series,
            "black_hole": self.bh_series,
            "spotlight": self.sp_series,
            "chrono_field": cf_series_for_stats,  # Return inverted version for graph display (2.0 active, 1.0 inactive)
            "total": self.total_series,
            "cooldowns": {
                "golden_bot": params['gb_cd'],
                "death_wave": params['dw_cd'],
                "golden_tower": params['gt_cd'],
                "black_hole": params['bh_cd'],
                "chrono_field": params['cf_cd'],
                "spotlight": 0.0,
            },
            "durations": {
                "golden_bot": params['gb_up'],
                "death_wave": params['dw_up'],
                "golden_tower": params['gt_up'],
                "black_hole": params['bh_up'],
                "chrono_field": params['cf_up'],
                "spotlight": 0.0,
            },
            "uptimes": self.uptime_counters,
            "spotlight_angle": params['sp_angle'],
            "spotlight_quantity": params['sp_quantity'],
            "spotlight_coverage": sp_coverage_frac * 100.0,
            "package_chance_pct": self.package_chance_pct,
            "package_times": self.package_times,
            "wave_starts": self.wave_starts_exact,
            "boss_wave_interval": self.boss_wave_interval,
            "boss_waves": self.boss_waves,
            "boss_package_times": self.boss_package_times,
            "lab_package_after_boss": self.lab_package_after_boss,
            "game_mode": self.game_mode,
            "uw_permanence": uw_permanence,
        }
