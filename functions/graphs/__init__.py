"""Graphs and visualization module."""

from .Graphs import (
    combined_metrics_figure,
    makeTable,
    optimize_figure,
    optimize_table,
    continuous_metrics_figure,
    build_daily_income_figure,
    build_current_scenario_daily_income_figure,
    build_current_scenario_weekly_details,
    build_current_scenario_weekly_proposal_figure,
    get_ci_triplet,
    get_smoothed_daily_data,
    get_color_for_metric,
    display_name,
    colors
)
from .subplot_builders import create_subplots_grid
from .Optimizer import *

__all__ = [
    "combined_metrics_figure",
    "makeTable",
    "optimize_figure",
    "optimize_table",
    "continuous_metrics_figure",
    "build_daily_income_figure",
    "build_current_scenario_daily_income_figure",
    "build_current_scenario_weekly_details",
    "build_current_scenario_weekly_proposal_figure",
    "get_ci_triplet",
    "create_subplots_grid",
    "get_smoothed_daily_data",
    "get_color_for_metric",
    "display_name",
    "colors"
]
