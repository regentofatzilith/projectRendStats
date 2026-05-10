"""
Generic Formatting Utilities - Display formatting for all data types.

Provides reusable functions for formatting numbers, times, and other values
for display in the UI.

Usage:
    from functions.computation.formatting import format_time, format_number
    
    time_str = format_time(3600)  # "1h 0m"
    num_str = format_number(1234567)  # "1,234,567"
"""

from typing import Union, Dict, Any, Optional
from datetime import timedelta


def format_number(
    value: Union[int, float],
    decimal_places: int = 1,
    thousand_sep: bool = True
) -> str:
    """
    Format a number for display with optional thousands separator.
    
    Args:
        value: Number to format
        decimal_places: Number of decimal places (0 for integers)
        thousand_sep: Whether to add thousands separators
        
    Returns:
        str: Formatted number
        
    Examples:
        >>> format_number(1234567)
        '1,234,567.0'
        
        >>> format_number(1234567, decimal_places=0)
        '1,234,567'
        
        >>> format_number(3.14159, decimal_places=2)
        '3.14'
    """
    if decimal_places == 0:
        formatted = f"{int(value):,}" if thousand_sep else str(int(value))
    else:
        formatted = f"{value:.{decimal_places}f}"
        if thousand_sep:
            # Split into integer and decimal parts
            parts = formatted.split(".")
            parts[0] = f"{int(parts[0]):,}"
            formatted = ".".join(parts)
    
    return formatted


def format_percentage(
    value: float,
    decimal_places: int = 1,
    include_sign: bool = False
) -> str:
    """
    Format a percentage value for display.
    
    Args:
        value: Value as decimal (e.g., 0.45 for 45%)
        decimal_places: Number of decimal places
        include_sign: Whether to include + prefix for positive values
        
    Returns:
        str: Formatted percentage (e.g., "45.0%", "+45.0%")
        
    Examples:
        >>> format_percentage(0.45)
        '45.0%'
        
        >>> format_percentage(0.45, include_sign=True)
        '+45.0%'
        
        >>> format_percentage(-0.15)
        '-15.0%'
    """
    percent_value = value * 100
    
    if include_sign:
        sign = "+" if percent_value >= 0 else ""
        return f"{sign}{percent_value:.{decimal_places}f}%"
    
    return f"{percent_value:.{decimal_places}f}%"


def format_time(
    seconds: float,
    include_seconds: bool = True,
    compact: bool = False
) -> str:
    """
    Format seconds into human-readable time string.
    
    Args:
        seconds: Number of seconds
        include_seconds: Whether to include seconds in output
        compact: If True, returns abbreviated form (e.g., "1h 30m")
                If False, returns full form (e.g., "1 hour, 30 minutes")
        
    Returns:
        str: Formatted time
        
    Examples:
        >>> format_time(3661)
        '1h 1m 1s'
        
        >>> format_time(3661, include_seconds=False)
        '1h 1m'
        
        >>> format_time(3661, compact=False)
        '1 hour, 1 minute, 1 second'
    """
    td = timedelta(seconds=seconds)
    total_seconds = int(td.total_seconds())
    
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    secs = total_seconds % 60
    
    if compact:
        parts = []
        if hours > 0:
            parts.append(f"{hours}h")
        if minutes > 0:
            parts.append(f"{minutes}m")
        if include_seconds and secs > 0:
            parts.append(f"{secs}s")
        elif not parts:  # If no hours/mins, show seconds
            parts.append(f"{secs}s")
        
        return " ".join(parts)
    else:
        parts = []
        if hours > 0:
            parts.append(f"{hours} {'hour' if hours == 1 else 'hours'}")
        if minutes > 0:
            parts.append(f"{minutes} {'minute' if minutes == 1 else 'minutes'}")
        if include_seconds and secs > 0:
            parts.append(f"{secs} {'second' if secs == 1 else 'seconds'}")
        
        if not parts:
            return "0 seconds"
        
        if len(parts) == 1:
            return parts[0]
        elif len(parts) == 2:
            return f"{parts[0]}, {parts[1]}"
        else:
            return ", ".join(parts[:-1]) + f", {parts[-1]}"


def format_duration(
    seconds: float,
    include_ms: bool = False
) -> str:
    """
    Format duration (shorter than format_time, always compact).
    
    Args:
        seconds: Duration in seconds
        include_ms: Whether to include milliseconds
        
    Returns:
        str: Short format like "1m 30s"
        
    Examples:
        >>> format_duration(90)
        '1m 30s'
        
        >>> format_duration(90, include_ms=True)
        '1m 30.0s'
    """
    return format_time(seconds, include_seconds=True, compact=True)


def format_unit_value(
    value: float,
    unit: str = "",
    decimal_places: int = 1
) -> str:
    """
    Format a value with its unit.
    
    Args:
        value: Numerical value
        unit: Unit string (e.g., "s", "ms", "%", "×")
        decimal_places: Number of decimal places
        
    Returns:
        str: Value with unit
        
    Examples:
        >>> format_unit_value(41.0, "s")
        '41.0s'
        
        >>> format_unit_value(0.45, "%")
        '45.0%'
    """
    if not unit:
        return f"{value:.{decimal_places}f}"
    
    return f"{value:.{decimal_places}f}{unit}"


def format_delta(
    value: float,
    unit: str = "",
    decimal_places: int = 1,
    show_sign: bool = True
) -> str:
    """
    Format a change/delta value with optional sign.
    
    Args:
        value: Change value
        unit: Unit string
        decimal_places: Number of decimal places
        show_sign: Whether to show + for positive values
        
    Returns:
        str: Formatted delta
        
    Examples:
        >>> format_delta(5.0, "s")
        '+5.0s'
        
        >>> format_delta(-2.5, "×")
        '-2.5×'
    """
    sign = ""
    if show_sign and value > 0:
        sign = "+"
    
    formatted_value = f"{abs(value):.{decimal_places}f}{unit}"
    return f"{sign if value >= 0 else '-'}{formatted_value}"


def format_range(
    min_val: float,
    max_val: float,
    unit: str = "",
    decimal_places: int = 1
) -> str:
    """
    Format a range of values.
    
    Args:
        min_val: Minimum value
        max_val: Maximum value
        unit: Unit string
        decimal_places: Number of decimal places
        
    Returns:
        str: Formatted range like "10.0s - 50.0s"
        
    Examples:
        >>> format_range(10.0, 50.0, "s")
        '10.0s - 50.0s'
    """
    min_str = format_unit_value(min_val, unit, decimal_places)
    max_str = format_unit_value(max_val, unit, decimal_places)
    return f"{min_str} - {max_str}"


def truncate_string(text: str, max_length: int = 50, suffix: str = "...") -> str:
    """
    Truncate a string to maximum length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to append if truncated
        
    Returns:
        str: Truncated text
        
    Examples:
        >>> truncate_string("This is a very long string", max_length=10)
        'This is...'
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def emphasize_value(
    value: float,
    threshold_low: float,
    threshold_high: float,
    decimal_places: int = 1,
    unit: str = ""
) -> Dict[str, Any]:
    """
    Format value and determine emphasis level based on threshold.
    
    Useful for color-coding values in the UI.
    
    Args:
        value: Value to format
        threshold_low: Value below which is "low" (bad)
        threshold_high: Value above which is "high" (good)
        decimal_places: Number of decimal places
        unit: Unit string
        
    Returns:
        Dict with:
        {
            "formatted": str (formatted value),
            "level": str ("low", "medium", "high"),
            "color": str ("danger", "warning", "success")
        }
        
    Examples:
        >>> result = emphasize_value(80, 50, 100)
        >>> print(result)
        {'formatted': '80.0', 'level': 'high', 'color': 'success'}
    """
    formatted = format_unit_value(value, unit, decimal_places)
    
    if value < threshold_low:
        level = "low"
        color = "danger"
    elif value > threshold_high:
        level = "high"
        color = "success"
    else:
        level = "medium"
        color = "warning"
    
    return {
        "formatted": formatted,
        "level": level,
        "color": color,
    }
