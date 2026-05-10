"""Debug script to compare Daily Results data from metrics page vs forecast page."""

import sys
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from functions import user_data_store
from functions.graphs import get_smoothed_daily_data
from functions.statistics import TimeSeriesStats

# Load user data
user_data_store.load_user_data()
df_raw = user_data_store.all_runs_time_series_df.copy()

if df_raw.empty:
    print("No data loaded!")
    sys.exit(1)

print(f"Total raw data rows: {len(df_raw)}")

# Filter last 100 days
cutoff = pd.Timestamp.now() - pd.Timedelta(days=100)
df_raw['timestamp'] = pd.to_datetime(df_raw['timestamp'])
df_recent = df_raw[df_raw['timestamp'] >= cutoff].copy()
print(f"Rows in last 100 days: {len(df_recent)}")

# Metrics to check
metrics = ['coins_earned', 'cells_earned', 'reroll_shards_earned', 
           'coins_per_hour', 'cells_per_hour', 'reroll_shards_per_hour']

print("\n" + "="*80)
print("COMPARING DAILY AGGREGATION METHODS")
print("="*80)

for metric in metrics:
    print(f"\n{'='*80}")
    print(f"METRIC: {metric}")
    print(f"{'='*80}")
    
    if metric not in df_recent.columns:
        print(f"  ⚠️  {metric} not in dataframe")
        continue
    
    # METHOD 1: Using continuous_metrics_figure logic directly
    print("\n[METHOD 1: Direct aggregation (like continuous_metrics_figure)]")
    ts = pd.to_datetime(df_recent['timestamp'], errors='coerce').dt.tz_localize(None)
    vals = pd.to_numeric(df_recent[metric], errors='coerce')
    base = pd.DataFrame({'timestamp': ts.dt.normalize(), metric: vals})
    
    abs_metrics = {'coins_earned', 'cells_earned', 'reroll_shards_earned', 'waves_per_tier'}
    rate_metrics = {'coins_per_hour', 'cells_per_hour', 'reroll_shards_per_hour', 'waves_per_hour'}
    
    if metric in abs_metrics:
        daily_df_method1 = base.dropna().groupby('timestamp', as_index=False)[metric].sum()
    elif metric in rate_metrics:
        if 'real_time' in df_recent.columns:
            weights = pd.to_numeric(df_recent['real_time'], errors='coerce')
            tmp = pd.DataFrame({'timestamp': ts.dt.normalize(), metric: vals, 'w': weights})
            tmp = tmp.dropna()
            safe_w = tmp['w'].clip(lower=0.0).replace([np.inf, -np.inf], np.nan).fillna(0.0)
            tmp = tmp.assign(w_safe=safe_w, wx=tmp[metric] * safe_w)
            grp = (
                tmp.groupby('timestamp', as_index=False)
                .agg(wx_sum=('wx', 'sum'), w_sum=('w_safe', 'sum'), mean_val=(metric, 'mean'))
            )
            grp[metric] = np.where(grp['w_sum'] > 0, grp['wx_sum'] / grp['w_sum'], grp['mean_val'])
            daily_df_method1 = grp[['timestamp', metric]]
        else:
            daily_df_method1 = base.dropna().groupby('timestamp', as_index=False)[metric].mean()
    else:
        daily_df_method1 = base.dropna().groupby('timestamp', as_index=False)[metric].mean()
    
    # Apply smoothing (method 1)
    stats_calc1 = TimeSeriesStats(daily_df_method1, None)
    smoothed_method1 = stats_calc1.compute_continuous_stats(metric, window_days=3.0)
    
    print(f"  Daily aggregated rows: {len(daily_df_method1)}")
    print(f"  Smoothed rows: {len(smoothed_method1)}")
    if not daily_df_method1.empty:
        print(f"  Daily values range: {daily_df_method1[metric].min():.2f} to {daily_df_method1[metric].max():.2f}")
        print(f"  Daily mean: {daily_df_method1[metric].mean():.2f}")
    if not smoothed_method1.empty and 'mean' in smoothed_method1.columns:
        print(f"  Smoothed mean values range: {smoothed_method1['mean'].min():.2f} to {smoothed_method1['mean'].max():.2f}")
        print(f"  Smoothed overall mean: {smoothed_method1['mean'].mean():.2f}")
    
    # METHOD 2: Using get_smoothed_daily_data (forecast page)
    print("\n[METHOD 2: get_smoothed_daily_data (forecast page)]")
    smoothed_method2 = get_smoothed_daily_data(df_recent, metric, window_days=3.0)
    
    print(f"  Smoothed rows: {len(smoothed_method2)}")
    if not smoothed_method2.empty and 'mean' in smoothed_method2.columns:
        print(f"  Smoothed mean values range: {smoothed_method2['mean'].min():.2f} to {smoothed_method2['mean'].max():.2f}")
        print(f"  Smoothed overall mean: {smoothed_method2['mean'].mean():.2f}")
    
    # COMPARE
    print("\n[COMPARISON]")
    if smoothed_method1.empty or smoothed_method2.empty:
        print("  ⚠️  One or both methods returned empty dataframe")
        continue
    
    # Merge on timestamp
    merged = smoothed_method1[['timestamp', 'mean']].merge(
        smoothed_method2[['timestamp', 'mean']], 
        on='timestamp', 
        suffixes=('_m1', '_m2'),
        how='outer'
    )
    
    print(f"  Rows in method1: {len(smoothed_method1)}")
    print(f"  Rows in method2: {len(smoothed_method2)}")
    print(f"  Merged rows: {len(merged)}")
    print(f"  Matching timestamps: {merged['mean_m1'].notna().sum() & merged['mean_m2'].notna().sum()}")
    
    # Check for differences
    if 'mean_m1' in merged.columns and 'mean_m2' in merged.columns:
        both_present = merged['mean_m1'].notna() & merged['mean_m2'].notna()
        if both_present.sum() > 0:
            diff = (merged.loc[both_present, 'mean_m1'] - merged.loc[both_present, 'mean_m2']).abs()
            max_diff = diff.max()
            mean_diff = diff.mean()
            
            print(f"  Max difference: {max_diff:.6f}")
            print(f"  Mean difference: {mean_diff:.6f}")
            
            if max_diff > 0.001:
                print(f"  ⚠️  DIFFERENCES FOUND!")
                print("\n  Sample of differences (first 10):")
                diff_df = merged[both_present].copy()
                diff_df['diff'] = (diff_df['mean_m1'] - diff_df['mean_m2']).abs()
                diff_df = diff_df.sort_values('diff', ascending=False).head(10)
                print(diff_df[['timestamp', 'mean_m1', 'mean_m2', 'diff']].to_string())
            else:
                print(f"  ✅ Values match (within tolerance)")
        else:
            print(f"  ⚠️  No overlapping timestamps!")
    
    # Show last few days for reference
    print(f"\n  Last 5 days (Method 1):")
    if not smoothed_method1.empty:
        print(smoothed_method1.tail(5)[['timestamp', 'mean']].to_string(index=False))
    
    print(f"\n  Last 5 days (Method 2):")
    if not smoothed_method2.empty:
        print(smoothed_method2.tail(5)[['timestamp', 'mean']].to_string(index=False))

print("\n" + "="*80)
print("COMPARISON COMPLETE")
print("="*80)
