"""
Cluster detection module for optimizer data.

Performs on-demand clustering of run data to identify distinct run modes
within each tier based on duration (perk RNG impact).
"""

import logging
import pandas as pd
import numpy as np
from typing import Tuple, Dict

logger = logging.getLogger("rend-cluster")


def detect_clusters(
    filtered_df: pd.DataFrame,
    cluster_review_days: int = 30
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Detect clusters in optimizer data for the specified review period.
    
    Args:
        filtered_df: Pre-filtered DataFrame with farming/overnight runs
        cluster_review_days: Number of days to look back for clustering
        
    Returns:
        Tuple of (optimizer_df, cluster_stats_df)
        - optimizer_df: DataFrame with tier, level_1, cluster_runs, cluster_pct, and metrics
        - cluster_stats_df: DataFrame with cluster statistics
    """
    if filtered_df is None or filtered_df.empty:
        logger.warning("detect_clusters: empty input dataframe")
        return pd.DataFrame(), pd.DataFrame()

    if 'timestamp' not in filtered_df.columns:
        logger.warning("detect_clusters: missing 'timestamp' column")
        return pd.DataFrame(), pd.DataFrame()

    # Normalize timestamps to tz-aware UTC for robust comparisons.
    ts = pd.to_datetime(filtered_df['timestamp'], errors='coerce', utc=True)
    valid_df = filtered_df.loc[ts.notna()].copy()
    if valid_df.empty:
        logger.warning("detect_clusters: no valid timestamps after parsing")
        return pd.DataFrame(), pd.DataFrame()
    valid_df['timestamp'] = ts.loc[ts.notna()]

    # Filter to review period
    now = pd.Timestamp.now(tz='UTC')
    filter_date = now - pd.Timedelta(days=cluster_review_days)
    optimizer_filtered_df = valid_df[valid_df['timestamp'] >= filter_date].copy()
    
    if optimizer_filtered_df.empty:
        logger.warning(f"No data found in last {cluster_review_days} days for clustering")
        return pd.DataFrame(), pd.DataFrame()
    
    # Apply clustering to identify distinct run modes within each tier
    # Primary feature: real_time (duration) as it best captures perk luck
    try:
        from functions.statistics.Clusters import cluster_optimizer_data
        
        # Exclude milestone runs from clustering
        clustering_df = optimizer_filtered_df
        if 'run_type' in clustering_df.columns:
            clustering_df = clustering_df[clustering_df['run_type'].astype(str).str.lower() != 'milestone']
        
        if clustering_df.empty:
            raise ValueError("No non-milestone runs available for clustering")

        clustered_data, cluster_stats = cluster_optimizer_data(
            clustering_df,
            tier_column='tier',
            features=['real_time'],
            max_clusters=3,
            min_duration_diff_pct=10.0  # 10% of max duration = minimum threshold for cluster separation
        )
        
        logger.info(f"Clustering successful: {len(cluster_stats)} clusters from {len(optimizer_filtered_df)} runs")
        
        # Group clustered data and build optimizer DataFrame
        optimizer_data = []
        
        for _, stats in cluster_stats.iterrows():
            cluster_id = stats.get('cluster_label', str(stats.get('cluster', 0)))
            tier = stats['tier']
            n_runs = stats['n_runs']
            
            # Get total runs for this tier to compute cluster percentage
            tier_total_runs = len(optimizer_filtered_df[optimizer_filtered_df['tier'] == tier])
            cluster_pct = n_runs / tier_total_runs if tier_total_runs > 0 else 0.0
            
            optimizer_row = {
                'tier': cluster_id,
                'level_1': 'mean',
                'cluster_id': cluster_id,
                'cluster_runs': int(n_runs),
                'cluster_pct': cluster_pct,
                'coins_earned': stats.get('coins_earned_mean', stats.get('coins_earned', 0.0)),
                'cells_earned': stats.get('cells_earned_mean', stats.get('cells_earned', 0.0)),
                'reroll_shards_earned': stats.get('reroll_shards_earned_mean', stats.get('reroll_shards_earned', 0.0)),
                'real_time': stats.get('real_time_mean', stats.get('real_time', 0.0)),
                'score': stats.get('score_mean', stats.get('score', 0.0))
            }
            
            # Add ci_lower and ci_upper rows
            for level in ['ci_lower', 'ci_upper']:
                row_copy = optimizer_row.copy()
                row_copy['level_1'] = level
                row_copy['coins_earned'] = stats.get(f'coins_earned_{level}', stats.get('coins_earned', 0.0))
                row_copy['cells_earned'] = stats.get(f'cells_earned_{level}', stats.get('cells_earned', 0.0))
                row_copy['reroll_shards_earned'] = stats.get(f'reroll_shards_earned_{level}', stats.get('reroll_shards_earned', 0.0))
                row_copy['real_time'] = stats.get(f'real_time_{level}', stats.get('real_time', 0.0))
                row_copy['score'] = stats.get(f'score_{level}', stats.get('score', 0.0))
                optimizer_data.append(row_copy)
            
            optimizer_data.append(optimizer_row)
        
        optimizer_df = pd.DataFrame(optimizer_data)
        
        logger.info(f"Optimizer: Created {len(cluster_stats)} clusters from {len(optimizer_filtered_df)} runs (last {cluster_review_days} days)")
        
        return optimizer_df, cluster_stats
        
    except Exception as e:
        logger.exception(f"Clustering failed: {e}")
        # Fallback: aggregate without clustering
        return _fallback_aggregation(optimizer_filtered_df, cluster_review_days)


def _fallback_aggregation(df: pd.DataFrame, cluster_review_days: int) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Fallback aggregation when clustering fails.
    Groups by tier only, treating each tier as a single cluster.
    """
    logger.warning("Using fallback aggregation (no clustering)")
    
    from functions.statistics.time_series_stats import TimeSeriesStats
    
    # Only use columns that exist in the dataframe
    available_cols = ['coins_earned', 'cells_earned', 'reroll_shards_earned', 'real_time']
    cols_to_use = [col for col in available_cols if col in df.columns]
    
    if not cols_to_use:
        # No columns to compute stats on, return empty result
        return pd.DataFrame(), pd.DataFrame()
    
    stats = TimeSeriesStats(df, 'tier')
    wide_stats = stats.compute_latest_stats(cols_to_use)
    
    # Reshape to long format
    long_stats = stats.reshape_to_long_format(wide_stats)
    
    # Add dummy cluster info
    long_stats['cluster_id'] = long_stats['tier'].astype(str)
    long_stats['cluster_runs'] = 1
    long_stats['cluster_pct'] = 1.0
    
    # Return empty DataFrame as cluster_stats since we're using simple aggregation
    return long_stats, pd.DataFrame()
