import pandas as pd
import numpy as np

def summarize_current(time_series_df: pd.DataFrame, n_days: int = 3) -> tuple[pd.DataFrame, pd.DataFrame, float]:
    """
    Summarize actual recent runs (last n days, all run types).
    Returns summary_df (metrics with error bars), breakdown_df (avg duration by run_type/tier), total_time_hours.
    """
    if time_series_df is None or time_series_df.empty:
        return pd.DataFrame(), pd.DataFrame(), 0.0
    ts: pd.DataFrame = time_series_df.copy()
    ts['timestamp'] = pd.to_datetime(ts['timestamp'])
    # Use .dt.date to ensure 'date' is a Python date, not a Timestamp
    # Use .apply(lambda x: x.date()) to avoid ambiguous .dt.date property error
    ts['date'] = ts['timestamp'].apply(lambda x: x.date() if hasattr(x, 'date') else x)
    today = pd.Timestamp.today().date()
    unique_dates = sorted(ts['date'].unique())
    unique_dates_prior = [d for d in unique_dates if d < today]
    last_dates = unique_dates_prior[-n_days:] if n_days > 0 else []
    recent_data = ts[ts['date'].isin(last_dates)].copy()
    if recent_data.empty:
        return pd.DataFrame(), pd.DataFrame(), 0.0

    # Metrics: coins, cells, reroll shards
    metrics = ['coins_earned', 'cells_earned', 'reroll_shards_earned']
    # Group by day, sum totals for each day
    daily_totals = recent_data.groupby('date')[metrics].sum().reset_index()

    # Compute optimizer-style daily score (normalized by max per-hour * 24)
    def _safe_max(series: pd.Series) -> float:
        try:
            val = float(series.max())
            return 0.0 if np.isnan(val) else val
        except Exception:
            return 0.0

    max_coins_per_hour = _safe_max(ts.get('coins_per_hour', pd.Series([0.0])))
    max_cells_per_hour = _safe_max(ts.get('cells_per_hour', pd.Series([0.0])))
    max_shards_per_hour = _safe_max(ts.get('reroll_shards_per_hour', pd.Series([0.0])))

    denom_coins = max_coins_per_hour * 24 if max_coins_per_hour else _safe_max(daily_totals.get('coins_earned', pd.Series([0.0])))
    denom_cells = max_cells_per_hour * 24 if max_cells_per_hour else _safe_max(daily_totals.get('cells_earned', pd.Series([0.0])))
    denom_shards = max_shards_per_hour * 24 if max_shards_per_hour else _safe_max(daily_totals.get('reroll_shards_earned', pd.Series([0.0])))

    def _safe_norm(series: pd.Series, denom: float) -> pd.Series:
        if denom and not np.isnan(denom):
            return series / denom
        return pd.Series([0.0] * len(series), index=series.index)

    daily_totals['optimizer_score'] = (
        _safe_norm(daily_totals['coins_earned'], denom_coins)
        + _safe_norm(daily_totals['cells_earned'], denom_cells)
        + _safe_norm(daily_totals['reroll_shards_earned'], denom_shards)
    ) / 3 * 100
    daily_totals['score'] = daily_totals['optimizer_score']
    summary_data = []
    metrics = ['coins_earned', 'cells_earned', 'reroll_shards_earned', 'score']
    for conf_level, percentile in [('mean', 50), ('ci_lower', 16), ('ci_upper', 84)]:
        summary_row: dict[str, float | str] = {'confidence': conf_level}
        for m in metrics:
            if conf_level == 'mean':
                summary_row[m] = daily_totals[m].mean()
            else:
                summary_row[m] = daily_totals[m].quantile(percentile / 100)
        summary_data.append(summary_row)
    summary_df = pd.DataFrame(summary_data)

    # --- Enhanced time allocation breakdown ---
    if 'run_type' not in recent_data.columns:
        # Set dtype to object so both float and str can coexist
        recent_data['run_type'] = pd.Series(['unknown'] * len(recent_data), dtype=object)
    if 'tier' not in recent_data.columns:
        # Set dtype to object so both float and str can coexist
        recent_data['tier'] = pd.Series(['unknown'] * len(recent_data), dtype=object)
    # Ensure correct dtypes for run_type and tier
    if recent_data['run_type'].dtype != object:
        recent_data['run_type'] = recent_data['run_type'].astype(object)
    # If tier is numeric, keep as int or float, else as string
    def clean_tier(x):
        if x is None:
            return 'unknown'
        try:
            return int(x)
        except Exception:
            try:
                return float(x)
            except Exception:
                return str(x)
    recent_data['tier'] = recent_data['tier'].apply(clean_tier)
    days_considered = int(len(last_dates)) if last_dates else 1
    # Compute total runs per (run_type, tier)
    total_runs = recent_data.groupby(['run_type', 'tier']).size().reset_index(name='total_runs')
    # Ensure tier is always int if possible
    def safe_tier(val):
        try:
            return int(val)
        except Exception:
            try:
                return float(val)
            except Exception:
                return str(val)
    total_runs['tier'] = total_runs['tier'].apply(safe_tier)
    # Compute average runs per day (exclude zero runs)
    total_runs = total_runs[total_runs['total_runs'] > 0]
    total_runs['avg_runs_per_day'] = total_runs['total_runs'].astype(float) / float(days_considered)
    # Compute average duration per run
    avg_run_duration = recent_data.groupby(['run_type', 'tier'])['real_time'].mean().reset_index(name='avg_duration')
    avg_run_duration['tier'] = avg_run_duration['tier'].apply(safe_tier)
    avg_run_duration['avg_duration'] = avg_run_duration['avg_duration'].astype(float)
    # Merge
    merged = pd.merge(total_runs, avg_run_duration, on=['run_type', 'tier'], how='left')
    breakdown_rows = []
    for _, row in merged.iterrows():
        tier = row['tier']
        avg_runs = float(row['avg_runs_per_day'])
        avg_duration = float(row['avg_duration'])
        total_duration = avg_runs * avg_duration
        runs = avg_runs
        run_type = row['run_type'] if 'run_type' in row else 'unknown'
        # Description matches Optimizer output
        description = f"{runs:.2f} x tier {tier} ({avg_duration:.2f} h each)<br>(total time: {total_duration:.2f} h)"
        breakdown_rows.append({
            'tier': tier,
            'runs': runs,
            'duration_per_run': avg_duration,
            'total_duration': total_duration,
            'run_type': run_type,
            'description': description
        })
    breakdown_df = pd.DataFrame(breakdown_rows)
    # Ensure dtypes are correct
    if not breakdown_df.empty:
        breakdown_df['tier'] = breakdown_df['tier'].apply(safe_tier)
        for col in ['runs', 'duration_per_run', 'total_duration']:
            if not pd.api.types.is_float_dtype(breakdown_df[col]):
                breakdown_df[col] = breakdown_df[col].astype(float)
    # Total time
    total_time_hours = float((recent_data['real_time']).sum()) if 'real_time' in recent_data.columns else 0.0
    return summary_df, breakdown_df, total_time_hours
