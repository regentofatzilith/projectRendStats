"""Time series statistics analysis with weighted calculations."""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional

from .weighted_stats import WeightedStats


class TimeSeriesStats:
    """
    Class for analyzing time series data with weighted statistics.
    Combines functionality of TierStats and TierStatsWeight into a single class
    with improved type safety and error handling.
    """
    def __init__(self, df: pd.DataFrame, group_col: Optional[str] = None):
        self.df = df
        self.group_col = group_col

    def prepare_data(self, column: str, time_col: str = "timestamp") -> pd.DataFrame:
        """Prepare and validate data for analysis."""
        df = self.df.copy()
        df[time_col] = pd.to_datetime(df[time_col], errors="coerce").dt.tz_localize(None)
        df = df.sort_values(time_col)
        return df

    def compute_continuous_stats(self, column: str, time_col: str = "timestamp", window_days: float = 3) -> pd.DataFrame:
        """
        Compute continuous weighted statistics over time.
        
        Args:
            column: The column to compute statistics for
            time_col: The timestamp column name
            window_days: The window size in days for the exponential weighting
            
        Returns:
            DataFrame with columns: timestamp, [group_col], mean, std, ci_lower, ci_upper
        """
        df = self.prepare_data(column, time_col)
        results = []

        # Handle grouping if specified
        groups = [("all", df)] if self.group_col is None else df.groupby(self.group_col)

        for group_name, group_data in groups:
            for current_time in group_data[time_col].unique():
                # Get data up to current time
                mask = (group_data[time_col] <= current_time)
                if not mask.any():
                    continue

                current_data = group_data[mask].copy()
                weights = WeightedStats.compute_time_weights(current_data[time_col], current_time, window_days)

                # Process valid data
                series = pd.to_numeric(current_data[column], errors="coerce")
                # Create Series with same index as the data for proper alignment
                weights_series = pd.Series(weights, index=current_data.index)
                valid = series.notna() & weights_series.notna()
                if not valid.any():
                    continue

                # Convert to numpy arrays for computation
                series_clean = series[valid].to_numpy(dtype=np.float64)
                weights_clean = weights_series[valid].to_numpy(dtype=np.float64)

                # Compute statistics
                mean, std, ci_lower, ci_upper = WeightedStats.compute_weighted_stats(
                    series_clean,
                    weights_clean
                )

                result = {
                    "timestamp": current_time,
                    "mean": mean,
                    "std": std,
                    "ci_lower": ci_lower,
                    "ci_upper": ci_upper
                }
                if self.group_col is not None:
                    result[self.group_col] = group_name
                results.append(result)

        return pd.DataFrame(results)

    def compute_latest_stats(self, columns: List[str], time_col: str = "timestamp", window_days: float = 3) -> pd.DataFrame:
        """
        Compute weighted statistics for the latest state, using all available data.
        Replaces the old compute_column_stats functionality with time-weighted calculations.
        
        Args:
            columns: List of columns to compute statistics for
            time_col: The timestamp column name
            window_days: The window size in days for the exponential weighting
        
        Returns:
            DataFrame with columns for each metric"s mean, std, ci_lower, and ci_upper
        """
        df = self.prepare_data(columns[0], time_col)  # Use first column to prepare data
        latest_time = df[time_col].max()
        
        results = []
        groups = [("all", df)] if self.group_col is None else df.groupby(self.group_col)

        for group_name, group_data in groups:
            group_stats = {}
            weights = WeightedStats.compute_time_weights(group_data[time_col], latest_time, window_days)

            for col in columns:
                series = pd.to_numeric(group_data[col], errors="coerce")
                # Create Series with same index as the data for proper alignment
                weights_series = pd.Series(weights, index=group_data.index)
                valid = series.notna() & weights_series.notna()
                if not valid.any():
                    continue

                series_clean = series[valid].to_numpy(dtype=np.float64)
                weights_clean = weights_series[valid].to_numpy(dtype=np.float64)

                mean, std, ci_lower, ci_upper = WeightedStats.compute_weighted_stats(
                    series_clean,
                    weights_clean
                )
                
                group_stats[f"{col}_mean"] = mean
                group_stats[f"{col}_std"] = std
                group_stats[f"{col}_ci_lower"] = ci_lower
                group_stats[f"{col}_ci_upper"] = ci_upper

            if self.group_col is not None:
                group_stats[self.group_col] = group_name
            results.append(group_stats)

        return pd.DataFrame(results)

    def reshape_to_long_format(self, wide_df: pd.DataFrame) -> pd.DataFrame:
        """
        Reshape wide format statistics to long format.
        Handles both grouped and ungrouped data.
        """
        # Make a copy to avoid modifying the original
        df = wide_df.copy()
        
        # Get all columns except group_col and std columns
        value_cols = [col for col in df.columns 
                     if col != self.group_col and not col.endswith('_std')]
        
        # Prepare the data for melting
        # First, create a list of metric names by removing suffixes
        metrics = sorted(set(col.rsplit('_', 1)[0] for col in value_cols))
        
        # Initialize the result DataFrame
        long_format = []
        
        # For each row in the original DataFrame
        for idx, row in df.iterrows():
            # For each metric
            for metric in metrics:
                entry = {
                    'metric': metric,
                    'mean': row.get(f'{metric}_mean', np.nan),
                    'ci_lower': row.get(f'{metric}_ci_lower', np.nan),
                    'ci_upper': row.get(f'{metric}_ci_upper', np.nan)
                }
                if self.group_col:
                    entry[self.group_col] = row[self.group_col]
                long_format.append(entry)
        
        # Convert to DataFrame
        result = pd.DataFrame(long_format)
        
        # Ensure proper column order (only if columns exist)
        cols = ([self.group_col] if self.group_col else []) + ['metric', 'mean', 'ci_lower', 'ci_upper']
        
        # Check if all required columns exist
        missing_cols = [c for c in cols if c not in result.columns]
        if missing_cols:
            # If result is empty or missing columns, return empty DataFrame with expected structure
            print(f"Warning: reshape_to_long_format - missing columns: {missing_cols}")
            print(f"Available columns: {result.columns.tolist()}")
            print(f"Result shape: {result.shape}")
            return pd.DataFrame(columns=cols)
        
        result = result[cols]
        
        return result

    def compute_score(self, stats_df: pd.DataFrame) -> pd.DataFrame:
        """
        Compute normalized score based on weighted metrics.
        """
        weights = {
            "coins_earned": 0.3,
            "coins_per_hour": 0.2,
            "cells_earned": 0.2,
            "cells_per_hour": 0.2,
            "reroll_shards_earned": 0.1
        }

        df = stats_df.copy()
        for metric in weights.keys():
            mean_col = f"{metric}_mean"
            if mean_col not in df.columns:
                continue
                
            max_val = df[mean_col].max()
            if max_val != 0 and not np.isnan(max_val):
                df[f"{metric}_normalized"] = df[mean_col] / max_val
            else:
                df[f"{metric}_normalized"] = 0

        df["score"] = sum(
            df[f"{metric}_normalized"] * weight 
            for metric, weight in weights.items() 
            if f"{metric}_normalized" in df.columns
        ) * 100

        return df


__all__ = ['TimeSeriesStats']
