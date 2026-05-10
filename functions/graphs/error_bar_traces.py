"""Reusable error-bar trace builders."""

import pandas as pd
import numpy as np
import plotly.graph_objs as go

from functions.data.ci_utils import get_ci_triplet
from .hover_formatting import common_unit


def build_error_bar_traces(
    df: pd.DataFrame,
    metric: str,
    group_col: str,
    color: str,
    scale_lookup: dict[str, float],
) -> list[go.Scatter]:
    """Create one marker+CI error-bar trace per group for a given metric."""
    if group_col not in df.columns or 'level_1' not in df.columns or metric not in df.columns:
        return []

    traces: list[go.Scatter] = []
    for group_label, group_data in df.groupby(group_col):
        ci_values = get_ci_triplet(group_data, metric, level_col='level_1', clamp_lower_zero=True)
        if ci_values is None:
            continue
        mean_val, lower_val, upper_val = ci_values

        if pd.isna(mean_val) or pd.isna(lower_val) or pd.isna(upper_val):
            continue

        mean_vals = np.array([mean_val])
        lower_vals = np.array([lower_val])
        upper_vals = np.array([upper_val])
        if len(mean_vals) == 0:
            continue

        err_minus = float(mean_vals[0] - lower_vals[0])
        err_plus = float(upper_vals[0] - mean_vals[0])

        factor, unit = common_unit([mean_vals[0], lower_vals[0], upper_vals[0]], scale_lookup)
        hover_text = (
            f"Mean: {mean_vals[0] / factor:.2f}{unit}<br>"
            f"CI: [{lower_vals[0] / factor:.2f}{unit}, {upper_vals[0] / factor:.2f}{unit}]"
        )

        traces.append(
            go.Scatter(
                x=[group_label],
                y=[float(f"{mean_vals[0]:.2f}")],
                name=f"Tier {group_label}",
                mode='markers',
                marker=dict(color=color, size=10),
                error_y=dict(
                    type='data',
                    symmetric=False,
                    array=[float(f"{err_plus:.2f}")],
                    arrayminus=[float(f"{err_minus:.2f}")],
                    color=color,
                    width=3,
                    visible=True,
                ),
                hovertext=hover_text,
                hoverinfo='text',
                showlegend=True,
            )
        )

    return traces
