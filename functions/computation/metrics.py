"""
Metrics Calculation Layer - Aggregate and compute metrics from raw data.

Provides stateless functions for computing metrics, aggregations, and statistics
used across the application pages.

Usage:
    from functions.computation.metrics import calculate_uptime_efficiency
    
    efficiency = calculate_uptime_efficiency(active_time=100, total_time=120)
"""

from typing import Dict, List, Any, Optional, Tuple
from statistics import mean, median, stdev


def calculate_average(values: List[float]) -> Optional[float]:
    """
    Calculate average of numeric values.
    
    Args:
        values: List of numeric values
        
    Returns:
        float: Average value, or None if empty
        
    Examples:
        >>> calculate_average([10, 20, 30])
        20.0
    """
    if not values:
        return None
    return mean(values)


def calculate_median(values: List[float]) -> Optional[float]:
    """
    Calculate median of numeric values.
    
    Args:
        values: List of numeric values
        
    Returns:
        float: Median value, or None if empty
        
    Examples:
        >>> calculate_median([10, 20, 30])
        20.0
    """
    if not values:
        return None
    return median(values)


def calculate_std_dev(values: List[float]) -> Optional[float]:
    """
    Calculate standard deviation of numeric values.
    
    Args:
        values: List of numeric values
        
    Returns:
        float: Standard deviation, or None if less than 2 values
        
    Examples:
        >>> calculate_std_dev([10, 20, 30])
        10.0
    """
    if len(values) < 2:
        return None
    return stdev(values)


def calculate_min_max_avg(values: List[float]) -> Dict[str, Optional[float]]:
    """
    Calculate min, max, and average for a list of values.
    
    Args:
        values: List of numeric values
        
    Returns:
        Dict with min, max, avg (or None if empty)
        
    Examples:
        >>> calculate_min_max_avg([10, 20, 30])
        {'min': 10.0, 'max': 30.0, 'avg': 20.0}
    """
    if not values:
        return {"min": None, "max": None, "avg": None}
    
    return {
        "min": min(values),
        "max": max(values),
        "avg": mean(values),
    }


def calculate_percentiles(
    values: List[float],
    percentiles: List[int] = [25, 50, 75, 90, 95]
) -> Dict[str, float]:
    """
    Calculate percentile values.
    
    Args:
        values: List of numeric values
        percentiles: List of percentile values (e.g., [25, 50, 75])
        
    Returns:
        Dict mapping percentile names to values
        
    Examples:
        >>> calculate_percentiles([1,2,3,4,5], percentiles=[25, 50, 75])
        {'p25': 1.5, 'p50': 3.0, 'p75': 4.5}
    """
    if not values:
        return {}
    
    sorted_vals = sorted(values)
    result = {}
    
    for p in percentiles:
        # Linear interpolation between values
        idx = (len(sorted_vals) - 1) * p / 100
        lower_idx = int(idx)
        upper_idx = min(lower_idx + 1, len(sorted_vals) - 1)
        fraction = idx - lower_idx
        
        percentile_val = (
            sorted_vals[lower_idx] * (1 - fraction) +
            sorted_vals[upper_idx] * fraction
        )
        result[f"p{p}"] = percentile_val
    
    return result


def calculate_uptime_efficiency(
    active_time: float,
    total_time: float
) -> float:
    """
    Calculate uptime efficiency as a percentage.
    
    Args:
        active_time: Time when ability is active
        total_time: Total elapsed time
        
    Returns:
        float: Efficiency as decimal (0.0 to 1.0)
        
    Examples:
        >>> calculate_uptime_efficiency(100, 120)
        0.833...
    """
    if total_time == 0:
        return 0.0
    
    return active_time / total_time


def calculate_cooldown_reduction(
    base_cooldown: float,
    reduction_percent: float
) -> float:
    """
    Calculate reduced cooldown from reduction percentage.
    
    Args:
        base_cooldown: Original cooldown time
        reduction_percent: Reduction percentage (0-1, e.g., 0.25 for 25%)
        
    Returns:
        float: Reduced cooldown time
        
    Examples:
        >>> calculate_cooldown_reduction(10.0, 0.25)
        7.5
    """
    return base_cooldown * (1 - reduction_percent)


def calculate_damage_multiplier(
    base_damage: float,
    multiplier_value: float
) -> float:
    """
    Calculate total damage with multiplier applied.
    
    Args:
        base_damage: Base damage value
        multiplier_value: Multiplier (e.g., 1.5 for 150%)
        
    Returns:
        float: Total damage
        
    Examples:
        >>> calculate_damage_multiplier(100, 1.5)
        150.0
    """
    return base_damage * multiplier_value


def calculate_stack_value(
    individual_value: float,
    stack_count: int,
    stack_bonus: bool = True
) -> float:
    """
    Calculate value when stacking (additive or multiplicative).
    
    Args:
        individual_value: Base value per stack
        stack_count: Number of stacks
        stack_bonus: If True, values add; if False, multiplicative
        
    Returns:
        float: Total stacked value
        
    Examples:
        >>> calculate_stack_value(10, 5)
        50.0
        
        >>> calculate_stack_value(10, 5, stack_bonus=False)
        61040.0
    """
    if stack_bonus:
        return individual_value * stack_count
    else:
        # Multiplicative: (1 + value) ^ count - 1
        return ((1 + individual_value) ** stack_count) - 1


def calculate_weighted_average(
    values: List[float],
    weights: List[float]
) -> Optional[float]:
    """
    Calculate weighted average of values.
    
    Args:
        values: List of values
        weights: List of weights (should sum to 1.0 ideally)
        
    Returns:
        float: Weighted average, or None if empty
        
    Examples:
        >>> calculate_weighted_average([10, 20], [0.3, 0.7])
        17.0
    """
    if not values or len(values) != len(weights):
        return None
    
    total_weight = sum(weights)
    if total_weight == 0:
        return None
    
    weighted_sum = sum(v * w for v, w in zip(values, weights))
    return weighted_sum / total_weight


def calculate_efficiency_score(
    metrics_dict: Dict[str, float],
    weights: Dict[str, float]
) -> float:
    """
    Calculate efficiency score from multiple metrics.
    
    Args:
        metrics_dict: Dict of metric names to values (0-1 range)
        weights: Dict of metric names to weights (should sum to 1.0)
        
    Returns:
        float: Weighted efficiency score (0-1)
        
    Examples:
        >>> metrics = {'dmg': 0.8, 'uptime': 0.9}
        >>> weights = {'dmg': 0.4, 'uptime': 0.6}
        >>> calculate_efficiency_score(metrics, weights)
        0.86
    """
    score = 0.0
    total_weight = sum(weights.get(name, 0) for name in metrics_dict)
    
    if total_weight == 0:
        return 0.0
    
    for name, value in metrics_dict.items():
        weight = weights.get(name, 0.0)
        score += value * weight
    
    return score / total_weight


def calculate_cumulative_values(values: List[float]) -> List[float]:
    """
    Calculate cumulative sum of values.
    
    Args:
        values: List of values
        
    Returns:
        List[float]: Cumulative values
        
    Examples:
        >>> calculate_cumulative_values([1, 2, 3, 4])
        [1.0, 3.0, 6.0, 10.0]
    """
    cumulative = []
    total = 0
    
    for value in values:
        total += value
        cumulative.append(total)
    
    return cumulative


def calculate_rolling_average(
    values: List[float],
    window_size: int
) -> List[Optional[float]]:
    """
    Calculate rolling average over a window.
    
    Args:
        values: List of values
        window_size: Size of rolling window
        
    Returns:
        List[Optional[float]]: Rolling averages (None for incomplete windows)
        
    Examples:
        >>> calculate_rolling_average([1, 2, 3, 4, 5], window_size=3)
        [None, None, 2.0, 3.0, 4.0]
    """
    if window_size <= 0:
        return []

    result: List[Optional[float]] = [None] * (window_size - 1)
    
    for i in range(window_size - 1, len(values)):
        window = values[i - window_size + 1:i + 1]
        result.append(mean(window))
    
    return result


def normalize_values(
    values: List[float],
    min_range: float = 0.0,
    max_range: float = 1.0
) -> List[float]:
    """
    Normalize values to a range.
    
    Args:
        values: List of values
        min_range: Minimum value of output range
        max_range: Maximum value of output range
        
    Returns:
        List[float]: Normalized values
        
    Examples:
        >>> normalize_values([10, 20, 30])
        [0.0, 0.5, 1.0]
    """
    if not values:
        return []
    
    val_min = min(values)
    val_max = max(values)
    range_diff = val_max - val_min
    
    if range_diff == 0:
        # All values are the same
        return [min_range] * len(values)
    
    normalized = []
    for val in values:
        # Map to 0-1, then scale to range
        norm_val = (val - val_min) / range_diff
        scaled_val = norm_val * (max_range - min_range) + min_range
        normalized.append(scaled_val)
    
    return normalized


def calculate_delta_values(values: List[float]) -> List[float]:
    """
    Calculate differences between consecutive values.
    
    Args:
        values: List of values
        
    Returns:
        List[float]: Delta values (one less than input)
        
    Examples:
        >>> calculate_delta_values([10, 15, 25, 30])
        [5.0, 10.0, 5.0]
    """
    deltas = []
    for i in range(1, len(values)):
        deltas.append(values[i] - values[i - 1])
    
    return deltas


def calculate_rate_of_change(
    values: List[float],
    time_intervals: List[float]
) -> Optional[float]:
    """
    Calculate average rate of change over time.
    
    Args:
        values: List of values at different times
        time_intervals: List of time intervals between values
        
    Returns:
        float: Average rate of change per time unit, or None if invalid
        
    Examples:
        >>> calculate_rate_of_change([10, 20, 30], [1, 2])
        10.0
    """
    if not values or len(values) != len(time_intervals) + 1:
        return None
    
    total_change = values[-1] - values[0]
    total_time = sum(time_intervals)
    
    if total_time == 0:
        return None
    
    return total_change / total_time


def categorize_value(
    value: float,
    thresholds: List[float],
    categories: List[str]
) -> str:
    """
    Categorize a value based on thresholds.
    
    Args:
        value: Value to categorize
        thresholds: Sorted list of threshold values
        categories: List of category names (should be len(thresholds) + 1)
        
    Returns:
        str: Category name
        
    Examples:
        >>> categorize_value(75, [50, 80], ['Low', 'Medium', 'High'])
        'Medium'
    """
    if len(categories) != len(thresholds) + 1:
        raise ValueError("Categories count must be thresholds count + 1")
    
    for i, threshold in enumerate(thresholds):
        if value < threshold:
            return categories[i]
    
    return categories[-1]


def aggregate_metrics(
    data_points: List[Dict[str, float]],
    metric_keys: List[str]
) -> Dict[str, Dict[str, float]]:
    """
    Aggregate metrics from multiple data points.
    
    Args:
        data_points: List of dicts with metric values
        metric_keys: Keys to aggregate
        
    Returns:
        Dict mapping metric names to min/max/avg
        
    Examples:
        >>> data = [{'dmg': 100}, {'dmg': 200}]
        >>> aggregate_metrics(data, ['dmg'])
        {'dmg': {'min': 100, 'max': 200, 'avg': 150.0}}
    """
    result = {}
    
    for key in metric_keys:
        values = [dp.get(key, 0) for dp in data_points if key in dp]
        result[key] = calculate_min_max_avg(values)
    
    return result
