import threading
import logging
import os
import json
import hashlib
from datetime import datetime
from typing import Any, Dict, Optional


import pandas as pd

# Try relative import first, fall back to absolute import if run as script
try:
    from .ImportJSON import (
        load_full_json,
        Import_JSON_record,
        cleanupJSON,
        extract_ultimate_weapon_upgrades,
        extract_golden_bot_info,
        load_todos_and_costs,
        analyze_full_json_file,
        extract_relics_data,
    )
    from .disco_import import extract_dissonance_runs
    from .disco_import import build_disco_tier_map
except ImportError:
    from ImportJSON import (
        load_full_json,
        Import_JSON_record,
        cleanupJSON,
        extract_ultimate_weapon_upgrades,
        extract_golden_bot_info,
        load_todos_and_costs,
        analyze_full_json_file,
        extract_relics_data,
    )
    from disco_import import extract_dissonance_runs
    from disco_import import build_disco_tier_map

logger = logging.getLogger("rend-datastore")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')


class UserDataStore:
    """Singleton store for the user's data and derived DataFrames.

    Access via UserDataStore.get().
    Thread-safe for simple Dash usage.
    """

    _instance: Optional["UserDataStore"] = None
    _lock = threading.RLock()

    @classmethod
    def get(cls) -> "UserDataStore":
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
            return cls._instance

    def __init__(self) -> None:
        # Source info
        self.source_path: Optional[str] = None
        self.current_path: Optional[str] = None  # Alias for easier access
        self.source_mtime: Optional[float] = None
        self.source_size: Optional[int] = None
        self.source_hash: Optional[str] = None
        self.last_loaded_at: Optional[datetime] = None

        # Raw and derived data
        self.full_json: Dict[str, Any] = {}
        self.game_stats_df: pd.DataFrame = pd.DataFrame()
        self.cleaned: Dict[str, pd.DataFrame] = {}
        self.ultimate_weapon_upgrades_df: pd.DataFrame = pd.DataFrame()
        self.golden_bot_info_df: pd.DataFrame = pd.DataFrame()
        self.relics_data: Dict[str, float] = {}

        self.workshop_todos_df: pd.DataFrame = pd.DataFrame()
        self.labs_todos_df: pd.DataFrame = pd.DataFrame()
        self.workshop_all_df: pd.DataFrame = pd.DataFrame()
        self.labs_all_df: pd.DataFrame = pd.DataFrame()

        self.analysis_results: Dict[str, pd.DataFrame] = {}
        self.dissonance_df: pd.DataFrame = pd.DataFrame(columns=["tier", "wave", "comment", "disco_type"])
        self.dissonance_tier_map: Dict[str, Dict[str, object]] = {}
        
        # Cache for combined ultimate weapons data (expensive to compute)
        self._combined_weapons_cache: Dict[str, Dict[str, pd.DataFrame]] = {}  # module_name -> weapon_data

    # --------------- Public API ---------------
    def clear(self) -> None:
        with self._lock:
            self.__init__()
    
    def get_combined_weapons_data(self, selected_module: str = "Primordial Collapse") -> Dict[str, pd.DataFrame]:
        """Get combined ultimate weapons data for a specific module, with caching.
        
        Returns:
            Dict with keys: "Death Wave", "Golden Tower", "Black Hole", "Spotlight", "Golden Bot"
            Each value is a DataFrame with: Parameter, Level, Target Level, Module Effect, Labs Level, Total Value
        """
        with self._lock:
            # Check cache first
            if selected_module in self._combined_weapons_cache:
                logger.info(f"UserDataStore: returning cached combined weapons data for module '{selected_module}'")
                return self._combined_weapons_cache[selected_module]
            
            # Compute if not cached
            from .ImportJSON import extract_combined_ultimate_weapons_data
            try:
                logger.info(f"UserDataStore: computing combined weapons data for module '{selected_module}'")
                combined = extract_combined_ultimate_weapons_data(self.full_json, selected_module=selected_module)
                
                # Log what we got
                for weapon_name, df in combined.items():
                    if not df.empty:
                        logger.info(f"  {weapon_name}: {len(df)} rows, columns={df.columns.tolist()}")
                        if 'Parameter' in df.columns and 'Level' in df.columns:
                            for _, row in df.iterrows():
                                logger.info(f"    {row['Parameter']}: Level={row['Level']}")
                    else:
                        logger.info(f"  {weapon_name}: EMPTY")
                
                self._combined_weapons_cache[selected_module] = combined
                logger.info(f"UserDataStore: cached combined weapons data for module '{selected_module}'")
                return combined
            except Exception as e:
                logger.exception(f"Failed to extract combined weapons data for module '{selected_module}': {e}")
                return {}
    
    def invalidate_weapons_cache(self) -> None:
        """Clear the combined weapons data cache (call when JSON is reloaded)."""
        with self._lock:
            self._combined_weapons_cache.clear()
            logger.debug("UserDataStore: cleared combined weapons cache")

    def get_dissonance_runs(self) -> pd.DataFrame:
        """Return cached dissonance rows (tier, wave, comment)."""
        with self._lock:
            return self.dissonance_df.copy()

    def get_dissonance_tier_map(self) -> Dict[str, Dict[str, object]]:
        """Return tier-level dissonance mapping with max wave and disco type."""
        with self._lock:
            return dict(self.dissonance_tier_map)

    def get_labs_all(self) -> pd.DataFrame:
        """Return all labs rows with name and level columns."""
        with self._lock:
            return self.labs_all_df.copy() if not self.labs_all_df.empty else pd.DataFrame()


    def get_current_weapon_levels_and_values(self, selected_module: str = "Primordial Collapse") -> Dict[str, Dict[str, tuple]]:
        """
        Returns for each weapon and parameter:
        {
            "header": [
                "uw_level", "uw_value", "lab_level", "lab_value", "relic_value", "module_level", "module_value", "total_value"
            ],
            "Golden Bot": {
                "Duration": (uw_level, uw_value, lab_level, lab_value, relic_value, module_level, module_value, total_value),
                ...
            },
            ...
        }
        total_value = uw_value + lab_value + relic_value + module_value
        """
        with self._lock:
            combined = self.get_combined_weapons_data(selected_module)
            result = {}
            # Add header for human readability
            result["header"] = [
                "uw_level", "uw_value", "lab_level", "lab_value", "relic_value", "module_level", "module_value", "total_value"
            ]
            from . import ImportJSON
            for weapon_name, df in combined.items():
                if df.empty:
                    continue
                weapon_data = {}
                for _, row in df.iterrows():
                    param = row.get("Parameter", "")
                    uw_level = row.get("Level", 0)
                    lab_level = row.get("Labs Level", 0)
                    module_effect = row.get("Module Effect", "")
                    relic_value = 0.0  # Placeholder, add logic if relics are available
                    module_level = 0
                    module_value = 0.0
                    # --- Lookup uw_value ---
                    uw_value = None
                    if weapon_name == "Golden Tower" and param in ImportJSON.GOLDEN_TOWER_LOOKUPS:
                        uw_value = ImportJSON.GOLDEN_TOWER_LOOKUPS[param].get(int(uw_level), 0.0)
                    elif weapon_name == "Black Hole" and param in ImportJSON.BLACK_HOLE_LOOKUPS:
                        uw_value = ImportJSON.BLACK_HOLE_LOOKUPS[param].get(int(uw_level), 0.0)
                    elif weapon_name == "Death Wave":
                        normalized_param = "Damage" if param == "Damage Mult" else param
                        if normalized_param in ImportJSON.DEATH_WAVE_LOOKUPS:
                            uw_value = ImportJSON.DEATH_WAVE_LOOKUPS[normalized_param].get(int(uw_level), 0.0)
                    elif weapon_name == "Golden Bot" and param in ImportJSON.GOLDEN_BOT_LOOKUPS:
                        uw_value = ImportJSON.GOLDEN_BOT_LOOKUPS[param].get(int(uw_level), 0.0)
                    elif weapon_name == "Chrono Field" and param in ImportJSON.CHRONO_FIELD_LOOKUPS:
                        uw_value = ImportJSON.CHRONO_FIELD_LOOKUPS[param].get(int(uw_level), 0.0)
                    elif weapon_name == "Spotlight" and param in ImportJSON.SPOTLIGHT_LOOKUPS:
                        uw_value = ImportJSON.SPOTLIGHT_LOOKUPS[param].get(int(uw_level), 0.0)
                    else:
                        uw_value = 0.0
                    # --- Lookup lab_value with correct mapping ---
                    lab_value = 0.0
                    lab_bonus_map = {
                        "Golden Tower": "Golden Tower Bonus",
                        "Death Wave": "Death Wave Coin Bonus",
                        "Black Hole": "Black Hole Coin Bonus",
                        "Spotlight": "Spotlight Coin Bonus",
                    }
                    lab_param_name = lab_bonus_map.get(weapon_name)
                    if lab_param_name and param.lower() == "bonus":
                        # Try to get lab value from the correct lab bonus column
                        lab_level_val = row.get("Labs Level", 0)
                        try:
                            lab_value = float(lab_level_val) if lab_level_val is not None else 0.0
                        except Exception:
                            lab_value = 0.0
                    else:
                        try:
                            lab_level_int = int(lab_level) if lab_level else 0
                            lab_value = float(lab_level_int)
                        except Exception:
                            lab_value = 0.0
                    # --- Parse module_value from module_effect ---
                    import re
                    if module_effect:
                        match = re.search(r'([+-]?\d+(?:\.\d+)?)', str(module_effect))
                        if match:
                            module_value = float(match.group(1))
                    # --- Parse module_level if available ---
                    # (Add logic if module level is encoded elsewhere)
                    # --- Relic value logic (add if you have relics_data) ---
                    # --- Compute total_value ---
                    uw_value_f = float(uw_value) if uw_value is not None else 0.0
                    lab_value_f = float(lab_value) if lab_value is not None else 0.0
                    relic_value_f = float(relic_value) if relic_value is not None else 0.0
                    module_value_f = float(module_value) if module_value is not None else 0.0
                    total_value = uw_value_f + lab_value_f + relic_value_f + module_value_f
                    weapon_data[param] = (uw_level, uw_value, lab_level, lab_value, relic_value, module_level, module_value, total_value)
                if weapon_data:
                    result[weapon_name] = weapon_data
            return result

    def load_from_path(self, path: str, force: bool = False) -> None:
        """Load from userData.json path and compute all derived structures.
        Uses quick-change detection to skip recompute unless force=True.
        
        Note: Clustering is now performed on-demand in optimizer.py for better performance.
        """
        with self._lock:
            path = os.fspath(path)
            mtime = None
            size = None
            try:
                st = os.stat(path)
                mtime = st.st_mtime
                size = st.st_size
            except OSError:
                logger.warning("Cannot stat path: %s", path)

            if not force and self.source_path == path and mtime == self.source_mtime and size == self.source_size:
                logger.debug("UserDataStore: no change detected; skipping reload")
                return

            # Load full JSON
            full_json = load_full_json(path)
            if not full_json:
                logger.warning("UserDataStore: loaded empty JSON from %s", path)
                # Still update source info so we don't loop
                self._update_source_meta(path, mtime, size, None)
                self.full_json = {}; self.game_stats_df = pd.DataFrame(); self.cleaned = {}; self.ultimate_weapon_upgrades_df = pd.DataFrame(); self.golden_bot_info_df = pd.DataFrame(); self.relics_data = {}
                self.workshop_todos_df = pd.DataFrame()
                self.labs_todos_df = pd.DataFrame()
                self.workshop_all_df = pd.DataFrame()
                self.labs_all_df = pd.DataFrame()
                self.analysis_results = {}
                self.dissonance_df = pd.DataFrame(columns=["tier", "wave", "comment", "disco_type"])
                self.dissonance_tier_map = build_disco_tier_map(self.dissonance_df)
                self.last_loaded_at = datetime.utcnow()
                return

            # Compute a quick content hash to detect true changes
            try:
                content_hash = self._hash_file(path)
            except Exception:
                # Fallback to hashing json string
                content_hash = hashlib.sha1(json.dumps(full_json, sort_keys=True).encode('utf-8')).hexdigest()

            # Build gameStats DataFrame
            try:
                game_stats_df = Import_JSON_record(path, 'gameStats')
            except Exception:
                # Fallback: derive from full_json if possible
                gs = full_json.get('gameStats')
                if isinstance(gs, list):
                    game_stats_df = pd.DataFrame(gs)
                else:
                    game_stats_df = pd.DataFrame()

            # Derived computations
            cleaned = {}
            try:
                if not game_stats_df.empty:
                    cleaned = cleanupJSON(game_stats_df)
            except Exception as e:
                logger.exception("cleanupJSON failed: %s", e)
            try:
                uw_df = extract_ultimate_weapon_upgrades(full_json)
            except Exception as e:
                logger.exception("extract_ultimate_weapon_upgrades failed: %s", e)
                uw_df = pd.DataFrame()

            try:
                gb_df = extract_golden_bot_info(full_json)
            except Exception as e:
                logger.exception("extract_golden_bot_info failed: %s", e)
                gb_df = pd.DataFrame()

            try:
                relics = extract_relics_data(full_json)
            except Exception as e:
                logger.exception("extract_relics_data failed: %s", e)
                relics = {}

            try:
                todos = load_todos_and_costs(path)
            except Exception as e:
                logger.exception("load_todos_and_costs failed: %s", e)
                todos = {
                    'workshop_todos_df': pd.DataFrame(),
                    'labs_todos_df': pd.DataFrame(),
                    'workshop_all_df': pd.DataFrame(),
                    'labs_all_df': pd.DataFrame(),
                }

            try:
                analysis = analyze_full_json_file(path)
            except Exception as e:
                logger.exception("analyze_full_json_file failed: %s", e)
                analysis = {}

            try:
                dissonance_df = extract_dissonance_runs(game_stats_df)
            except Exception as e:
                logger.exception("extract_dissonance_runs failed: %s", e)
                dissonance_df = pd.DataFrame(columns=["tier", "wave", "comment", "disco_type"])

            # Commit
            self._update_source_meta(path, mtime, size, content_hash)
            self.full_json = full_json
            self.game_stats_df = game_stats_df
            self.cleaned = cleaned
            self.ultimate_weapon_upgrades_df = uw_df
            self.golden_bot_info_df = gb_df
            self.relics_data = relics
            self.workshop_todos_df = todos.get('workshop_todos_df', pd.DataFrame())
            self.labs_todos_df = todos.get('labs_todos_df', pd.DataFrame())
            self.workshop_all_df = todos.get('workshop_all_df', pd.DataFrame())
            self.labs_all_df = todos.get('labs_all_df', pd.DataFrame())
            self.analysis_results = analysis
            self.dissonance_df = dissonance_df
            self.dissonance_tier_map = build_disco_tier_map(dissonance_df)
            self.last_loaded_at = datetime.utcnow()
            
            # Invalidate cached combined weapons data since source changed
            self._combined_weapons_cache.clear()

    def load_from_json(self, data: Dict[str, Any]) -> None:
        """Load from an already parsed JSON dict (e.g., uploaded content).
        
        Note: Clustering is now performed on-demand in optimizer.py for better performance.
        """
        """Load from an already parsed JSON dict (e.g., uploaded content)."""
        with self._lock:
            self.source_path = None
            self.source_mtime = None
            self.source_size = None
            try:
                self.source_hash = hashlib.sha1(json.dumps(data, sort_keys=True).encode('utf-8')).hexdigest()
            except Exception:
                self.source_hash = None

            self.full_json = data or {}

            # Build gameStats DataFrame from dict
            gs = self.full_json.get('gameStats') if isinstance(self.full_json, dict) else None
            if isinstance(gs, list):
                self.game_stats_df = pd.DataFrame(gs)
            else:
                self.game_stats_df = pd.DataFrame()

            # Derived computations
            try:
                self.cleaned = cleanupJSON(self.game_stats_df) if not self.game_stats_df.empty else {}
            except Exception as e:
                logger.exception("cleanupJSON failed: %s", e)
                self.cleaned = {}

            try:
                self.ultimate_weapon_upgrades_df = extract_ultimate_weapon_upgrades(self.full_json)
            except Exception as e:
                logger.exception("extract_ultimate_weapon_upgrades failed: %s", e)
                self.ultimate_weapon_upgrades_df = pd.DataFrame()

            try:
                self.golden_bot_info_df = extract_golden_bot_info(self.full_json)
            except Exception as e:
                logger.exception("extract_golden_bot_info failed: %s", e)
                self.golden_bot_info_df = pd.DataFrame()

            try:
                self.relics_data = extract_relics_data(self.full_json)
            except Exception as e:
                logger.exception("extract_relics_data failed: %s", e)
                self.relics_data = {}

            # For uploaded dict, we can still analyze todos against dict by writing temp file is overkill;
            # Instead, reuse the dict-flow extractors when possible.
            try:
                # Minimal replicas of load_todos_and_costs using dict inputs
                from .ImportJSON import extract_workshop_todos, extract_labs_todos
                workshop_all = extract_workshop_todos(self.full_json)
                labs_all = extract_labs_todos(self.full_json)
                self.workshop_all_df = workshop_all
                self.labs_all_df = labs_all
                self.workshop_todos_df = workshop_all[workshop_all['is_todo'] == True].copy() if not workshop_all.empty else pd.DataFrame()
                self.labs_todos_df = labs_all[labs_all['is_todo'] == True].copy() if not labs_all.empty else pd.DataFrame()
            except Exception as e:
                logger.exception("extract_*_todos failed: %s", e)
                self.workshop_todos_df = pd.DataFrame()
                self.labs_todos_df = pd.DataFrame()
                self.workshop_all_df = pd.DataFrame()
                self.labs_all_df = pd.DataFrame()

            # analysis_results requires a path for saving/sorting by file; skip here
            self.analysis_results = {}

            try:
                self.dissonance_df = extract_dissonance_runs(self.game_stats_df)
            except Exception as e:
                logger.exception("extract_dissonance_runs failed: %s", e)
                self.dissonance_df = pd.DataFrame(columns=["tier", "wave", "comment", "disco_type"])

            self.dissonance_tier_map = build_disco_tier_map(self.dissonance_df)

            self.last_loaded_at = datetime.utcnow()
            
            # Invalidate cached combined weapons data since source changed
            self._combined_weapons_cache.clear()

    # --------------- Helpers ---------------
    def _update_source_meta(self, path: Optional[str], mtime: Optional[float], size: Optional[int], content_hash: Optional[str]) -> None:
        self.source_path = path
        self.current_path = path  # Keep current_path in sync
        self.source_mtime = mtime
        self.source_size = size
        self.source_hash = content_hash

    @staticmethod
    def _hash_file(path: str, chunk_size: int = 1024 * 1024) -> str:
        sha1 = hashlib.sha1()
        with open(path, 'rb') as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                sha1.update(chunk)
        return sha1.hexdigest()

if __name__ == "__main__":
    import argparse
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))  # Ensure current dir is in path
    from ImportJSON import (
        load_full_json,
        Import_JSON_record,
        cleanupJSON,
        extract_ultimate_weapon_upgrades,
        extract_golden_bot_info,
        load_todos_and_costs,
        analyze_full_json_file,
        extract_relics_data,
        extract_workshop_todos,
        extract_labs_todos,
    )
    parser = argparse.ArgumentParser(description="Show sample output for an Ultimate Weapon.")
    parser.add_argument("--json", type=str, help="Path to userData.json file", required=True)
    parser.add_argument("--uw", type=str, help="Ultimate Weapon name (e.g., 'Black Hole')", required=True)
    parser.add_argument("--module", type=str, help="Module name (default: Primordial Collapse)", default="Primordial Collapse")
    args = parser.parse_args()

    store = UserDataStore.get()
    store.load_from_path(args.json)
    uw_data = store.get_current_weapon_levels_and_values(selected_module=args.module)
    header = uw_data.get("header", [])
    weapon = args.uw
    print(f"Header: {header}")
    if weapon in uw_data:
        print(f"\n{weapon}:")
        for param, values in uw_data[weapon].items():
            print(f"  {param}: {values}")
    else:
        print(f"No data found for '{weapon}'. Available weapons: {', '.join([k for k in uw_data.keys() if k != 'header'])}")
