"""
Weapon Data Formatting - Transform weapon data for display.

Provides functions to format Ultimate Weapon data from consolidated/detailed
sources into display-ready formats for cards, tables, and summaries.

Usage:
    from functions.computation.weapons import get_weapon_cards
    from functions.data import DataManager
    
    data_mgr = DataManager.get_instance()
    all_weapons = data_mgr.get_all_weapons(detailed=True)
    
    cards = get_weapon_cards(all_weapons)
    # Ready to render in Dash
"""

from typing import Dict, Any, List, Tuple, Optional


def _format_value_auto(value: float) -> str:
    """Format small non-zero values with enough precision for readability."""
    abs_value = abs(float(value))
    if abs_value == 0:
        return "0.0"
    if abs_value < 0.1:
        return f"{value:.3f}"
    if abs_value < 1:
        return f"{value:.2f}"
    return f"{value:.1f}"


def format_parameter_value(value: float, unit: str = "") -> str:
    """
    Format a numerical value with its unit for display.
    
    Args:
        value: Numerical value to format
        unit: Unit string (e.g., "s", "%", "×", "#")
        
    Returns:
        str: Formatted value (e.g., "41.0s", "20.0%")
        
    Examples:
        >>> format_parameter_value(41.0, "s")
        '41.0s'
        
        >>> format_parameter_value(4.45, "×")
        '4.45×'
    """
    formatted = _format_value_auto(value)
    if unit:
        return f"{formatted}{unit}"
    return formatted


def format_parameter_component(value: float, prefix: str = "", unit: str = "") -> str:
    """
    Format a component value (UW, Lab, Module, Relic) for display.
    
    Args:
        value: Numerical value
        prefix: Prefix like "+", "-" (auto-determined if empty)
        unit: Unit string
        
    Returns:
        str: Formatted value
        
    Examples:
        >>> format_parameter_component(2.45, unit="×")
        '+2.45×'
        
        >>> format_parameter_component(-7.0, unit="s")
        '-7.0s'
    """
    if not prefix:
        prefix = "+" if value >= 0 else ""
    
    formatted_value = f"{_format_value_auto(value)}{unit}"
    return f"{prefix}{formatted_value}"


def format_parameter_breakdown(param_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Format all components of a parameter for display.
    
    Args:
        param_data: Parameter data from UltimateWeaponAnalyzer.get_detailed()
                   Format: {"uw_level": int, "uw_value": float, "labs_value": float, ...}
                   
    Returns:
        Dict with keys: levels_display, labs_display, module_display, relic_display, total_display
        
    Example:
        >>> param_data = {
        ...     "uw_level": 7,
        ...     "uw_target_level": 16,
        ...     "uw_value": 12.0,
        ...     "labs_level": 29,
        ...     "labs_value": 29.0,
        ...     "module_value": 0.0,
        ...     "relic_value": 0.0,
        ...     "total_value": 41.0,
        ...     "unit": "s"
        ... }
        >>> formatted = format_parameter_breakdown(param_data)
        >>> print(formatted["levels_display"])
        'Lvl 7/16: 12.0s'
    """
    unit = param_data.get("unit", "")
    
    # Format UW Effect with level
    uw_level = param_data.get("uw_level", 0)
    uw_target = param_data.get("uw_target_level", 0)
    uw_value = param_data.get("uw_value", 0.0)
    levels_supported = bool(param_data.get("levels_supported", True))
    
    uw_level_str = f"{uw_level}/{uw_target}" if uw_target > 0 else f"{uw_level}"
    levels_display = (
        f"Lvl {uw_level_str}: {format_parameter_value(uw_value, unit)}"
        if levels_supported else "N/A"
    )
    
    # Format Labs Effect with level
    labs_level = param_data.get("labs_level", 0)
    labs_value = param_data.get("labs_value", 0.0)
    labs_supported = bool(param_data.get("labs_supported", False))

    # Read module/relic early so unlock-toggle detection can use them.
    module_value = param_data.get("module_value", 0.0)
    relic_value = param_data.get("relic_value", 0.0)

    is_unlock_toggle = (
        levels_supported is False
        and labs_supported is True
        and module_value == 0.0
        and relic_value == 0.0
        and uw_value == 0.0
        and float(labs_value) in (0.0, 1.0)
        and int(labs_level) in (0, 1)
    )
    
    labs_level_str = f"{labs_level}" if labs_level > 0 else "0"
    if labs_supported:
        if is_unlock_toggle:
            labs_display = f"Lvl {labs_level_str}: {'Unlocked' if int(labs_level) > 0 else 'Locked'}"
        else:
            labs_display = f"Lvl {labs_level_str}: {format_parameter_component(labs_value, unit=unit)}"
    else:
        labs_display = "N/A"
    
    # Format Module and Relic Effects
    module_supported = bool(param_data.get("module_supported", False))
    relic_supported = bool(param_data.get("relic_supported", False))
    
    module_display = (
        format_parameter_component(module_value, unit=unit) if module_value != 0 else "None"
    ) if module_supported else "N/A"
    relic_display = (
        format_parameter_component(relic_value, unit=unit) if relic_value != 0 else "None"
    ) if relic_supported else "N/A"
    
    # Format Total
    total_value = param_data.get("total_value", 0.0)
    total_display = "Unlocked" if is_unlock_toggle and float(total_value) >= 1.0 else (
        "Locked" if is_unlock_toggle else format_parameter_value(total_value, unit)
    )
    
    return {
        "levels_display": levels_display,
        "labs_display": labs_display,
        "module_display": module_display,
        "relic_display": relic_display,
        "total_display": total_display,
    }


def format_single_parameter(
    param_name: str,
    param_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Transform a single parameter into display-ready format.
    
    Args:
        param_name: Name of parameter (e.g., "Duration", "Cooldown")
        param_data: Parameter breakdown from UltimateWeaponAnalyzer
        
    Returns:
        Dict with all formatting info:
        {
            "name": str,
            "levels_display": str,
            "labs_display": str,
            "module_display": str,
            "relic_display": str,
            "total_display": str,
        }
    """
    breakdown = format_parameter_breakdown(param_data)
    
    return {
        "name": param_name,
        "levels_display": breakdown["levels_display"],
        "labs_display": breakdown["labs_display"],
        "module_display": breakdown["module_display"],
        "relic_display": breakdown["relic_display"],
        "total_display": breakdown["total_display"],
        "levels_supported": bool(param_data.get("levels_supported", True)),
        "labs_supported": bool(param_data.get("labs_supported", False)),
        "module_supported": bool(param_data.get("module_supported", False)),
        "relic_supported": bool(param_data.get("relic_supported", False)),
        "available_effect_sources": list(param_data.get("available_effect_sources", [])),
        "has_any_effect_source": bool(param_data.get("has_any_effect_source", False)),
    }


def format_weapon_detailed(
    weapon_name: str,
    weapon_detailed: Dict[str, Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Transform a weapon's detailed data into display-ready format.
    
    Args:
        weapon_name: Name of the weapon
        weapon_detailed: Dict of parameters with their breakdowns
                        Form: {"Duration": {"uw_level": ..., ...}, ...}
                        
    Returns:
        Dict with weapon info ready for cards:
        {
            "name": str,
            "parameters": [
                {"name": str, "levels_display": str, "labs_display": str, ...},
                ...
            ]
        }
    """
    parameters = []
    
    for param_name in sorted(weapon_detailed.keys()):
        param_data = weapon_detailed[param_name]
        
        if not isinstance(param_data, dict):
            continue
        
        formatted_param = format_single_parameter(param_name, param_data)
        parameters.append(formatted_param)
    
    return {
        "name": weapon_name,
        "parameters": parameters,
    }


def get_weapon_cards(
    all_weapons_detailed: Dict[str, Dict[str, Any]]
) -> Dict[str, Dict[str, Any]]:
    """
    Transform all weapons' detailed data into card format.
    
    This is the main function used by uw_overview.py to get display-ready data.
    
    Args:
        all_weapons_detailed: Dict with all weapons from DataManager.get_all_weapons(detailed=True)
                             Form: {"Chrono Field": {"Duration": {...}, ...}, ...}
        
    Returns:
        Dict of weapons, each formatted for card display:
        {
            "Chrono Field": {
                "name": "Chrono Field",
                "parameters": [
                    {"name": "Duration", "levels_display": "Lvl 7/16: 12.0s", ...},
                    ...
                ]
            },
            ...
        }
        
    Example:
        >>> from functions.data import DataManager
        >>> from functions.computation.weapons import get_weapon_cards
        >>>
        >>> data_mgr = DataManager.get_instance()
        >>> all_weapons = data_mgr.get_all_weapons(detailed=True)
        >>> cards = get_weapon_cards(all_weapons)
        >>>
        >>> # Now render in Dash
        >>> for weapon_name, card_data in cards.items():
        ...     print(f"{card_data['name']}: {len(card_data['parameters'])} parameters")
    """
    cards = {}
    
    for weapon_name, weapon_detailed in all_weapons_detailed.items():
        if not weapon_detailed:
            continue
        
        card_data = format_weapon_detailed(weapon_name, weapon_detailed)
        cards[weapon_name] = card_data
    
    return cards


def get_weapon_summary(
    weapon_consolidated: Dict[str, float],
    weapon_name: str = ""
) -> Dict[str, Any]:
    """
    Create a summary view of a weapon's key stats.
    
    Args:
        weapon_consolidated: Consolidated data from DataManager (final values)
        weapon_name: Optional weapon name for reference
        
    Returns:
        Dict with summary:
        {
            "name": str,
            "num_parameters": int,
            "parameters": {
                "parameter_name": "formatted_value",
                ...
            }
        }
    """
    summary = {
        "name": weapon_name,
        "num_parameters": len(weapon_consolidated),
        "parameters": {
            param_name: f"{value:.1f}"
            for param_name, value in weapon_consolidated.items()
        }
    }
    
    return summary


def get_all_weapons_summary(
    all_weapons_consolidated: Dict[str, Dict[str, float]]
) -> Dict[str, Dict[str, Any]]:
    """
    Create summary views for all weapons.
    
    Args:
        all_weapons_consolidated: All weapons consolidated from DataManager
        
    Returns:
        Dict of weapon summaries
    """
    return {
        weapon_name: get_weapon_summary(weapon_data, weapon_name)
        for weapon_name, weapon_data in all_weapons_consolidated.items()
    }


def filter_weapons_by_parameter(
    all_weapons_data: Dict[str, Dict[str, Any]],
    parameter_name: str,
    detailed: bool = False
) -> Dict[str, Any]:
    """
    Extract a specific parameter from all weapons.
    
    Useful for comparing how a parameter varies across weapons.
    
    Args:
        all_weapons_data: All weapons data (consolidated or detailed)
        parameter_name: Parameter to extract (e.g., "Duration")
        detailed: If True, expect detailed format; if False, expect consolidated
        
    Returns:
        Dict where each weapon maps to that parameter's value(s)
        
    Example:
        >>> from functions.data import DataManager
        >>> data_mgr = DataManager.get_instance()
        >>> all_weapons = data_mgr.get_all_weapons(consolidated=True)
        >>> durations = filter_weapons_by_parameter(all_weapons, "Duration")
        >>> # durations = {"Chrono Field": 41.0, "Death Wave": 20.0, ...}
    """
    result = {}
    
    for weapon_name, weapon_data in all_weapons_data.items():
        if isinstance(weapon_data, dict):
            if parameter_name in weapon_data:
                result[weapon_name] = weapon_data[parameter_name]
    
    return result


def get_parameter_stats(
    weapons_parameter_values: Dict[str, float]
) -> Dict[str, float]:
    """
    Calculate statistics for a parameter across all weapons.
    
    Args:
        weapons_parameter_values: Dict of weapon_name -> parameter_value
        
    Returns:
        Dict with statistics:
        {
            "min": float,
            "max": float,
            "avg": float,
            "count": int
        }
    """
    if not weapons_parameter_values:
        return {"min": 0, "max": 0, "avg": 0, "count": 0}
    
    values = list(weapons_parameter_values.values())
    
    return {
        "min": min(values),
        "max": max(values),
        "avg": sum(values) / len(values),
        "count": len(values),
    }
