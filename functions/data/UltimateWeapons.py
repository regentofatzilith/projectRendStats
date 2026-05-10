"""
Ultimate Weapons - Unified interface for ultimate weapon data analysis.

This module provides a clean, consolidated interface for working with ultimate weapon data,
combining information from multiple sources (upgrades, labs, relics, modules).

Architecture:
- ImportJSON.py: Raw data extraction from JSON
- DataStore.py: Caching and state management
- UltimateWeapons.py (this file): Business logic for combining and presenting data

Usage:
    from functions.data.UltimateWeapons import UltimateWeaponAnalyzer
    
    analyzer = UltimateWeaponAnalyzer(json_data)
    
    # Get consolidated output (final effective values only)
    consolidated = analyzer.get_consolidated("Chrono Field")
    # Returns: {"Duration": 51.0, "Cooldown": 73.0}
    
    # Get detailed output (breakdown of all sources)
    detailed = analyzer.get_detailed("Chrono Field")
    # Returns: {"Duration": {"uw_level": 7, "uw_value": 22, "labs_level": 29, ...}}
"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass
import pandas as pd
import logging

# Import lookup tables from config
from . import config

logger = logging.getLogger(__name__)


@dataclass
class WeaponParameter:
    """Represents a single parameter of an ultimate weapon with all its components."""
    name: str  # e.g., "Duration", "Damage", "Cooldown"
    
    # Upgrade levels
    uw_level: int = 0
    uw_target_level: int = 0
    
    # Effective values from each source
    uw_value: float = 0.0        # Base value from ultimate weapon upgrade
    labs_level: int = 0           # Labs research level
    labs_value: float = 0.0       # Bonus from labs research
    relic_value: float = 0.0      # Bonus from relics
    module_level: int = 0         # Module upgrade level
    module_value: float = 0.0     # Bonus from module
    
    # Metadata
    unit: str = ""                # e.g., "s", "%", ""
    
    @property
    def total_value(self) -> float:
        """Calculate the total effective value."""
        return self.uw_value + self.labs_value + self.relic_value + self.module_value
    
    @property
    def consolidated(self) -> float:
        """Return just the final value (for consolidated output)."""
        return self.total_value
    
    @property
    def detailed(self) -> Dict[str, Any]:
        """Return full breakdown (for detailed output)."""
        return {
            "uw_level": self.uw_level,
            "uw_target_level": self.uw_target_level,
            "uw_value": self.uw_value,
            "labs_level": self.labs_level,
            "labs_value": self.labs_value,
            "relic_value": self.relic_value,
            "module_level": self.module_level,
            "module_value": self.module_value,
            "total_value": self.total_value,
            "unit": self.unit
        }
    
    def __repr__(self) -> str:
        return f"{self.name}: {self.total_value}{self.unit} (UW:{self.uw_value} + Labs:{self.labs_value} + Relic:{self.relic_value} + Module:{self.module_value})"


@dataclass
class UltimateWeapon:
    """Represents a complete ultimate weapon with all its parameters."""
    name: str  # e.g., "Chrono Field", "Death Wave"
    parameters: Dict[str, WeaponParameter]  # e.g., {"Duration": WeaponParameter(...), ...}
    
    def get_consolidated(self) -> Dict[str, float]:
        """Get consolidated output: parameter name -> final effective value."""
        return {param_name: param.consolidated for param_name, param in self.parameters.items()}
    
    def get_detailed(self) -> Dict[str, Dict[str, Any]]:
        """Get detailed output: parameter name -> breakdown dictionary."""
        return {param_name: param.detailed for param_name, param in self.parameters.items()}
    
    def __repr__(self) -> str:
        params_str = "\n  ".join(str(p) for p in self.parameters.values())
        return f"{self.name}:\n  {params_str}"


class UltimateWeaponAnalyzer:
    """
    Main interface for analyzing ultimate weapon data.
    
    This class handles all the business logic for combining data from multiple sources
    (ultimate weapon upgrades, labs research, relics, modules) into a clean, unified output.
    """
    
    # Base values from perma_calc_hybrid (used when JSON has no data)
    BASE_VALUES = {
        "Chrono Field": {"Cooldown": 53, "Duration": 41},
        "Black Hole": {"Cooldown": 46, "Duration": 33},
        "Golden Tower": {"Cooldown": 170, "Duration": 45},
        "Death Wave": {"Cooldown": 170, "Duration": 20},
        "Golden Bot": {"Cooldown": 100, "Duration": 26},
        "Summon Guardian": {"Cooldown": 100, "Duration": 30},
        "Smart Missiles": {"Cooldown": 120, "Duration": 15},
        "Inner Land Mines": {"Cooldown": 130, "Duration": 25},
        "Poison Swamp": {"Cooldown": 140, "Duration": 30},
    }
    
    def __init__(self, json_data: Dict[str, Any], selected_module: str = "Primordial Collapse"):
        """
        Initialize the analyzer with JSON data.
        
        Args:
            json_data: Full JSON data dictionary (from userData.json or similar)
            selected_module: Module name to use for module effects
        """
        self.json_data = json_data
        self.selected_module = selected_module
        self._weapons_cache: Optional[Dict[str, UltimateWeapon]] = None

        catalog = config.get_data_view_entry_catalog()
        dynamic_defs: Dict[str, List[str]] = {}
        for section_name in ("Ultimate Weapons", "Bots"):
            section = catalog.get(section_name, {})
            for entity_name, info in section.items():
                entries = info.get("entries", []) if isinstance(info, dict) else []
                if isinstance(entries, list):
                    dynamic_defs[entity_name] = [str(e) for e in entries]
        self.weapon_definitions: Dict[str, List[str]] = dynamic_defs
    
    def _extract_weapons_data(self) -> Dict[str, UltimateWeapon]:
        """
        Extract and combine all ultimate weapon data from JSON.
        
        This is the core method that pulls data from ImportJSON and combines it.
        Now properly extracts individual component values instead of using pre-combined totals.
        """
        import time
        start_time = time.time()
        logger = logging.getLogger(__name__)
        logger.debug("[UWA] _extract_weapons_data() starting")
        
        from . import ImportJSON
        
        # Extract relics data first (needed for specific bonuses)
        logger.debug("[UWA] Extracting relics data...")
        relics_start = time.time()
        relics_data = self._extract_relics_data()
        logger.debug(f"[UWA] Relics data extracted ({time.time() - relics_start:.3f}s)")
        
        # Get combined data from ImportJSON (this already does the heavy lifting)
        logger.debug("[UWA] Calling ImportJSON.extract_combined_ultimate_weapons_data()...")
        json_start = time.time()
        combined_df_dict = ImportJSON.extract_combined_ultimate_weapons_data(self.json_data, self.selected_module)
        logger.debug(f"[UWA] ImportJSON extraction done ({time.time() - json_start:.3f}s)")
        
        # Convert DataFrames to our cleaner object model
        weapons = {}
        
        logger.debug(f"[UWA] Processing {len(self.weapon_definitions)} weapons...")
        
        # Process all weapons defined by config-driven catalog.
        for weapon_idx, weapon_name in enumerate(self.weapon_definitions.keys()):
            if weapon_idx % max(1, len(self.weapon_definitions) // 5) == 0:
                logger.debug(f"[UWA] Processing weapon {weapon_idx + 1}/{len(self.weapon_definitions)}: {weapon_name}")
            
            parameters = {}
            
            # First, process any data from JSON if available
            if weapon_name in combined_df_dict:
                df = combined_df_dict[weapon_name]
                if not df.empty:
                    for _, row in df.iterrows():
                        param_name = row.get("Parameter", "Unknown")
                        
                        # Parse the row data
                        param = WeaponParameter(name=param_name)
                        
                        # Ultimate weapon level and value
                        param.uw_level = int(row.get("Level", 0)) if pd.notna(row.get("Level")) else 0
                        target_level = row.get("Target Level", "")
                        param.uw_target_level = int(target_level) if pd.notna(target_level) and target_level != "" else 0
                        
                        # Labs level
                        labs_level_str = row.get("Labs Level", "")
                        param.labs_level = int(labs_level_str) if pd.notna(labs_level_str) and labs_level_str != "" else 0
                        
                        # Extract base value from UW upgrade lookups
                        param.uw_value = self._get_base_value(weapon_name, param_name, param.uw_level)
                        
                        # Extract labs bonus value
                        param.labs_value = self._get_labs_bonus(weapon_name, param_name, param.labs_level)
                        
                        # Extract module effect value
                        module_effect_str = row.get("Module Effect", "")
                        param.module_value = self._parse_module_effect(module_effect_str)
                        
                        # Extract relic bonus value
                        param.relic_value = self._get_relic_bonus(weapon_name, param_name, relics_data)
                        
                        # Determine unit based on parameter type and weapon
                        param.unit = self._determine_unit(weapon_name, param_name)
                        
                        parameters[param_name] = param
            
            # Now add any missing expected parameters with base/zero values
            expected_params = self.weapon_definitions.get(weapon_name, [])
            for param_name in expected_params:
                if param_name not in parameters:
                    # Create placeholder parameter
                    param = WeaponParameter(name=param_name)
                    param.uw_level = 0
                    param.uw_target_level = 0
                    
                    # Use base values for Duration/Cooldown if available
                    if weapon_name in self.BASE_VALUES and param_name in self.BASE_VALUES[weapon_name]:
                        param.uw_value = float(self.BASE_VALUES[weapon_name][param_name])
                    else:
                        param.uw_value = 0.0
                    
                    param.labs_value = 0.0
                    param.module_value = 0.0
                    param.relic_value = 0.0
                    param.unit = self._determine_unit(weapon_name, param_name)
                    
                    parameters[param_name] = param
            
            # Only add weapon if it has at least one parameter
            if parameters:
                weapons[weapon_name] = UltimateWeapon(name=weapon_name, parameters=parameters)
        
        total_time = time.time() - start_time
        logger.debug(f"[UWA] _extract_weapons_data() completed ({total_time:.3f}s, {len(weapons)} weapons)")
        return weapons
    
    def _get_base_value(self, weapon_name: str, param_name: str, level: int) -> float:
        """Get the base value from ultimate weapon upgrade lookup tables."""
        _, normalized_param = config.normalize_weapon_parameter(weapon_name, param_name)

        lookup_group = config.LEVEL_LOOKUPS_BY_ENTITY.get(weapon_name, {})
        if normalized_param in lookup_group:
            lookup = lookup_group[normalized_param]
            return float(lookup.get(level, 0))
        
        return 0.0
    
    def _get_labs_bonus(self, weapon_name: str, param_name: str, labs_level: int) -> float:
        """Get the labs research bonus value."""
        _, normalized_param = config.normalize_weapon_parameter(weapon_name, param_name)

        labs_lookup = config.get_labs_lookup_table(weapon_name, normalized_param)
        if isinstance(labs_lookup, dict) and labs_level >= 0:
            raw_value = labs_lookup.get(labs_level, 0)
            if isinstance(raw_value, bool):
                return 1.0 if raw_value else 0.0
            try:
                return float(raw_value)
            except (TypeError, ValueError):
                return 0.0
        
        return 0.0

    def _is_boolean_labs_parameter(self, weapon_name: str, param_name: str) -> bool:
        """Return True when the labs lookup for a parameter is a bool unlock table."""
        labs_lookup = config.get_labs_lookup_table(weapon_name, param_name)
        if not isinstance(labs_lookup, dict) or not labs_lookup:
            return False

        for value in labs_lookup.values():
            if value is None:
                continue
            return isinstance(value, bool)

        return False
    
    def _extract_relics_data(self) -> Dict[str, float]:
        """Extract relic bonuses from JSON data."""
        relics_data = {}
        
        # Try to find relicsData.bonuses section in JSON
        def find_relics_bonuses(obj: Any) -> Optional[list]:
            """Recursively search for relics bonuses list."""
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if k.lower() == "relicsdata" and isinstance(v, dict):
                        bonuses = v.get("bonuses", [])
                        if isinstance(bonuses, list):
                            return bonuses
                    found = find_relics_bonuses(v)
                    if found is not None:
                        return found
            elif isinstance(obj, list):
                for item in obj:
                    found = find_relics_bonuses(item)
                    if found is not None:
                        return found
            return None
        
        bonuses_list = find_relics_bonuses(self.json_data) or []
        
        # Extract relic bonus values
        for bonus in bonuses_list:
            if isinstance(bonus, dict):
                name = bonus.get("name", "")
                value = bonus.get("value", 0)
                if name and value:
                    relics_data[name] = float(value)
        
        return relics_data
    
    def _get_relic_bonus(self, weapon_name: str, param_name: str, relics_data: Dict[str, float]) -> float:
        """Get relic bonus for a specific weapon parameter using the entity's LUT Relics section."""
        lut = config._get_registry_lut(weapon_name)
        if isinstance(lut, dict):
            relics_map = lut.get("Relics") or {}
            relic_name = relics_map.get(param_name)
            if relic_name:
                return float(relics_data.get(relic_name, 0.0))
        return 0.0
    
    def _parse_module_effect(self, module_effect_str: str) -> float:
        """Parse module effect string like '+3', '-7s', '+2.5' into a numeric value."""
        if not module_effect_str or module_effect_str == "":
            return 0.0
        
        import re
        match = re.search(r'([+\-]?\d+(?:\.\d+)?)', str(module_effect_str))
        if match:
            return float(match.group(1))
        return 0.0
    
    def _determine_unit(self, weapon_name: str, param_name: str) -> str:
        """Determine the unit for a parameter based on weapon type and parameter name."""
        if self._is_boolean_labs_parameter(weapon_name, param_name):
            return ""

        param_lower = param_name.lower()
        
        # Unit mappings
        if "duration" in param_lower:
            return "s"
        elif "cooldown" in param_lower:
            return "s"
        elif "quantity" in param_lower:
            return "#"
        elif "size" in param_lower:
            return "m"
        elif "range" in param_lower and "ranged" not in param_lower:
            return "m"
        elif "angle" in param_lower:
            return "°"
        elif "slow" in param_lower or "%" in param_name:
            return "%"
        elif "bonus" in param_lower or "damage" in param_lower or "mult" in param_lower:
            return "×"
        
        return ""
    
    def get_all_weapons(self) -> Dict[str, UltimateWeapon]:
        """Get all ultimate weapons with their data."""
        if self._weapons_cache is None:
            self._weapons_cache = self._extract_weapons_data()
        return self._weapons_cache
    
    def get_weapon(self, weapon_name: str) -> Optional[UltimateWeapon]:
        """Get a specific ultimate weapon by name."""
        weapons = self.get_all_weapons()
        return weapons.get(weapon_name)
    
    def get_consolidated(self, weapon_name: str) -> Dict[str, float]:
        """
        Get consolidated output for a weapon: final effective values only.
        
        Example:
            >>> analyzer.get_consolidated("Chrono Field")
            {"Duration": 51.0, "Cooldown": 73.0}
        """
        weapon = self.get_weapon(weapon_name)
        if weapon is None:
            logger.warning(f"Weapon not found: {weapon_name}")
            return {}
        return weapon.get_consolidated()
    
    def get_detailed(self, weapon_name: str) -> Dict[str, Dict[str, Any]]:
        """
        Get detailed output for a weapon: breakdown of all sources.
        
        Example:
            >>> analyzer.get_detailed("Chrono Field")
            {
                "Duration": {
                    "uw_level": 7,
                    "uw_value": 22.0,
                    "labs_level": 29,
                    "labs_value": 29.0,
                    "relic_value": 0.0,
                    "module_level": 0,
                    "module_value": 0.0,
                    "total_value": 51.0,
                    "unit": "s"
                },
                ...
            }
        """
        weapon = self.get_weapon(weapon_name)
        if weapon is None:
            logger.warning(f"Weapon not found: {weapon_name}")
            return {}
        return weapon.get_detailed()
    
    def get_all_consolidated(self) -> Dict[str, Dict[str, float]]:
        """Get consolidated output for all weapons."""
        weapons = self.get_all_weapons()
        return {name: weapon.get_consolidated() for name, weapon in weapons.items()}
    
    def get_all_detailed(self) -> Dict[str, Dict[str, Dict[str, Any]]]:
        """Get detailed output for all weapons."""
        weapons = self.get_all_weapons()
        return {name: weapon.get_detailed() for name, weapon in weapons.items()}
    
    def print_weapon(self, weapon_name: str, show_detailed: bool = True) -> None:
        """
        Pretty-print a weapon's data to console.
        
        Args:
            weapon_name: Name of the weapon
            show_detailed: If True, show detailed breakdown; if False, show consolidated only
        """
        weapon = self.get_weapon(weapon_name)
        if weapon is None:
            print(f"❌ Weapon not found: {weapon_name}")
            return
        
        print(f"\n{'='*80}")
        print(f"{weapon_name.upper()}")
        print(f"{'='*80}")
        
        if show_detailed:
            detailed = weapon.get_detailed()
            for param_name, breakdown in detailed.items():
                print(f"\n🔹 {param_name}:")
                print(f"   Ultimate Weapon: Level {breakdown['uw_level']}/{breakdown['uw_target_level']} → {breakdown['uw_value']}{breakdown['unit']}")
                if breakdown['labs_level'] > 0:
                    print(f"   Labs Research: Level {breakdown['labs_level']} → +{breakdown['labs_value']}{breakdown['unit']}")
                if breakdown['relic_value'] != 0:
                    print(f"   Relics: +{breakdown['relic_value']}{breakdown['unit']}")
                if breakdown['module_value'] != 0:
                    print(f"   Module: Level {breakdown['module_level']} → {'+' if breakdown['module_value'] >= 0 else ''}{breakdown['module_value']}{breakdown['unit']}")
                print(f"   {'─'*50}")
                print(f"   💎 Total: {breakdown['total_value']}{breakdown['unit']}")
        else:
            consolidated = weapon.get_consolidated()
            for param_name, value in consolidated.items():
                param = weapon.parameters[param_name]
                print(f"   {param_name}: {value}{param.unit}")
    
    def print_all_weapons(self, show_detailed: bool = False) -> None:
        """Print all weapons' data to console."""
        for weapon_name in self.weapon_definitions.keys():
            self.print_weapon(weapon_name, show_detailed=show_detailed)


# Convenience function for quick access
def analyze_ultimate_weapons(json_data: Dict[str, Any], selected_module: str = "Primordial Collapse") -> UltimateWeaponAnalyzer:
    """
    Create an analyzer instance for ultimate weapon data.
    
    Example:
        >>> from functions.data.UltimateWeapons import analyze_ultimate_weapons
        >>> analyzer = analyze_ultimate_weapons(json_data)
        >>> chrono_field = analyzer.get_detailed("Chrono Field")
    """
    return UltimateWeaponAnalyzer(json_data, selected_module)
