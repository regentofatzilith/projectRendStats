import pandas as pd
import plotly.graph_objs as go
import numpy as np  # Added for array operations
import math
import time
from datetime import datetime

from .Optimizer import Optimizer
from .summarize_current import summarize_current
from .error_bar_traces import build_error_bar_traces
from .hover_formatting import common_unit
from .subplot_builders import create_subplots_grid
from .time_allocation_charts import build_time_allocation_figure
from functions.data.ConvertNumbers import apply_abbreviation, format_display_value, generate_abbreviation_ticks
from functions.data.ci_utils import get_ci_triplet as _get_ci_triplet
from functions.data.config import scale
from functions.statistics import compute_normalized_score_100
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    # Help static analyzers/IDEs resolve the symbol in different workspace layouts
    from functions.statistics.Statistics import TimeSeriesStats  # type: ignore

# Runtime import (relative within package)
from functions.statistics.Statistics import TimeSeriesStats

from typing import Tuple, List, Optional, Any, cast

# Debug flag - set to False to disable all debug prints
DEBUG = False

def get_rgba(color: str, alpha: float = 0.2) -> str:
    """Convert color to rgba format with given alpha."""
    color_map = {
        'green': '0,128,0',
        'purple': '128,0,128',
        'orange': '255,165,0',
        'lightgrey': '211,211,211',
        'white': '255,255,255'
    }
    if color.startswith('#'):
        hex_color = color.lstrip('#')
        rgb = ','.join(str(int(hex_color[i:i+2], 16)) for i in (0, 2, 4))
    else:
        rgb = color_map.get(color, '128,128,128')  # default to gray if color not found
    return f'rgba({rgb},{alpha})'

# Color scheme
colors = {
    'background': '#000000',      # main page background
    'secondary_bg': '#202128',    # secondary background
    'card': '#0c0d10',            # card color
    'text': '#FAFAFA',            # text color
    # Metric colors
    'coins': '#1EE2A5',           # green
    'cells': '#6E18FF',           # purple
    'reroll': '#F97316',          # orange
    'score': '#D1D5DB',
    'time': '#D1D5DB'
}


def _current_detail_today_date() -> datetime.date:
    return datetime.now().date()


def _format_current_detail_day_label(dt_value: Any, prefix: str | None = None) -> str:
    ts = pd.Timestamp(dt_value)
    base = ts.strftime('%a %b-%d')
    if prefix:
        base = f"{prefix} {ts.strftime('%b-%d')}"
    if ts.date() == _current_detail_today_date():
        base = f"{base} - TODAY"
    return base


def _current_detail_duration_hours_from_run_row(row: pd.Series) -> float:
    for gt_col in ["game_time", "gametime"]:
        if gt_col in row and pd.notna(row[gt_col]):
            try:
                return max(0.0, float(row[gt_col]) / 3600.0)
            except Exception:
                pass
    if "real_time" in row and pd.notna(row["real_time"]):
        try:
            return max(0.0, float(str(row["real_time"]).replace("h", "").strip()))
        except Exception:
            return 0.0
    return 0.0


def _current_detail_run_color(run_type: str, tier: Any) -> str:
    tier_num = 0
    try:
        tier_num = int(float(str(tier).replace("+", "")))
    except Exception:
        tier_num = 0

    if run_type == "tournament":
        return "#991b1b"
    if run_type == "milestone":
        palette = ["#fdba74", "#fb923c", "#f97316", "#ea580c", "#c2410c", "#9a3412"]
        return palette[tier_num % len(palette)]
    if run_type == "quit":
        palette = ["#f3e8ff", "#d8b4fe", "#c084fc", "#a855f7", "#7e22ce", "#581c87"]
        return palette[tier_num % len(palette)]
    if run_type == "buffer":
        return "#10b981"

    if tier_num >= 11:
        farming_palette = ["#9ca3af", "#6b7280", "#52525b", "#3f3f46", "#27272a", "#18181b", "#09090b"]
        idx = min(tier_num - 11, len(farming_palette) - 1)
        return farming_palette[idx]
    return "#9ca3af"


def _build_current_detail_run_segments(
    df_all_runs: pd.DataFrame | None,
    score_weights: dict[str, float] | None = None,
    max_per_hour: dict[str, float] | None = None,
    lookback_days: int = 8,
) -> list[dict[str, Any]]:
    if df_all_runs is None or df_all_runs.empty or "timestamp" not in df_all_runs.columns:
        return []

    df_runs = df_all_runs.copy()
    ts = pd.to_datetime(df_runs["timestamp"], errors="coerce", utc=True).dt.tz_localize(None)
    df_runs = df_runs.loc[ts.notna()].copy()
    if df_runs.empty:
        return []
    df_runs["timestamp"] = ts.loc[ts.notna()]

    max_ts = pd.to_datetime(df_runs["timestamp"], errors="coerce").max()
    if pd.isna(max_ts):
        return []

    today = max_ts.normalize()
    lookback_days = max(1, int(lookback_days or 8))
    window_start = today - pd.Timedelta(days=lookback_days - 1)
    window_end = today + pd.Timedelta(days=1)

    w_coins = score_weights.get('coins', 1 / 3) if score_weights else 1 / 3
    w_cells = score_weights.get('cells', 1 / 3) if score_weights else 1 / 3
    w_shards = score_weights.get('shards', 1 / 3) if score_weights else 1 / 3
    max_coins_ph = max_per_hour.get('coins', 1.0) if max_per_hour else 1.0
    max_cells_ph = max_per_hour.get('cells', 1.0) if max_per_hour else 1.0
    max_shards_ph = max_per_hour.get('shards', 1.0) if max_per_hour else 1.0

    out: list[dict[str, Any]] = []
    for _, row in df_runs.iterrows():
        row_timestamp = row.get("timestamp")
        if row_timestamp is None:
            continue
        end_ts = pd.to_datetime(row_timestamp, errors="coerce")
        if pd.isna(end_ts):
            continue

        duration_h = _current_detail_duration_hours_from_run_row(row)
        if duration_h <= 0:
            continue

        start_ts = end_ts - pd.to_timedelta(duration_h, unit="h")
        seg_start = max(start_ts, window_start)
        seg_end = min(end_ts, window_end)
        if seg_end <= seg_start:
            continue

        run_type = str(row.get("run_type", "farming") or "farming")
        tier = row.get("tier", "?")
        coins_earned = float(row.get("coins_earned", 0.0) or 0.0)
        cells_earned = float(row.get("cells_earned", 0.0) or 0.0)
        shards_earned = float(row.get("reroll_shards_earned", 0.0) or 0.0)
        waves_earned = float(row.get("waves_per_tier", row.get("wave", 0.0)) or 0.0)
        killed_by = str(row.get("killed_by", "") or "")

        if 'optimizer_score' in row and pd.notna(row.get('optimizer_score')):
            total_score = float(row.get('optimizer_score', 0.0) or 0.0)
        else:
            coins_ph = coins_earned / duration_h if duration_h > 0 else 0.0
            cells_ph = cells_earned / duration_h if duration_h > 0 else 0.0
            shards_ph = shards_earned / duration_h if duration_h > 0 else 0.0
            tier_score_coins = coins_ph / (max_coins_ph * 24) if max_coins_ph > 0 else 0.0
            tier_score_cells = cells_ph / (max_cells_ph * 24) if max_cells_ph > 0 else 0.0
            tier_score_shards = shards_ph / (max_shards_ph * 24) if max_shards_ph > 0 else 0.0
            total_score = (w_coins * tier_score_coins + w_cells * tier_score_cells + w_shards * tier_score_shards) * duration_h

        cursor = seg_start
        while cursor < seg_end:
            current_date = cursor.normalize()
            day_end = current_date + pd.Timedelta(days=1)
            chunk_end = min(seg_end, day_end)
            hours = (chunk_end - cursor).total_seconds() / 3600.0
            if hours > 1e-6:
                base_h = (cursor - current_date).total_seconds() / 3600.0
                scale_factor = hours / duration_h if duration_h > 0 else 0.0
                out.append({
                    "day": _format_current_detail_day_label(current_date),
                    "sort_date": current_date,
                    "base": base_h,
                    "height": hours,
                    "run_type": run_type,
                    "tier": tier,
                    "coins": coins_earned * scale_factor,
                    "cells": cells_earned * scale_factor,
                    "shards": shards_earned * scale_factor,
                    "waves": waves_earned * scale_factor,
                    "score": total_score * scale_factor,
                    "duration": duration_h,
                    "killed_by": killed_by,
                })
            cursor = chunk_end

    out.sort(key=lambda item: item.get("sort_date", window_start))
    return out


def _current_detail_daily_totals_from_segments(segments: list[dict[str, Any]]) -> pd.DataFrame:
    if not segments:
        return pd.DataFrame(columns=['coins', 'cells', 'shards', 'score'])

    rows = []
    day_dates: dict[str, pd.Timestamp] = {}
    for seg in segments:
        day_label = str(seg.get('day', ''))
        if not day_label:
            continue
        sort_date = seg.get('sort_date')
        day_dates[day_label] = pd.to_datetime(sort_date) if sort_date is not None else pd.Timestamp.min
        rows.append({
            'day': day_label,
            'coins': float(seg.get('coins', 0.0) or 0.0),
            'cells': float(seg.get('cells', 0.0) or 0.0),
            'shards': float(seg.get('shards', 0.0) or 0.0),
            'score': float(seg.get('score', 0.0) or 0.0),
        })

    if not rows:
        return pd.DataFrame(columns=['coins', 'cells', 'shards', 'score'])

    daily_df = pd.DataFrame(rows).groupby('day', as_index=True).sum()
    ordered_days = sorted(day_dates.keys(), key=lambda label: day_dates[label])
    return daily_df.reindex(ordered_days, fill_value=0.0)


def build_current_scenario_weekly_details(
    all_runs_time_series_df: pd.DataFrame | None,
    score_weights: dict[str, float] | None = None,
    max_per_hour: dict[str, float] | None = None,
    current_days: int = 7,
) -> dict[str, Any]:
    segments = _build_current_detail_run_segments(
        all_runs_time_series_df,
        score_weights=score_weights,
        max_per_hour=max_per_hour,
        lookback_days=int(current_days or 7) + 1,
    )
    current_daily_all = _current_detail_daily_totals_from_segments(segments)

    max_coins_per_hour = max_per_hour.get('coins', 0.0) if max_per_hour else 0.0
    max_cells_per_hour = max_per_hour.get('cells', 0.0) if max_per_hour else 0.0
    max_shards_per_hour = max_per_hour.get('shards', 0.0) if max_per_hour else 0.0
    weights = score_weights or {'coins': 1.0 / 3.0, 'cells': 1.0 / 3.0, 'shards': 1.0 / 3.0}

    if not current_daily_all.empty:
        current_daily_all['score'] = current_daily_all.apply(
            lambda row: compute_normalized_score_100(
                float(row.get('coins', 0.0) or 0.0),
                float(row.get('cells', 0.0) or 0.0),
                float(row.get('shards', 0.0) or 0.0),
                max_coins_per_hour * 24.0,
                max_cells_per_hour * 24.0,
                max_shards_per_hour * 24.0,
                weights=weights,
            ),
            axis=1,
        )

    today_mask = (
        current_daily_all.index.to_series().astype(str).str.contains('TODAY', na=False)
        if not current_daily_all.empty
        else pd.Series(dtype=bool)
    )
    current_daily_complete = current_daily_all.loc[~today_mask].tail(int(current_days or 7)) if not current_daily_all.empty else current_daily_all
    current_daily_display = current_daily_complete.copy()
    if not current_daily_all.empty and bool(today_mask.any()):
        current_daily_display = pd.concat([current_daily_complete, current_daily_all.loc[today_mask]], axis=0)

    return {
        'segments': segments,
        'daily_all': current_daily_all,
        'daily_complete': current_daily_complete,
        'daily_display': current_daily_display,
    }


def build_current_scenario_daily_income_figure(
    current_details: dict[str, Any],
    title: str = 'Current Scenario: Daily Income',
    max_per_day: dict[str, float] | None = None,
) -> go.Figure:
    daily_totals_df = current_details.get('daily_display', pd.DataFrame())
    return build_daily_income_figure(
        daily_totals_df,
        title=title,
        no_results_title='Current Scenario: No Results',
        max_per_day=max_per_day,
    )


def build_daily_income_figure(
    daily_totals_df: pd.DataFrame,
    title: str,
    no_results_title: str = 'Daily Income: No Results',
    max_per_day: dict[str, float] | None = None,
) -> go.Figure:
    if daily_totals_df is None or daily_totals_df.empty:
        fig = go.Figure()
        fig.update_layout(
            title=no_results_title,
            plot_bgcolor=colors['background'],
            paper_bgcolor=colors['background'],
            font_color=colors['text'],
        )
        return fig

    fig = create_subplots_grid(
        rows=1,
        cols=4,
        subplot_titles=('Daily Coins', 'Daily Cells', 'Daily Reroll Shards', 'Daily Score'),
        horizontal_spacing=0.06,
    )
    fig.add_trace(
        go.Bar(
            x=daily_totals_df.index,
            y=daily_totals_df['coins'],
            name='Coins',
            marker_color=colors['coins'],
            customdata=[[format_display_value(v)] for v in daily_totals_df['coins']],
            hovertemplate='Day: %{x}<br>Coins: %{customdata[0]}<extra></extra>',
            showlegend=False,
        ),
        row=1,
        col=1,
    )
    fig.add_trace(
        go.Bar(
            x=daily_totals_df.index,
            y=daily_totals_df['cells'],
            name='Cells',
            marker_color=colors['cells'],
            customdata=[[format_display_value(v)] for v in daily_totals_df['cells']],
            hovertemplate='Day: %{x}<br>Cells: %{customdata[0]}<extra></extra>',
            showlegend=False,
        ),
        row=1,
        col=2,
    )
    fig.add_trace(
        go.Bar(
            x=daily_totals_df.index,
            y=daily_totals_df['shards'],
            name='Reroll Shards',
            marker_color=colors['reroll'],
            customdata=[[format_display_value(v)] for v in daily_totals_df['shards']],
            hovertemplate='Day: %{x}<br>Shards: %{customdata[0]}<extra></extra>',
            showlegend=False,
        ),
        row=1,
        col=3,
    )
    fig.add_trace(
        go.Bar(
            x=daily_totals_df.index,
            y=daily_totals_df['score'],
            name='Score',
            marker_color='white',
            customdata=[[format_display_value(v)] for v in daily_totals_df['score']],
            hovertemplate='Day: %{x}<br>Score: %{customdata[0]}<extra></extra>',
            showlegend=False,
        ),
        row=1,
        col=4,
    )
    fig.update_layout(
        title=title,
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text'],
        barmode='group',
        height=400,
        legend=dict(bgcolor='rgba(0,0,0,0.35)', font=dict(size=10)),
    )
    fig.update_yaxes(title_text='Coins', side='left', row=1, col=1)
    fig.update_yaxes(title_text='Cells', side='left', row=1, col=2)
    fig.update_yaxes(title_text='Shards', side='left', row=1, col=3)
    fig.update_yaxes(title_text='Score', side='left', row=1, col=4)

    # Max-income dashed reference lines
    _max_ref = max_per_day or {}
    _ref_specs = [
        ('coins', 1, colors['coins']),
        ('cells', 2, colors['cells']),
        ('shards', 3, colors['reroll']),
    ]
    for _key, _col, _color in _ref_specs:
        _ref_val = float(_max_ref.get(_key, 0.0) or 0.0)
        if _ref_val > 0:
            fig.add_hline(
                y=_ref_val,
                row=1,
                col=_col,
                line=dict(dash='dash', color=_color, width=1.5),
                opacity=0.55,
                annotation_text=f'Max {format_display_value(_ref_val)}',
                annotation_position='top right',
                annotation_font_size=10,
                annotation_font_color=_color,
            )

    fig.add_hline(
        y=100.0,
        row=1,
        col=4,
        line=dict(dash='dash', color='white', width=1.5),
        opacity=0.55,
        annotation_text='Max 100',
        annotation_position='top right',
        annotation_font_size=10,
        annotation_font_color='white',
    )

    for metric_col, axis_col in [('coins', 1), ('cells', 2), ('shards', 3)]:
        bar_max = float(pd.to_numeric(daily_totals_df.get(metric_col, pd.Series([0.0])), errors='coerce').max() or 0.0)
        ref_max = float((_max_ref.get(metric_col) or 0.0))
        max_val = max(bar_max, ref_max)
        tickvals, ticktext = generate_abbreviation_ticks(0.0, max_val, num_ticks=5)
        fig.update_yaxes(
            tickmode='array',
            tickvals=tickvals,
            ticktext=ticktext,
            row=1,
            col=axis_col,
        )

    score_max = float(pd.to_numeric(daily_totals_df.get('score', pd.Series([0.0])), errors='coerce').max() or 0.0)
    fig.update_yaxes(
        range=[0.0, max(100.0, score_max) * 1.05],
        tickmode='array',
        tickvals=[0, 25, 50, 75, 100],
        ticktext=['0', '25', '50', '75', '100'],
        row=1,
        col=4,
    )

    return fig


def get_ci_triplet(
    df: pd.DataFrame,
    metric: str,
    level_col: str = 'level_1',
    clamp_lower_zero: bool = False,
) -> tuple[float, float, float] | None:
    # Backward-compatible local API; implementation is centralized in functions.data.ci_utils.
    return _get_ci_triplet(df, metric, level_col=level_col, clamp_lower_zero=clamp_lower_zero)


def build_current_scenario_weekly_proposal_figure(
    current_details: dict[str, Any],
    score_weights: dict[str, float] | None = None,
    max_per_hour: dict[str, float] | None = None,
    title: str = 'Weekly Proposal (Current (Recent Actual Runs))',
) -> go.Figure:
    segments = current_details.get('segments', []) or []
    return build_time_allocation_figure(
        segments,
        title=title,
        colors=colors,
        score_weights=score_weights,
        max_per_hour=max_per_hour,
        categoryarray=None,
    )

def display_name(metric: str) -> str:
    """Return a pretty display name for a metric column."""
    mapping = {
        'coins_earned': 'Coins Earned',
        'cells_earned': 'Cells Earned',
        'reroll_shards_earned': 'Reroll Shards Earned',
        'waves_per_tier': 'Waves',
        'coins_per_hour': 'Coins per Hour',
        'cells_per_hour': 'Cells per Hour',
        'reroll_shards_per_hour': 'Reroll Shards per Hour',
        'waves_per_hour': 'Waves per Hour',
        'real_time': 'Time (h)',
        'score': 'Score'
    }
    return mapping.get(metric, metric.replace('_', ' ').title())

def get_color_for_metric(metric: str) -> str:
    metric_lower = metric.lower()
    if 'coins' in metric_lower:
        return colors['coins']
    elif 'cells' in metric_lower:
        return colors['cells']
    elif 'reroll' in metric_lower:
        return colors['reroll']
    elif 'waves' in metric_lower:
        return '#60A5FA'  # light blue for waves
    elif 'score' in metric_lower or 'time' in metric_lower:
        return colors['score']
    else:
        return 'white'


def error_bar_trace(df: pd.DataFrame, metric: str, group_col: str, color: str) -> list[go.Scatter]:
    """
    Creates error bar traces for each group in the data, showing mean values with CI bounds.
    
    Parameters:
    - df: DataFrame with level_1 containing 'mean', 'ci_lower', 'ci_upper'
    - metric: Column name for the metric to plot
    - group_col: Column to group by (e.g., 'tier' or 'scenario')
    - color: Color for the traces
    
    Returns:
    - List of Plotly traces (one per group)
    """
    return build_error_bar_traces(df, metric, group_col, color, scale)


def combined_metrics_figure(filtered_df: pd.DataFrame, metric_type: str = 'real_time') -> go.Figure:
    # Always include waves metrics, place them between reroll shards and time/score
    sub_graphs = [
        'coins_earned', 'cells_earned', 'reroll_shards_earned', 'waves_per_tier', 'real_time',
        'coins_per_hour', 'cells_per_hour', 'reroll_shards_per_hour', 'waves_per_hour', 'score'
    ]

    titles = [display_name(m) for m in sub_graphs]
    fig = create_subplots_grid(rows=2, cols=5, subplot_titles=titles)

    if DEBUG:
        print(f"\n=== DEBUG combined_metrics_figure ===")
        print(f"DataFrame shape: {filtered_df.shape}")
        print(f"Unique tiers: {sorted(filtered_df['tier'].unique())}")
        print(f"Columns: {filtered_df.columns.tolist()}")
        if 'score' in filtered_df.columns:
            print(f"Score column present")
            print(f"Score values by tier:\n{filtered_df.groupby('tier')['score'].describe()}")
        else:
            print(f"WARNING: 'score' column NOT FOUND in filtered_df")
        print(f"=== END DEBUG ===\n")

    row, col = 1, 1
    metric_ranges = {}  # Store min/max for each metric subplot
    
    for metric in sub_graphs:
        color = get_color_for_metric(metric)
        traces = error_bar_trace(filtered_df, metric, 'tier', color)
        
        # Collect y-values to compute range for this metric
        y_values = []
        for trace in traces:
            if trace.y:
                y_arr = [float(v) for v in trace.y if v is not None]
                y_values.extend(y_arr)

                # Include absolute CI bounds in range calculation (not just error magnitudes).
                err_plus_arr = []
                err_minus_arr = []
                if trace.error_y and hasattr(trace.error_y, 'array') and trace.error_y.array:
                    err_plus_arr = [float(v) for v in trace.error_y.array if v is not None]
                if trace.error_y and hasattr(trace.error_y, 'arrayminus') and trace.error_y.arrayminus:
                    err_minus_arr = [float(v) for v in trace.error_y.arrayminus if v is not None]

                for i, y in enumerate(y_arr):
                    if i < len(err_plus_arr):
                        y_values.append(y + err_plus_arr[i])
                    if i < len(err_minus_arr):
                        y_values.append(max(0.0, y - err_minus_arr[i]))
        
        if y_values:
            metric_ranges[(row, col)] = (min(y_values), max(y_values))
        
        # Add all traces to the subplot
        for trace in traces:
            fig.add_trace(trace, row=row, col=col)

        col += 1
        if col > 5:
            col = 1
            row += 1

    fig.update_layout(
        height=800,
        showlegend=False,
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text'],
        margin=dict(l=10, r=10, t=40, b=10)
    )

    # Y-axis: dark grey gridlines, start at zero
    # Apply custom abbreviated ticks to each subplot based on its data range
    for (subplot_row, subplot_col), (min_val, max_val) in metric_ranges.items():
        tickvals, ticktext = generate_abbreviation_ticks(min_val, max_val, num_ticks=5)
        fig.update_yaxes(
            tickvals=tickvals,
            ticktext=ticktext,
            showgrid=True,
            gridcolor='darkgrey',
            zeroline=True,
            zerolinecolor='white',
            range=[0, max_val * 1.05],
            row=subplot_row,
            col=subplot_col
        )
    
    # X-axis: no gridlines
    fig.update_xaxes(showgrid=False)

    return fig


def makeTable(df: pd.DataFrame) -> go.Figure:
    """
    Creates a table with two rows per tier:
    - First row: absolute metrics (earned)
    - Second row: per hour metrics
    Common cells (tier, real time, score) are merged across rows.
    """
    def format_metric(data, metric_col, decimals=2):
        try:
            if DEBUG:
                print(f"\nFormatting metric: {metric_col}")
                print(f"Available level_1 values: {data['level_1'].unique()}")
                print(f"Data for {metric_col}:")
                print(data[['level_1', metric_col]])
            
            # Get mean and confidence intervals
            mean_val = float(data[data['level_1'] == 'mean'][metric_col].iloc[0])
            lower_val = float(data[data['level_1'] == 'ci_lower'][metric_col].iloc[0])
            # Clamp lower CI to zero for presentation
            lower_val = max(0.0, lower_val)
            upper_val = float(data[data['level_1'] == 'ci_upper'][metric_col].iloc[0])
            
            # Format based on magnitude
            if abs(mean_val) < 1000:
                mean_str = f"{mean_val:.{decimals}f}"
                lower_str = f"{lower_val:.{decimals}f}"
                upper_str = f"{upper_val:.{decimals}f}"
            else:
                mean_str = format_display_value(mean_val)
                lower_str = format_display_value(lower_val)
                upper_str = format_display_value(upper_val)
            
            # One line: mean (lower ... upper)
            return f"{mean_str} ({lower_str} ... {upper_str})"
        except (IndexError, KeyError, ValueError, TypeError) as e:
            if DEBUG:
                print(f"Error formatting {metric_col}: {e}")
            return "N/A"

    # Helper to combine total and per-hour into a single cell
    def format_total_and_rate(tier_data, total_col, rate_col):
        def extract(metric_col):
            try:
                mean_val = float(tier_data[tier_data['level_1'] == 'mean'][metric_col].iloc[0])
                lower_val = float(tier_data[tier_data['level_1'] == 'ci_lower'][metric_col].iloc[0])
                # Clamp lower CI to zero for presentation
                lower_val = max(0.0, lower_val)
                upper_val = float(tier_data[tier_data['level_1'] == 'ci_upper'][metric_col].iloc[0])
                return mean_val, lower_val, upper_val
            except Exception:
                return 0.0, 0.0, 0.0

        tm, tl, tu = extract(total_col)
        rm, rl, ru = extract(rate_col)

        # Use abbreviation helper for consistency
        t_mean = format_display_value(tm)
        t_low = format_display_value(tl)
        t_up = format_display_value(tu)

        r_mean = format_display_value(rm, suffix="/h")
        r_low = format_display_value(rl, suffix="/h")
        r_up = format_display_value(ru, suffix="/h")

        # Two lines: totals and per-hour, each with CI on the same line
        return f"{t_mean} ({t_low} ... {t_up})<br>{r_mean} ({r_low} ... {r_up})"

    # Build one row per tier with total and per-hour combined
    formatted_rows = []
    for tier in sorted(df['tier'].unique()):
        tier_data = df[df['tier'] == tier]

        time_info = format_metric(tier_data, 'real_time')
        score_info = format_metric(tier_data, 'score')

        row = {
            'Tier': f"<b>Tier {int(tier)}</b>",
            'Coins': format_total_and_rate(tier_data, 'coins_earned', 'coins_per_hour'),
            'Cells': format_total_and_rate(tier_data, 'cells_earned', 'cells_per_hour'),
            'Reroll Shards': format_total_and_rate(tier_data, 'reroll_shards_earned', 'reroll_shards_per_hour'),
            'Time (h)': time_info,
            'Score': score_info
        }

        formatted_rows.append(row)
    
    if not formatted_rows:
        return go.Figure()  # Return empty figure if no data
        
    # Convert to DataFrame and define column order
    formatted_df = pd.DataFrame(formatted_rows)
    columns = ['Tier', 'Coins', 'Cells', 'Reroll Shards', 'Time (h)', 'Score']
    
    # Create alternating colors for pairs of rows (same tier)
    n_rows = len(formatted_rows)
    fill_colors = []
    for i in range(n_rows):
        tier_color = colors.get('card', '#0c0d10') if i % 2 == 0 else colors.get('secondary_bg', '#202128')
        fill_colors.append(tier_color)

    fig = go.Figure(data=[go.Table(
        header=dict(
            values=[f"<b>{col}</b>" for col in columns],
            fill_color=colors.get('secondary_bg', '#202128'),
            align='center',
            height=36,
            font=dict(color=colors.get('text', '#FAFAFA'), size=13)
        ),
        cells=dict(
            values=[formatted_df[col] for col in columns],
            fill_color=[fill_colors],
            align='center',
            height=32,
            font=dict(color=colors.get('text', '#FAFAFA'), size=12)
        ),
        columnwidth=[12, 22, 22, 22, 12, 10]
    )])

    # Match page background and use full-width layout margins
    fig.update_layout(
        plot_bgcolor=colors.get('background', '#000000'),
        paper_bgcolor=colors.get('background', '#000000'),
        font_color=colors.get('text', '#FAFAFA'),
        margin=dict(l=10, r=10, t=20, b=10),
    )

    return fig


def simple_table(df: pd.DataFrame, title: str | None = None) -> go.Figure:
    """Render a generic DataFrame as a Plotly table without metric-specific assumptions.

    - Displays all columns as-is
    - Applies project colors
    - Optional title
    """
    if df is None or df.empty:
        return go.Figure()

    # Ensure all values are stringifiable and avoid nested dict/list objects by JSON-dumping them
    def _stringify(val: Any) -> str:
        try:
            if isinstance(val, (dict, list)):
                import json as _json
                return _json.dumps(val, ensure_ascii=False)
            return str(val)
        except Exception:
            return ""

    safe_df = df.copy()
    for c in safe_df.columns:
        safe_df[c] = safe_df[c].map(_stringify)

    fig = go.Figure(data=[go.Table(
        header=dict(
            values=[f"<b>{col}</b>" for col in safe_df.columns],
            fill_color=colors.get('secondary_bg', '#202128'),
            align='left',
            height=34,
            font=dict(color=colors.get('text', '#FAFAFA'), size=12)
        ),
        cells=dict(
            values=[safe_df[col] for col in safe_df.columns],
            fill_color=colors.get('card', '#0C0D10'),
            align='left',
            height=28,
            font=dict(color=colors.get('text', '#FAFAFA'), size=11)
        )
    )])

    fig.update_layout(
        title=title or None,
        plot_bgcolor=colors.get('background', '#000000'),
        paper_bgcolor=colors.get('background', '#000000'),
        font_color=colors.get('text', '#FAFAFA'),
        margin=dict(l=10, r=10, t=40 if title else 10, b=10)
    )
    return fig


def generate_optimize_df(df: pd.DataFrame, daytime: int, time_series_df: Optional[pd.DataFrame] = None, 
                                     all_runs_time_series_df: Optional[pd.DataFrame] = None, current_days: int = 3,
                                 nighttime_max_runs: int = 1, required_tiers: Optional[list[int]] = None,
                                 tournament_runs: int = 2, tournament_tier: int = 12) -> dict[str, Any]:
    # Always filter to last 30 days for optimization
    if 'date' in df.columns:
        cutoff_date = pd.Timestamp.today().date() - pd.Timedelta(days=30)
        df = df[df['date'] >= cutoff_date].copy()
        if df.empty:
            import warnings as _warnings
            _warnings.warn("No optimizer data in the last 30 days.", RuntimeWarning)
            # Optionally, return empty results or fallback to most recent data
    # ...existing code...
    # Get raw DataFrames for standard scenarios
    # Standard Day+Night optimization (always computed)
    import time  # Ensure time is imported (idempotent)
    timing_info = {}
    overnight_hours = float(max(0.0, 24.0 - float(daytime)))

    def _ensure_run_type(bdf: pd.DataFrame, default_type: str = 'farming') -> pd.DataFrame:
        if bdf is None or bdf.empty:
            return bdf
        bdf = bdf.copy()
        if 'run_type' not in bdf.columns:
            bdf['run_type'] = default_type
        else:
            bdf['run_type'] = bdf['run_type'].fillna(default_type).replace('', default_type)
        return bdf

    def _buffer_df(hours: float) -> pd.DataFrame:
        return pd.DataFrame([{
            'tier': 'Buffer',
            'runs': 1,
            'duration_per_run': float(hours),
            'total_duration': float(hours),
            'description': f"1 x tier Buffer ({float(hours):.2f} h each)<br>(total time: {float(hours):.2f} h)",
            'run_type': 'buffer'
        }])

    def _used_hours(bdf: pd.DataFrame, used_val: float) -> float:
        if used_val and used_val > 0:
            return float(used_val)
        if bdf is not None and not bdf.empty and 'total_duration' in bdf.columns:
            try:
                return float(bdf['total_duration'].sum())
            except Exception:
                return 0.0
        return 0.0

    def _combine_summaries(summary_a: pd.DataFrame, summary_b: pd.DataFrame, extra_duration: float = 0.0) -> pd.DataFrame:
        if summary_a is None or summary_a.empty:
            if summary_b is None or summary_b.empty:
                return pd.DataFrame()
            summary_b = summary_b.copy()
            if 'total_duration' in summary_b.columns:
                summary_b['total_duration'] = summary_b['total_duration'].astype(float) + float(extra_duration)
            return summary_b
        if summary_b is None or summary_b.empty:
            summary_a = summary_a.copy()
            if 'total_duration' in summary_a.columns:
                summary_a['total_duration'] = summary_a['total_duration'].astype(float) + float(extra_duration)
            return summary_a

        combined_rows = []
        for conf in ['ci_lower', 'mean', 'ci_upper']:
            row_a = summary_a[summary_a['confidence'] == conf]
            row_b = summary_b[summary_b['confidence'] == conf]
            if row_a.empty or row_b.empty:
                continue
            row_a = row_a.iloc[0]
            row_b = row_b.iloc[0]
            combined = {
                'confidence': conf,
                'coins_earned': float(row_a['coins_earned']) + float(row_b['coins_earned']),
                'cells_earned': float(row_a['cells_earned']) + float(row_b['cells_earned']),
                'reroll_shards_earned': float(row_a['reroll_shards_earned']) + float(row_b['reroll_shards_earned']),
                'score': float(row_a['score']) + float(row_b['score']) if 'score' in row_a and 'score' in row_b else 0.0,
                'total_duration': float(row_a.get('total_duration', 0.0)) + float(row_b.get('total_duration', 0.0)) + float(extra_duration)
            }
            combined_rows.append(combined)
        return pd.DataFrame(combined_rows)

    def _build_day_night_breakdown(breakdown_night: pd.DataFrame, used_night: float, night_hours: float,
                                   breakdown_day: pd.DataFrame, used_day: float, day_hours: float,
                                   extra_daytime_hours: float = 0.0, extra_daytime_rows: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        parts = []
        if breakdown_night is not None and not breakdown_night.empty:
            parts.append(_ensure_run_type(breakdown_night))
        night_buffer = max(0.0, float(night_hours) - float(used_night))
        if night_buffer > 1e-6:
            parts.append(_buffer_df(night_buffer))
        if extra_daytime_rows is not None and not extra_daytime_rows.empty:
            parts.append(extra_daytime_rows)
        if breakdown_day is not None and not breakdown_day.empty:
            parts.append(_ensure_run_type(breakdown_day))
        day_buffer = max(0.0, float(day_hours) - float(used_day) - float(extra_daytime_hours))
        if day_buffer > 1e-6:
            parts.append(_buffer_df(day_buffer))
        return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()

    def _mean_score(summary_df: pd.DataFrame) -> float:
        if summary_df is None or summary_df.empty or 'confidence' not in summary_df.columns:
            return float('-inf')
        row = summary_df[summary_df['confidence'] == 'mean']
        if row.empty or 'score' not in row.columns:
            return float('-inf')
        try:
            return float(row['score'].iloc[0])
        except Exception:
            return float('-inf')

    def _best_overnight_overrun(df_src: pd.DataFrame, overnight_limit: float, required_tier: Optional[int] = None) -> tuple[pd.DataFrame, pd.DataFrame, float]:
        df_clean = df_src.copy()
        df_clean['real_time'] = df_clean['real_time'].apply(lambda x: float(str(x).replace('h', '').strip()))
        df_clean['coins_earned'] = pd.to_numeric(df_clean['coins_earned'], errors='coerce')
        df_clean['cells_earned'] = pd.to_numeric(df_clean['cells_earned'], errors='coerce')
        df_clean['reroll_shards_earned'] = pd.to_numeric(df_clean['reroll_shards_earned'], errors='coerce')
        df_clean['score'] = pd.to_numeric(df_clean['score'], errors='coerce')
        df_clean = df_clean.dropna(subset=['coins_earned', 'cells_earned', 'reroll_shards_earned', 'real_time', 'score'])

        df_clean['tier_int'] = df_clean['tier'].apply(lambda x: int(float(x)))
        grouped = df_clean.groupby(['tier_int', 'level_1'], as_index=False).mean(numeric_only=True)
        grouped = grouped.pivot(index='tier_int', columns='level_1')
        grouped.index = grouped.index.map(lambda x: float(x) if not isinstance(x, float) else x)

        if 'real_time' not in grouped.columns or 'ci_upper' not in grouped['real_time'].columns:
            return pd.DataFrame(), pd.DataFrame(), 0.0

        durations = grouped['real_time']['ci_upper']
        candidates = durations[durations > float(overnight_limit)]
        if candidates.empty:
            return pd.DataFrame(), pd.DataFrame(), 0.0

        if required_tier is not None:
            try:
                required_tier_val = float(required_tier)
            except Exception:
                return pd.DataFrame(), pd.DataFrame(), 0.0
            candidates = candidates[candidates.index == required_tier_val]
            if candidates.empty:
                return pd.DataFrame(), pd.DataFrame(), 0.0

        best_tier = None
        best_score = float('-inf')
        best_score_per_hour = float('-inf')
        score_col = 'optimizer_score' if 'optimizer_score' in grouped.columns else 'score'
        for tier_val, dur in candidates.items():
            try:
                score_mean = float(cast(float, grouped.loc[tier_val, (score_col, 'mean')]))
            except Exception:
                continue
            score_per_hour = score_mean / float(dur) if float(dur) > 0 else 0.0
            if score_mean > best_score or (score_mean == best_score and score_per_hour > best_score_per_hour):
                best_score = score_mean
                best_score_per_hour = score_per_hour
                best_tier = tier_val

        if best_tier is None:
            return pd.DataFrame(), pd.DataFrame(), 0.0

        try:
            tier_out = int(best_tier) if float(best_tier).is_integer() else float(best_tier)
        except Exception:
            tier_out = best_tier

        duration = float(cast(float, grouped.loc[best_tier, ('real_time', 'ci_upper')]))
        def _metric_row(level: str) -> dict[str, float | str]:
            return {
                'confidence': level,
                'coins_earned': float(cast(float, grouped.loc[best_tier, ('coins_earned', level)])),
                'cells_earned': float(cast(float, grouped.loc[best_tier, ('cells_earned', level)])),
                'reroll_shards_earned': float(cast(float, grouped.loc[best_tier, ('reroll_shards_earned', level)])),
                'score': float(cast(float, grouped.loc[best_tier, (score_col, level)])),
                'total_duration': duration
            }

        summary_df = pd.DataFrame([_metric_row('ci_lower'), _metric_row('mean'), _metric_row('ci_upper')])
        breakdown_df = pd.DataFrame([{
            'tier': tier_out,
            'runs': 1,
            'duration_per_run': duration,
            'total_duration': duration,
            'description': f"1 x tier {tier_out} ({duration:.2f} h each)<br>(total time: {duration:.2f} h)",
            'run_type': 'farming'
        }])
        return summary_df, breakdown_df, duration

    def _choose_overnight_plan(
        df_src: pd.DataFrame,
        overnight_limit: float,
        max_runs: int,
        required_tiers: Optional[list[int]] = None
    ) -> tuple[pd.DataFrame, pd.DataFrame, float]:
        if required_tiers:
            opt_night = Optimizer(df_src, duration=overnight_limit, max_runs=max_runs, custom_tier=required_tiers)
            summary_std, breakdown_std, used_std = opt_night.run()
            summary_over = pd.DataFrame()
            breakdown_over = pd.DataFrame()
            used_over = 0.0
            if len(required_tiers) == 1:
                summary_over, breakdown_over, used_over = _best_overnight_overrun(
                    df_src,
                    overnight_limit,
                    required_tier=required_tiers[0]
                )
            if not summary_over.empty and _mean_score(summary_over) > _mean_score(summary_std):
                return summary_over, breakdown_over, used_over
            return summary_std, breakdown_std, used_std

        opt_night = Optimizer(df_src, duration=overnight_limit, max_runs=max_runs)
        summary_std, breakdown_std, used_std = opt_night.run()
        summary_over, breakdown_over, used_over = _best_overnight_overrun(df_src, overnight_limit)

        if not summary_over.empty and _mean_score(summary_over) > _mean_score(summary_std):
            return summary_over, breakdown_over, used_over
        return summary_std, breakdown_std, used_std

    # Nighttime optimization (fixed overnight hours, limited runs) with overrun candidate
    t1 = time.perf_counter()
    summary_nt, breakdown_nt, used_nt = _choose_overnight_plan(df, overnight_hours, nighttime_max_runs)
    timing_info['night'] = time.perf_counter() - t1

    overlap_hours = max(0.0, float(used_nt) - float(overnight_hours))
    daytime_available = max(0.0, float(daytime) - float(overlap_hours))

    t0 = time.perf_counter()
    opt_day = Optimizer(df, duration=daytime_available)
    summary_dt, breakdown_dt, used_dt = opt_day.run()
    timing_info['day'] = time.perf_counter() - t0
    # 24-hour optimization (no run limit, no tier requirements for comparison)
    t2 = time.perf_counter()
    opt_24 = Optimizer(df, duration=24)
    summary_24, breakdown_24, used_24 = opt_24.run()
    timing_info['24h'] = time.perf_counter() - t2
    # Custom scenario with required tiers (only if specified) - use daytime/overnight split
    t3 = time.perf_counter()
    summary_custom = pd.DataFrame()
    breakdown_custom = pd.DataFrame()
    used_custom = 0.0
    if required_tiers is not None and len(required_tiers) > 0:
        required_tiers_list = [int(t) for t in required_tiers]

        # Option A: required tiers during daytime
        opt_custom_day = Optimizer(df, duration=daytime_available, custom_tier=required_tiers_list)
        summary_custom_day, breakdown_custom_day, used_custom_day = opt_custom_day.run()
        summary_custom_a = pd.DataFrame()
        breakdown_custom_a = pd.DataFrame()
        used_custom_a = 0.0
        if not summary_custom_day.empty:
            summary_custom_a = _combine_summaries(summary_custom_day, summary_nt)
            used_custom_a = float(used_custom_day) + float(used_nt)
            breakdown_custom_a = _build_day_night_breakdown(
                breakdown_nt,
                _used_hours(breakdown_nt, used_nt),
                overnight_hours,
                breakdown_custom_day,
                _used_hours(breakdown_custom_day, used_custom_day),
                float(daytime_available)
            )

        # Option B: required tiers during overnight
        summary_custom_night, breakdown_custom_night, used_custom_night = _choose_overnight_plan(
            df,
            overnight_hours,
            nighttime_max_runs,
            required_tiers=required_tiers_list
        )
        summary_custom_b = pd.DataFrame()
        breakdown_custom_b = pd.DataFrame()
        used_custom_b = 0.0
        if not summary_custom_night.empty:
            overlap_custom = max(0.0, float(used_custom_night) - float(overnight_hours))
            day_available_custom = max(0.0, float(daytime) - float(overlap_custom))
            opt_custom_day_b = Optimizer(df, duration=day_available_custom)
            summary_custom_day_b, breakdown_custom_day_b, used_custom_day_b = opt_custom_day_b.run()
            summary_custom_b = _combine_summaries(summary_custom_day_b, summary_custom_night)
            used_custom_b = float(used_custom_day_b) + float(used_custom_night)
            breakdown_custom_b = _build_day_night_breakdown(
                breakdown_custom_night,
                _used_hours(breakdown_custom_night, used_custom_night),
                overnight_hours,
                breakdown_custom_day_b,
                _used_hours(breakdown_custom_day_b, used_custom_day_b),
                float(day_available_custom)
            )

        # Choose the better feasible option
        if not summary_custom_a.empty and not summary_custom_b.empty:
            if _mean_score(summary_custom_b) > _mean_score(summary_custom_a):
                summary_custom, breakdown_custom, used_custom = summary_custom_b, breakdown_custom_b, used_custom_b
            else:
                summary_custom, breakdown_custom, used_custom = summary_custom_a, breakdown_custom_a, used_custom_a
        elif not summary_custom_a.empty:
            summary_custom, breakdown_custom, used_custom = summary_custom_a, breakdown_custom_a, used_custom_a
        elif not summary_custom_b.empty:
            summary_custom, breakdown_custom, used_custom = summary_custom_b, breakdown_custom_b, used_custom_b
        else:
            summary_custom = pd.DataFrame()
            breakdown_custom = pd.DataFrame()
            used_custom = 0.0

        timing_info['custom'] = time.perf_counter() - t3

    # Tournament scenario (tournament runs + optimized remainder)
    # Always create Tournament scenario, even if tournament_runs is 0 (it will just be same as 24h optimization)
    t4 = time.perf_counter()
    summary_tournament = pd.DataFrame()
    breakdown_tournament = pd.DataFrame()
    used_tournament = 0.0
    tournament_duration = 0.0
    
    if tournament_runs > 0 and tournament_tier is not None:
        # Find the tournament tier in the data (look for tournament runs in all_runs_time_series_df)
        tournament_tier_found = None
        tournament_tier_duration = 0.0
        actual_tier_str = f"{tournament_tier}+"  # Default display format
        
        # First, try to find tournament tier from tournament runs in time series data
        if all_runs_time_series_df is not None and not all_runs_time_series_df.empty:
            # Extract base tier number from strings like "12+", "17+" for comparison
            def extract_tier_base(tier_str):
                """Extract base tier number from strings like '12+' or '12'"""
                try:
                    tier_clean = str(tier_str).replace('+', '').strip()
                    return int(float(tier_clean))
                except:
                    return None
            
            all_runs_copy = all_runs_time_series_df.copy()
            all_runs_copy['tier_base'] = all_runs_copy['tier'].apply(extract_tier_base)
            
            # Filter tournament runs with tier >= tournament_tier
            tournament_df = all_runs_copy[
                (all_runs_copy['run_type'] == 'tournament') & 
                (all_runs_copy['tier_base'] >= tournament_tier) &
                (all_runs_copy['tier_base'].notna())
            ]
            
            if not tournament_df.empty:
                # Get the mean duration for tournament runs at this tier+
                tournament_tier_duration = float(tournament_df['real_time'].mean())
                tournament_tier_found = tournament_tier
                # Use the selected tier for display (e.g., "12+" for Champion)
                actual_tier_str = f"{tournament_tier}+"
        
        # Fallback: if no tournament data found, use the grouped data (farming/overnight)
        if tournament_tier_found is None or tournament_tier_duration == 0:
            # Try to find the tier in the grouped optimizer data
            df_clean = df.copy()
            df_clean['real_time'] = df_clean['real_time'].apply(lambda x: float(str(x).replace('h', '').strip()))
            df_clean['tier_int'] = df_clean['tier'].apply(lambda x: int(float(x)))
            grouped_tournament = df_clean.groupby(['tier_int', 'level_1'], as_index=False).mean(numeric_only=True)
            grouped_tournament = grouped_tournament.pivot(index='tier_int', columns='level_1')
            grouped_tournament.index = grouped_tournament.index.map(lambda x: float(x) if not isinstance(x, float) else x)
            
            # Find the closest tier >= tournament_tier
            available_tiers = sorted([t for t in grouped_tournament.index if t >= tournament_tier])
            if available_tiers:
                tournament_tier_found = available_tiers[0]
                actual_tier_str = str(int(tournament_tier_found))
                # Use ci_upper for conservative estimate
                if 'real_time' in grouped_tournament.columns and 'ci_upper' in grouped_tournament['real_time'].columns:
                    val = grouped_tournament.loc[tournament_tier_found, ('real_time', 'ci_upper')]
                    tournament_tier_duration = float(cast(float, val))  # type: ignore
        
        # Calculate total tournament duration
        if tournament_tier_found is not None and float(tournament_tier_duration) > 0:
            tournament_duration = float(tournament_runs * float(tournament_tier_duration))

            # Optimize within daytime/overnight blocks (tournament assumed during daytime)
            day_available_hours = max(0.0, float(daytime_available) - float(tournament_duration))
            opt_tournament_day = Optimizer(df, duration=day_available_hours)
            summary_tournament_day, breakdown_tournament_day, used_tournament_day = opt_tournament_day.run()

            tournament_desc = f"{tournament_runs} x tier {actual_tier_str} ({float(tournament_tier_duration):.2f} h each)<br>(total time: {float(tournament_duration):.2f} h)"
            tournament_row = pd.DataFrame([{
                'tier': actual_tier_str,
                'runs': tournament_runs,
                'duration_per_run': float(tournament_tier_duration),
                'total_duration': float(tournament_duration),
                'description': tournament_desc,
                'run_type': 'tournament'
            }])

            summary_tournament = _combine_summaries(
                summary_tournament_day,
                summary_nt,
                extra_duration=float(tournament_duration)
            )
            if summary_tournament.empty:
                summary_tournament = pd.DataFrame([
                    {'confidence': 'ci_lower', 'coins_earned': 0.0, 'cells_earned': 0.0, 'reroll_shards_earned': 0.0, 'score': 0.0, 'total_duration': float(tournament_duration)},
                    {'confidence': 'mean', 'coins_earned': 0.0, 'cells_earned': 0.0, 'reroll_shards_earned': 0.0, 'score': 0.0, 'total_duration': float(tournament_duration)},
                    {'confidence': 'ci_upper', 'coins_earned': 0.0, 'cells_earned': 0.0, 'reroll_shards_earned': 0.0, 'score': 0.0, 'total_duration': float(tournament_duration)}
                ])
            used_tournament = float(used_tournament_day) + float(used_nt) + float(tournament_duration)

            breakdown_tournament = _build_day_night_breakdown(
                breakdown_nt,
                _used_hours(breakdown_nt, used_nt),
                overnight_hours,
                breakdown_tournament_day,
                _used_hours(breakdown_tournament_day, used_tournament_day),
                float(daytime_available),
                extra_daytime_hours=float(tournament_duration),
                extra_daytime_rows=tournament_row
            )
        else:
            summary_tournament = pd.DataFrame([
                {'confidence': 'ci_lower', 'coins_earned': 0.0, 'cells_earned': 0.0, 'reroll_shards_earned': 0.0, 'score': 0.0, 'total_duration': float(tournament_duration)},
                {'confidence': 'mean', 'coins_earned': 0.0, 'cells_earned': 0.0, 'reroll_shards_earned': 0.0, 'score': 0.0, 'total_duration': float(tournament_duration)},
                {'confidence': 'ci_upper', 'coins_earned': 0.0, 'cells_earned': 0.0, 'reroll_shards_earned': 0.0, 'score': 0.0, 'total_duration': float(tournament_duration)}
            ])
            breakdown_tournament = pd.DataFrame([{
                'tier': actual_tier_str,
                'runs': tournament_runs,
                'duration_per_run': float(tournament_tier_duration),
                'total_duration': float(tournament_duration),
                'description': f"{tournament_runs} x tier {actual_tier_str} ({float(tournament_tier_duration):.2f} h each)<br>(total time: {float(tournament_duration):.2f} h)",
                'run_type': 'tournament'
            }])
            used_tournament = float(tournament_duration)
    else:
        # If no tournament runs specified, Tournament is same as 24h optimization
        summary_tournament = summary_24.copy()
        breakdown_tournament = breakdown_24.copy()
        used_tournament = used_24
    
    timing_info['tournament'] = time.perf_counter() - t4

    # Always return summary_custom and breakdown_custom, even if empty, so the plotting code can handle it robustly
    # If custom was requested but no solution, fill with a labeled empty row for clarity
    if required_tiers is not None and len(required_tiers) > 0:
        if summary_custom.empty:
            summary_custom = pd.DataFrame([
                {
                    'confidence': 'none',
                    'coins_earned': 0.0,
                    'cells_earned': 0.0,
                    'reroll_shards_earned': 0.0,
                    'score': 0.0,
                    'total_duration': 0.0,
                    'note': 'No feasible schedule with required tiers'
                }
            ])
        if breakdown_custom.empty:
            breakdown_custom = pd.DataFrame([
                {'description': 'No feasible combination for required tiers'}
            ])
    # Combine daytime + nighttime by summing incomes for each confidence level
    summary_combined = _combine_summaries(summary_dt, summary_nt)
    
    # Combine breakdown descriptions (robust to missing columns/empty frames)
    def _extract_descriptions(bdf: Optional[pd.DataFrame]) -> list[str]:
        if bdf is None or bdf.empty:
            return []
        if 'description' in bdf.columns:
            return [str(x) for x in bdf['description'].dropna().tolist()]
        # Try to synthesize from components if available
        needed = {'tier', 'runs', 'duration_per_run', 'total_duration'}
        if needed.issubset(set(bdf.columns)):
            rows = []
            for _, r in bdf.iterrows():
                try:
                    rows.append(
                        f"{int(r['runs'])} x tier {int(r['tier'])} ({float(r['duration_per_run']):.2f} h each)"  # noqa: E501
                    )
                except Exception:
                    continue
            return rows
        return []

    breakdown_combined = _build_day_night_breakdown(
        breakdown_nt,
        _used_hours(breakdown_nt, used_nt),
        overnight_hours,
        breakdown_dt,
        _used_hours(breakdown_dt, used_dt),
        float(daytime_available)
    )
    
    # Use summarize_current for the Current scenario
    current_ts_df = all_runs_time_series_df if all_runs_time_series_df is not None and not all_runs_time_series_df.empty else time_series_df
    if current_ts_df is not None and not current_ts_df.empty and 'timestamp' in current_ts_df.columns:
        summary_current, breakdown_current, _ = summarize_current(current_ts_df, n_days=current_days)
    else:
        summary_current = pd.DataFrame()
        breakdown_current = pd.DataFrame({'description': ['Based on current average performance']})
    
    # Compute time utilization stats
    day_used_hours = float(_used_hours(breakdown_dt, used_dt))
    night_used_hours = float(_used_hours(breakdown_nt, used_nt))
    combined_used_hours = float(day_used_hours + night_used_hours)
    overnight_available_hours = float(max(0.0, overnight_hours - night_used_hours))
    free_hours = float(max(0.0, 24.0 - combined_used_hours))

    return {
        'summary_combined': summary_combined,
        'breakdown_combined': breakdown_combined,
        'summary_24h': summary_24,
        'breakdown_24h': breakdown_24,
        'summary_custom': summary_custom,
        'breakdown_custom': breakdown_custom,
        'summary_tournament': summary_tournament,
        'breakdown_tournament': breakdown_tournament,
        'summary_current': summary_current,
        'breakdown_current': breakdown_current,
        'day_used_hours': day_used_hours,
        'night_used_hours': night_used_hours,
        'combined_used_hours': combined_used_hours,
        'custom_used_hours': used_custom,
        'tournament_used_hours': used_tournament,
        'tournament_duration': tournament_duration,
        'overnight_available_hours': overnight_available_hours,
        'free_hours': free_hours,
    }


def forward_optimize_weekly(
    df: pd.DataFrame,
    sleep_window: str,
    nighttime_max_runs: int,
    tournament_runs: int,
    tournament_tier: int,
    score_weights: dict[str, float],  # {'coins': w1, 'cells': w2, 'shards': w3}
    all_runs_time_series_df: Optional[pd.DataFrame] = None,
    scenario_key: str = 'daynight',
    required_tiers: Optional[list[int]] = None,
) -> dict[str, Any]:
    """
    Forward optimizer: Sequentially optimize each day starting Monday at wakeup.
    
    - Monday-Sunday: Optimize daytime -> optimize overnight (allowing spillover)
    - Tournament days (Wed/Sat): Conduct tournament runs first, then optimize remaining time
    
    Score calculation per user's formula:
    - tier_score_x = average_x_perHour / (max(x_perHour) * 24)
    - perHour_Score = w_coins * tier_score_coins + w_cells * tier_score_cells + w_shards * tier_score_rerollShards
    - total_Tier_Score = perHour_Score * average_Tier_Duration
    
    Returns:
    - weekly_schedule: DataFrame with columns [day, time_slot, tier, duration, coins, cells, shards, waves, score]
    - weekly_summary: Dict with total income and score for the week
    """
    # Parse sleep window to get daytime/overnight hours (supports HH:MM-HH:MM and decimal hours)
    def _parse_sleep_window(sw: str) -> tuple[float, float]:
        parts = str(sw or '').split('-')
        if len(parts) != 2:
            return 22.0, 7.0

        def _parse_part(part: str) -> float | None:
            token = str(part).strip().lower().replace('h', '')
            if ':' in token:
                hhmm = token.split(':')
                if len(hhmm) != 2:
                    return None
                try:
                    hh = int(hhmm[0])
                    mm = int(hhmm[1])
                except Exception:
                    return None
                hh = max(0, min(23, hh))
                mm = max(0, min(59, mm))
                return float(hh) + (float(mm) / 60.0)
            try:
                raw = float(token)
            except Exception:
                return None
            return max(0.0, min(24.0, raw))

        start = _parse_part(parts[0])
        end = _parse_part(parts[1])
        if start is None or end is None:
            return 22.0, 7.0
        return float(start), float(end)
    
    sleep_start, sleep_end = _parse_sleep_window(sleep_window)
    if sleep_end > sleep_start:
        overnight_hours = float(sleep_end - sleep_start)
        daytime_hours = float(24.0 - overnight_hours)
    else:
        overnight_hours = float(24.0 - sleep_start + sleep_end)
        daytime_hours = float(24.0 - overnight_hours)
    
    # Calculate max per-hour metrics for normalization (from last 7 days)
    df_clean = df.copy()
    df_clean['real_time'] = df_clean['real_time'].apply(lambda x: float(str(x).replace('h', '').strip()))
    df_clean['coins_earned'] = pd.to_numeric(df_clean['coins_earned'], errors='coerce')
    df_clean['cells_earned'] = pd.to_numeric(df_clean['cells_earned'], errors='coerce')
    df_clean['reroll_shards_earned'] = pd.to_numeric(df_clean['reroll_shards_earned'], errors='coerce')
    df_clean = df_clean.dropna(subset=['coins_earned', 'cells_earned', 'reroll_shards_earned', 'real_time'])
    
    # Calculate per-hour metrics
    df_clean['coins_per_hour'] = df_clean['coins_earned'] / df_clean['real_time']
    df_clean['cells_per_hour'] = df_clean['cells_earned'] / df_clean['real_time']
    df_clean['shards_per_hour'] = df_clean['reroll_shards_earned'] / df_clean['real_time']
    
    # Get mean rows for maximum calculation
    mean_rows = df_clean[df_clean.get('level_1') == 'mean'] if 'level_1' in df_clean.columns else df_clean
    
    max_coins_ph = float(mean_rows['coins_per_hour'].max() if not mean_rows['coins_per_hour'].empty else 1.0)
    max_cells_ph = float(mean_rows['cells_per_hour'].max() if not mean_rows['cells_per_hour'].empty else 1.0)
    max_shards_ph = float(mean_rows['shards_per_hour'].max() if not mean_rows['shards_per_hour'].empty else 1.0)
    
    # Normalize weights
    w_coins = float(score_weights.get('coins', 1.0))
    w_cells = float(score_weights.get('cells', 1.0))
    w_shards = float(score_weights.get('shards', 1.0))
    weight_sum = w_coins + w_cells + w_shards
    if weight_sum > 0:
        w_coins /= weight_sum
        w_cells /= weight_sum
        w_shards /= weight_sum
    else:
        w_coins = w_cells = w_shards = 1.0 / 3.0
    
    # Prepare tier data grouped by tier
    df_clean['tier_int'] = df_clean['tier'].apply(lambda x: int(float(x)) if str(x).replace('.', '', 1).replace('+', '').isdigit() else None)
    df_clean = df_clean[df_clean['tier_int'].notna()]
    grouped = df_clean.groupby(['tier_int', 'level_1'], as_index=False).mean(numeric_only=True)
    grouped = grouped.pivot(index='tier_int', columns='level_1')
    grouped.index = grouped.index.map(lambda x: float(x) if not isinstance(x, float) else x)
    
    # Helper function to calculate tier score based on user's formula
    def _tier_score(tier_val: float) -> tuple[float, float, float, float, float, float]:
        """
        Calculate score for a tier.
        Returns: (score, duration, coins, cells, shards, waves)
        """
        try:
            # Use mean values for income, ci_upper for duration (conservative)
            duration = float(grouped.loc[tier_val, ('real_time', 'ci_upper')])
            coins = float(grouped.loc[tier_val, ('coins_earned', 'mean')])
            cells = float(grouped.loc[tier_val, ('cells_earned', 'mean')])
            shards = float(grouped.loc[tier_val, ('reroll_shards_earned', 'mean')])
            waves = float(grouped.loc[tier_val, ('waves_per_tier', 'mean')]) if ('waves_per_tier', 'mean') in grouped.columns else 0.0
            
            # Calculate per-hour metrics
            coins_ph = coins / duration if duration > 0 else 0.0
            cells_ph = cells / duration if duration > 0 else 0.0
            shards_ph = shards / duration if duration > 0 else 0.0
            
            # Normalize by max per-hour * 24 (user's formula)
            tier_score_coins = coins_ph / (max_coins_ph * 24) if max_coins_ph > 0 else 0.0
            tier_score_cells = cells_ph / (max_cells_ph * 24) if max_cells_ph > 0 else 0.0
            tier_score_shards = shards_ph / (max_shards_ph * 24) if max_shards_ph > 0 else 0.0
            
            # Calculate per-hour score
            per_hour_score = (
                w_coins * tier_score_coins +
                w_cells * tier_score_cells +
                w_shards * tier_score_shards
            )
            
            # Total tier score = per_hour_score * duration
            total_score = per_hour_score * duration
            
            return total_score, duration, coins, cells, shards, waves
        except Exception:
            return 0.0, 0.0, 0.0, 0.0, 0.0, 0.0
    
    # Helper to get tournament tier duration
    def _tournament_duration() -> float:
        if all_runs_time_series_df is not None and not all_runs_time_series_df.empty:
            def extract_tier_base(tier_str):
                try:
                    return int(float(str(tier_str).replace('+', '').strip()))
                except:
                    return None
            
            all_runs_copy = all_runs_time_series_df.copy()
            all_runs_copy['tier_base'] = all_runs_copy['tier'].apply(extract_tier_base)
            tournament_df = all_runs_copy[
                (all_runs_copy['run_type'] == 'tournament') &
                (all_runs_copy['tier_base'] >= tournament_tier) &
                (all_runs_copy['tier_base'].notna())
            ]
            if not tournament_df.empty:
                return float(tournament_df['real_time'].mean())
        
        # Fallback to grouped data
        available_tiers = sorted([t for t in grouped.index if t >= tournament_tier])
        if available_tiers:
            tier_val = available_tiers[0]
            if 'real_time' in grouped.columns and 'ci_upper' in grouped['real_time'].columns:
                return float(grouped.loc[tier_val, ('real_time', 'ci_upper')])
        return 0.0

    def _summary_mean_score(summary_df: pd.DataFrame) -> float:
        if summary_df is None or summary_df.empty or 'confidence' not in summary_df.columns:
            return float('-inf')
        row = summary_df[summary_df['confidence'] == 'mean']
        if row.empty or 'score' not in row.columns:
            return float('-inf')
        try:
            return float(row['score'].iloc[0])
        except Exception:
            return float('-inf')

    def _expand_optimizer_breakdown(breakdown_df: pd.DataFrame) -> list[dict[str, Any]]:
        runs: list[dict[str, Any]] = []
        if breakdown_df is None or breakdown_df.empty:
            return runs
        for _, row in breakdown_df.iterrows():
            try:
                tier_val = float(row.get('tier'))
                run_count = float(row.get('runs', 0) or 0)
                run_duration = float(row.get('duration_per_run', 0) or 0)
            except Exception:
                continue
            if run_count <= 0 or run_duration <= 0:
                continue

            score, full_duration, coins, cells, shards, waves = _tier_score(tier_val)
            if full_duration <= 0:
                continue

            full_runs = int(math.floor(run_count))
            remainder = max(0.0, run_count - full_runs)
            for _ in range(full_runs):
                runs.append({
                    'tier': int(tier_val) if float(tier_val).is_integer() else float(tier_val),
                    'duration': full_duration,
                    'coins': coins,
                    'cells': cells,
                    'shards': shards,
                    'waves': waves,
                    'score': score,
                    'run_type': 'farming',
                })
            if remainder > 1e-6:
                scale_factor = remainder
                runs.append({
                    'tier': int(tier_val) if float(tier_val).is_integer() else float(tier_val),
                    'duration': full_duration * scale_factor,
                    'coins': coins * scale_factor,
                    'cells': cells * scale_factor,
                    'shards': shards * scale_factor,
                    'waves': waves * scale_factor,
                    'score': score * scale_factor,
                    'run_type': 'farming',
                })
        return runs

    def _optimize_window_runs(
        time_limit: float,
        required: Optional[list[int]] = None,
        max_runs: Optional[int] = None,
    ) -> tuple[list[dict[str, Any]], pd.DataFrame, float]:
        if time_limit <= 1e-6:
            return [], pd.DataFrame(), 0.0
        opt = Optimizer(df, duration=float(time_limit), custom_tier=required, max_runs=max_runs)
        summary_df, breakdown_df, used_hours = opt.run()
        return _expand_optimizer_breakdown(breakdown_df), summary_df, float(used_hours or 0.0)

    def _pick_best_single_run(candidate_tiers: Optional[list[int]] = None) -> dict[str, Any] | None:
        if candidate_tiers:
            available_tiers = [float(t) for t in candidate_tiers if float(t) in grouped.index]
        else:
            available_tiers = [float(t) for t in grouped.index]
        best_run: dict[str, Any] | None = None
        best_score = float('-inf')
        for tier in available_tiers:
            score, duration, coins, cells, shards, waves = _tier_score(tier)
            if duration <= 0:
                continue
            if score > best_score:
                best_score = score
                best_run = {
                    'tier': int(tier) if float(tier).is_integer() else float(tier),
                    'duration': duration,
                    'coins': coins,
                    'cells': cells,
                    'shards': shards,
                    'waves': waves,
                    'score': score,
                    'run_type': 'farming',
                }
        return best_run

    def _best_daytime_coins_per_hour() -> float:
        best = 0.0
        for tier in grouped.index:
            _, duration, coins, _, _, _ = _tier_score(float(tier))
            if duration > 0:
                best = max(best, coins / duration)
        return best

    best_day_coins_ph = _best_daytime_coins_per_hour()

    def _build_daytime_runs_bonus_malus(time_limit: float, required: Optional[list[int]] = None) -> list[dict[str, Any]]:
        """
        Daytime optimizer with bonus/malus objective.

        bonus: income per hour (implemented via coins contribution)
        malus: unused daytime hours
        """
        runs: list[dict[str, Any]] = []
        remaining = float(max(0.0, time_limit))
        if remaining <= 1e-6:
            return runs

        # Tune gap aversion relative to best achievable daytime coins/hour.
        daytime_unused_malus_per_hour = 0.35 * best_day_coins_ph

        # If required tiers are requested, place one required run first when feasible.
        if required:
            best_req: dict[str, Any] | None = None
            best_req_cph = -1.0
            for req in required:
                tier = float(req)
                if tier not in grouped.index:
                    continue
                score, duration, coins, cells, shards, waves = _tier_score(tier)
                if duration <= 0 or duration > remaining + 1e-6:
                    continue
                coins_ph = coins / duration
                if coins_ph > best_req_cph:
                    best_req_cph = coins_ph
                    best_req = {
                        'tier': int(tier) if float(tier).is_integer() else float(tier),
                        'duration': duration,
                        'coins': coins,
                        'cells': cells,
                        'shards': shards,
                        'waves': waves,
                        'score': score,
                        'run_type': 'farming',
                    }
            if best_req is not None:
                runs.append(best_req)
                remaining -= float(best_req['duration'])

        if remaining <= 1e-6:
            return runs

        # Discretize to keep the search efficient but still reasonably accurate.
        step_h = 0.1  # 6 minutes
        capacity_steps = int(max(0, math.floor(remaining / step_h + 1e-9)))
        if capacity_steps <= 0:
            return runs

        templates: list[dict[str, Any]] = []
        for tier in grouped.index:
            score, duration, coins, cells, shards, waves = _tier_score(float(tier))
            if duration <= 0 or duration > remaining + 1e-6:
                continue
            dur_steps = int(max(1, math.ceil(duration / step_h - 1e-9)))
            # Additive objective: total coins bonus + fill incentive (unused-time malus as used-time reward).
            utility = float(coins) + float(daytime_unused_malus_per_hour * duration)
            templates.append({
                'tier': int(float(tier)) if float(tier).is_integer() else float(tier),
                'duration': float(duration),
                'coins': float(coins),
                'cells': float(cells),
                'shards': float(shards),
                'waves': float(waves),
                'score': float(score),
                'run_type': 'farming',
                'dur_steps': dur_steps,
                'utility': utility,
            })

        if not templates:
            return runs

        best_val = [float('-inf')] * (capacity_steps + 1)
        prev: list[tuple[int, int] | None] = [None] * (capacity_steps + 1)
        best_val[0] = 0.0

        # Unbounded knapsack on discretized daytime budget.
        for t in range(1, capacity_steps + 1):
            for i, tpl in enumerate(templates):
                d = int(tpl['dur_steps'])
                if d > t or best_val[t - d] == float('-inf'):
                    continue
                cand = best_val[t - d] + float(tpl['utility'])
                if cand > best_val[t] + 1e-9:
                    best_val[t] = cand
                    prev[t] = (t - d, i)

        best_t = 0
        best_obj = float('-inf')
        for t in range(capacity_steps + 1):
            if best_val[t] == float('-inf'):
                continue
            # Prefer fuller usage when objective is tied.
            if best_val[t] > best_obj + 1e-9 or (abs(best_val[t] - best_obj) < 1e-9 and t > best_t):
                best_obj = best_val[t]
                best_t = t

        if best_t <= 0:
            return runs

        chosen: list[dict[str, Any]] = []
        cursor = best_t
        while cursor > 0 and prev[cursor] is not None:
            prev_t, tpl_idx = prev[cursor]
            tpl = templates[tpl_idx]
            chosen.append({
                'tier': tpl['tier'],
                'duration': tpl['duration'],
                'coins': tpl['coins'],
                'cells': tpl['cells'],
                'shards': tpl['shards'],
                'waves': tpl['waves'],
                'score': tpl['score'],
                'run_type': tpl['run_type'],
            })
            cursor = prev_t

        chosen.reverse()
        runs.extend(chosen)
        return runs

    def _pick_best_overnight_run(candidate_tiers: Optional[list[int]] = None) -> dict[str, Any] | None:
        if candidate_tiers:
            tiers = [float(t) for t in candidate_tiers if float(t) in grouped.index]
        else:
            tiers = [float(t) for t in grouped.index]
        best_run: dict[str, Any] | None = None
        best_net = float('-inf')

        # Heuristic preference for "long" overnight runs that bridge sleep boundaries.
        # Interpreted via duration relative to sleep window length:
        # overnight+2h (e.g., 21:00->08:00 for a 22:00-07:00 window): big bonus
        # overnight+4h: medium bonus
        # overnight+6h: small bonus
        # shorter than overnight window: malus
        def _overnight_alignment_bonus(duration_h: float) -> float:
            if overnight_hours <= 0:
                return 0.0
            extra = float(duration_h) - float(overnight_hours)
            scale = max(1e-9, best_day_coins_ph)

            if 1.0 <= extra <= 3.0:
                return 1.50 * scale  # big bonus
            if 3.0 < extra <= 5.0:
                return 1.00 * scale  # medium bonus
            if 5.0 < extra <= 7.0:
                return 0.50 * scale  # small bonus
            if extra < 0.0:
                # Penalize short runs that fail to cover the sleep window.
                return -1.20 * scale * abs(extra)
            return 0.0

        for tier in tiers:
            score, duration, coins, cells, shards, waves = _tier_score(tier)
            if duration <= 0:
                continue
            coins_ph = coins / duration
            overnight_used = min(duration, overnight_hours)
            spill = max(0.0, duration - overnight_hours)
            night_coins = coins_ph * overnight_used
            opportunity_cost = spill * best_day_coins_ph
            alignment_bonus = _overnight_alignment_bonus(duration)
            net_value = night_coins - opportunity_cost + alignment_bonus

            if (
                best_run is None
                or net_value > best_net
                or (abs(net_value - best_net) < 1e-9 and spill < max(0.0, float(best_run['duration']) - overnight_hours))
            ):
                best_net = net_value
                best_run = {
                    'tier': int(tier) if float(tier).is_integer() else float(tier),
                    'duration': duration,
                    'coins': coins,
                    'cells': cells,
                    'shards': shards,
                    'waves': waves,
                    'score': score,
                    'run_type': 'farming',
                }
        return best_run
    
    scenario = str(scenario_key or 'daynight').strip().lower()
    if scenario not in {'24h', 'daynight', 'custom'}:
        scenario = 'daynight'

    if scenario == '24h':
        daytime_hours = 24.0
        overnight_hours = 0.0
    elif scenario == 'daynight':
        pass
    else:  # custom
        pass

    required_tier_list = sorted(set(int(t) for t in (required_tiers or [])))
    required_tier_set = set(required_tier_list)

    # Build weekly schedule with time_slot tracking
    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    tournament_days = [2, 5]  # Wednesday (index 2), Saturday (index 5)
    
    weekly_schedule = []
    time_remaining = 0.0  # Spillover from previous overnight run
    required_cycle = sorted(required_tier_set)
    required_cycle_idx = 0
    
    for day_idx, day in enumerate(days):
        last_daytime_tier = None
        required_placed_today = False
        required_tier_today: int | None = None
        if scenario == 'custom' and required_cycle:
            required_tier_today = required_cycle[required_cycle_idx]
        
        # Handle spillover from previous night
        if time_remaining > 0:
            # Previous overnight run is still ongoing
            spillover = min(time_remaining, daytime_hours)
            time_remaining -= spillover
            daytime_available = max(0.0, daytime_hours - spillover)
        else:
            daytime_available = daytime_hours
        
        # Tournament runs on Wed/Sat (not in 24h mode; 24h should stay continuous farming).
        if scenario != '24h' and day_idx in tournament_days and tournament_runs > 0:
            tourn_dur = _tournament_duration()
            if tourn_dur > 0:
                total_tourn_time = tournament_runs * tourn_dur
                if total_tourn_time <= daytime_available:
                    for _ in range(tournament_runs):
                        weekly_schedule.append({
                            'day': day,
                            'time_slot': 'daytime',
                            'tier': f"{tournament_tier}+",
                            'duration': tourn_dur,
                            'coins': 0.0,
                            'cells': 0.0,
                            'shards': 0.0,
                            'waves': 0.0,
                            'score': 0.0,
                            'run_type': 'tournament'
                        })
                    daytime_available -= total_tourn_time

        if scenario == 'custom':
            # Evaluate full-day custom options using multi-run daytime optimization.
            day_runs_std = _build_daytime_runs_bonus_malus(daytime_available)
            night_run_std = _pick_best_overnight_run()

            option_a_score = float('-inf')
            option_a_day_runs: list[dict[str, Any]] = []
            option_a_night_run: dict[str, Any] | None = None
            if required_tier_list:
                option_a_day_runs = _build_daytime_runs_bonus_malus(daytime_available, required=required_tier_list)
                if option_a_day_runs:
                    option_a_night_run = night_run_std
                    option_a_score = sum(float(run.get('score', 0.0) or 0.0) for run in option_a_day_runs)
                    if option_a_night_run is not None:
                        option_a_score += float(option_a_night_run['score'])

            option_b_score = float('-inf')
            option_b_day_runs = day_runs_std
            option_b_night_run: dict[str, Any] | None = None
            if required_tier_list and len(required_tier_list) <= max(1, int(nighttime_max_runs or 1)):
                option_b_night_run = _pick_best_overnight_run(required_tier_list)
                if option_b_night_run is not None:
                    option_b_score = sum(float(run.get('score', 0.0) or 0.0) for run in day_runs_std)
                    option_b_score += float(option_b_night_run['score'])

            chosen_day_runs = day_runs_std
            chosen_night_run = night_run_std
            if option_a_score > float('-inf') or option_b_score > float('-inf'):
                if option_b_score > option_a_score:
                    chosen_day_runs = option_b_day_runs
                    chosen_night_run = option_b_night_run
                else:
                    chosen_day_runs = option_a_day_runs
                    chosen_night_run = option_a_night_run

            for run in chosen_day_runs:
                weekly_schedule.append({
                    'day': day,
                    'time_slot': 'daytime',
                    'tier': run['tier'],
                    'duration': run['duration'],
                    'coins': run['coins'],
                    'cells': run['cells'],
                    'shards': run['shards'],
                    'waves': run.get('waves', 0.0),
                    'score': run['score'],
                    'run_type': run['run_type'],
                })

            if chosen_night_run is not None and overnight_hours > 0:
                weekly_schedule.append({
                    'day': day,
                    'time_slot': 'overnight',
                    'tier': chosen_night_run['tier'],
                    'duration': chosen_night_run['duration'],
                    'coins': chosen_night_run['coins'],
                    'cells': chosen_night_run['cells'],
                    'shards': chosen_night_run['shards'],
                    'waves': chosen_night_run.get('waves', 0.0),
                    'score': chosen_night_run['score'],
                    'run_type': chosen_night_run['run_type'],
                })
                if float(chosen_night_run['duration']) > overnight_hours:
                    time_remaining = float(chosen_night_run['duration']) - overnight_hours
                else:
                    time_remaining = 0.0
            else:
                time_remaining = 0.0
            continue

        if scenario == 'daynight':
            # Daytime objective: maximize coins/hour while packing runs that fit the window.
            chosen_day_runs = _build_daytime_runs_bonus_malus(daytime_available)
            # Nighttime objective: maximize overnight coins while penalizing spillover into next daytime.
            chosen_night_run = _pick_best_overnight_run()

            for run in chosen_day_runs:
                weekly_schedule.append({
                    'day': day,
                    'time_slot': 'daytime',
                    'tier': run['tier'],
                    'duration': run['duration'],
                    'coins': run['coins'],
                    'cells': run['cells'],
                    'shards': run['shards'],
                    'waves': run.get('waves', 0.0),
                    'score': run['score'],
                    'run_type': run['run_type'],
                })

            if chosen_night_run is not None and overnight_hours > 0:
                weekly_schedule.append({
                    'day': day,
                    'time_slot': 'overnight',
                    'tier': chosen_night_run['tier'],
                    'duration': chosen_night_run['duration'],
                    'coins': chosen_night_run['coins'],
                    'cells': chosen_night_run['cells'],
                    'shards': chosen_night_run['shards'],
                    'waves': chosen_night_run.get('waves', 0.0),
                    'score': chosen_night_run['score'],
                    'run_type': chosen_night_run['run_type'],
                })
                if float(chosen_night_run['duration']) > overnight_hours:
                    time_remaining = float(chosen_night_run['duration']) - overnight_hours
                else:
                    time_remaining = 0.0
            else:
                time_remaining = 0.0
            continue

        # Custom mode: force at least one required-tier daytime run per day when feasible.
        if scenario == 'custom' and daytime_available > 0 and required_cycle:
            ordered_required = required_cycle[required_cycle_idx:] + required_cycle[:required_cycle_idx]
            forced_choice = None
            forced_score = -1.0
            for req_tier in ordered_required:
                tier_key = float(req_tier)
                if tier_key not in grouped.index:
                    continue
                score, duration, coins, cells, shards, waves = _tier_score(tier_key)
                if duration <= daytime_available and score > forced_score:
                    forced_score = score
                    forced_choice = (req_tier, duration, coins, cells, shards, waves, score)

            if forced_choice is not None:
                req_tier, duration, coins, cells, shards, waves, forced_score = forced_choice
                weekly_schedule.append({
                    'day': day,
                    'time_slot': 'daytime',
                    'tier': int(req_tier),
                    'duration': duration,
                    'coins': coins,
                    'cells': cells,
                    'shards': shards,
                    'waves': waves,
                    'score': forced_score,
                    'run_type': 'farming'
                })
                daytime_available -= duration
                last_daytime_tier = float(req_tier)
                required_placed_today = True
                if req_tier in required_cycle:
                    required_cycle_idx = (required_cycle.index(req_tier) + 1) % len(required_cycle)
        
        # Optimize daytime runs - prevent same tier from repeating consecutively
        while daytime_available > 0:
            available_tiers = [t for t in grouped.index]
            best_score = 0.0
            best_tier = None
            best_data = None
            best_rank_value = 0.0
            
            # Find the best run that fits in remaining daytime
            for tier in available_tiers:
                # Skip the same tier if it was just added (prevent consecutive duplicates)
                if scenario != '24h' and tier == last_daytime_tier:
                    continue
                score, duration, coins, cells, shards, waves = _tier_score(tier)
                if duration <= daytime_available:
                    # In 24h mode pick best score/hour; in other modes keep best total run score.
                    rank_value = (score / duration) if (scenario == '24h' and duration > 0) else score
                    if rank_value > best_rank_value:
                        best_rank_value = rank_value
                        best_score = score
                        best_tier = tier
                        best_data = (duration, coins, cells, shards, waves)

            # 24h mode: if nothing fits in remaining hours, allow best tier to spill into next day.
            if scenario == '24h' and best_tier is None:
                for tier in available_tiers:
                    score, duration, coins, cells, shards, waves = _tier_score(tier)
                    if duration <= 0:
                        continue
                    rank_value = score / duration
                    if rank_value > best_rank_value:
                        best_rank_value = rank_value
                        best_score = score
                        best_tier = tier
                        best_data = (duration, coins, cells, shards, waves)
            
            if best_tier is not None and best_data is not None:
                duration, coins, cells, shards, waves = best_data
                weekly_schedule.append({
                    'day': day,
                    'time_slot': 'daytime',
                    'tier': int(best_tier),
                    'duration': duration,
                    'coins': coins,
                    'cells': cells,
                    'shards': shards,
                    'waves': waves,
                    'score': best_score,
                    'run_type': 'farming'
                })
                last_daytime_tier = best_tier
                if scenario == '24h' and duration > daytime_available:
                    # Carry over unfinished runtime into the next day for continuous 24h operation.
                    time_remaining = duration - daytime_available
                    daytime_available = 0.0
                else:
                    daytime_available -= duration
            else:
                # No more runs fit in remaining daytime
                break
        
        if scenario != '24h' and overnight_hours > 0:
            # Optimize overnight run (allow spillover into next morning)
            available_tiers = [t for t in grouped.index]
            best_score = 0.0
            best_tier = None
            best_data = None

            # Custom mode fallback: ensure at least one required tier is started each day.
            if scenario == 'custom' and (not required_placed_today) and required_tier_today is not None:
                required_key = float(required_tier_today)
                if required_key in grouped.index:
                    forced_score, forced_duration, forced_coins, forced_cells, forced_shards, forced_waves = _tier_score(required_key)
                    if forced_duration > 0:
                        best_score = forced_score
                        best_tier = required_key
                        best_data = (forced_duration, forced_coins, forced_cells, forced_shards, forced_waves)

            # For overnight, we can consider runs longer than overnight_hours (with spillover)
            if best_data is None:
                for tier in available_tiers:
                    score, duration, coins, cells, shards, waves = _tier_score(tier)
                    if score > best_score:
                        best_score = score
                        best_tier = tier
                        best_data = (duration, coins, cells, shards, waves)

            if best_tier is not None and best_data is not None:
                duration, coins, cells, shards, waves = best_data
                weekly_schedule.append({
                    'day': day,
                    'time_slot': 'overnight',
                    'tier': int(best_tier),
                    'duration': duration,
                    'coins': coins,
                    'cells': cells,
                    'shards': shards,
                    'waves': waves,
                    'score': best_score,
                    'run_type': 'farming'
                })

                if scenario == 'custom' and required_tier_today is not None and int(best_tier) == int(required_tier_today):
                    required_placed_today = True
                    if required_tier_today in required_cycle:
                        required_cycle_idx = (required_cycle.index(required_tier_today) + 1) % len(required_cycle)

                # Calculate spillover for next day
                if duration > overnight_hours:
                    time_remaining = duration - overnight_hours
                else:
                    time_remaining = 0.0
        else:
            time_remaining = 0.0
    
    # Convert to DataFrame
    schedule_df = pd.DataFrame(weekly_schedule)
    
    # Add start_absolute column for display: calculate cumulative absolute time
    if not schedule_df.empty:
        if scenario == '24h':
            wake_start_time = 0.0
        else:
            wake_start_time = sleep_end if sleep_end > sleep_start else sleep_end + 24.0
            if wake_start_time >= 24.0:
                wake_start_time -= 24.0
        
        start_absolute_list = []
        current_absolute = wake_start_time  # Monday daytime starts at wake_start
        
        for idx, row in schedule_df.iterrows():
            day_name = str(row['day'])
            time_slot = str(row['time_slot'])
            day_idx = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'].index(day_name)
            
            # If this is a new day's daytime, reset to that day's wake time
            if time_slot == 'daytime':
                day_wake = day_idx * 24.0 + wake_start_time
                if current_absolute < day_wake or int(current_absolute // 24.0) < day_idx:
                    current_absolute = day_wake
            elif time_slot == 'overnight':
                # Start overnight as soon as daytime is done (no forced wait until bedtime).
                pass
            
            start_absolute_list.append(current_absolute)
            current_absolute += float(row['duration'])
        
        schedule_df['start_absolute'] = start_absolute_list
    
    # Calculate weekly summary
    weekly_summary = {
        'total_coins': float(schedule_df['coins'].sum()),
        'total_cells': float(schedule_df['cells'].sum()),
        'total_shards': float(schedule_df['shards'].sum()),
        'total_waves': float(schedule_df['waves'].sum()) if 'waves' in schedule_df.columns else 0.0,
        'total_score': float(schedule_df['score'].sum()),
        'total_runs': len(schedule_df),
        'farming_runs': len(schedule_df[schedule_df['run_type'] == 'farming']),
        'tournament_runs': len(schedule_df[schedule_df['run_type'] == 'tournament'])
    }
    
    return {
        'weekly_schedule': schedule_df,
        'weekly_summary': weekly_summary
    }


def build_score_reference_table(df: pd.DataFrame) -> go.Figure:
    """Build a diagnostic table showing tier, duration (ci_upper), score (mean), and score/hour for reference."""
    # Clean and pivot similar to optimize_runs setup
    df_clean = df.copy()
    df_clean['real_time'] = df_clean['real_time'].apply(lambda x: float(str(x).replace('h', '').strip()))
    df_clean['score'] = pd.to_numeric(df_clean['score'], errors='coerce')
    df_clean = df_clean.dropna(subset=['real_time', 'score'])

    grouped = df_clean.pivot(index='tier', columns='level_1')
    durations = grouped['real_time']['ci_upper'].values
    scores = grouped['score']['mean'].values
    tiers = grouped.index.tolist()

    # Build rows for the table
    rows = []
    for i, tier in enumerate(tiers):
        dur = float(durations[i])
        sc = float(scores[i])
        score_per_hour = sc / dur if dur > 0 else 0.0
        rows.append({
            'Tier': f"Tier {tier}",
            'Duration (ci_upper)': f"{dur:.2f} h",
            'Score (mean)': f"{sc:.2f}",
            'Score/Hour': f"{score_per_hour:.2f}"
        })
    
    ref_df = pd.DataFrame(rows)
    fig = go.Figure(data=[go.Table(
        header=dict(
            values=list(ref_df.columns),
            fill_color=colors.get('secondary_bg', '#202128'),
            align='center',
            font=dict(color=colors.get('text', '#FAFAFA'), size=12)
        ),
        cells=dict(
            values=[ref_df[col] for col in ref_df.columns],
            fill_color=colors.get('card', '#0C0D10'),
            align='center',
            font=dict(color=colors.get('text', '#FAFAFA'), size=11)
        )
    )])
    fig.update_layout(
        plot_bgcolor=colors.get('background', '#000000'),
        paper_bgcolor=colors.get('background', '#000000'),
        font_color=colors.get('text', '#FAFAFA'),
        margin=dict(l=10, r=10, t=20, b=10)
    )
    return fig


def compute_time_stats(df: pd.DataFrame, daytime: int, time_series_df: Optional[pd.DataFrame] = None) -> dict[str, float]:
    """Compute time utilization metrics based on optimized schedules.

    Returns:
    - day_used_hours: hours used by optimized daytime schedule
    - night_used_hours: hours used by optimized nighttime schedule
    - combined_used_hours: day + night used hours
    - overnight_available_hours: 24 - day_used_hours
    - free_hours: 24 - (day_used_hours + night_used_hours)
    """
    res = generate_optimize_df(df, daytime, time_series_df)
    return {
        'day_used_hours': float(cast(float, res.get('day_used_hours', 0.0))),
        'night_used_hours': float(cast(float, res.get('night_used_hours', 0.0))),
        'combined_used_hours': float(cast(float, res.get('combined_used_hours', 0.0))),
        'overnight_available_hours': float(cast(float, res.get('overnight_available_hours', 0.0))),
        'free_hours': float(cast(float, res.get('free_hours', 0.0))),
    }


def optimize_table(df: pd.DataFrame, daytime: int, time_series_df: Optional[pd.DataFrame] = None) -> Tuple[go.Figure, go.Figure]:
    # Get raw DataFrames for scenarios
    result = generate_optimize_df(df, daytime, time_series_df)

    # Create summary with three scenarios
    summary_24 = cast(pd.DataFrame, result['summary_24h']).copy()
    summary_24['scenario'] = '24h Optimal'
    
    summary_combined = cast(pd.DataFrame, result['summary_combined']).copy()
    summary_combined['scenario'] = f'Day+Night ({daytime}h+{24-daytime}h)'
    
    summary_current = cast(pd.DataFrame, result['summary_current']).copy()
    summary_current['scenario'] = 'Current'
    
    summary_df = pd.concat([summary_24, summary_combined, summary_current], ignore_index=True)

    # Create breakdown with three scenarios
    breakdown_24 = cast(pd.DataFrame, result['breakdown_24h']).copy()
    breakdown_24['scenario'] = '24h Optimal'
    
    breakdown_combined = cast(pd.DataFrame, result['breakdown_combined']).copy()
    breakdown_combined['scenario'] = f'Day+Night ({daytime}h+{24-daytime}h)'
    
    breakdown_current = cast(pd.DataFrame, result['breakdown_current']).copy()
    breakdown_current['scenario'] = 'Current'
    
    breakdown_df = pd.concat([breakdown_24, breakdown_combined, breakdown_current], ignore_index=True)


    # Combine them with keys
    #summary_df = pd.concat([summary_dt, summary_nt, summary_24], keys=['daytime', 'nighttime', '24h']).reset_index().rename(columns={'level_0': 'scenario'})
    #breakdown_df = pd.concat([breakdown_dt, breakdown_nt, breakdown_24], keys=['daytime', 'nighttime', '24h']).reset_index().rename(columns={'level_0': 'scenario'})
    summary_df = apply_abbreviation(summary_df, ['coins_earned', 'cells_earned', 'reroll_shards_earned'])
    breakdown_df = apply_abbreviation(breakdown_df, ['duration_per_run', 'total_duration'], suffix_format=" {unit} h")

    #  Transform summary_df to formatted style
    formatted_rows = []
    for scenario, group in summary_df.groupby('scenario'):
        # defensive: ensure the expected confidence rows exist
        mean_row = group[group['confidence'] == 'mean']
        lower_row = group[group['confidence'] == 'ci_lower']
        upper_row = group[group['confidence'] == 'ci_upper']
        if mean_row.empty or lower_row.empty or upper_row.empty:
            # skip incomplete scenario
            continue
        mean_row = mean_row.iloc[0]
        lower_row = lower_row.iloc[0]
        upper_row = upper_row.iloc[0]

        coins_summary = f"{mean_row['coins_earned']} <br> ({lower_row['coins_earned']} ... {upper_row['coins_earned']})"
        cells_summary = f"{mean_row['cells_earned']} <br> ({lower_row['cells_earned']} ... {upper_row['cells_earned']})"
        shards_summary = f"{mean_row['reroll_shards_earned']} <br> ({lower_row['reroll_shards_earned']} ... {upper_row['reroll_shards_earned']})"

        formatted_rows.append({
            'scenario': scenario,
            'coins_earned': coins_summary,
            'cells_earned': cells_summary,
            'reroll_shards_earned': shards_summary
        })

    formatted_summary_df = pd.DataFrame(formatted_rows)

    # If no valid formatted summary rows were produced, create a safe fallback
    if formatted_summary_df.empty:
        # Build an empty optimize figure or use breakdown if available
        if not breakdown_df.empty and 'scenario' in breakdown_df.columns:
            try:
                optimize_df = breakdown_df.set_index('scenario').transpose().reset_index()
                optimize_figure = go.Figure(data=[go.Table(
                    header=dict(values=list(optimize_df.columns)),
                    cells=dict(values=[optimize_df[col] for col in optimize_df.columns])
                )])
            except Exception:
                optimize_figure = go.Figure()
        else:
            optimize_figure = go.Figure()

        # create a simple summary table as well (empty)
        summary_fig = go.Figure(data=[go.Table(header=dict(values=[]), cells=dict(values=[]))])
        return summary_fig, optimize_figure

    #  Create Plotly tables
    summary_fig = go.Figure(data=[go.Table(
        header=dict(values=list(formatted_summary_df.columns), align='center'),
        cells=dict(values=[formatted_summary_df[col] for col in formatted_summary_df.columns], align='center')
    )])

    breakdown_fig = go.Figure(data=[go.Table(
        header=dict(values=list(breakdown_df.columns)),
        cells=dict(values=[breakdown_df[col] for col in breakdown_df.columns])
    )])

    optimize_df = pd.merge(formatted_summary_df, breakdown_df, left_on='scenario', right_on='scenario', how='outer')
    # Only drop 'level_1' if it exists (some breakdowns may not include it)
    if 'level_1' in optimize_df.columns:
        optimize_df = optimize_df.drop(columns=['level_1'])
    optimize_df = optimize_df.set_index('scenario').transpose().reset_index()
    optimize_figure = go.Figure(data=[go.Table(
        header=dict(values=list(optimize_df.columns)),
        cells=dict(
            values=[optimize_df[col] for col in optimize_df.columns],
            align='left',
            font=dict(size=11)
        )
    )])

    return summary_fig, optimize_figure


def get_smoothed_daily_data(df: pd.DataFrame, metric: str, window_days: float = 3.0) -> pd.DataFrame:
    """
    Get smoothed daily data for a single metric using the same logic as Daily Results chart.
    This ensures consistency between Daily Results and Forecast pages.
    
    Args:
        df: Raw dataframe with timestamp and metric columns
        metric: The metric name to process
        window_days: The window size in days for exponential weighting (default: 3.0)
    
    Returns:
        DataFrame with columns: timestamp, mean, lower, upper
        Empty DataFrame if insufficient data
    """
    if 'timestamp' not in df.columns or metric not in df.columns:
        return pd.DataFrame()
    
    # Aggregate to daily values (exact same logic as continuous_metrics_figure)
    ts = pd.to_datetime(df['timestamp'], errors='coerce').dt.tz_localize(None)
    vals = pd.to_numeric(df[metric], errors='coerce')
    base = pd.DataFrame({'timestamp': ts.dt.normalize(), metric: vals})
    
    # Decide aggregation per metric
    abs_metrics = {'coins_earned', 'cells_earned', 'reroll_shards_earned', 'waves_per_tier'}
    rate_metrics = {'coins_per_hour', 'cells_per_hour', 'reroll_shards_per_hour', 'waves_per_hour'}
    
    if metric in abs_metrics:
        daily_df = base.dropna().groupby('timestamp', as_index=False)[metric].sum()
    elif metric in rate_metrics:
        if 'real_time' in df.columns:
            weights = pd.to_numeric(df['real_time'], errors='coerce')
            tmp = pd.DataFrame({'timestamp': ts.dt.normalize(), metric: vals, 'w': weights})
            tmp = tmp.dropna()
            # Time-weighted daily mean of per-hour metrics (vectorized, no .apply)
            safe_w = tmp['w'].clip(lower=0.0).replace([np.inf, -np.inf], np.nan).fillna(0.0)
            tmp = tmp.assign(w_safe=safe_w, wx=tmp[metric] * safe_w)
            grp = (
                tmp.groupby('timestamp', as_index=False)
                .agg(wx_sum=('wx', 'sum'), w_sum=('w_safe', 'sum'), mean_val=(metric, 'mean'))
            )
            grp[metric] = np.where(grp['w_sum'] > 0, grp['wx_sum'] / grp['w_sum'], grp['mean_val'])
            daily_df = grp[['timestamp', metric]]
        else:
            daily_df = base.dropna().groupby('timestamp', as_index=False)[metric].mean()
    else:
        daily_df = base.dropna().groupby('timestamp', as_index=False)[metric].mean()
    
    # Normalize type to DataFrame with required columns
    if isinstance(daily_df, pd.Series):
        daily_df = daily_df.to_frame(name=metric).reset_index()
    daily_df = daily_df[['timestamp', metric]].copy()
    
    if daily_df.empty:
        return pd.DataFrame()
    
    # Compute continuous stats on the daily series (exponential smoothing)
    from functions.statistics import TimeSeriesStats
    stats_daily = TimeSeriesStats(daily_df, None)
    stats_df = stats_daily.compute_continuous_stats(metric, window_days=window_days)
    
    return stats_df


def continuous_metrics_figure(df: pd.DataFrame, window_days: float = 3.0) -> go.Figure:
    """
    Creates a figure with continuous error bands for key metrics over time.
    Shows both absolute and per-hour metrics.
    
    Args:
        df: DataFrame with the time series data
        window_days: The window size in days for exponential weighting (default: 3.0)
    """
    metrics = [
        'coins_earned', 'cells_earned', 'reroll_shards_earned',
        'coins_per_hour', 'cells_per_hour', 'reroll_shards_per_hour'
    ]
    
    titles = [display_name(m) for m in metrics]
    fig = create_subplots_grid(
        rows=2,
        cols=3,
        subplot_titles=titles,
        x_title="Time",
        y_title="Value",
        vertical_spacing=0.06,
        horizontal_spacing=0.04
    )
    
    metric_ranges = {}  # Track min/max for each metric subplot
    
    # Create continuous error bands for each metric
    for idx, metric in enumerate(metrics):
        row = idx // 3 + 1
        col = idx % 3 + 1
        
        # Build daily aggregates for this metric
        if 'timestamp' not in df.columns or metric not in df.columns:
            continue

        ts = pd.to_datetime(df['timestamp'], errors='coerce').dt.tz_localize(None)
        vals = pd.to_numeric(df[metric], errors='coerce')
        base = pd.DataFrame({'timestamp': ts.dt.normalize(), metric: vals})

        # Decide aggregation per metric
        abs_metrics = {'coins_earned', 'cells_earned', 'reroll_shards_earned'}
        rate_metrics = {'coins_per_hour', 'cells_per_hour', 'reroll_shards_per_hour', 'waves_per_hour'}

        if metric in abs_metrics:
            daily_df = base.dropna().groupby('timestamp', as_index=False)[metric].sum()
        elif metric in rate_metrics:
            if 'real_time' in df.columns:
                weights = pd.to_numeric(df['real_time'], errors='coerce')
                tmp = pd.DataFrame({'timestamp': ts.dt.normalize(), metric: vals, 'w': weights})
                tmp = tmp.dropna()
                # Time-weighted daily mean of per-hour metrics (vectorized, no .apply)
                safe_w = tmp['w'].clip(lower=0.0).replace([np.inf, -np.inf], np.nan).fillna(0.0)
                tmp = tmp.assign(w_safe=safe_w, wx=tmp[metric] * safe_w)
                grp = (
                    tmp.groupby('timestamp', as_index=False)
                    .agg(wx_sum=('wx', 'sum'), w_sum=('w_safe', 'sum'), mean_val=(metric, 'mean'))
                )
                grp[metric] = np.where(grp['w_sum'] > 0, grp['wx_sum'] / grp['w_sum'], grp['mean_val'])
                daily_df = grp[['timestamp', metric]]
            else:
                daily_df = base.dropna().groupby('timestamp', as_index=False)[metric].mean()
        else:
            daily_df = base.dropna().groupby('timestamp', as_index=False)[metric].mean()

        # Normalize type to DataFrame with required columns
        if isinstance(daily_df, pd.Series):
            daily_df = daily_df.to_frame(name=metric).reset_index()
        daily_df = daily_df[['timestamp', metric]].copy()

        if daily_df.empty:
            continue

        # Debug: report missing days since Aug 12, 2025
        if not daily_df.empty and idx == 0:  # Only print once (first metric)
            cutoff_date = pd.Timestamp('2025-08-12').normalize()
            all_dates = daily_df['timestamp'].sort_values()
            date_range = pd.date_range(start=all_dates.min(), end=all_dates.max(), freq='D')
            present_dates = set(pd.to_datetime(daily_df['timestamp']).dt.floor('D'))
            missing_dates = [d for d in date_range if d not in present_dates and d >= cutoff_date]
            if missing_dates and DEBUG:
                print(f"\n=== Missing data days since Aug 12, 2025 ===")
                for d in missing_dates:
                    print(f"  {d.strftime('%Y-%m-%d')}")
                print(f"Total missing: {len(missing_dates)} days\n")

        # Compute continuous stats on the daily series
        stats_daily = TimeSeriesStats(daily_df, None)
        stats_df = stats_daily.compute_continuous_stats(metric, window_days=window_days)
        if stats_df.empty:
            continue
            
        color = get_color_for_metric(metric)

        # Add faint background bars from daily aggregates (uniform near-1-day widths)
        day_ms = 24 * 60 * 60 * 1000
        if not daily_df.empty:
            fig.add_trace(
                go.Bar(
                    name=f'{display_name(metric)} (daily)',
                    x=daily_df['timestamp'],
                    y=daily_df[metric],
                    width=[int(day_ms * 1.0)] * len(daily_df),
                    marker=dict(color='rgba(255,255,255,0.08)', line=dict(width=0)),
                    hoverinfo='skip',
                    showlegend=False,
                ),
                row=row, col=col
            )
        
        # Clamp ci_lower for presentation and build hover text with CI info
        ci_lower_clamped = stats_df['ci_lower'].clip(lower=0.0)
        
        # Track data range for this metric (for custom tick formatting)
        y_values = list(ci_lower_clamped) + list(stats_df['ci_upper'])
        y_values = [v for v in y_values if v is not None and not np.isnan(v)]
        if y_values:
            metric_ranges[(row, col)] = (min(y_values), max(y_values))
        
        ts_str = pd.to_datetime(stats_df['timestamp']).dt.strftime('%Y-%m-%d')
        hover_text = [
            f"{d}<br>Mean: {format_display_value(float(m))}<br>CI: [{format_display_value(float(l))}, {format_display_value(float(u))}]"
            for d, m, l, u in zip(ts_str, stats_df['mean'], ci_lower_clamped, stats_df['ci_upper'])
        ]

        # Add upper CI boundary first.
        fig.add_trace(
            go.Scatter(
                name=f'{metric} (upper)',
                x=stats_df['timestamp'],
                y=stats_df['ci_upper'],
                mode='lines',
                line=dict(color=get_rgba(color, 0.6), width=1.1),
                legendgroup=metric,
                showlegend=False,
                hoverinfo='skip'
            ),
            row=row, col=col
        )

        # Add lower CI boundary with fill to upper CI trace.
        fig.add_trace(
            go.Scatter(
                name=f'{metric} (lower)',
                x=stats_df['timestamp'],
                y=ci_lower_clamped,
                mode='lines',
                line=dict(color=get_rgba(color, 0.6), width=1.1),
                fillcolor=get_rgba(color, 0.28),
                fill='tonexty',  # Fill to next trace above
                legendgroup=metric,
                showlegend=False,
                hoverinfo='skip'
            ),
            row=row, col=col
        )

        # Add mean line last so it stays visually on top of the confidence band.
        fig.add_trace(
            go.Scatter(
                name=f'{display_name(metric)} (mean)',
                x=stats_df['timestamp'],
                y=stats_df['mean'],
                mode='lines',
                line=dict(color=color, width=2.4),
                legendgroup=metric,
                showlegend=True,
                hovertext=hover_text,
                hoverinfo='text'
            ),
            row=row, col=col
        )
    
    fig.update_layout(
        height=800,
        showlegend=False,
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text'],
        margin=dict(l=10, r=10, t=40, b=10),
        bargap=0.0,
        bargroupgap=0.0,
        barmode='overlay',
        legend=dict(
            yanchor="top",
            y=0.99,
            xanchor="right",
            x=0.99,
            bgcolor="rgba(0,0,0,0.5)"
        )
    )
    
    # Format axes (no per-axis title to avoid double "Time" with global x_title)
    fig.update_xaxes(
        showgrid=True,
        gridcolor='rgba(255,255,255,0.18)',
        layer='below traces',
        rangeslider_visible=False,
        showspikes=True,
        spikethickness=1,
        spikecolor='gray',
        spikedash='dot'
    )
    
    # Apply custom abbreviated ticks to each subplot based on its data range
    for (subplot_row, subplot_col), (min_val, max_val) in metric_ranges.items():
        tickvals, ticktext = generate_abbreviation_ticks(min_val, max_val, num_ticks=5)
        fig.update_yaxes(
            tickvals=tickvals,
            ticktext=ticktext,
            showgrid=True,
            gridcolor='rgba(255,255,255,0.18)',
            layer='below traces',
            zeroline=True,
            zerolinecolor='white',
            showspikes=True,
            spikethickness=1,
            spikecolor='gray',
            spikedash='dot',
            range=[0, max_val * 1.05],
            row=subplot_row,
            col=subplot_col
        )

    # Enforce grid layer on every axis (xaxis/xaxis2/... and yaxis/yaxis2/...) so
    # subplot/template defaults cannot bring grid lines in front of traces.
    fig.for_each_xaxis(lambda axis: axis.update(layer='below traces'))
    fig.for_each_yaxis(lambda axis: axis.update(layer='below traces'))
    
    return fig

def optimize_figure(df: pd.DataFrame, daytime: int, time_series_df: Optional[pd.DataFrame] = None, 
                    all_runs_time_series_df: Optional[pd.DataFrame] = None, current_days: int = 3,
                    nighttime_max_runs: int = 1, required_tiers: Optional[list[int]] = None,
                    tournament_runs: int = 2, tournament_tier: int = 12, 
                    show_time_allocation: bool = True, show_tournament: bool = True,
                    precomputed_result: Optional[dict[str, Any]] = None) -> tuple[go.Figure, Optional[str]]:
    """
    Creates optimizer visualization with:
    - 4 subplots with error bars for coins, cells, reroll shards, and score
    - 1 subplot with stacked bar chart showing time allocation by tier (optional)
    
    Args:
        df: Optimizer data
        daytime: Daytime hours
        time_series_df: Time series data (farming/overnight only) for 24h and Day+Night scenarios
        all_runs_time_series_df: Time series data including all run types (tournament, quit, milestone) for Current scenario
        current_days: Number of days to look back for current scenario (default 3)
        nighttime_max_runs: Maximum runs allowed during nighttime (default 1)
        required_tiers: List of tiers that must each appear at least once (optional)
        show_time_allocation: Whether to show the time allocation subplot (default True)
        show_tournament: Whether to show the tournament scenario (default True)
        
    Returns:
        Tuple of (figure, warning_message)
    """
    import time
    t_start = time.perf_counter()
    result = precomputed_result if precomputed_result is not None else generate_optimize_df(
        df,
        daytime,
        time_series_df,
        all_runs_time_series_df,
        current_days=current_days,
        nighttime_max_runs=nighttime_max_runs,
        required_tiers=required_tiers,
        tournament_runs=tournament_runs,
        tournament_tier=tournament_tier,
    )
    t_end = time.perf_counter()
    # print(f"[OPTIMIZER TIMING] optimize_figure total: {t_end - t_start:.3f}s")
    
    # Check for error from custom tier optimization
    warning_message = None
    if isinstance(result, dict) and 'error' in result:
        warning_message = result['error']
        # Return empty figure with warning
        fig = go.Figure()
        fig.update_layout(
            title="Optimizer Error",
            plot_bgcolor=colors['background'],
            paper_bgcolor=colors['background'],
            font_color=colors['text']
        )
        return fig, warning_message

    # Create summary with scenarios (3 or 4 depending on whether Custom is available)
    summary_24 = cast(pd.DataFrame, result['summary_24h']).copy()
    summary_24['scenario'] = '24h'
    
    summary_combined = cast(pd.DataFrame, result['summary_combined']).copy()
    summary_combined['scenario'] = 'Day+Night'
    
    summary_tournament = cast(pd.DataFrame, result['summary_tournament']).copy()
    has_tournament = not summary_tournament.empty
    if has_tournament:
        summary_tournament['scenario'] = 'Tournament'
    
    summary_custom = cast(pd.DataFrame, result['summary_custom']).copy()
    has_custom = not summary_custom.empty
    if has_custom:
        summary_custom['scenario'] = 'Custom'
    
    summary_current = cast(pd.DataFrame, result['summary_current']).copy()
    summary_current['scenario'] = 'Current'
    
    # Concatenate all scenarios (Tournament conditionally shown, Custom only if specified)
    scenarios_to_concat = [summary_24, summary_combined]
    if has_tournament and show_tournament:
        scenarios_to_concat.append(summary_tournament)
    if has_custom:
        scenarios_to_concat.append(summary_custom)
    scenarios_to_concat.append(summary_current)
    summary_df = pd.concat(scenarios_to_concat, ignore_index=True)

    # print("=== optimize_figure: summary_df ===")
    # print(summary_df)
    # print("Columns:", summary_df.columns.tolist())
    # print("Scenario labels:", summary_df['scenario'].unique() if 'scenario' in summary_df.columns else 'NO SCENARIO COLUMN')
    # print("====================================")
    
    # Get breakdown for time visualization
    breakdown_24 = cast(pd.DataFrame, result['breakdown_24h']).copy()
    breakdown_combined = cast(pd.DataFrame, result['breakdown_combined']).copy()
    breakdown_tournament = cast(pd.DataFrame, result['breakdown_tournament']).copy() if has_tournament else pd.DataFrame()
    breakdown_custom = cast(pd.DataFrame, result['breakdown_custom']).copy() if has_custom else pd.DataFrame()
    breakdown_current = cast(pd.DataFrame, result['breakdown_current']).copy()

    # Create subplots: 4 error bars + optional time allocation
    if show_time_allocation:
        fig = create_subplots_grid(
            rows=1, cols=5,
            subplot_titles=['Coins Earned', 'Cells Earned', 'Reroll Shards', 'Score', 'Time Allocation'],
            specs=[[{'type': 'scatter'}, {'type': 'scatter'}, {'type': 'scatter'}, {'type': 'scatter'}, {'type': 'bar'}]],
            horizontal_spacing=0.06
        )
    else:
        fig = create_subplots_grid(
            rows=1, cols=4,
            subplot_titles=['Coins Earned', 'Cells Earned', 'Reroll Shards', 'Score'],
            specs=[[{'type': 'scatter'}, {'type': 'scatter'}, {'type': 'scatter'}, {'type': 'scatter'}]],
            horizontal_spacing=0.08
        )
    
    # Define metrics for the first 4 subplots
    metrics = ['coins_earned', 'cells_earned', 'reroll_shards_earned', 'score']
    colors_list = [colors['coins'], colors['cells'], colors['reroll'], colors['score']]
    
    metric_ranges = {}  # Track min/max for each metric subplot
    
    # Debug: Check what columns are available
    if DEBUG:
        print(f"\n=== DEBUG optimize_figure ===")
        print(f"summary_df columns: {summary_df.columns.tolist()}")
        print(f"summary_df shape: {summary_df.shape}")
        print(f"summary_df scenarios: {summary_df['scenario'].unique().tolist() if 'scenario' in summary_df.columns else 'NO SCENARIO COLUMN'}")
        for scenario in summary_df['scenario'].unique():
            scenario_data = summary_df[summary_df['scenario'] == scenario]
            print(f"\nScenario '{scenario}':")
            print(scenario_data[['confidence', 'coins_earned', 'cells_earned', 'reroll_shards_earned'] + (['score'] if 'score' in scenario_data.columns else [])].to_string())
        print(f"=== END DEBUG ===\n")
    
    # Add error bar traces for each metric
    # Determine which scenarios to plot (Tournament conditionally shown, Custom only if specified)
    scenarios_to_plot = ['24h', 'Day+Night']
    if has_tournament and show_tournament:
        scenarios_to_plot.append('Tournament')
    if has_custom:
        scenarios_to_plot.append('Custom')
    scenarios_to_plot.append('Current')
    
    for idx, (metric, color) in enumerate(zip(metrics, colors_list), 1):
        # Track data range for this metric subplot
        y_values = []
        
        for scenario in scenarios_to_plot:
            scenario_data = summary_df[summary_df['scenario'] == scenario]
            # Only plot if all required confidence rows exist
            if not scenario_data.empty and all(conf in scenario_data['confidence'].values for conf in ['mean', 'ci_lower', 'ci_upper']):
                if metric not in scenario_data.columns:
                    if DEBUG:
                        print(f"WARNING: metric '{metric}' not found in scenario '{scenario}' columns: {scenario_data.columns.tolist()}")
                    continue
                ci_values = get_ci_triplet(scenario_data, metric, level_col='confidence', clamp_lower_zero=False)
                if ci_values is None:
                    continue
                mean_val, lower_val, upper_val = ci_values
                
                # Track y-values for custom ticks
                y_values.extend([lower_val, mean_val, upper_val])
                
                err_minus = mean_val - lower_val
                err_plus = upper_val - mean_val
                factor, unit = common_unit([mean_val, lower_val, upper_val], scale)
                hover_text = (
                    f"Mean: {mean_val / factor:.2f}{unit}<br>"
                    f"CI: [{lower_val / factor:.2f}{unit}, {upper_val / factor:.2f}{unit}]"
                )
                fig.add_trace(
                    go.Scatter(
                        x=[scenario],
                        y=[mean_val],
                        name=scenario,
                        mode='markers',
                        marker=dict(color=color, size=12),
                        error_y=dict(
                            type='data',
                            symmetric=False,
                            array=[err_plus],
                            arrayminus=[err_minus],
                            color=color,
                            width=6,
                            thickness=2
                        ),
                        hovertext=hover_text,
                        hoverinfo='text',
                        showlegend=False,
                        legendgroup=scenario
                    ),
                    row=1, col=idx
                )
            elif not scenario_data.empty and 'note' in scenario_data.columns:
                # Plot a zero marker with a hover note for empty custom scenario
                note = scenario_data['note'].iloc[0]
                fig.add_trace(
                    go.Scatter(
                        x=[scenario],
                        y=[0],
                        name=scenario,
                        mode='markers',
                        marker=dict(color=color, size=12, symbol='x'),
                        hovertext=note,
                        hoverinfo='text',
                        showlegend=False,
                        legendgroup=scenario
                    ),
                    row=1, col=idx
                )
        
        # Store range for this metric and apply custom ticks
        if y_values:
            min_val = min(y_values)
            max_val = max(y_values)
            metric_ranges[idx] = (min_val, max_val)
            tickvals, ticktext = generate_abbreviation_ticks(min_val, max_val, num_ticks=5)
            fig.update_yaxes(
                tickvals=tickvals,
                ticktext=ticktext,
                showgrid=True,
                gridcolor='darkgrey',
                zeroline=True,
                zerolinecolor='white',
                range=[0, max_val * 1.05],
                row=1,
                col=idx
            )
        
        # Remove vertical gridlines for first 4 subplots, keep horizontal gridlines
        fig.update_xaxes(showgrid=False, row=1, col=idx)
        fig.update_yaxes(showgrid=True, gridcolor='darkgrey', zeroline=True, zerolinecolor='white', row=1, col=idx)
    
    # Parse breakdown for time allocation (5th subplot)
    # Parse descriptions like "3 x tier 11 (7.59 h each)" and normalize fractional runs
    import re
    import math
    
    def normalize_runs(count_str, hours_each):
        """
        Normalize fractional runs to integer runs with adjusted duration.
        Example: 1.8 x 10h = 2 x 9h (2 runs of 9 hours each)
        """
        count_float = float(count_str)
        total_hours = count_float * hours_each
        
        # Round to nearest integer count
        count_int = round(count_float)
        if count_int == 0:
            count_int = 1
        
        # Adjust hours per run to maintain total time
        adjusted_hours = total_hours / count_int
        
        return count_int, adjusted_hours
    
    # --- Time Allocation Bar Chart (optional 5th subplot) ---
    if show_time_allocation:
        def create_run_bars(breakdown_df, scenario_name):
            """Create individual bar traces for each run in the breakdown."""
            traces = []
            run_counter = 1
            if breakdown_df is None or breakdown_df.empty:
                return traces
            for _, row in breakdown_df.iterrows():
                desc = row.get('description', '')
                run_type = row.get('run_type', 'farming') if 'run_type' in breakdown_df.columns else 'farming'
                if pd.isna(run_type) or str(run_type).strip() == '':
                    run_type = 'farming'
                has_structured = all(col in breakdown_df.columns for col in ['runs', 'duration_per_run', 'tier'])
                if has_structured and pd.notna(row.get('runs')) and pd.notna(row.get('duration_per_run')):
                    count_str = str(row.get('runs'))
                    hours_each = float(row.get('duration_per_run'))
                    count_float = float(count_str)
                    tier_val = row.get('tier')
                    tier_label = str(tier_val)
                    try:
                        tier_num = int(tier_val) if str(tier_val).isdigit() else None
                    except Exception:
                        tier_num = None
                    if scenario_name == 'Current':
                        full_runs = int(math.floor(count_float))
                        remainder = count_float - full_runs
                        for _ in range(full_runs):
                            traces.append({
                                'scenario': scenario_name,
                                'run_id': f'Run {run_counter}',
                                'tier': tier_label,
                                'tier_num': tier_num,
                                'run_type': run_type,
                                'hours': hours_each
                            })
                            run_counter += 1
                        if remainder > 1e-6:
                            traces.append({
                                'scenario': scenario_name,
                                'run_id': f'Run {run_counter} (partial)',
                                'tier': tier_label,
                                'tier_num': tier_num,
                                'run_type': run_type,
                                'hours': hours_each * remainder
                            })
                            run_counter += 1
                    else:
                        count_normalized, hours_normalized = normalize_runs(count_str, hours_each)
                        for _ in range(count_normalized):
                            traces.append({
                                'scenario': scenario_name,
                                'run_id': f'Run {run_counter}',
                                'tier': tier_label,
                                'tier_num': tier_num,
                                'run_type': run_type,
                                'hours': hours_normalized
                            })
                            run_counter += 1
                else:
                    match = re.match(r'(\d+(?:\.\d+)?) x tier ([0-9.+-]+) \(([0-9.]+) h each\)', desc)
                    if match:
                        count_str, tier, hours_each_str = match.groups()
                        hours_each = float(hours_each_str)
                        count_float = float(count_str)
                        tier_label = str(tier)
                        try:
                            tier_num = int(tier) if str(tier).isdigit() else None
                        except Exception:
                            tier_num = None
                        if scenario_name == 'Current':
                            full_runs = int(math.floor(count_float))
                            remainder = count_float - full_runs
                            for _ in range(full_runs):
                                traces.append({
                                    'scenario': scenario_name,
                                    'run_id': f'Run {run_counter}',
                                    'tier': tier_label,
                                    'tier_num': tier_num,
                                    'run_type': run_type,
                                    'hours': hours_each
                                })
                                run_counter += 1
                            if remainder > 1e-6:
                                traces.append({
                                    'scenario': scenario_name,
                                    'run_id': f'Run {run_counter} (partial)',
                                    'tier': tier_label,
                                    'tier_num': tier_num,
                                    'run_type': run_type,
                                    'hours': hours_each * remainder
                                })
                                run_counter += 1
                        else:
                            count_normalized, hours_normalized = normalize_runs(count_str, hours_each)
                            for _ in range(count_normalized):
                                traces.append({
                                    'scenario': scenario_name,
                                    'run_id': f'Run {run_counter}',
                                    'tier': tier_label,
                                    'tier_num': tier_num,
                                    'run_type': run_type,
                                    'hours': hours_normalized
                                })
                                run_counter += 1
                    elif desc:
                        traces.append({
                            'scenario': scenario_name,
                            'run_id': f'Run {run_counter} (partial)',
                            'tier': None,
                            'tier_num': None,
                            'run_type': run_type,
                            'hours': None,
                            'desc': desc
                        })
                    run_counter += 1
            return traces

        # Collect all run data for each scenario
        all_run_data = []
        all_run_data.extend(create_run_bars(breakdown_24, '24h'))
        all_run_data.extend(create_run_bars(breakdown_combined, 'Day+Night'))
        if has_tournament and show_tournament:
            all_run_data.extend(create_run_bars(breakdown_tournament, 'Tournament'))
        if has_custom:
            all_run_data.extend(create_run_bars(breakdown_custom, 'Custom'))
        all_run_data.extend(create_run_bars(breakdown_current, 'Current'))

        # Debug: Print all run_type values and breakdown_current for diagnosis
        if all_run_data:
            runs_df_debug = pd.DataFrame(all_run_data)
            print("[DEBUG] Time Allocation - all_run_data run_types:", runs_df_debug['run_type'].unique().tolist() if 'run_type' in runs_df_debug.columns else 'NO run_type')
            print("[DEBUG] Time Allocation - breakdown_current:")
            print(breakdown_current)

        if all_run_data:
            runs_df = pd.DataFrame(all_run_data)
            runs_df = runs_df[runs_df['hours'].notnull()]
            # Add buffer bars per scenario (24h minus used hours)
            for scenario_name in runs_df['scenario'].unique().tolist():
                scenario_used = float(runs_df[runs_df['scenario'] == scenario_name]['hours'].sum())
                buffer_hours = max(0.0, 24.0 - scenario_used)
                if buffer_hours > 1e-6:
                    runs_df = pd.concat([
                        runs_df,
                        pd.DataFrame([{
                            'scenario': scenario_name,
                            'run_id': 'Buffer',
                            'tier': 'Buffer',
                            'tier_num': None,
                            'run_type': 'buffer',
                            'hours': buffer_hours
                        }])
                    ], ignore_index=True)

            x_order = ['24h', 'Day+Night']
            if has_tournament and show_tournament:
                x_order.append('Tournament')
            if has_custom:
                x_order.append('Custom')
            x_order.append('Current')
            runs_df['scenario'] = pd.Categorical(runs_df['scenario'], categories=x_order, ordered=True)

            def get_color(run_type, tier_num):
                if run_type == 'quit':
                    greys = ['#d1d5db', '#9ca3af', '#6b7280', '#4b5563', '#374151', '#1f2937']
                    idx = (tier_num or 0) % len(greys)
                    return greys[idx]
                if run_type == 'milestone':
                    oranges = ['#fdba74', '#fb923c', '#f97316', '#ea580c', '#c2410c', '#9a3412']
                    idx = (tier_num or 0) % len(oranges)
                    return oranges[idx]
                if run_type == 'tournament':
                    return '#991b1b'
                if run_type == 'buffer':
                    return '#10b981'
                dark_greys = ['#6b7280', '#52525b', '#3f3f46', '#27272a', '#18181b', '#09090b']
                idx = (tier_num or 0) % len(dark_greys)
                return dark_greys[idx]

            runs_df['color'] = runs_df.apply(lambda r: get_color(r['run_type'], int(r['tier_num']) if pd.notnull(r['tier_num']) else 0), axis=1)
            legend_entries = set()
            valid_tiers = set(str(t) for t in breakdown_current['tier'].unique()) if not breakdown_current.empty and 'tier' in breakdown_current.columns else set()
            for _, run in runs_df.iterrows():
                tier_str = str(run['tier'])
                run_type = str(run['run_type'])
                if run_type == 'unknown' and tier_str not in valid_tiers:
                    continue
                if run_type == 'buffer':
                    legend_label = 'Buffer'
                elif tier_str.lower().startswith('tier '):
                    legend_label = f"{run_type.capitalize()}, {tier_str}"
                else:
                    legend_label = f"{run_type.capitalize()}, Tier {tier_str}"
                show_legend = legend_label not in legend_entries
                legend_entries.add(legend_label)
                fig.add_trace(
                    go.Bar(
                        x=[run['scenario']],
                        y=[run['hours']],
                        name=legend_label,
                        marker_color=run['color'],
                        customdata=[[run.get('run_id', ''), tier_str, run_type.capitalize()]],
                        hovertemplate="Run: %{customdata[0]}<br>Tier: %{customdata[1]}<br>Type: %{customdata[2]}<br>Hours: %{y:.2f}<extra></extra>",
                        showlegend=show_legend,
                        legendgroup=legend_label,
                        offsetgroup="time_allocation"
                    ),
                    row=1, col=5
                )
            fig.update_yaxes(title_text="Hours", showgrid=False, range=[0, 24], tickvals=[0, 4, 8, 12, 16, 20, 24], row=1, col=5)
            fig.update_xaxes(title_text="Scenario", showgrid=False, row=1, col=5)

    # --- Apply consistent style/layout to the whole figure ---
    fig.update_layout(
        height=500,
        showlegend=True,
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text'],
        barmode='stack',
        margin=dict(l=10, r=10, t=40, b=10),
        title_font=dict(size=22, color=colors['text']),
        font=dict(size=14, color=colors['text'])
    )

    return fig, warning_message


def tower_layout_figure(
    tower_range: float = 69.5,
    wall_inner_ratio: float = 0.25,
    wall_outer_ratio: float = 0.32,
    black_hole_ratio: float = 0.85,
    golden_bot_ratio: float = 0.60,
    bricks: int = 40,
) -> go.Figure:
    """Create a stylized tower layout schematic.

    Elements:
    - Wall: rendered as a ring with radial dividers ("bricks").
    - Tower range: full light grey/blue circle (radius = tower_range).
    - Black hole orbit: dashed purple circle at black_hole_ratio * tower_range.
    - Golden bot range/orbit: dashed yellow circle at golden_bot_ratio * tower_range.

    Parameters are ratios so the visual can be rescaled. All circles are centered at (0,0).
    """
    # Basic radii
    wall_r_in = wall_inner_ratio * tower_range
    wall_r_out = wall_outer_ratio * tower_range
    bh_r = black_hole_ratio * tower_range
    gold_r = golden_bot_ratio * tower_range

    fig = go.Figure()

    # Helper to make circle coordinates
    def circle_xy(r: float, steps: int = 360):
        ang = np.linspace(0, 2 * np.pi, steps)
        return r * np.cos(ang), r * np.sin(ang)

    # Tower range (outermost)
    x_tr, y_tr = circle_xy(tower_range)
    fig.add_trace(go.Scatter(
        x=x_tr, y=y_tr,
        mode='lines',
        line=dict(color='#7DA6C7', width=2),
        name='Tower Range',
        hoverinfo='skip'
    ))

    # Wall outer & inner to create thick band (draw outer then inner filled to background to simulate ring)
    x_w_out, y_w_out = circle_xy(wall_r_out)
    x_w_in, y_w_in = circle_xy(wall_r_in)
    fig.add_trace(go.Scatter(
        x=x_w_out, y=y_w_out,
        mode='lines',
        fill='toself',
        fillcolor='rgba(110,24,255,0.15)',
        line=dict(color='#6E18FF', width=3),
        name='Wall (outer)',
        hoverinfo='skip'
    ))
    fig.add_trace(go.Scatter(
        x=x_w_in, y=y_w_in,
        mode='lines',
        fill='toself',
        fillcolor=colors['background'],
        line=dict(color=colors['background'], width=1),
        name='Wall (inner mask)',
        hoverinfo='skip',
        showlegend=False
    ))

    # Brick dividers: radial lines between inner & outer wall radii
    for i in range(bricks):
        theta = (2 * np.pi / bricks) * i
        x0 = wall_r_in * np.cos(theta)
        y0 = wall_r_in * np.sin(theta)
        x1 = wall_r_out * np.cos(theta)
        y1 = wall_r_out * np.sin(theta)
        fig.add_trace(go.Scatter(
            x=[x0, x1], y=[y0, y1],
            mode='lines',
            line=dict(color='rgba(255,255,255,0.18)', width=1),
            hoverinfo='skip',
            showlegend=False
        ))

    # Black hole orbit (dashed)
    x_bh, y_bh = circle_xy(bh_r)
    fig.add_trace(go.Scatter(
        x=x_bh, y=y_bh,
        mode='lines',
        line=dict(color='#C060FF', width=2, dash='dash'),
        name='Black Hole Orbit',
        hovertemplate=f"Black Hole Radius: {bh_r:.2f}m<extra></extra>"
    ))

    # Golden bot range/orbit (dashed)
    x_gold, y_gold = circle_xy(gold_r)
    fig.add_trace(go.Scatter(
        x=x_gold, y=y_gold,
        mode='lines',
        line=dict(color='#FFD700', width=2, dash='dash'),
        name='Golden Bot',
        hovertemplate=f"Golden Bot Radius: {gold_r:.2f}m<extra></extra>"
    ))

    # Center marker
    fig.add_trace(go.Scatter(
        x=[0], y=[0],
        mode='markers',
        marker=dict(color='#FFFFFF', size=10, symbol='circle-open'),
        name='Center',
        hoverinfo='skip'
    ))

    # Axis styling (equal aspect)
    span = tower_range * 1.05
    fig.update_xaxes(visible=False, range=[-span, span])
    fig.update_yaxes(visible=False, range=[-span, span], scaleanchor='x', scaleratio=1)

    fig.update_layout(
        title=f"Tower Layout (Range {tower_range} m)",
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text'],
        showlegend=True,
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(bgcolor='rgba(0,0,0,0.4)')
    )

    return fig
