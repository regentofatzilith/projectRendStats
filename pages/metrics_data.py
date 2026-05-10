"""Metrics data preparation and processing functions.

Shared utilities for preparing and computing metrics data across pages.
"""

import pandas as pd
import plotly.graph_objects as go
from typing import List, TypedDict, Union, Tuple, Optional
import logging

from functions import user_data_store
from functions.graphs import combined_metrics_figure, optimize_figure, continuous_metrics_figure
from functions.statistics import TimeSeriesStats, compute_normalized_score_100

logger = logging.getLogger(__name__)


class DropdownOption(TypedDict):
    """Type definition for Dash Dropdown option."""
    label: str
    value: Union[str, int, float]


def build_tier_options(df: pd.DataFrame) -> List[DropdownOption]:
    """Build tier dropdown options from dataframe.
    
    Accepts any dataframe with a 'tier' column; falls back to time series if empty 
    to include brand-new tiers.
    
    Args:
        df: DataFrame with 'tier' column
        
    Returns:
        List of dropdown options with tier labels and values
    """
    # If provided df is empty or missing column, attempt to use time_series_df
    if (df.empty or 'tier' not in df.columns):
        ts_df = user_data_store.cleaned.get('time_series_df', pd.DataFrame())
        df = ts_df if ('tier' in ts_df.columns and not ts_df.empty) else df
    if df.empty or 'tier' not in df.columns:
        return []
    vals = []
    for x in df['tier'].tolist():
        try:
            f = float(x)
            if f > 0:
                vals.append(int(f))
        except Exception:
            continue
    unique_vals = sorted(set(vals))
    return [{'label': f'Tier {v}', 'value': float(v)} for v in unique_vals]


def prepare_metrics_data(
    selected_tier: Optional[List[float]] = None,
    window_days: float = 2.0,
    timeline_scope: str = '3m',
    current_days: int = 3
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, List[DropdownOption]]:
    """Prepare all metrics data with optional filtering.
    
    Args:
        selected_tier: List of tier values to filter by, or None for all tiers
        window_days: Window size in days for exponential weighting
        timeline_scope: Timeline scope selector ('3m' for last 90 days, 'all' for full history)
        current_days: Number of days to look back for current scenario
        
    Returns:
        Tuple of (metrics_df, ts_filtered, all_runs_filtered, optimizer_df, tier_options)
    """
    # Get data from store
    filtered_df = user_data_store.cleaned.get('grouped_by_tier_df', pd.DataFrame())
    time_series_df = user_data_store.cleaned.get('time_series_df', pd.DataFrame())
    all_runs_time_series_df = user_data_store.cleaned.get('all_runs_time_series_df', pd.DataFrame())
    long_stats = user_data_store.cleaned.get('optimizer_df', pd.DataFrame())

    def _filter_timeline(df: pd.DataFrame) -> pd.DataFrame:
        if df is None or df.empty:
            return pd.DataFrame() if df is None else df.copy()
        if str(timeline_scope or '3m').lower() == 'all':
            return df.copy()
        if 'timestamp' not in df.columns:
            return df.copy()
        out = df.copy()
        ts = pd.to_datetime(out['timestamp'], errors='coerce', utc=True, format='mixed')
        valid = ts.notna()
        if not valid.any():
            return out
        latest = ts[valid].max()
        cutoff = latest - pd.Timedelta(days=90)
        return out.loc[valid & (ts >= cutoff)].copy()

    # Scope the heavy input datasets before downstream calculations.
    time_series_df = _filter_timeline(time_series_df)
    all_runs_time_series_df = _filter_timeline(all_runs_time_series_df)
    
    # Rebuild tier options
    tier_options = build_tier_options(time_series_df if not time_series_df.empty else filtered_df)

    def _safe_max(series: pd.Series) -> float:
        try:
            val = float(pd.to_numeric(series, errors='coerce').max())
            return 0.0 if pd.isna(val) else val
        except Exception:
            return 0.0

    # Build normalization maxima consistent with weekly optimizer scoring.
    max_coins_per_hour = 0.0
    max_cells_per_hour = 0.0
    max_shards_per_hour = 0.0
    if not filtered_df.empty:
        mean_rows = filtered_df[filtered_df.get('level_1') == 'mean'] if 'level_1' in filtered_df.columns else filtered_df
        max_coins_per_hour = _safe_max(mean_rows.get('coins_per_hour', pd.Series([0.0])))
        max_cells_per_hour = _safe_max(mean_rows.get('cells_per_hour', pd.Series([0.0])))
        max_shards_per_hour = _safe_max(mean_rows.get('reroll_shards_per_hour', pd.Series([0.0])))

    max_income_baseline_df = user_data_store.cleaned.get('max_income_baseline_df', pd.DataFrame())
    if max_income_baseline_df is not None and not max_income_baseline_df.empty:
        base_row = max_income_baseline_df.iloc[0]
        max_coins_per_hour = max(max_coins_per_hour, float(base_row.get('max_coins_per_hour', 0.0) or 0.0))
        max_cells_per_hour = max(max_cells_per_hour, float(base_row.get('max_cells_per_hour', 0.0) or 0.0))
        max_shards_per_hour = max(max_shards_per_hour, float(base_row.get('max_shards_per_hour', 0.0) or 0.0))

    denom_coins = max_coins_per_hour * 24.0 if max_coins_per_hour > 0 else 0.0
    denom_cells = max_cells_per_hour * 24.0 if max_cells_per_hour > 0 else 0.0
    denom_shards = max_shards_per_hour * 24.0 if max_shards_per_hour > 0 else 0.0
    
    # Recompute stats with user-selected window_days for exponential weighting
    metrics_df = pd.DataFrame()
    if not time_series_df.empty:
        try:
            ts_for_stats = time_series_df.copy()
            if {'coins_earned', 'cells_earned', 'reroll_shards_earned'}.issubset(ts_for_stats.columns):
                ts_for_stats['coins_earned'] = pd.to_numeric(ts_for_stats['coins_earned'], errors='coerce').fillna(0.0)
                ts_for_stats['cells_earned'] = pd.to_numeric(ts_for_stats['cells_earned'], errors='coerce').fillna(0.0)
                ts_for_stats['reroll_shards_earned'] = pd.to_numeric(ts_for_stats['reroll_shards_earned'], errors='coerce').fillna(0.0)
                ts_for_stats['score'] = ts_for_stats.apply(
                    lambda r: compute_normalized_score_100(
                        float(r.get('coins_earned', 0.0) or 0.0),
                        float(r.get('cells_earned', 0.0) or 0.0),
                        float(r.get('reroll_shards_earned', 0.0) or 0.0),
                        denom_coins,
                        denom_cells,
                        denom_shards,
                        weights={'coins': 1.0 / 3.0, 'cells': 1.0 / 3.0, 'shards': 1.0 / 3.0},
                    ),
                    axis=1,
                )

            stats = TimeSeriesStats(ts_for_stats, 'tier')
            wide_stats = stats.compute_latest_stats([
                'coins_earned', 'cells_earned', 'reroll_shards_earned', 'waves_per_tier', 'real_time',
                'coins_per_hour', 'cells_per_hour', 'reroll_shards_per_hour', 'waves_per_hour', 'score'
            ], window_days=window_days)
            long_stats_overview = stats.reshape_to_long_format(wide_stats)
            # Rebuild metrics_df in the same format as grouped_by_tier_df
            plot_data = []
            for tier in sorted(long_stats_overview['tier'].unique()):
                for level in ['mean', 'ci_lower', 'ci_upper']:
                    plot_row = {'tier': tier, 'level_1': level}
                    tier_data = long_stats_overview[long_stats_overview['tier'] == tier]
                    for _, row in tier_data.iterrows():
                        plot_row[row['metric']] = row[level]
                    plot_data.append(plot_row)
            metrics_df = pd.DataFrame(plot_data) if plot_data else pd.DataFrame()
        except Exception as e:
            logger.error(f"Error computing weighted stats: {e}")
            # Fall back to original data if computation fails
            metrics_df = filtered_df.copy()

    # Ensure score in fallback/legacy frames also follows normalized optimizer score.
    if not metrics_df.empty and {'coins_earned', 'cells_earned', 'reroll_shards_earned'}.issubset(metrics_df.columns):
        metrics_df['score'] = metrics_df.apply(
            lambda r: compute_normalized_score_100(
                float(r.get('coins_earned', 0.0) or 0.0),
                float(r.get('cells_earned', 0.0) or 0.0),
                float(r.get('reroll_shards_earned', 0.0) or 0.0),
                denom_coins,
                denom_cells,
                denom_shards,
                weights={'coins': 1.0 / 3.0, 'cells': 1.0 / 3.0, 'shards': 1.0 / 3.0},
            ),
            axis=1,
        )
    
    # Filter metrics_df by tier selection
    if selected_tier and len(selected_tier) > 0 and not metrics_df.empty:
        metrics_df['tier'] = pd.to_numeric(metrics_df['tier'], errors='coerce')
        metrics_df = metrics_df[metrics_df['tier'].isin(selected_tier)]
    
    # Filter time series data
    ts_filtered = time_series_df.copy()
    if selected_tier and len(selected_tier) > 0:
        ts_filtered['tier'] = pd.to_numeric(ts_filtered['tier'], errors='coerce')
        ts_filtered = ts_filtered[ts_filtered['tier'].isin(selected_tier)]
    
    # Filter all_runs for Current scenario by tier
    all_runs_filtered = all_runs_time_series_df.copy() if not all_runs_time_series_df.empty else pd.DataFrame()
    if selected_tier and len(selected_tier) > 0 and not all_runs_filtered.empty:
        all_runs_filtered['tier'] = pd.to_numeric(all_runs_filtered['tier'], errors='coerce')
        all_runs_filtered = all_runs_filtered[all_runs_filtered['tier'].isin(selected_tier)]
    
    # Filter optimizer data
    optimizer_df = long_stats.copy() if not long_stats.empty else pd.DataFrame()
    if selected_tier and len(selected_tier) > 0 and not optimizer_df.empty:
        optimizer_df['tier'] = pd.to_numeric(optimizer_df['tier'], errors='coerce')
        optimizer_df = optimizer_df[optimizer_df['tier'].isin(selected_tier)]
    
    return metrics_df, ts_filtered, all_runs_filtered, optimizer_df, tier_options


def create_metrics_figures(
    metrics_df: pd.DataFrame,
    ts_filtered: pd.DataFrame,
    all_runs_filtered: pd.DataFrame,
    optimizer_df: pd.DataFrame,
    window_days: float = 2.0,
    daytime_hours: int = 16,
    nighttime_max_runs: int = 1,
    required_tiers: Optional[list[int]] = None,
    current_days: int = 3,
    metric_type: str = 'real_time'
) -> Tuple[go.Figure, go.Figure, go.Figure, Optional[str]]:
    """Create all metrics visualization figures.
    
    Args:
        metrics_df: Metrics overview data
        ts_filtered: Filtered time series data
        all_runs_filtered: Filtered all runs data
        optimizer_df: Optimizer data
        window_days: Window size for continuous metrics
        daytime_hours: Hours awake/active for optimizer
        nighttime_max_runs: Maximum runs allowed during nighttime
        required_tiers: List of tiers that must each appear at least once
        current_days: Days to look back for current scenario
        metric_type: Type of metric for overview ('real_time' or 'waves_per_tier')
        
    Returns:
        Tuple of (metrics_graph, continuous_graph, optimizer_graph, warning_message)
    """
    # Create figures
    metrics_graph = combined_metrics_figure(metrics_df, metric_type=metric_type) if not metrics_df.empty else go.Figure()
    continuous_graph = continuous_metrics_figure(ts_filtered, window_days=window_days) if not ts_filtered.empty else go.Figure()
    
    warning_message = None
    if not optimizer_df.empty:
        # Pass all new parameters to optimize_figure
        optimizer_graph, warning_message = optimize_figure(
            optimizer_df, 
            daytime_hours, 
            ts_filtered, 
            all_runs_filtered, 
            current_days=current_days,
            nighttime_max_runs=nighttime_max_runs,
            required_tiers=required_tiers
        )
    else:
        optimizer_graph = go.Figure()
    
    return metrics_graph, continuous_graph, optimizer_graph, warning_message


__all__ = [
    'DropdownOption',
    'build_tier_options',
    'prepare_metrics_data',
    'create_metrics_figures'
]
