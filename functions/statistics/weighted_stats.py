"""Weighted statistics computation with exponential time decay."""

import pandas as pd
import numpy as np
from typing import Tuple

from .scipy_fallback import stats


class WeightedStats:
    """
    Core class for computing weighted statistics with exponential time decay.
    """
    @staticmethod
    def compute_time_weights(timestamps: pd.Series, reference_time: pd.Timestamp, window_days: float = 3) -> np.ndarray:
        """Compute exponential time-based weights."""        
        timestamps_clean = pd.to_datetime(timestamps).dt.tz_localize(None)
        time_diff = pd.Series([(reference_time - ts).total_seconds() for ts in timestamps_clean])
        return np.exp(-time_diff.to_numpy() / (60 * 60 * 24 * window_days))

    @staticmethod
    def compute_weighted_stats(series: np.ndarray | pd.Series, weights: np.ndarray | pd.Series) -> Tuple[float, float, float, float]:
        """Compute weighted mean, variance, and confidence intervals."""
        # Convert inputs to numpy arrays
        series_array = np.asarray(series, dtype=np.float64)
        weights_array = np.asarray(weights, dtype=np.float64)
        
        if len(series_array) == 0:
            weighted_mean = weighted_std = sem = ci_lower = ci_upper = float(np.nan)
            return weighted_mean, weighted_std, ci_lower, ci_upper

        weighted_mean = float(np.average(series_array, weights=weights_array))
        sum_weights = np.sum(weights_array)
        sum_weights_sq = np.sum(weights_array ** 2)
        # Weighted sample variance with Bessel's correction
        # Use explicit np.float64 for broadcasting to satisfy type checkers
        numerator = np.sum(weights_array * (series_array - np.float64(weighted_mean)) ** 2)
        denominator = sum_weights - (sum_weights_sq / sum_weights) if sum_weights != 0 else np.nan
        weighted_var = numerator / denominator if denominator > 0 else np.nan
        weighted_std = float(np.sqrt(weighted_var)) if weighted_var >= 0 else np.nan

        # Effective sample size for weighted data (Kish, 1965): n_eff = (sum w)^2 / sum(w^2)
        n_eff = (sum_weights ** 2) / sum_weights_sq if sum_weights_sq > 0 else float(len(series_array))
        n_eff = max(n_eff, 3.0)   # floor to avoid exploding sem

        # Standard error uses weighted standard deviation divided by sqrt(effective sample size)
        sem = float(weighted_std / np.sqrt(n_eff)) if (weighted_std >= 0 and n_eff > 0) else np.nan

        # Degrees of freedom for t-interval: use floor(n_eff) - 1 but at least 1
        try:
            df = max(1, int(np.floor(n_eff)) - 1)
        except Exception:
            df = max(1, int(len(series_array) - 1))

        if n_eff > 1 and np.isfinite(sem) and sem > 0:
            # 95% t-based confidence interval around the weighted mean
            ci = stats.t.interval(0.95, df=df, loc=weighted_mean, scale=sem)
            ci_lower = max(0, ci[0])
            ci_upper = ci[1]
        else:
            ci_lower = ci_upper = weighted_mean

        return weighted_mean, weighted_std, ci_lower, ci_upper


__all__ = ['WeightedStats']
