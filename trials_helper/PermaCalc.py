"""PermaCalc - Ultimate Weapon (UW) permanence calculations and overview.
Inspired by simulation.py.
"""

import numpy as np
import pandas as pd

# UW definitions
UW_LIST = [
    {
        'name': 'Death Wave',
        'cooldown': 60.0,  # seconds
        'duration': 1      # quantity (not time)
    },
    {
        'name': 'Golden Tower',
        'cooldown': 120.0,
        'duration': 30.0   # seconds
    },
    {
        'name': 'Black Hole',
        'cooldown': 180.0,
        'duration': 20.0   # seconds
    },
    {
        'name': 'Chrono Field',
        'cooldown': 90.0,
        'duration': 15.0   # seconds
    }
]

# Overview callback logic (stub)
def get_uw_overview():
    """Return overview for all UW: cooldown and duration."""
    return [
        {
            'name': uw['name'],
            'cooldown': uw['cooldown'],
            'duration': uw['duration']
        }
        for uw in UW_LIST
    ]

# Simulate random packages and packages after boss
def simulate_packages(n_trials=1000, boss_package=False):
    """Simulate random packages and packages after boss."""
    # For demonstration, assume package times are normal(60, 10)
    base_time = 60.0 if not boss_package else 45.0
    times = np.random.normal(loc=base_time, scale=10.0, size=n_trials)
    return times

# Simulate UW uptime
def simulate_uw_uptime(cooldown, package_time_reduction, duration):
    """Simulate UW uptime.
    Input: cooldown, package time reduction
    Output: remaining uptime, boolean for active/inactive
    """
    # Example: cooldown reduced by package_time_reduction
    effective_cooldown = max(0.0, cooldown - package_time_reduction)
    remaining_uptime = max(0.0, duration - effective_cooldown)
    is_active = remaining_uptime > 0.0
    return {
        'remaining_uptime': remaining_uptime,
        'is_active': is_active
    }

# Example usage (for testing)
if __name__ == "__main__":
    print("UW Overview:")
    for uw in get_uw_overview():
        print(uw)
    print("\nSimulate random packages:")
    print(simulate_packages(n_trials=5))
    print("\nSimulate UW uptime:")
    print(simulate_uw_uptime(120, 30, 30))
