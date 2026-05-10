import pandas as pd
import numpy as np
import re
from typing import Optional, Iterable

from .config import scale

def convert_abbreviated_number(s: str) -> Optional[float]:
    if not isinstance(s, str) or not s.strip():
        return None
    
    s = s.strip()

    # Sort suffixes by length to match longer ones first
    for suffix in sorted(scale.keys(), key=len, reverse=True):
        if s.endswith(suffix):
            # handle empty suffix correctly
            if len(suffix) > 0:
                number_part = s[:-len(suffix)]
            else:
                number_part = s
            try:
                number = float(number_part)
                return number * scale[suffix]
            except ValueError:
                return None

    return None



def abbreviate_value(num: Optional[float], suffix_format="{unit}") -> str:
    """
    Abbreviate a number using scale suffixes (K, M, B, T, etc.) from config.scale.
    
    Args:
        num: The number to abbreviate
        suffix_format: Format string for the suffix (default: "{unit}")
    
    Returns:
        Abbreviated string representation of the number
    """
    if num is None or num <= 0:
        return "0"

    # Build lookup from scale dict, sorted by value descending (largest first)
    # Map to display format: e.g., "K" -> " K", "" -> ""
    lookup = [(f" {unit}" if unit else "", factor) for unit, factor in sorted(scale.items(), key=lambda x: x[1], reverse=True)]

    for unit, factor in lookup:
        try:
            if num >= factor:
                suffix = suffix_format.format(unit=unit)
                # Format cleanly: use full numbers, no unnecessary decimals
                scaled = num / factor
                if scaled == int(scaled):
                    return f"{int(scaled)}{suffix}"
                elif scaled < 10:
                    return f"{scaled:.1f}{suffix}"
                else:
                    return f"{scaled:.0f}{suffix}"
        except ValueError:
            formatted = num
            if formatted == int(formatted):
                return str(int(formatted))
            elif formatted < 10:
                return f"{formatted:.1f}"
            else:
                return f"{formatted:.0f}"
    # For very small numbers, format cleanly
    if num == int(num):
        return str(int(num))
    elif num < 10:
        return f"{num:.1f}"
    else:
        return f"{num:.0f}"


def abbreviate_value_sig(num: Optional[float], sig_digits: int = 3, suffix_format: str = "{unit}") -> str:
    """Abbreviate using engineering suffixes while keeping a fixed number of significant digits."""
    if num is None:
        return "0"

    try:
        value = float(num)
    except (TypeError, ValueError):
        return "0"

    if value == 0:
        return "0"

    sign = "-" if value < 0 else ""
    abs_value = abs(value)
    sig_digits = max(1, int(sig_digits))

    lookup = sorted(scale.items(), key=lambda x: x[1], reverse=True)
    chosen_unit = ""
    chosen_factor = 1.0
    for unit, factor in lookup:
        if abs_value >= factor:
            chosen_unit = unit
            chosen_factor = float(factor)
            break

    scaled = abs_value / chosen_factor

    if scaled <= 0:
        decimals = sig_digits - 1
    else:
        digits_before = int(np.floor(np.log10(scaled))) + 1
        decimals = max(0, sig_digits - digits_before)

    formatted = f"{scaled:.{decimals}f}"
    suffix = suffix_format.format(unit=f" {chosen_unit}" if chosen_unit else "")
    return f"{sign}{formatted}{suffix}"


def format_display_value(num: Optional[float], sig_digits: int = 3, suffix: str = "") -> str:
    """Format non-axis UI values with fixed significant digits and optional suffix."""
    base = abbreviate_value_sig(num, sig_digits=sig_digits)
    if suffix:
        return f"{base}{suffix}"
    return base

from typing import Union, List

def apply_abbreviation(df: pd.DataFrame, columns: Union[str, List[str]],suffix_format="{unit}") -> pd.DataFrame:
    #Convert single column name to list
    if isinstance(columns, str):
        columns = [columns]

    for col in columns:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: abbreviate_value(x, suffix_format))
    return df




def axis_abbreviation(x: float, pos:float) -> str:
    return abbreviate_value(x)


def generate_abbreviation_ticks(min_val: float, max_val: float, num_ticks: int = 5) -> tuple[list[float], list[str]]:
    """
    Generate custom tick values and labels for Plotly axes using abbreviation formatting.
    
    Args:
        min_val: Minimum value on the axis
        max_val: Maximum value on the axis
        num_ticks: Desired number of ticks (approximate)
    
    Returns:
        Tuple of (tick_values, tick_labels) for use with Plotly's tickvals/ticktext
    """
    # Ensure y-axis always starts at 0
    if max_val <= 0:
        max_val = 1.0
    min_val = 0.0
    
    # Generate roughly evenly-spaced tick values
    tick_values = np.linspace(min_val, max_val, num_ticks)
    tick_labels = [abbreviate_value(tv) for tv in tick_values]
    
    return tick_values.tolist(), tick_labels


def time_to_decimal_hours(time_str: str) -> Optional[float]:
    """
    Convert a time-like value to decimal hours.

    Supported inputs:
    - Strings like "1h 30m 15s", "45m", "1.5h"
    - Colon-separated strings like "HH:MM:SS" or "MM:SS"
    - Numeric values (int/float) — returned as-is (assumed to already be hours)
    - None/NaN -> None

    Return value is rounded to 2 decimal places or None if input can't be parsed.
    """
    # Handle missing/NaN values
    try:
        if pd.isna(time_str):
            return None
    except Exception:
        # pd.isna may throw for some custom types — fall through to string handling
        pass

    # If caller passed a numeric value we assume it is already in hours
    if isinstance(time_str, (int, float)):
        # Interpret numeric values as seconds (new format)
        return round(float(time_str) / 3600.0, 2)

    s = str(time_str).strip()
    if not s:
        return None

    # Handle colon separated times like HH:MM:SS or MM:SS
    if ":" in s:
        parts = [float(p) for p in s.split(":") if p != ""]
        # Support MM:SS and HH:MM:SS
        if len(parts) == 2:  # MM:SS
            minutes, seconds = parts
            total_hours = minutes / 60 + seconds / 3600
            return round(total_hours, 2)
        elif len(parts) >= 3:  # H:M:S or H:M:S:<ignore extras>
            hours, minutes, seconds = parts[-3], parts[-2], parts[-1]
            total_hours = hours + minutes / 60 + seconds / 3600
            return round(total_hours, 2)

    # Extract hours, minutes, and seconds using regex (allow decimals)
    match = re.match(r'(?:(\d+(?:\.\d+)?)h)?\s*(?:(\d+(?:\.\d+)?)m)?\s*(?:(\d+(?:\.\d+)?)s)?', s)
    if match and any(match.groups()):
        hours = float(match.group(1)) if match.group(1) else 0.0
        minutes = float(match.group(2)) if match.group(2) else 0.0
        seconds = float(match.group(3)) if match.group(3) else 0.0
        total_hours = hours + minutes / 60 + seconds / 3600
        return round(total_hours, 2)

    # Fallback: if the string is a number in text form, try to parse it as hours
    try:
        return round(float(s), 2)
    except ValueError:
        return None

    hours = int(match.group(1)) if match.group(1) else 0
    minutes = int(match.group(2)) if match.group(2) else 0
    seconds = int(match.group(3)) if match.group(3) else 0

    # Convert to decimal hours
    total_hours = hours + minutes / 60 + seconds / 3600
    return round(total_hours, 2)



def pad_tier(tier: str) -> str:
    # Match numeric part followed optionally by a '+'
    match = re.match(r'^(\d+)(\+?)$', str(tier).strip())
    if not match:
        return str(tier)  # fallback if format is unexpected

    number, plus = match.groups()
    padded = number.zfill(2)
    return padded + plus
