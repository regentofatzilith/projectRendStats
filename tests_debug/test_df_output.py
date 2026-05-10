import numpy as np
import pandas as pd

# Global variables
wave_time = 30.140
boss_time = wave_time * 11
package_after_boss = True
package_reduction_value = 13
package_chance = 0.76
total_time = 3600

def is_package(time: int, rng: np.random.Generator, pkg_chance: float, pkg_reduction: float) -> float:
    package_reduction = 0.0
    if time % boss_time < 1:
        package_reduction = pkg_reduction if package_after_boss else 0.0
    elif time % wave_time < 1:
        package_reduction = pkg_reduction if rng.random() < pkg_chance else 0.0
    return package_reduction

def simulate_package_reductions(
    total_time: int, 
    pkg_chance: float, 
    pkg_reduction: float, 
    seed: int = 0
) -> np.ndarray:
    rng = np.random.default_rng(seed)
    reductions = np.zeros(total_time, dtype=float)
    for t in range(total_time):
        reductions[t] = is_package(t, rng, pkg_chance, pkg_reduction)
    return reductions

def calculate_uw_uptime(
    uw_cooldown: float,
    uw_duration: float,
    total_time: int,
    package_reduction_series: np.ndarray | None = None,
) -> pd.DataFrame:
    timeline = np.arange(0, total_time)
    if package_reduction_series is None:
        package_reduction_series = simulate_package_reductions(total_time, 0.76, 13.0)
    package_reduction_series = np.asarray(package_reduction_series, dtype=float)
    
    package_reduction = package_reduction_series.copy()
    cooldown_remaining = np.zeros(total_time, dtype=float)
    active_remaining = np.zeros(total_time, dtype=float)
    remaining_active_time = np.zeros(total_time, dtype=float)
    is_active = np.zeros(total_time, dtype=bool)

    cooldown_remaining_val = float(uw_cooldown)
    active_remaining_val = float(uw_duration)

    for t in timeline:
        pr = float(package_reduction_series[t])
        cooldown_remaining_val -= pr
        
        while cooldown_remaining_val <= 0:
            active_remaining_val += uw_duration
            cooldown_remaining_val += uw_cooldown

        cooldown_remaining[t] = cooldown_remaining_val
        active_remaining[t] = active_remaining_val
        remaining_active_time[t] = active_remaining_val
        is_active[t] = active_remaining_val > 0

        cooldown_remaining_val -= 1
        if active_remaining_val > 0:
            active_remaining_val -= 1

    return pd.DataFrame(
        {
            "t": timeline,
            "package_reduction": package_reduction,
            "cooldown_remaining": cooldown_remaining,
            "active_remaining": active_remaining,
            "remaining_active_time": remaining_active_time,
            "is_active": is_active,
        }
    )

# Test with Death Wave parameters
df = calculate_uw_uptime(46, 34, 3600)
print(df.head(600).to_string(index=False))
