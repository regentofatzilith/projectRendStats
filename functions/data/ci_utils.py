"""Confidence interval extraction helpers."""

import pandas as pd


def get_ci_triplet(
    df: pd.DataFrame,
    metric: str,
    level_col: str = 'level_1',
    clamp_lower_zero: bool = False,
) -> tuple[float, float, float] | None:
    """Return (mean, ci_lower, ci_upper) for a metric from confidence rows."""
    try:
        mean_val = float(df[df[level_col] == 'mean'][metric].iloc[0])
        lower_val = float(df[df[level_col] == 'ci_lower'][metric].iloc[0])
        upper_val = float(df[df[level_col] == 'ci_upper'][metric].iloc[0])
    except Exception:
        return None
    if clamp_lower_zero:
        lower_val = max(0.0, lower_val)
    return mean_val, lower_val, upper_val
