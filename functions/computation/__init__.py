"""
Computation Layer - Stateless transformation and calculation functions.

This layer contains pure functions (no I/O, deterministic) that:
1. Transform raw data into display-ready formats
2. Calculate metrics and statistics
3. Perform simulations and analysis

The computation layer sits between the Data layer (DataManager) and Display layer (pages).

Module Structure:
    - weapons.py: Transform Ultimate Weapon data for display
    - simulation.py: Simulate Ultimate Weapon behavior (uptime, cooldown, packages)
    - formatting.py: Generic formatting utilities for UI display
    - metrics.py: Metric calculations and statistics

Usage:
    from functions.computation import get_weapon_cards, calculate_uw_uptime
    from functions.computation.formatting import format_time
"""

# Import submodules
from . import weapons
from . import simulation
from . import formatting
from . import metrics

# Export all commonly used functions at package level
from .weapons import (
    format_parameter_value,
    format_parameter_component,
    format_parameter_breakdown,
    format_single_parameter,
    format_weapon_detailed,
    get_weapon_cards,
    get_weapon_summary,
    get_all_weapons_summary,
    filter_weapons_by_parameter,
    get_parameter_stats,
)

from .simulation import (
    get_tier_config,
    get_uw_config,
    simulate_package_reductions,
    calculate_uw_uptime,
    calculate_uptime_stats,
    downsample_simulation_df,
)

from .formatting import (
    format_number,
    format_percentage,
    format_time,
    format_duration,
    format_unit_value,
    format_delta,
    format_range,
    truncate_string,
    emphasize_value,
)

from .metrics import (
    calculate_average,
    calculate_median,
    calculate_std_dev,
    calculate_min_max_avg,
    calculate_percentiles,
    calculate_uptime_efficiency,
    calculate_cooldown_reduction,
    calculate_damage_multiplier,
    calculate_stack_value,
    calculate_weighted_average,
    calculate_efficiency_score,
    calculate_cumulative_values,
    calculate_rolling_average,
    normalize_values,
    calculate_delta_values,
    calculate_rate_of_change,
    categorize_value,
    aggregate_metrics,
)

__all__ = [
    # Modules
    "weapons",
    "simulation",
    "formatting",
    "metrics",
    
    # Weapons functions
    "format_parameter_value",
    "format_parameter_component",
    "format_parameter_breakdown",
    "format_single_parameter",
    "format_weapon_detailed",
    "get_weapon_cards",
    "get_weapon_summary",
    "get_all_weapons_summary",
    "filter_weapons_by_parameter",
    "get_parameter_stats",
    
    # Simulation functions
    "get_tier_config",
    "get_uw_config",
    "simulate_package_reductions",
    "calculate_uw_uptime",
    "calculate_uptime_stats",
    "downsample_simulation_df",
    
    # Formatting functions
    "format_number",
    "format_percentage",
    "format_time",
    "format_duration",
    "format_unit_value",
    "format_delta",
    "format_range",
    "truncate_string",
    "emphasize_value",
    
    # Metrics functions
    "calculate_average",
    "calculate_median",
    "calculate_std_dev",
    "calculate_min_max_avg",
    "calculate_percentiles",
    "calculate_uptime_efficiency",
    "calculate_cooldown_reduction",
    "calculate_damage_multiplier",
    "calculate_stack_value",
    "calculate_weighted_average",
    "calculate_efficiency_score",
    "calculate_cumulative_values",
    "calculate_rolling_average",
    "normalize_values",
    "calculate_delta_values",
    "calculate_rate_of_change",
    "categorize_value",
    "aggregate_metrics",
]
