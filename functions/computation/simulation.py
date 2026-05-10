"""
Simulation Layer - Ultimate Weapon simulation calculations.

Provides stateless functions for simulating Ultimate Weapon behavior,
including cooldown calculations, package generation, and uptime tracking.

Usage:
    from functions.computation.simulation import calculate_uw_uptime
    
    result = calculate_uw_uptime(
        uw_cooldown=53,
        uw_duration=41,
        total_time=3600
    )
"""

from typing import Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from functions.data import config


# --- Configuration Constants (from static config) ---
TIER_CONFIG = config.TIER_CONFIG
UW_CONFIG = config.UW_CONFIG

# Default simulation parameters
DEFAULT_PKG_CHANCE = 0.78  # 78% chance for package
DEFAULT_PKG_REDUCTION = 13.0  # Seconds of cooldown reduction
DEFAULT_GC_REDUCTION = 13.0  # Golden Core reduction
DEFAULT_BOSS_WAVES = 10
DEFAULT_WAVE_TIME = 26 + 9  # base + cooldown
DEFAULT_TOTAL_TIME = 3600  # 1 hour


def get_tier_config(tier_name: str) -> Optional[Dict[str, Any]]:
    """
    Get configuration for a specific tier.
    
    Args:
        tier_name: Name of tier (e.g., "Tier 14", "Copper")
        
    Returns:
        Dict with wave_time, wave_cooldown, boss_waves, type
        or None if tier not found
        
    Examples:
        >>> config = get_tier_config("Tier 14")
        >>> print(config['boss_waves'])
        9
    """
    return TIER_CONFIG.get(tier_name)


def get_uw_config(weapon_name: str) -> Optional[Dict[str, Any]]:
    """
    Get configuration for a specific Ultimate Weapon.
    
    Args:
        weapon_name: Name of UW (e.g., "Golden Bot")
        
    Returns:
        Dict with base_cooldown, base_duration, color_hex, can_queue
        or None if weapon not found
        
    Examples:
        >>> config = get_uw_config("Golden Bot")
        >>> print(config['base_cooldown'])
        100
    """
    return UW_CONFIG.get(weapon_name)


def simulate_package_reductions(
    total_time: int,
    pkg_chance: float = DEFAULT_PKG_CHANCE,
    pkg_reduction: float = DEFAULT_PKG_REDUCTION,
    wave_time: float = DEFAULT_WAVE_TIME,
    boss_every_x: int = DEFAULT_BOSS_WAVES,
    seed: int = 0,
    boss_package_enabled: bool = True
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Simulate cooldown package occurrences and reductions.
    
    Args:
        total_time: Total simulation time in seconds
        pkg_chance: Probability of package on regular waves (0-1)
        pkg_reduction: Cooldown reduction amount (seconds)
        wave_time: Duration per wave (seconds)
        boss_every_x: Boss wave frequency (every X waves)
        seed: Random seed for reproducibility
        boss_package_enabled: Whether boss waves grant packages
        
    Returns:
        Tuple of:
        - reductions: Array of cooldown reductions per second
        - is_boss: Array of booleans indicating boss packages
        
    Examples:
        >>> reductions, is_boss = simulate_package_reductions(3600, seed=42)
        >>> print(f"Total packages: {(reductions > 0).sum()}")
    """
    timeline = np.arange(total_time)
    boss_time = wave_time * boss_every_x
    is_boss_wave = (timeline % boss_time) < 1
    is_wave = (timeline % wave_time) < 1
    
    rng = np.random.default_rng(seed)
    rand_vals = rng.random(total_time)
    
    boss_mask = is_boss_wave & boss_package_enabled
    pkg_mask = is_wave & (rand_vals < pkg_chance)
    
    reductions = np.where(boss_mask | pkg_mask, pkg_reduction, 0.0).astype(float)
    is_boss = boss_mask.astype(bool)
    
    return reductions, is_boss


def calculate_uw_uptime(
    uw_cooldown: float,
    uw_duration: float,
    total_time: int = DEFAULT_TOTAL_TIME,
    return_df: bool = False,
    package_reduction_series: Optional[np.ndarray] = None,
    is_boss_package_series: Optional[np.ndarray] = None,
    wave_time: float = DEFAULT_WAVE_TIME,
    can_queue: bool = True,
) -> Dict[str, Any] | pd.DataFrame:
    """
    Calculate Ultimate Weapon uptime across simulation period.
    
    Simulates the active/cooldown state of an Ultimate Weapon accounting for:
    - Cooldown mechanics
    - Duration effects
    - Package-based cooldown reductions
    - Queue behavior (can activate multiple times per cooldown)
    
    Args:
        uw_cooldown: Base cooldown duration (seconds)
        uw_duration: Duration weapon stays active (seconds)
        total_time: Total simulation time (seconds)
        return_df: If True, returns full DataFrame; if False, returns summary dict
        package_reduction_series: Array of cooldown reductions per second
        is_boss_package_series: Array of booleans for boss packages
        wave_time: Duration per wave for package generation
        can_queue: Whether weapon can queue (activate multiple times before active)
        
    Returns:
        If return_df=False:
            Dict with keys:
            - perma_result: bool, whether weapon is permanently active
            - perma_timeline: list of timestamps
            - perma_active: list of bool, active status per second
            - perma_remaining_active_time: list of remaining active time
            
        If return_df=True:
            DataFrame with columns:
            - t: timestamp
            - wave_number: which wave this is
            - package_reduction: cooldown reduction applied
            - is_boss_package: whether this is a boss package
            - cooldown_remaining: seconds until next activation
            - active_remaining: seconds weapon will stay active
            - remaining_active_time: same as active_remaining
            - is_active: boolean, is weapon currently active
            
    Examples:
        >>> result = calculate_uw_uptime(53, 41, total_time=3600)
        >>> print(f"Permanent: {result['perma_result']}")
    """
    if uw_cooldown is None or uw_duration is None:
        raise ValueError("uw_cooldown and uw_duration must be numeric, got None")

    uw_cooldown = float(uw_cooldown)
    uw_duration = float(uw_duration)

    timeline = np.arange(0, total_time)
    
    # Generate packages if not provided
    if package_reduction_series is None:
        package_reduction_series, is_boss_package_series = simulate_package_reductions(
            total_time, wave_time=wave_time, boss_every_x=DEFAULT_BOSS_WAVES
        )
    
    # Convert to arrays
    package_reduction_series = np.asarray(package_reduction_series, dtype=float)
    if package_reduction_series.shape[0] != total_time:
        raise ValueError("package_reduction_series length must equal total_time")
    
    if is_boss_package_series is None:
        is_boss_package_series = np.zeros(total_time, dtype=bool)
    is_boss_package_series = np.asarray(is_boss_package_series, dtype=bool)
    
    # Initialize tracking arrays
    package_reduction = package_reduction_series.copy()
    cooldown_remaining = np.zeros(total_time, dtype=float)
    active_remaining = np.zeros(total_time, dtype=float)
    remaining_active_time = np.zeros(total_time, dtype=float)
    is_active = np.zeros(total_time, dtype=bool)
    wave_number = np.zeros(total_time, dtype=int)
    
    # Simulation state
    cooldown_remaining_val = float(uw_cooldown)
    active_remaining_val = 0.0
    
    # Simulate each second
    for t in timeline:
        pr = float(package_reduction_series[t])
        wave_number[t] = int(t / wave_time) + 1
        
        # Apply time step
        cooldown_remaining_val -= 1
        if pr > 0:
            cooldown_remaining_val -= pr
        
        # Check for activations
        activation_occurred = False
        if can_queue:
            # Queue mode: keep activating while cooldown ready
            while cooldown_remaining_val <= 0:
                activation_occurred = True
                active_remaining_val += uw_duration
                cooldown_remaining_val += uw_cooldown
        else:
            # No queue: activate once per cooldown
            if cooldown_remaining_val <= 0:
                activation_occurred = True
                active_remaining_val = uw_duration
                cooldown_remaining_val += uw_cooldown
        
        # Update tracking
        if activation_occurred:
            cooldown_remaining[t] = 0.0
        else:
            cooldown_remaining[t] = max(0.0, cooldown_remaining_val)
        
        active_remaining[t] = active_remaining_val
        remaining_active_time[t] = active_remaining_val
        is_active[t] = active_remaining_val > 0
        
        # Decay active time
        if active_remaining_val > 0:
            active_remaining_val = max(0.0, active_remaining_val - 1)
    
    # Calculate permanence
    perma_result = bool(np.all(is_active))
    
    if return_df:
        return pd.DataFrame({
            "t": timeline,
            "wave_number": wave_number,
            "package_reduction": package_reduction,
            "is_boss_package": is_boss_package_series,
            "cooldown_remaining": cooldown_remaining,
            "active_remaining": active_remaining,
            "remaining_active_time": remaining_active_time,
            "is_active": is_active,
        })
    
    return {
        "perma_result": perma_result,
        "perma_timeline": timeline.tolist(),
        "perma_active": is_active.tolist(),
        "perma_remaining_active_time": remaining_active_time.tolist(),
    }


def calculate_uptime_stats(df: pd.DataFrame) -> Dict[str, Optional[float]]:
    """
    Calculate uptime and downtime statistics from simulation DataFrame.
    
    Args:
        df: DataFrame from calculate_uw_uptime(return_df=True)
        
    Returns:
        Dict with statistics:
        - uptime_pct: Percentage weapon is active
        - downtime_pct: Percentage weapon is inactive
        - avg_uptime: Average duration of active periods
        - max_downtime: Maximum duration of inactive periods
        - min_downtime: Minimum duration of inactive periods
        - avg_downtime: Average duration of inactive periods
        - avg_activation_interval: Average time between activations
        
    Examples:
        >>> df = calculate_uw_uptime(53, 41, return_df=True)
        >>> stats = calculate_uptime_stats(df)
        >>> print(f"Uptime: {stats['uptime_pct']:.1f}%")
    """
    def run_stats(mask: np.ndarray, value: bool) -> Tuple[float, float, float]:
        """Calculate (mean, min, max) for runs of value in mask."""
        changes = np.concatenate(([True], mask[1:] != mask[:-1], [True]))
        change_indices = np.where(changes)[0]
        run_lengths = np.diff(change_indices)
        run_values = mask[change_indices[:-1]]
        
        if len(run_lengths) > 0:
            run_lengths = run_lengths[:-1]
            run_values = run_values[:-1]
        
        runs = run_lengths[run_values == value] if len(run_values) > 0 else np.array([])
        
        if len(runs) > 0:
            return float(runs.mean()), float(runs.min()), float(runs.max())
        else:
            return 0.0, 0.0, 0.0
    
    active_mask = df["is_active"].to_numpy()
    total_seconds = len(df)
    uptime_seconds = int(active_mask.sum())
    downtime_seconds = total_seconds - uptime_seconds
    uptime_pct = (uptime_seconds / total_seconds * 100) if total_seconds > 0 else 0.0
    downtime_pct = (downtime_seconds / total_seconds * 100) if total_seconds > 0 else 0.0
    
    avg_uptime, min_uptime, max_uptime = run_stats(active_mask, True)
    avg_downtime, min_downtime, max_downtime = run_stats(active_mask, False)
    
    # Mask out constant downtime (not really meaningful)
    if min_downtime == max_downtime == avg_downtime and avg_downtime > 0:
        min_downtime = None
        max_downtime = None
    
    # Calculate activation interval
    activation_starts = np.where(
        (active_mask) & (np.concatenate(([True], ~active_mask[:-1])))
    )[0]
    avg_activation_interval = None
    if len(activation_starts) > 1:
        intervals = np.diff(activation_starts)
        avg_activation_interval = float(intervals.mean())
    
    return {
        "uptime_pct": uptime_pct,
        "downtime_pct": downtime_pct,
        "avg_uptime": avg_uptime,
        "max_downtime": max_downtime,
        "min_downtime": min_downtime,
        "avg_downtime": avg_downtime,
        "avg_activation_interval": avg_activation_interval,
    }


def downsample_simulation_df(
    df: pd.DataFrame,
    max_points: int = 600
) -> pd.DataFrame:
    """
    Downsample simulation DataFrame for efficient plotting.
    
    Preserves:
    - First and last points
    - All package events
    - Wave transitions
    - Active/inactive transitions
    
    Args:
        df: Full simulation DataFrame
        max_points: Maximum points to keep
        
    Returns:
        Downsampled DataFrame
        
    Examples:
        >>> df = calculate_uw_uptime(53, 41, return_df=True)
        >>> df_plot = downsample_simulation_df(df, max_points=500)
    """
    n = len(df)
    if n <= max_points:
        return df
    
    keep_mask = np.zeros(n, dtype=bool)
    keep_mask[0] = True
    keep_mask[-1] = True
    
    # Keep all package events
    keep_mask |= (df["package_reduction"] > 0).to_numpy()
    
    # Keep wave transitions
    wave_changes = df["wave_number"].diff().fillna(0) != 0
    keep_mask |= wave_changes.to_numpy()
    
    # Keep active/inactive transitions
    active_changes = df["is_active"].astype(int).diff().fillna(0) != 0
    keep_mask |= active_changes.to_numpy()
    
    # Add sampling to reach max_points
    kept_count = keep_mask.sum()
    if kept_count < max_points:
        step = max(1, n // (max_points - kept_count))
        keep_mask[::step] = True
    
    return df[keep_mask].copy()
