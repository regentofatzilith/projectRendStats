"""
DataManager - Single source of truth for all data access.

This module provides global access to cached data, eliminating the need for
pages to load JSON files or create analyzer instances independently.

Architecture:
- Singleton pattern: Only one instance exists
- Thread-safe: Uses locks for concurrent access
- Lazy loading: JSON and analyzer created on first access
- Cached: Subsequent accesses return cached instances

Usage:
    from functions.data import DataManager
    
    # Get global instance
    data_mgr = DataManager.get_instance()
    
    # Access data (loads JSON on first call)
    all_weapons = data_mgr.get_all_weapons(detailed=True)
    chrono_field = data_mgr.get_weapon_data("Chrono Field", detailed=False)
    
    # Force reload (for development/testing)
    data_mgr.reload_data()
"""

import logging
import threading
import json
from pathlib import Path
from typing import Dict, Any, Optional, cast, List
from datetime import datetime
import pandas as pd

# Try to import from current environment, fall back if needed
try:
    from .UltimateWeapons import UltimateWeaponAnalyzer
    from . import config
    from .disco_import import extract_dissonance_runs_from_json
except ImportError:
    from functions.data.UltimateWeapons import UltimateWeaponAnalyzer
    from functions.data import config
    from functions.data.disco_import import extract_dissonance_runs_from_json

logger = logging.getLogger(__name__)


def _normalize_key(text: str) -> str:
    return "".join(ch for ch in str(text).lower() if ch.isalnum())


class DataManager:
    """
    Global data manager - singleton providing single source of truth for all data.
    
    Responsibilities:
    - Load JSON from userData.json (or fall back to assets/active_manifest.json)
    - Create and cache UltimateWeaponAnalyzer
    - Provide clean API for data access across entire application
    - Thread-safe access to cached data
    
    Examples:
        >>> mgr = DataManager.get_instance()
        >>> weapons = mgr.get_all_weapons(detailed=True)
        >>> chrono = mgr.get_weapon_data("Chrono Field")
    """
    
    _instance: Optional['DataManager'] = None
    _lock = threading.Lock()
    
    def __init__(self):
        """Initialize DataManager with lazy loading."""
        self._json_path: Optional[Path] = None
        self._json_data: Optional[Dict[str, Any]] = None
        self._analyzer: Optional[UltimateWeaponAnalyzer] = None
        self._data_lock = threading.RLock()  # Use RLock for reentrant locking!
        self._load_timestamp: Optional[datetime] = None
        
        logger.info("DataManager initialized (lazy loading enabled)")
    
    @staticmethod
    def get_instance() -> 'DataManager':
        """
        Get or create the singleton DataManager instance.
        
        Thread-safe using double-checked locking pattern.
        
        Returns:
            DataManager: The global singleton instance
        """
        if DataManager._instance is None:
            with DataManager._lock:
                # Double-check lock pattern
                if DataManager._instance is None:
                    DataManager._instance = DataManager()
                    logger.debug("Created new DataManager singleton instance")
        
        return DataManager._instance
    
    def _find_json_path(self) -> Path:
        """
        Find the JSON data file.
        
        Priority:
        1. ~/AppData/Roaming/rendapp/userData.json (actual game data)
        2. assets/active_manifest.json (fallback)
        
        Returns:
            Path: Path to the JSON file
            
        Raises:
            FileNotFoundError: If neither path exists
        """
        # Prefer the same path loaded by the shared user_data_store, if available.
        try:
            from functions import user_data_store  # Imported lazily to avoid circular imports

            store_path = user_data_store.current_path or user_data_store.source_path
            if store_path:
                shared_path = Path(store_path)
                if shared_path.exists():
                    logger.debug(f"Using shared user_data_store path: {shared_path}")
                    return shared_path
        except Exception:
            # Fall through to normal path resolution.
            pass

        # Try user's AppData (actual game data)
        appdata_path = Path.home() / "AppData" / "Roaming" / "rendapp" / "userData.json"
        if appdata_path.exists():
            logger.debug(f"Found userData.json at: {appdata_path}")
            return appdata_path
        
        # Fall back to assets
        assets_path = Path("assets/active_manifest.json")
        if assets_path.exists():
            logger.debug(f"userData.json not found, using: {assets_path}")
            logger.warning("Using fallback assets/active_manifest.json - data may be outdated")
            return assets_path
        
        # Neither found
        error_msg = (
            f"Could not find JSON data file:\n"
            f"  - Expected: {appdata_path}\n"
            f"  - Fallback: {assets_path}"
        )
        logger.error(error_msg)
        raise FileNotFoundError(error_msg)
    
    def _load_json(self) -> Dict[str, Any]:
        """
        Load JSON data from file.
        
        Returns:
            Dict: Parsed JSON data
            
        Raises:
            FileNotFoundError: If JSON file not found
            json.JSONDecodeError: If JSON is invalid
        """
        json_path = self._find_json_path()
        
        try:
            logger.info(f"Loading JSON data from: {json_path}")
            with open(json_path, 'r', encoding='utf-8') as f:
                json_data = json.load(f)
            
            file_size = json_path.stat().st_size / 1024  # KB
            logger.info(f"✓ Successfully loaded JSON ({file_size:.1f} KB)")
            self._load_timestamp = datetime.now()
            
            return json_data
            
        except json.JSONDecodeError as e:
            error_msg = f"Invalid JSON in {json_path}: {e}"
            logger.error(error_msg)
            raise
        except Exception as e:
            error_msg = f"Error reading JSON from {json_path}: {e}"
            logger.error(error_msg)
            raise
    
    def _ensure_data_loaded(self) -> None:
        """
        Ensure JSON data is loaded (lazy loading).
        
        Thread-safe. Only loads once, subsequent calls return cached data.
        """
        import time
        start = time.time()
        
        if self._json_data is not None:
            logger.debug(f"[DM] JSON data already cached ({time.time() - start:.3f}s)")
            return  # Already loaded
        
        logger.debug("[DM] Acquiring data lock for JSON load...")
        with self._data_lock:
            # Double-check lock pattern
            if self._json_data is not None:
                logger.debug(f"[DM] JSON data already cached (lock) ({time.time() - start:.3f}s)")
                return

            # Prefer in-memory JSON from user_data_store uploads.
            # This is required for Settings->Upload flow, where no filesystem path exists.
            try:
                from functions import user_data_store  # Imported lazily to avoid circular imports

                in_memory_json = user_data_store.full_json
                has_in_memory_upload = (
                    user_data_store.source_path is None
                    and isinstance(in_memory_json, dict)
                    and bool(in_memory_json)
                )
                if has_in_memory_upload:
                    self._json_path = None
                    self._json_data = in_memory_json
                    self._load_timestamp = user_data_store.last_loaded_at or datetime.now()
                    logger.debug("[DM] Using in-memory JSON from user_data_store upload")
                    return
            except Exception:
                # Fall through to filesystem-backed loading.
                pass
            
            logger.debug("[DM] Finding JSON path...")
            self._json_path = self._find_json_path()
            logger.debug(f"[DM] JSON path found: {self._json_path} ({time.time() - start:.3f}s)")
            
            logger.debug("[DM] Loading JSON file...")
            self._json_data = self._load_json()
            logger.debug(f"[DM] JSON loaded successfully ({time.time() - start:.3f}s)")
    
    def _ensure_analyzer_created(self, module: str = "Primordial Collapse") -> None:
        """
        Ensure UltimateWeaponAnalyzer is created (lazy loading).
        
        Thread-safe. Only creates once, subsequent calls return cached instance.
        
        Args:
            module: Module name to use for module effects
        """
        import time
        start = time.time()
        
        if self._analyzer is not None:
            logger.debug(f"[DM] Analyzer already cached, returning ({time.time() - start:.3f}s)")
            return  # Already created
        
        logger.debug("[DM] Acquiring data lock for analyzer creation...")
        with self._data_lock:
            # Double-check lock pattern
            if self._analyzer is not None:
                logger.debug(f"[DM] Analyzer already cached (lock), returning ({time.time() - start:.3f}s)")
                return
            
            logger.debug("[DM] Ensuring JSON data is loaded...")
            self._ensure_data_loaded()
            logger.debug(f"[DM] Data loaded ({time.time() - start:.3f}s)")
            
            if self._json_data is None:
                raise RuntimeError("JSON data failed to load before analyzer creation")
            
            logger.info(f"[DM] Creating UltimateWeaponAnalyzer (module: {module})")
            self._analyzer = UltimateWeaponAnalyzer(self._json_data, selected_module=module)
            logger.debug(f"[DM] UltimateWeaponAnalyzer created ({time.time() - start:.3f}s)")

    
    def get_analyzer(self, module: str = "Primordial Collapse") -> UltimateWeaponAnalyzer:
        """
        Get or create the analyzer instance.
        
        Args:
            module: Module name to use ("Primordial Collapse" or "Multiverse Nexus")
            
        Returns:
            UltimateWeaponAnalyzer: The cached analyzer instance
        """
        import time
        start = time.time()
        logger.debug(f"[DM] get_analyzer(module={module}) called")
        
        logger.debug("[DM] Ensuring analyzer is created...")
        self._ensure_analyzer_created(module)
        logger.debug(f"[DM] _ensure_analyzer_created done ({time.time() - start:.3f}s)")
        
        analyzer = self._analyzer
        if analyzer is None:
            raise RuntimeError("Analyzer was not initialized")
        logger.debug(f"[DM] Returning analyzer ({time.time() - start:.3f}s)")
        return analyzer
    
    def get_weapon_data(
        self,
        weapon_name: str,
        detailed: bool = False,
        module: str = "Primordial Collapse"
    ) -> Dict[str, Any]:
        """
        Get data for a single weapon.
        
        Args:
            weapon_name: Name of the weapon (e.g., "Chrono Field")
            detailed: If True, return breakdown of all sources.
                     If False, return final effective values only.
            module: Module name to use for module effects
            
        Returns:
            Dict: Weapon data (format depends on detailed flag)
            
        Examples:
            >>> mgr = DataManager.get_instance()
            
            # Get consolidated (final values)
            >>> data = mgr.get_weapon_data("Chrono Field")
            >>> print(data)  # {"Duration": 41.0, "Cooldown": 53.0, ...}
            
            # Get detailed (all components)
            >>> data = mgr.get_weapon_data("Chrono Field", detailed=True)
            >>> print(data)  # {"Duration": {"uw_level": 7, "uw_value": 12.0, ...}, ...}
        """
        analyzer = self.get_analyzer(module)
        
        if detailed:
            result = analyzer.get_detailed(weapon_name)
        else:
            result = analyzer.get_consolidated(weapon_name)

        response = result if result else {}
        if detailed and response:
            return self._annotate_parameter_source_flags({weapon_name: response}).get(weapon_name, {})

        return response

    def _annotate_parameter_source_flags(self, weapons_data: Dict[str, Any]) -> Dict[str, Any]:
        """Attach effect-source capability flags to detailed parameter payloads."""
        for weapon_name, weapon_params in weapons_data.items():
            if not isinstance(weapon_params, dict):
                continue

            for param_name, param_data in weapon_params.items():
                if not isinstance(param_data, dict):
                    continue

                param_data.update(config.get_effect_source_flags(weapon_name, str(param_name)))

        return weapons_data

    def _canonicalize_parameter_payloads(self, weapons_data: Dict[str, Any], detailed: bool) -> Dict[str, Any]:
        """Normalize legacy parameter aliases to canonical config names per entity."""
        canonicalized: Dict[str, Any] = {}

        for entity_name, entity_payload in weapons_data.items():
            if not isinstance(entity_payload, dict):
                canonicalized[entity_name] = entity_payload
                continue

            merged_params: Dict[str, Any] = {}
            for param_name, param_payload in entity_payload.items():
                _, canonical_param = config.normalize_weapon_parameter(entity_name, str(param_name))

                if canonical_param not in merged_params:
                    merged_params[canonical_param] = param_payload
                    continue

                if not detailed:
                    try:
                        incoming = float(param_payload)
                    except Exception:
                        incoming = 0.0
                    try:
                        existing = float(merged_params[canonical_param])
                    except Exception:
                        existing = 0.0
                    if abs(incoming) > abs(existing):
                        merged_params[canonical_param] = param_payload
                    continue

                existing_payload = merged_params.get(canonical_param)
                if not isinstance(existing_payload, dict) or not isinstance(param_payload, dict):
                    merged_params[canonical_param] = param_payload
                    continue

                def _score(payload: Dict[str, Any]) -> float:
                    total = payload.get("total_value", 0.0)
                    try:
                        total_num = abs(float(total))
                    except Exception:
                        total_num = 0.0
                    uw_level = 1.0 if int(payload.get("uw_level", 0) or 0) > 0 else 0.0
                    labs_level = 1.0 if int(payload.get("labs_level", 0) or 0) > 0 else 0.0
                    return (1000.0 * uw_level) + (100.0 * labs_level) + total_num

                if _score(param_payload) > _score(existing_payload):
                    merged_params[canonical_param] = param_payload

            canonicalized[entity_name] = merged_params

        return canonicalized
    
    def get_all_weapons(
        self,
        detailed: bool = False,
        module: str = "Primordial Collapse"
    ) -> Dict[str, Any]:
        """
        Get data for all weapons.
        
        Args:
            detailed: If True, return breakdown for each weapon.
                     If False, return final values only.
            module: Module name to use for module effects
            
        Returns:
            Dict: All weapons data
                 - Keys: weapon names ("Chrono Field", "Death Wave", etc.)
                 - Values: weapon data (format depends on detailed flag)
            
        Examples:
            >>> mgr = DataManager.get_instance()
            
            # Get all weapons (consolidated)
            >>> all_weapons = mgr.get_all_weapons()
            >>> print(all_weapons.keys())  # ["Death Wave", "Golden Tower", ...]
            
            # Get detailed breakdown for all
            >>> all_weapons = mgr.get_all_weapons(detailed=True)
            >>> chrono = all_weapons["Chrono Field"]
            >>> print(chrono["Duration"])  # {"uw_level": 7, ...}
        """
        import time
        start = time.time()
        logger.debug(f"[DM] get_all_weapons(detailed={detailed}, module={module}) called")
        
        logger.debug("[DM] Getting analyzer...")
        analyzer = self.get_analyzer(module)
        logger.debug(f"[DM] Analyzer retrieved ({time.time() - start:.3f}s)")
        
        if detailed:
            logger.debug("[DM] Calling analyzer.get_all_detailed()...")
            result = analyzer.get_all_detailed()
            logger.debug(f"[DM] get_all_detailed completed ({time.time() - start:.3f}s)")
        else:
            logger.debug("[DM] Calling analyzer.get_all_consolidated()...")
            result = analyzer.get_all_consolidated()
            logger.debug(f"[DM] get_all_consolidated completed ({time.time() - start:.3f}s)")
        
        response: Dict[str, Any] = result if result else {}
        # Merge guardians/chips from JSON data so they are available to overview pages.
        response.update(self.get_guardians(detailed=detailed))

        response = self._canonicalize_parameter_payloads(response, detailed=detailed)

        if detailed and response:
            response = self._annotate_parameter_source_flags(response)

        logger.debug(f"[DM] get_all_weapons returning {len(response)} weapons ({time.time() - start:.3f}s)")
        return response

    def _get_guardian_chip_objects(self) -> Dict[str, Dict[str, Any]]:
        """Best-effort extraction of guardian chip objects keyed by chip name."""
        self._ensure_data_loaded()
        data = self._json_data or {}
        guardians_registry = cast(Dict[str, Dict[str, Any]], config.LOOKUP_TABLE_REGISTRY.get("Guardians", {}))
        chip_names = set(guardians_registry.keys())
        found: Dict[str, Dict[str, Any]] = {}

        def _merge_chip_map(chips_obj: Any) -> None:
            if isinstance(chips_obj, dict):
                for chip_name, chip_data in chips_obj.items():
                    if isinstance(chip_name, str) and chip_name in chip_names and isinstance(chip_data, dict):
                        merged = dict(chip_data)
                        merged.setdefault("name", chip_name)
                        found[chip_name] = merged

        # First, use the canonical guardians.chips map when present at root.
        guardians_obj = data.get("guardians") if isinstance(data, dict) else None
        if isinstance(guardians_obj, dict):
            _merge_chip_map(guardians_obj.get("chips"))

        def _walk(node: Any) -> None:
            if isinstance(node, dict):
                # Common nested shape: { ..., "guardians": {"chips": {...}} }
                nested_guardians = node.get("guardians")
                if isinstance(nested_guardians, dict):
                    _merge_chip_map(nested_guardians.get("chips"))

                # Also support direct chip map objects discovered in traversal.
                if "chips" in node:
                    _merge_chip_map(node.get("chips"))

                name = node.get("name")
                if isinstance(name, str) and name in chip_names:
                    found[name] = node
                for value in node.values():
                    _walk(value)
            elif isinstance(node, list):
                for item in node:
                    _walk(item)

        _walk(data)
        return found

    def _extract_chip_level(self, chip_obj: Dict[str, Any], param_name: str) -> int:
        """Extract a chip level (bits) from possible JSON shapes.

        Prefers parameter-specific level dictionaries, then falls back to global chip level.
        """
        param_norm = _normalize_key(param_name)

        # Canonical guardians shape uses per-parameter component values as levels.
        components = chip_obj.get("components")
        if isinstance(components, dict):
            for key, value in components.items():
                if _normalize_key(str(key)) == param_norm:
                    try:
                        return max(0, int(value))
                    except Exception:
                        pass

        # Parameter-specific levels in common nested dicts.
        for container_key in ["upgrades", "levels", "stats", "bits", "chipUpgrades"]:
            container = chip_obj.get(container_key)
            if isinstance(container, dict):
                for k, v in container.items():
                    if _normalize_key(k) == param_norm:
                        try:
                            return max(0, int(v))
                        except Exception:
                            pass

        # Global level fallback.
        for key in ["level", "currentLevel", "chipLevel", "bits", "upgradeLevel"]:
            if key in chip_obj:
                try:
                    return max(0, int(chip_obj[key]))
                except Exception:
                    pass

        return 0

    def get_guardians(self, detailed: bool = False) -> Dict[str, Any]:
        """Build guardian chip data in same schema as weapons for UI reuse."""
        chip_objects = self._get_guardian_chip_objects()
        out: Dict[str, Any] = {}

        guardians_registry = cast(Dict[str, Dict[str, Any]], config.LOOKUP_TABLE_REGISTRY.get("Guardians", {}))

        for chip_name, registry_entry in guardians_registry.items():
            lookup = cast(Dict[str, Any], registry_entry.get("lut", {}))
            levels_lookup = cast(Dict[str, Dict[int, Any]], lookup.get("Levels", {}))
            chip_obj = chip_objects.get(chip_name, {})
            params: Dict[str, Any] = {}

            for param_name, table in levels_lookup.items():
                level = self._extract_chip_level(chip_obj, param_name)
                raw = config.lookup_with_clamp(cast(Dict[int, object], table), level)
                if raw is None:
                    continue
                total_value = config.convert_guardian_lookup_value(param_name, raw)
                unit = config.get_guardian_param_unit(param_name)

                if detailed:
                    params[param_name] = {
                        "uw_level": level,
                        "uw_target_level": 0,
                        "uw_value": total_value,
                        "labs_level": 0,
                        "labs_value": 0.0,
                        "module_value": 0.0,
                        "relic_value": 0.0,
                        "total_value": total_value,
                        "unit": unit,
                    }
                else:
                    params[param_name] = total_value

            # Static config fallback values when a chip is absent in userData.json.
            if chip_name not in chip_objects:
                fallback = config.get_guardian_fallback_param_values(chip_name)
                for p_name, (p_value, unit) in fallback.items():
                    if detailed:
                        params[p_name] = {
                            "uw_level": 0,
                            "uw_target_level": 0,
                            "uw_value": p_value,
                            "labs_level": 0,
                            "labs_value": 0.0,
                            "module_value": 0.0,
                            "relic_value": 0.0,
                            "total_value": p_value,
                            "unit": unit,
                        }
                    else:
                        params[p_name] = p_value

            if params:
                out[chip_name] = params

        return out
    
    def get_json_data(self) -> Dict[str, Any]:
        """
        Get the raw JSON data.
        
        Use this only when you need direct access to the underlying JSON
        (e.g., for extracting data not handled by UltimateWeaponAnalyzer).
        
        Returns:
            Dict: Raw JSON data loaded from userData.json
        """
        self._ensure_data_loaded()
        json_data = self._json_data
        if json_data is None:
            raise RuntimeError("JSON data was not loaded")
        return json_data

    def get_dissonance_runs(self) -> pd.DataFrame:
        """Return dissonance rows extracted from the currently loaded JSON."""
        return extract_dissonance_runs_from_json(self.get_json_data())

    def get_load_info(self) -> Dict[str, Any]:
        """
        Get information about loaded data.
        
        Returns:
            Dict: Information including:
                - json_path: Path to loaded JSON file
                - load_timestamp: When data was loaded
                - file_size_kb: Size of JSON file
                - analyzer_cached: Whether analyzer is cached
        """
        info = {}

        # Include whether source is in-memory upload (Settings page upload mode).
        try:
            from functions import user_data_store  # Imported lazily to avoid circular imports

            if user_data_store.source_path is None and isinstance(user_data_store.full_json, dict) and user_data_store.full_json:
                info["source"] = "in-memory-upload"
                if user_data_store.last_loaded_at:
                    info["load_timestamp"] = user_data_store.last_loaded_at.isoformat()
        except Exception:
            pass
        
        if self._json_path:
            info["json_path"] = str(self._json_path)
            file_size = self._json_path.stat().st_size / 1024
            info["file_size_kb"] = round(file_size, 1)
        
        if self._load_timestamp:
            info["load_timestamp"] = self._load_timestamp.isoformat()
        
        info["analyzer_cached"] = self._analyzer is not None
        
        return info
    
    def reload_data(self) -> None:
        """
        Force reload of JSON and analyzer.
        
        Use this for development/testing when you want to pick up changes
        in the JSON file without restarting the app.
        
        Thread-safe.
        """
        with self._data_lock:
            logger.warning("Force reloading data...")
            self._json_data = None
            self._analyzer = None
            self._json_path = None
            self._load_timestamp = None
            
            # Pre-load to verify success
            self._ensure_data_loaded()
            self._ensure_analyzer_created()
            
            logger.warning("✓ Data reloaded successfully")
    
    def get_weapons_list(self, module: str = "Primordial Collapse") -> list:
        """
        Get list of all available weapon names.
        
        Args:
            module: Module name to use for module effects
            
        Returns:
            list: Sorted list of weapon names
            
        Example:
            >>> mgr = DataManager.get_instance()
            >>> weapons = mgr.get_weapons_list()
            >>> print(weapons)  # ["Black Hole", "Chrono Field", "Death Wave", ...]
        """
        all_weapons = self.get_all_weapons(detailed=False, module=module)
        return sorted(all_weapons.keys())
    
    def validate_weapon_exists(self, weapon_name: str, module: str = "Primordial Collapse") -> bool:
        """
        Check if a weapon exists in the data.
        
        Args:
            weapon_name: Name of the weapon to check
            module: Module name to use for module effects
            
        Returns:
            bool: True if weapon exists, False otherwise
        """
        all_weapons = self.get_all_weapons(detailed=False, module=module)
        return weapon_name in all_weapons
    
    def __repr__(self) -> str:
        """String representation of DataManager state."""
        status = "loaded" if self._json_data else "not loaded"
        analyzer_status = "cached" if self._analyzer else "not cached"
        
        return (
            f"<DataManager: "
            f"json={status}, "
            f"analyzer={analyzer_status}, "
            f"path={self._json_path}>"
        )
