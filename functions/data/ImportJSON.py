import pandas as pd
import numpy as np
import logging
from typing import Tuple, Any, Dict, List, Optional, cast
import json
import re

# Expose TimeSeriesStats for static analysis and IDE resolution
try:
    from functions.statistics import TimeSeriesStats
    from functions.statistics import compute_max_income_baseline, compute_normalized_score_100
except ImportError:
    from functions.statistics.Statistics import TimeSeriesStats
    from functions.statistics.score_utils import compute_max_income_baseline, compute_normalized_score_100

# Import all lookup tables from config
from . import config

# Re-export lookups for backward compatibility with existing code
GOLDEN_TOWER_LOOKUPS = config.GOLDEN_TOWER_LOOKUPS
BLACK_HOLE_LOOKUPS = config.BLACK_HOLE_LOOKUPS
DEATH_WAVE_LOOKUPS = config.DEATH_WAVE_LOOKUPS
GOLDEN_BOT_LOOKUPS = config.GOLDEN_BOT_LOOKUPS
SPOTLIGHT_LOOKUPS = config.SPOTLIGHT_LOOKUPS
CHRONO_FIELD_LOOKUPS = config.CHRONO_FIELD_LOOKUPS
LABS_LOOKUPS = config.LABS_LOOKUPS

# --- Extraction helpers for tower layout tab ---

# --- Recursive search helpers ---
def _find_first_list_by_key(obj: Any, key: str) -> Optional[list]:
    """Recursively search for the first list under the given key in a nested dict/list structure."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k == key and isinstance(v, list):
                return v
            found = _find_first_list_by_key(v, key)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = _find_first_list_by_key(item, key)
            if found is not None:
                return found
    return None

def extract_ultimate_weapon_upgrades(json_data: Dict[str, Any]) -> pd.DataFrame:
    """Extract upgrades for specific Ultimate Weapons into a flat DataFrame.

    Returns columns: Ultimate Weapon, Upgrade, Level, TargetLevel
    """
    target_names = {"Death Wave", "Golden Bot", "Black Hole", "Spotlight", "Golden Tower", "Chrono Field"}
    uw_list = _find_first_list_by_key(json_data, "ultimateWeapons") or []
    rows: List[Dict[str, Any]] = []
    for uw in uw_list:
        if not isinstance(uw, dict):
            continue
        name = uw.get("name")
        if name not in target_names:
            continue
        upgrades = uw.get("upgrades", {})
        target_levels = uw.get("targetLevels", {})
        if isinstance(upgrades, dict):
            for upg, val in upgrades.items():
                if isinstance(val, dict):
                    level = val.get("level")
                else:
                    level = val
                # Get target level for this upgrade
                target_level = None
                if isinstance(target_levels, dict):
                    target_level = target_levels.get(upg)
                rows.append({
                    "Ultimate Weapon": name,
                    "Upgrade": upg,
                    "Level": level,
                    "TargetLevel": target_level
                })
    return pd.DataFrame(rows)



def extract_bot_info(json_data: Dict[str, Any], bot_name: str) -> pd.DataFrame:
    """Extract any bot entry from the bots section, flattened to key/value rows."""
    bots = _find_first_list_by_key(json_data, "bots") or []
    bot: Optional[Dict[str, Any]] = None
    for b in bots:
        if isinstance(b, dict) and b.get("name") == bot_name:
            bot = b
            break
    if not bot:
        return pd.DataFrame()
    components = bot.get("components", {}) if isinstance(bot, dict) else {}
    rows: List[Dict[str, Any]] = []
    if isinstance(components, dict) and components:
        for comp_name, comp_val in components.items():
            level = None
            if isinstance(comp_val, dict):
                level = comp_val.get("level")
            else:
                level = comp_val
            rows.append({
                "Component": comp_name,
                "Level": level,
                "TargetLevel": None
            })
    else:
        for k, v in bot.items():
            if isinstance(v, (dict, list)):
                rows.append({"Component": k, "Level": json.dumps(v, ensure_ascii=False), "TargetLevel": None})
            else:
                rows.append({"Component": k, "Level": v, "TargetLevel": None})
    return pd.DataFrame(rows)

def extract_golden_bot_info(json_data: Dict[str, Any]) -> pd.DataFrame:
    """Extract the 'Golden Bot' entry from bots section, flattened to key/value rows."""
    return extract_bot_info(json_data, "Golden Bot")

# --- New: extract modulesData for future use ---
def extract_modules_data(json_data: Dict[str, Any]) -> pd.DataFrame:
    """Extract the modulesData section as a DataFrame (future use)."""
    modules = _find_first_list_by_key(json_data, "modulesData") or []
    if not modules:
        return pd.DataFrame()
    # Flatten each module dict (ignore nested lists/dicts for now)
    rows = []
    for mod in modules:
        if isinstance(mod, dict):
            flat = {k: v for k, v in mod.items() if not isinstance(v, (dict, list))}
            rows.append(flat)
    return pd.DataFrame(rows)


def extract_relevant_module_upgrades(json_data: Dict[str, Any]) -> pd.DataFrame:
    """Extract modules with submodule effects related to Death Wave, Golden Tower, Black Hole, or Spotlight.
    
    Returns DataFrame with columns:
    - Module Name
    - Type
    - Rarity
    - Level
    - Effect Name
    - Effect Value
    - Effect Unit
    - Effect Rarity
    """
    target_weapons = {"Death Wave", "Golden Tower", "Black Hole", "Spotlight", "Chrono Field"}
    modules = _find_first_list_by_key(json_data, "modulesData") or []
    
    rows: List[Dict[str, Any]] = []
    for mod in modules:
        if not isinstance(mod, dict):
            continue
        
        mod_name = mod.get("name")
        mod_type = mod.get("type")
        mod_rarity = mod.get("currentRarity")
        mod_level = mod.get("currentLevel")
        
        sub_effects = mod.get("subModuleEffects", [])
        if not isinstance(sub_effects, list):
            continue
        
        # Check if any submodule effect relates to our target weapons
        for effect in sub_effects:
            if not isinstance(effect, dict):
                continue
            
            effect_name = effect.get("name", "")
            # Check if effect name starts with any target weapon
            is_relevant = any(effect_name.startswith(weapon) for weapon in target_weapons)
            
            if is_relevant:
                rows.append({
                    "Module Name": mod_name,
                    "Type": mod_type,
                    "Rarity": mod_rarity,
                    "Level": mod_level,
                    "Effect Name": effect_name,
                    "Effect Value": effect.get("value"),
                    "Effect Unit": effect.get("unit", ""),
                    "Effect Rarity": effect.get("rarity")
                })
    
    return pd.DataFrame(rows)

def extract_relevant_labs_progress(json_data: Dict[str, Any]) -> pd.DataFrame:
    """Extract labs progress for research related to Golden Tower, Golden Bot, Black Hole, Spotlight, Death Wave, and Chrono Field.
    
    Returns DataFrame with columns:
    - Research Name
    - Level
    - Target Level (if present)
    """
    # Keywords to search for in research names (include all bots)
    target_keywords = [
        "Golden Tower", "Golden Bot", "Black Hole", "Spotlight",
        "Death Wave", "DeathWave", "Chrono Field",
        "Flame Bot", "FlamBot", "Thunder Bot", "ThunderBot", "Amplify Bot", "AmplifyBot",
    ]

    labs_progress = _find_first_list_by_key(json_data, "labs") or []

    rows: List[Dict[str, Any]] = []
    for lab in labs_progress:
        if not isinstance(lab, dict):
            continue

        name = lab.get("name", "")
        level = lab.get("level")
        target_level = lab.get("targetLevel")

        # Check if any target keyword appears in the research name (robust to spacing)
        name_lower = name.lower()
        collapsed_lower = name_lower.replace(" ", "")
        is_relevant = any(
            kw.lower() in name_lower or kw.lower().replace(" ", "") in collapsed_lower
            for kw in target_keywords
        )

        if is_relevant:
            row = {
                "Research Name": name,
                "Level": level
            }
            if target_level is not None:
                row["Target Level"] = target_level
            rows.append(row)

    return pd.DataFrame(rows)


def _normalize_match_key(text: Any) -> str:
    """Normalize text for tolerant comparisons across spacing/punctuation variants."""
    return "".join(ch for ch in str(text).lower() if ch.isalnum())

def compute_total_value(weapon_type: str, param: str, level: int, module_effect_str: str, labs_level: Any) -> str:
    """Compute the total value for a parameter based on upgrade level, module effect, and labs level.
    
    Args:
        weapon_type: Weapon type (e.g., "Golden Tower", "Death Wave", "Black Hole")
        param: Parameter name (e.g., "Bonus", "Duration", "Cooldown", "Size")
        level: Current upgrade level
        module_effect_str: Module effect string (e.g., "+3", "+2s")
        labs_level: Labs research level (used for percentage bonuses)
    
    Returns:
        String representation of computed total value
    """
    # Get base value from lookup table
    base_value = None
    # Normalize aliases to canonical config key names.
    _, normalized_param = config.normalize_weapon_parameter(weapon_type, param)
    lookup_key = (weapon_type, normalized_param)
    
    lookup_group = config.LEVEL_LOOKUPS_BY_ENTITY.get(weapon_type, {})
    if normalized_param in lookup_group:
        lookup = lookup_group[normalized_param]
        base_value = lookup.get(level)
    
    # Parse module effect first (before checking base_value)
    module_bonus = 0
    if module_effect_str:
        # Extract numeric value from module effect string (e.g., "+3", "+2s", "+50x")
        import re
        match = re.search(r'([+\-]?\d+(?:\.\d+)?)', module_effect_str)
        if match:
            module_bonus = float(match.group(1))
    
    # Get labs bonus if available (direct map first, LUT fallback second)
    labs_bonus = 0
    labs_lookup = config.get_labs_lookup_table(weapon_type, normalized_param)
    if isinstance(labs_lookup, dict) and labs_level != "":
        try:
            labs_level_int = int(labs_level)
            raw_bonus = labs_lookup.get(labs_level_int, 0)
            if isinstance(raw_bonus, bool):
                labs_bonus = 1.0 if raw_bonus else 0.0
            else:
                labs_bonus = float(raw_bonus)
        except (ValueError, TypeError):
            labs_bonus = 0
    
    # Special case: Some parameters don't have upgrade levels, only labs research
    # If base_value is None but we have module effect or labs bonus, allow calculation
    if base_value is None:
        if isinstance(labs_lookup, dict) or module_bonus != 0:
            # Allow calculation with just module effect + labs bonus (no base value)
            base_value = 0
        else:
            # No data available to compute total
            return ""
    
    # Compute total based on parameter type
    if normalized_param == "Cooldown":
        # Cooldown: subtract module bonus, add labs effect (labs values are negative for reduction)
        total = base_value - module_bonus + labs_bonus
        return f"{total:.0f}s"
    elif normalized_param == "Duration":
        # Duration: add module bonus and labs bonus
        total = base_value + module_bonus + labs_bonus
        return f"{total:.0f}s"
    elif normalized_param in {"Bonus", "Coin Bonus"}:
        # Bonus/Multiplier: add module bonus (and labs bonus if applicable)
        total = base_value + module_bonus + labs_bonus
        return f"{total:.1f}×" if total > 0 else ""
    elif normalized_param in {"Damage", "Damage Mult"}:
        # Death Wave damage is a large base numeric; labs bonus should be multiplicative (additive in lookup holds bonus multiplier)
        # If labs_bonus represents a multiplier (e.g., 2.35) and base_value is raw damage, compute base * labs_bonus then
        # apply any module bonus additively.
        if weapon_type == "Death Wave" and labs_bonus and labs_bonus > 0 and base_value is not None:
            total = (base_value * labs_bonus) + module_bonus
        else:
            total = (base_value or 0) + module_bonus + labs_bonus
        return f"{total:.0f}×" if total > 0 else ""
    elif normalized_param == "Quantity":
        # Quantity: add module bonus and labs bonus
        total = base_value + module_bonus + labs_bonus
        return f"{total:.0f}#" if total > 0 else ""
    elif normalized_param == "Size":
        # Size: add module bonus and labs bonus (for Black Hole)
        total = base_value + module_bonus + labs_bonus
        return f"{total:.0f}m"
    elif normalized_param == "Range":
        # Range: add module bonus and labs bonus (for Golden Bot)
        total = base_value + module_bonus + labs_bonus
        return f"{total:.0f}m"
    elif normalized_param == "Angle":
        # Angle: add module bonus and labs bonus (for Spotlight)
        total = base_value + module_bonus + labs_bonus
        return f"{total:.0f}°"
    elif normalized_param == "Slow %":
        # Slow %: add module bonus and labs bonus (for Chrono Field)
        total = base_value + module_bonus + labs_bonus
        return f"{total:.0f}%" if total > 0 else ""
    
    return f"{base_value}" if base_value else ""

def extract_combined_ultimate_weapons_data(json_data: Dict[str, Any], selected_module: str = "Primordial Collapse") -> Dict[str, pd.DataFrame]:
    """Extract and combine data for each ultimate weapon type from multiple sources.
    
    Combines data from:
    - Ultimate weapon upgrades (level, target level)
    - Golden Bot components (level, target level)
    - Module effects (filtered by selected_module)
    - Labs progress (research levels)
    
    Args:
        json_data: Full JSON data dictionary
        selected_module: Module name to filter for ("Primordial Collapse" or "Multiverse Nexus")
    
    Returns:
        Dict with keys for each weapon type (Death Wave, Golden Tower, Black Hole, Spotlight, Golden Bot)
        Each value is a DataFrame with columns: Parameter, Level, Target Level, Module Effect, Labs Level, Total Value
    """
    import time
    import logging as _logging
    _logger = _logging.getLogger(__name__)
    _start_total = time.time()
    _logger.debug("[IJ] extract_combined_ultimate_weapons_data() starting")
    
    # Define weapon types — UWs and all bots
    _BOT_NAMES = {"Golden Bot", "Flame Bot", "Thunder Bot", "Amplify Bot"}
    weapon_types = ["Death Wave", "Golden Tower", "Black Hole", "Spotlight", "Golden Bot", "Chrono Field",
                    "Flame Bot", "Thunder Bot", "Amplify Bot"]
    
    # Extract all data sources
    _t = time.time()
    _logger.debug("[IJ] Calling extract_ultimate_weapon_upgrades...")
    uw_df = extract_ultimate_weapon_upgrades(json_data)
    _logger.debug(f"[IJ] extract_ultimate_weapon_upgrades done ({time.time() - _t:.3f}s)")
    
    _t = time.time()
    _logger.debug("[IJ] Calling extract_golden_bot_info...")
    gb_df = extract_golden_bot_info(json_data)
    _logger.debug(f"[IJ] extract_golden_bot_info done ({time.time() - _t:.3f}s)")

    # Pre-extract all bot DataFrames keyed by bot name for the main loop
    _other_bots = ["Flame Bot", "Thunder Bot", "Amplify Bot"]
    _t = time.time()
    _logger.debug("[IJ] Pre-extracting other bot data...")
    _bot_dfs: Dict[str, pd.DataFrame] = {"Golden Bot": gb_df}
    for _bn in _other_bots:
        _bot_dfs[_bn] = extract_bot_info(json_data, _bn)
    _logger.debug(f"[IJ] Other bot extraction done ({time.time() - _t:.3f}s)")
    
    _t = time.time()
    _logger.debug("[IJ] Calling extract_relevant_module_upgrades...")
    modules_df = extract_relevant_module_upgrades(json_data)
    _logger.debug(f"[IJ] extract_relevant_module_upgrades done ({time.time() - _t:.3f}s)")
    
    _t = time.time()
    _logger.debug("[IJ] Calling extract_relevant_labs_progress...")
    labs_df = extract_relevant_labs_progress(json_data)
    _logger.debug(f"[IJ] extract_relevant_labs_progress done ({time.time() - _t:.3f}s)")
    
    # Filter modules by selected module
    if not modules_df.empty:
        modules_df = modules_df[modules_df["Module Name"] == selected_module].copy()
    
    # Create a mapping helper for labs research to parameter names
    def find_matching_labs_level(weapon_type: str, param: str, labs_df: pd.DataFrame) -> str:
        """Find matching labs level for a given weapon type and parameter.

        Heuristics:
        - Filter research rows that reference the weapon (robust to whitespace variants)
        - Prefer rows whose name contains param-specific keywords
        - Prefer coin-related research for Black Hole Bonus if present
        - If multiple candidates remain, choose the one with the highest numeric Level
        Also emits DEBUG logs with candidates and selected level.
        """
        if labs_df.empty:
            return ""
        
        # Direct search in research name (robust matching for spacing/word variants)
        plain_mask = labs_df["Research Name"].str.contains(weapon_type, case=False, na=False)
        collapsed_weapon = weapon_type.replace(" ", "")
        research_collapsed = labs_df["Research Name"].str.replace(" ", "", regex=False)
        collapsed_mask = research_collapsed.str.contains(collapsed_weapon, case=False, na=False)
        labs_match = labs_df[plain_mask | collapsed_mask]

        if labs_match.empty:
            # 3. Require each word of weapon_type to appear somewhere in research name
            import re as _re
            words = [w for w in _re.split(r"\s+", weapon_type) if w]
            subset = labs_df.copy()
            for w in words:
                subset = subset[subset["Research Name"].str.contains(w, case=False, na=False)]
            labs_match = subset

        if labs_match.empty:
            if DEBUG:
                logger.debug(f"[labs-map] No research name match for weapon '{weapon_type}' param '{param}'")
            return ""
        
        # Score each candidate using normalized token overlap.
        _, canonical_param = config.normalize_weapon_parameter(weapon_type, param)
        param_key = _normalize_match_key(canonical_param)
        param_tokens = [tok for tok in re.split(r"[^a-z0-9]+", canonical_param.lower()) if tok]

        # Common lab naming variants across sources.
        token_aliases = {
            "coin": ["coin", "coins"],
            "coins": ["coin", "coins"],
            "mult": ["mult", "multiplier"],
            "missiles": ["missile", "missiles"],
            "armor": ["armor", "armour"],
            "health": ["health", "hp"],
        }

        scored_rows: List[tuple[float, Any]] = []
        for _, row in labs_match.iterrows():
            research_name = row.get("Research Name", "")
            research_key = _normalize_match_key(research_name)
            research_lower = str(research_name).lower()
            score = 0.0

            if param_key and param_key in research_key:
                score += 100.0

            for token in param_tokens:
                aliases = token_aliases.get(token, [token])
                token_hit = any(alias and alias in research_lower for alias in aliases)
                if token_hit:
                    score += 20.0

            # Strong disambiguation for historically ambiguous rows.
            if canonical_param == "Coin Bonus" and "coin" in research_lower:
                score += 25.0
            if canonical_param == "Damage Mult" and "damage" in research_lower:
                score += 25.0

            if score > 0:
                scored_rows.append((score, row))

        if scored_rows:
            # Tie-break on numeric level, preferring higher completed research.
            best = None
            best_key = None
            for score, row in scored_rows:
                try:
                    lvl = float(pd.to_numeric(row.get("Level"), errors="coerce"))
                except Exception:
                    lvl = -1.0
                rank = (score, lvl)
                if best is None or rank > cast(tuple[float, float], best_key):
                    best = row
                    best_key = rank

            if best is not None:
                chosen_level = best.get("Level", "")
                if pd.notna(chosen_level):
                    return str(chosen_level)

        if DEBUG:
            logger.debug("[labs-map] No match for %s/%s after heuristics", weapon_type, param)
        return ""
    
    result = {}
    
    for weapon_type in weapon_types:
        rows = []
        
        if weapon_type in _BOT_NAMES:
            # Use bot components from bots JSON section
            bot_df = _bot_dfs.get(weapon_type, pd.DataFrame())
            if not bot_df.empty:
                for _, row in bot_df.iterrows():
                    param = row["Component"]
                    level = row["Level"]
                    target = row.get("TargetLevel")
                    
                    # Find matching module effect
                    module_effect = ""
                    if not modules_df.empty:
                        module_match = modules_df[modules_df["Effect Name"].str.contains(weapon_type, case=False, na=False)]
                        for _, mod_row in module_match.iterrows():
                            if param.lower() in mod_row["Effect Name"].lower():
                                value = mod_row["Effect Value"]
                                unit = mod_row["Effect Unit"]
                                module_effect = f"+{value}{unit}" if unit else f"+{value}"
                                break
                    
                    # Find matching labs level
                    labs_level = find_matching_labs_level(weapon_type, param, labs_df)
                    
                    # Compute total value
                    total_value = compute_total_value(weapon_type, param, level, module_effect, labs_level)
                    
                    rows.append({
                        "Parameter": param,
                        "Level": level,
                        "Target Level": target if pd.notna(target) else "",
                        "Module Effect": module_effect,
                        "Labs Level": labs_level,
                        "Total Value": total_value
                    })

            # Add labs-only parameters (e.g. Burn Stack, Linger Time) not present as components.
            existing_params = {
                config.normalize_weapon_parameter(weapon_type, str(r.get("Parameter", "")))[1]
                for r in rows
            }
            for lab_param in config.get_labs_parameters(weapon_type):
                _, canonical_lab_param = config.normalize_weapon_parameter(weapon_type, lab_param)
                if canonical_lab_param in existing_params:
                    continue
                labs_level = find_matching_labs_level(weapon_type, canonical_lab_param, labs_df)
                total_value = compute_total_value(weapon_type, canonical_lab_param, 0, "", labs_level)
                rows.append({
                    "Parameter": canonical_lab_param,
                    "Level": 0,
                    "Target Level": "",
                    "Module Effect": "",
                    "Labs Level": labs_level,
                    "Total Value": total_value
                })
                existing_params.add(canonical_lab_param)

        else:
            # Use ultimate weapon upgrades
            if not uw_df.empty:
                weapon_data = uw_df[uw_df["Ultimate Weapon"] == weapon_type]
                
                for _, row in weapon_data.iterrows():
                    param = row["Upgrade"]
                    level = row["Level"]
                    target = row["TargetLevel"]
                    
                    # Find matching module effect
                    module_effect = ""
                    if not modules_df.empty:
                        module_match = modules_df[
                            modules_df["Effect Name"].str.startswith(weapon_type, na=False)
                        ]
                        for _, mod_row in module_match.iterrows():
                            # Check if the effect name matches the parameter
                            effect_name = mod_row["Effect Name"].replace(f"{weapon_type} - ", "")
                            if param.lower() in effect_name.lower() or effect_name.lower() in param.lower():
                                value = mod_row["Effect Value"]
                                unit = mod_row["Effect Unit"]
                                module_effect = f"+{value}{unit}" if unit else f"+{value}"
                                break
                    
                    # Find matching labs level
                    labs_level = find_matching_labs_level(weapon_type, param, labs_df)
                    
                    # Compute total value
                    total_value = compute_total_value(weapon_type, param, level, module_effect, labs_level)
                    
                    rows.append({
                        "Parameter": param,
                        "Level": level,
                        "Target Level": target if pd.notna(target) else "",
                        "Module Effect": module_effect,
                        "Labs Level": labs_level,
                        "Total Value": total_value
                    })
            
            # Add labs-only parameters from the full LUT labs bucket, not just legacy LABS_LOOKUPS.
            existing_params = {
                config.normalize_weapon_parameter(weapon_type, str(r.get("Parameter", "")))[1]
                for r in rows
            }
            for lab_param in config.get_labs_parameters(weapon_type):
                _, canonical_lab_param = config.normalize_weapon_parameter(weapon_type, lab_param)
                if canonical_lab_param in existing_params:
                    continue

                labs_level = find_matching_labs_level(weapon_type, canonical_lab_param, labs_df)

                module_effect = ""
                if not modules_df.empty:
                    module_match = modules_df[
                        modules_df["Effect Name"].str.startswith(weapon_type, na=False)
                    ]
                    for _, mod_row in module_match.iterrows():
                        effect_name = mod_row["Effect Name"].replace(f"{weapon_type} - ", "")
                        if (
                            canonical_lab_param.lower() in effect_name.lower()
                            or effect_name.lower() in canonical_lab_param.lower()
                        ):
                            value = mod_row["Effect Value"]
                            unit = mod_row["Effect Unit"]
                            module_effect = f"+{value}{unit}" if unit else f"+{value}"
                            break

                total_value = compute_total_value(weapon_type, canonical_lab_param, 0, module_effect, labs_level)
                rows.append({
                    "Parameter": canonical_lab_param,
                    "Level": 0,
                    "Target Level": "",
                    "Module Effect": module_effect,
                    "Labs Level": labs_level,
                    "Total Value": total_value
                })
                existing_params.add(canonical_lab_param)
        
        # Create DataFrame for this weapon type
        if rows:
            result[weapon_type] = pd.DataFrame(rows)
        else:
            result[weapon_type] = pd.DataFrame(columns=["Parameter", "Level", "Target Level", "Module Effect", "Labs Level", "Total Value"])
    
    _logger.debug(f"[IJ] extract_combined_ultimate_weapons_data() completed ({time.time() - _start_total:.3f}s, {len(result)} weapons)")
    return result

# Debug flag - set to False to disable all debug prints
DEBUG = False
logger = logging.getLogger("rend-import")
if not logger.handlers:
    logging.basicConfig(level=logging.INFO, format='[%(levelname)s] %(message)s')
logger.setLevel(logging.DEBUG if DEBUG else logging.INFO)

#Import JSON file and cover exceptions
def Import_JSON_record(path: str, record: str) -> pd.DataFrame:   

    
    df = pd.read_json(path, typ='series')
    df = pd.DataFrame(df[record])
    return df


def import_selected_sections(path: str, card_id: int = 31) -> dict[str, pd.DataFrame]:
    """Import selected userData.json sections as DataFrames.

    Sections:
        1) cardTracker.cardSlots filtered by id
        2) gameStats (all runs)
        3) relicsData (all relics)
        4) workshopData (all workshops)
        5) modulesData (all modules, including submodules)
        6) labsProgress (all labs)
    """
    with open(path, 'r') as file:
        data = json.load(file)

    def _normalize_section(section: Any) -> pd.DataFrame:
        if section is None:
            return pd.DataFrame()
        if isinstance(section, list):
            return pd.json_normalize(section, sep='.')
        if isinstance(section, dict):
            # If values are dicts, keep the key for traceability
            if section and all(isinstance(v, dict) for v in section.values()):
                rows: list[dict[str, Any]] = []
                for k, v in section.items():
                    row: dict[str, Any] = {'_key': k}
                    row.update(v)
                    rows.append(row)
                return pd.json_normalize(rows, sep='.')
            return pd.json_normalize(section, sep='.')
        return pd.DataFrame([{'value': section}])

    def _normalize_game_stats(game_stats: Any) -> pd.DataFrame:
        if game_stats is None:
            return pd.DataFrame()
        if isinstance(game_stats, list):
            return pd.json_normalize(game_stats, sep='.')
        if isinstance(game_stats, dict):
            rows: list[dict[str, Any]] = []
            for k, v in game_stats.items():
                if isinstance(v, dict):
                    row = {'run_id': k}
                    row.update(v)
                else:
                    row = {'run_id': k, 'value': v}
                rows.append(row)
            return pd.json_normalize(rows, sep='.')
        return pd.DataFrame([{'value': game_stats}])

    # 1) CardTracker > CardSlots (id filter)
    card_slots = data.get('cardTracker', {}).get('cardSlots', [])
    card_slots_filtered = [s for s in card_slots if s.get('id') == card_id]
    df_card_slots = pd.DataFrame(card_slots_filtered)

    # 2) gameStats > all runs
    df_game_stats = _normalize_game_stats(data.get('gameStats'))

    # 3) relicsData > all relics
    df_relics = _normalize_section(data.get('relicsData'))

    # 4) workshopData > all workshops
    df_workshop = _normalize_section(data.get('workshopData'))

    # 5) modulesData > all modules including submodules
    df_modules = _normalize_section(data.get('modulesData'))

    # 6) labsProgress > all labs
    df_labs = _normalize_section(data.get('labsProgress'))

    return {
        'card_slots_id_31': df_card_slots,
        'game_stats': df_game_stats,
        'relics': df_relics,
        'workshop': df_workshop,
        'modules': df_modules,
        'labs': df_labs
    }


def extract_bot_supporter_data(df: pd.DataFrame) -> pd.DataFrame:
    """Extract and aggregate bot supporter data by day.
    
    The bot supporter provides the following per run:
    - cannon_shards, armor_shards, generator_shards, core_shards
    - common_modules (cap: 5/day), rare_modules (cap: 2/day)
    - summoned_enemies, guardian_damage, guardian_catches
    - coins_stolen, coins_fetched, reroll_shards
    - gems (cap: 10/day), medals (cap: 10/day)
    
    Returns DataFrame with daily totals and capped values.
    """
    from .ConvertNumbers import convert_abbreviated_number
    
    # Define bot supporter fields
    bot_fields = [
        'cannon_shards', 'armor_shards', 'generator_shards', 'core_shards',
        'common_modules', 'rare_modules', 'summoned_enemies',
        'guardian_damage', 'guardian_catches', 'coins_stolen', 'coins_fetched',
        'reroll_shards', 'gems', 'medals'
    ]
    
    # Check which fields exist in the dataframe
    available_fields = [f for f in bot_fields if f in df.columns]
    
    if not available_fields or 'timestamp' not in df.columns:
        logger.warning("extract_bot_supporter_data: Required fields not found in dataframe")
        return pd.DataFrame()
    
    # Create a copy with only needed fields
    bot_df = df[['timestamp'] + available_fields].copy()
    
    # Convert abbreviated numbers for coin fields
    for field in ['coins_fetched', 'coins_stolen', 'summoned_enemies']:
        if field in bot_df.columns:
            bot_df[field] = bot_df[field].apply(convert_abbreviated_number)
    
    # Convert numeric fields
    for field in available_fields:
        bot_df[field] = pd.to_numeric(bot_df[field], errors='coerce').fillna(0)
    
    # Ensure timestamp is datetime and extract date
    bot_df['timestamp'] = pd.to_datetime(bot_df['timestamp'], errors='coerce')
    bot_df['date'] = bot_df['timestamp'].apply(lambda x: x.date() if pd.notna(x) else None)
    
    # Group by date and sum
    daily_agg = bot_df.groupby('date')[available_fields].sum().reset_index()
    
    # Apply daily caps
    daily_caps = {
        'gems': 10,
        'medals': 10,
        'common_modules': 5,
        'rare_modules': 2
    }
    
    for field, cap in daily_caps.items():
        if field in daily_agg.columns:
            daily_agg[f'{field}_uncapped'] = daily_agg[field]
            daily_agg[field] = daily_agg[field].clip(upper=cap)
    
    # Mark consecutive zeros as NaN (data entry errors / guardian not activated)
    for field in available_fields:
        if field in daily_agg.columns:
            # Find runs of zeros (minimum 2 consecutive zeros)
            is_zero = daily_agg[field] == 0
            # Create groups of consecutive values
            zero_groups = (is_zero != is_zero.shift()).cumsum()
            # Count consecutive zeros in each group
            zero_counts = is_zero.groupby(zero_groups).transform('sum')
            # Mark as NaN if part of 2+ consecutive zeros
            consecutive_zeros = is_zero & (zero_counts >= 2)
            daily_agg.loc[consecutive_zeros, field] = np.nan
            
            # Also mark uncapped versions if they exist
            uncapped_col = f'{field}_uncapped'
            if uncapped_col in daily_agg.columns:
                daily_agg.loc[consecutive_zeros, uncapped_col] = np.nan
    
    # Find the first valid date (first date with any non-zero guardian data)
    # Sum across all fields for each row (ignoring NaN)
    row_sums = daily_agg[available_fields].sum(axis=1, skipna=True)
    valid_rows = row_sums > 0
    
    if valid_rows.any():
        first_valid_idx = valid_rows.idxmax()
        daily_agg = daily_agg.iloc[first_valid_idx:].reset_index(drop=True)
    
    return daily_agg


#ParsedJSON = Import_JSON_record('C:\\Users\\thors\\AppData\\Roaming\\rendapp\\userData.json','gameStats')
#print("Parsed JSON:")
#print(ParsedJSON)

def cleanupJSON(df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    #Convert Numbers Function
    from .ConvertNumbers import convert_abbreviated_number, time_to_decimal_hours, pad_tier

    #Assign data formats
    # Timestamps in userData.json can be mixed ISO8601 forms (with/without fractional seconds or timezone).
    # Use pandas' mixed parsing and normalize to UTC for consistent comparisons.
    ts = pd.to_datetime(df['timestamp'], errors='coerce', utc=True, format='mixed')
    bad_ts = int(ts.isna().sum())
    if bad_ts:
        logger.warning("cleanupJSON: dropping %d rows with unparseable timestamp", bad_ts)
        df = df.loc[~ts.isna()].copy()
        ts = ts.loc[~ts.isna()]
    df['timestamp'] = ts
    df['tier']=df['tier'].apply(pad_tier)
    df['wave'] = pd.to_numeric(df['wave'])
    df['real_time']=df['real_time'].apply(time_to_decimal_hours)

    #df=df.drop(columns=['damage_taken_while_berserked', 'damage_gain_from_berserk','death_defy'])
    
    #Convert 1.08M -> 1.080.000
    df['coins_earned']=df['coins_earned'].apply(convert_abbreviated_number)
    df['cells_earned']=df['cells_earned'].apply(convert_abbreviated_number)
    df['reroll_shards_earned']=df['reroll_shards_earned'].apply(convert_abbreviated_number)
    
    # Extract bot supporter data (daily aggregation)
    bot_daily_df = extract_bot_supporter_data(df)
    
    # Normalize run type using kill reason when available (e.g., "Killed By: Quit").
    if 'run_type' not in df.columns:
        df['run_type'] = 'farming'
    else:
        df['run_type'] = df['run_type'].astype(str).str.strip().str.lower().replace('', 'farming').fillna('farming')

    kill_reason_col = next(
        (
            col for col in df.columns
            if ''.join(ch for ch in str(col).lower() if ch.isalnum()) in {'killedby', 'killreason', 'deathreason'}
        ),
        None,
    )
    # Preserve raw kill reason as 'killed_by' for single-run tooltip display.
    # run_type is NO LONGER overwritten to 'quit' — the game-reported run_type
    # is kept; quit is surfaced via killed_by in hover instead.
    # Future tweak: if a 'quit' run_type still appears from the game export itself
    # (rather than derived here), it passes through as-is.
    if kill_reason_col is not None:
        _kb_raw = df[kill_reason_col].astype(str).str.strip()
        df['killed_by'] = _kb_raw.replace({'nan': '', 'None': '', 'none': ''}).fillna('')
    else:
        df['killed_by'] = ''

    # ── Tag dissonance (disco) runs from notes ───────────────────────────────
    # The disco feature launched 2026-04-07. Any run with a note/comment
    # containing a disco keyword on or after that date is tagged run_type='disco'.
    # The raw note is preserved so dissonance.py can read the subcategory
    # (attack / defense / utility / uw) from it.
    #
    # Future tweak: extend _DISCO_NOTE_ALIASES to add more keyword variants.
    _DISCO_NOTE_ALIASES = ['disco', 'dissonance', 'disso']
    _DISCO_LAUNCH = pd.Timestamp('2026-04-07', tz='UTC')
    _notes_col = next(
        (col for col in df.columns
         if ''.join(ch for ch in str(col).lower() if ch.isalnum()) in {'notes', 'note', 'comment'}),
        None,
    )
    if _notes_col is not None:
        _notes_norm = df[_notes_col].fillna('').astype(str).str.lower()
        _note_disco_mask = pd.Series(False, index=df.index)
        for _alias in _DISCO_NOTE_ALIASES:
            _note_disco_mask |= _notes_norm.str.contains(_alias, regex=False, na=False)
        if _note_disco_mask.any():
            _ts_col = next(
                (col for col in df.columns
                 if ''.join(ch for ch in str(col).lower() if ch.isalnum()) in {'timestamp', 'date', 'createdat'}),
                None,
            )
            if _ts_col is not None:
                _ts = pd.to_datetime(df[_ts_col], errors='coerce', utc=True)
                _note_disco_mask = _note_disco_mask & _ts.ge(_DISCO_LAUNCH).fillna(False)
            df.loc[_note_disco_mask, 'run_type'] = 'disco'

    #Compute x per hour
    df['coins_per_hour']=df['coins_earned']/df['real_time']
    df['cells_per_hour']=df['cells_earned']/df['real_time']
    df['reroll_shards_per_hour']=df['reroll_shards_earned']/df['real_time']
    
    # Compute wave metrics
    df['waves_per_tier']=df['wave']
    df['waves_per_hour']=df['wave']/df['real_time']

    # Exclude deleted runs first
    filter_status=['deleted']
    df_no_deleted = df[~df['status'].isin(filter_status)]
    
    # Store ALL run types for time series (used by Current scenario and grouped_by_run_type_tier_df).
    # 'disco' is included so dissonance runs appear in the weekly Current view.
    # Future tweak: add run types here to include them in time series analytics.
    filter_all_types = ['farming', 'overnight', 'tournament', 'quit', 'milestone', 'disco']
    all_runs_df = df_no_deleted[df_no_deleted['run_type'].isin(filter_all_types)]
    
    # Filter [Farming, Overnight] for standard metrics (overview, 24h, Day+Night)
    filter_runtype=['farming','overnight']
    filtered_runtype=df_no_deleted[df_no_deleted['run_type'].isin(filter_runtype)]
    
    #Keep only needed columns
    # 'killed_by' is an optional run-level column for single-run tooltip display.
    # Future tweak: add columns here to propagate them to time_series_df / all_runs.
    _base_columns=['timestamp','tier','run_type','wave','coins_earned','cells_earned','reroll_shards_earned','waves_per_tier','real_time','coins_per_hour','cells_per_hour','reroll_shards_per_hour','waves_per_hour']
    # Carry optional per-run columns through to all_runs_time_series_df.
    # 'killed_by': raw kill reason for tooltip display.
    # 'notes'/'note'/'comment': run notes, needed by dissonance.py for disco_type derivation.
    _notes_candidate = next((c for c in df.columns if ''.join(ch for ch in str(c).lower() if ch.isalnum()) in {'notes', 'note', 'comment'}), None)
    _optional_extra = [c for c in ['killed_by'] + ([_notes_candidate] if _notes_candidate else []) if c in df.columns]
    filtered_columns = _base_columns
    _all_runs_columns = _base_columns + _optional_extra
    filtered_df=filtered_runtype[filtered_columns]

    # Store filtered data for standard time series (farming/overnight only)
    time_series_df = filtered_df.copy()

    # Prepare all_runs time series — includes optional columns (e.g. killed_by)
    all_runs_time_series_df = all_runs_df[[c for c in _all_runs_columns if c in all_runs_df.columns]].copy()
    # Compute score for each row in time_series_df using the same weights as compute_score
    # Normalize each metric across all rows, then compute weighted sum
    weights = {
        "coins_earned": 0.3,
        "coins_per_hour": 0.2,
        "cells_earned": 0.2,
        "cells_per_hour": 0.2,
        "reroll_shards_earned": 0.1
    }
    
    # Compute scores for farming/overnight time series
    score_components = []
    for metric, weight in weights.items():
        if metric in time_series_df.columns:
            max_val = time_series_df[metric].max()
            if max_val != 0 and not pd.isna(max_val):
                normalized = (time_series_df[metric] / max_val) * weight * 100
                score_components.append(normalized)
    
    if score_components:
        time_series_df['score'] = sum(score_components)
    else:
        time_series_df['score'] = 0.0
    
    # Compute scores for all_runs time series (include tournament, quit, milestone)
    all_score_components = []
    for metric, weight in weights.items():
        if metric in all_runs_time_series_df.columns:
            max_val = all_runs_time_series_df[metric].max()
            if max_val != 0 and not pd.isna(max_val):
                normalized = (all_runs_time_series_df[metric] / max_val) * weight * 100
                all_score_components.append(normalized)
    
    if all_score_components:
        all_runs_time_series_df['score'] = sum(all_score_components)
    else:
        all_runs_time_series_df['score'] = 0.0

    # Compute per-run optimizer score using:
    # max_metric = max(metric_per_hour over all runs) * 24
    # overall = w_coins * coins/max_coins + w_cells * cells/max_cells + w_shards * shards/max_shards
    def _add_run_optimizer_score(runs_df: pd.DataFrame) -> pd.DataFrame:
        out_df = runs_df.copy()
        if out_df.empty:
            out_df['optimizer_score'] = 0.0
            return out_df

        baseline = compute_max_income_baseline(out_df)
        out_df['optimizer_score'] = out_df.apply(
            lambda r: compute_normalized_score_100(
                float(r.get('coins_earned', 0.0) or 0.0),
                float(r.get('cells_earned', 0.0) or 0.0),
                float(r.get('reroll_shards_earned', 0.0) or 0.0),
                float(baseline.get('max_coins_per_day', 0.0) or 0.0),
                float(baseline.get('max_cells_per_day', 0.0) or 0.0),
                float(baseline.get('max_shards_per_day', 0.0) or 0.0),
            ),
            axis=1,
        )

        return out_df

    time_series_df = _add_run_optimizer_score(time_series_df)
    all_runs_time_series_df = _add_run_optimizer_score(all_runs_time_series_df)
    baseline_source_df = all_runs_time_series_df if not all_runs_time_series_df.empty else time_series_df
    max_income_baseline = compute_max_income_baseline(baseline_source_df)
    max_income_baseline_df = pd.DataFrame([max_income_baseline])

    # Daily source-of-truth dataframe for all run types with sums, means and weighted CIs.
    daily_metrics_df = pd.DataFrame()
    if not all_runs_time_series_df.empty:
        daily_base = all_runs_time_series_df.copy()
        daily_base['timestamp'] = pd.to_datetime(daily_base['timestamp'], errors='coerce').dt.tz_localize(None)
        daily_base = daily_base[daily_base['timestamp'].notna()].copy()
        if not daily_base.empty:
            daily_base['date'] = daily_base['timestamp'].dt.floor('D')

            metrics = ['coins_earned', 'cells_earned', 'reroll_shards_earned', 'waves_per_tier', 'score', 'optimizer_score']
            sum_df = daily_base.groupby('date', as_index=False)[metrics].sum().rename(columns={m: f'sum_{m}' for m in metrics})
            avg_df = daily_base.groupby('date', as_index=False)[metrics].mean().rename(columns={m: f'avg_{m}' for m in metrics})

            daily_metrics_df = pd.merge(sum_df, avg_df, on='date', how='outer')
            daily_metrics_df = daily_metrics_df.sort_values('date').reset_index(drop=True)
            daily_metrics_df = daily_metrics_df.rename(columns={'date': 'timestamp'})

            # Weighted CI bands for each daily metric series (time-aware exponential weighting).
            for prefix in ['sum', 'avg']:
                for metric in metrics:
                    col = f'{prefix}_{metric}'
                    ts_input = daily_metrics_df[['timestamp', col]].dropna().copy()
                    if ts_input.empty:
                        continue
                    stats_daily = TimeSeriesStats(ts_input, None)
                    stats_df = stats_daily.compute_continuous_stats(col, window_days=2.0)
                    if stats_df.empty:
                        continue
                    stats_df = stats_df[['timestamp', 'mean', 'ci_lower', 'ci_upper']].rename(columns={
                        'mean': f'{col}_wmean',
                        'ci_lower': f'{col}_ci_lower',
                        'ci_upper': f'{col}_ci_upper',
                    })
                    daily_metrics_df = pd.merge(daily_metrics_df, stats_df, on='timestamp', how='left')
    
    def _build_plot_target_from_long(long_df: pd.DataFrame, group_col: str) -> pd.DataFrame:
        """Build the standard plot-target shape from long-format weighted stats."""
        plot_data: list[dict[str, object]] = []
        unique_groups = sorted(long_df[group_col].dropna().unique()) if not long_df.empty else []

        for group_value in unique_groups:
            for level in ['mean', 'ci_lower', 'ci_upper']:
                plot_row: dict[str, object] = {group_col: group_value, 'level_1': level}
                group_data = long_df[long_df[group_col] == group_value]
                for _, row in group_data.iterrows():
                    metric = row['metric']
                    plot_row[metric] = row[level]
                plot_data.append(plot_row)

        return pd.DataFrame(plot_data)

    # Group by tier for stats calculation
    # Previously we filtered to tiers with more than one run, which hid brand-new tiers (e.g., first Tier 12 run).
    # Use all available runs per tier so new tiers appear immediately; CI will degenerate to the single value.
    df_by_tier = filtered_df.copy()

    stats = TimeSeriesStats(df_by_tier, 'tier')
    # Compute statistics with new TimeSeriesStats
    wide_stats = stats.compute_latest_stats([
        'coins_earned', 'cells_earned', 'reroll_shards_earned', 'waves_per_tier', 'real_time',
        'coins_per_hour', 'cells_per_hour', 'reroll_shards_per_hour', 'waves_per_hour'
    ])
    
    # Reshape to long format and compute scores
    long_stats = stats.reshape_to_long_format(wide_stats)
    
    # Note: Clustering is now performed on-demand in optimizer.py via ClusterDetection.py
    # This filtered_df is stored for the optimizer to use
    # No longer performing clustering here to improve app startup performance
    
    # Keep only mean values for scoring
    # Create a DataFrame for plot data (all historical data)
    plot_target = _build_plot_target_from_long(long_stats, 'tier')
    unique_tiers = sorted(long_stats['tier'].unique()) if not long_stats.empty else []
    
    # Ensure all required columns exist in plot_target
    required_plot_cols = ['coins_earned', 'cells_earned', 'reroll_shards_earned', 'waves_per_tier', 'real_time',
                       'coins_per_hour', 'cells_per_hour', 'reroll_shards_per_hour', 'waves_per_hour', 'score', 'optimizer_score']
    for col in required_plot_cols:
        if col not in plot_target.columns:
            plot_target[col] = 0.0
    
    # Prepare data for scoring (need wide format with _mean suffix)
    # Compute statistics with new TimeSeriesStats (already done above)
    # wide_stats already has the correct format with columns like coins_earned_mean
    
    if DEBUG:
        logger.debug("=== DEBUG: Score Calculation ===")
        logger.debug("wide_stats head:\n%s", wide_stats.head())
        logger.debug("wide_stats columns: %s", wide_stats.columns.tolist())
    
    def compute_optimizer_score(stats_df: pd.DataFrame) -> pd.DataFrame:
        """Compute optimizer-specific score using max per-hour * 24 as denominator (earned metrics only)."""
        weights = {
            "coins_earned": 1 / 3,
            "cells_earned": 1 / 3,
            "reroll_shards_earned": 1 / 3
        }

        df = stats_df.copy()
        def _safe_float(val: object) -> float:
            try:
                num = float(cast(float, val))
                return 0.0 if np.isnan(num) else num
            except Exception:
                return 0.0

        max_coins_per_hour = _safe_float(df.get('coins_per_hour_mean', pd.Series([0.0])).max())
        max_cells_per_hour = _safe_float(df.get('cells_per_hour_mean', pd.Series([0.0])).max())
        max_shards_per_hour = _safe_float(df.get('reroll_shards_per_hour_mean', pd.Series([0.0])).max())

        denom_coins_earned = max_coins_per_hour * 24 if max_coins_per_hour else _safe_float(df.get('coins_earned_mean', pd.Series([0.0])).max())
        denom_cells_earned = max_cells_per_hour * 24 if max_cells_per_hour else _safe_float(df.get('cells_earned_mean', pd.Series([0.0])).max())
        denom_shards_earned = max_shards_per_hour * 24 if max_shards_per_hour else _safe_float(df.get('reroll_shards_earned_mean', pd.Series([0.0])).max())

        def safe_norm(series: pd.Series, denom: float) -> pd.Series:
            if denom and not pd.isna(denom) and denom != 0:
                return series / denom
            return pd.Series([0.0] * len(series), index=series.index)

        if 'coins_earned_mean' in df.columns:
            df['coins_earned_normalized'] = safe_norm(df['coins_earned_mean'], float(denom_coins_earned))
        if 'cells_earned_mean' in df.columns:
            df['cells_earned_normalized'] = safe_norm(df['cells_earned_mean'], float(denom_cells_earned))
        if 'reroll_shards_earned_mean' in df.columns:
            df['reroll_shards_earned_normalized'] = safe_norm(df['reroll_shards_earned_mean'], float(denom_shards_earned))

        df['optimizer_score'] = sum(
            df.get(f"{metric}_normalized", 0) * weight
            for metric, weight in weights.items()
        ) * 100

        return df

    # Compute scores for each confidence level separately
    # For mean values
    scored_stats_mean = stats.compute_score(wide_stats)
    optimizer_scored_mean = compute_optimizer_score(wide_stats)
    
    # For ci_lower values - create a DataFrame with ci_lower as "mean" for scoring
    ci_lower_df = wide_stats.copy()
    for metric in ['coins_earned', 'cells_earned', 'reroll_shards_earned', 'coins_per_hour', 'cells_per_hour', 'reroll_shards_per_hour']:
        if f'{metric}_ci_lower' in ci_lower_df.columns:
            ci_lower_df[f'{metric}_mean'] = ci_lower_df[f'{metric}_ci_lower']
    scored_stats_lower = stats.compute_score(ci_lower_df)
    optimizer_scored_lower = compute_optimizer_score(ci_lower_df)
    
    # For ci_upper values - create a DataFrame with ci_upper as "mean" for scoring
    ci_upper_df = wide_stats.copy()
    for metric in ['coins_earned', 'cells_earned', 'reroll_shards_earned', 'coins_per_hour', 'cells_per_hour', 'reroll_shards_per_hour']:
        if f'{metric}_ci_upper' in ci_upper_df.columns:
            ci_upper_df[f'{metric}_mean'] = ci_upper_df[f'{metric}_ci_upper']
    scored_stats_upper = stats.compute_score(ci_upper_df)
    optimizer_scored_upper = compute_optimizer_score(ci_upper_df)
    
    if DEBUG:
        logger.debug("Scored stats mean:\n%s", scored_stats_mean[['tier','score']])
        logger.debug("Scored stats ci_lower:\n%s", scored_stats_lower[['tier','score']])
        logger.debug("Scored stats ci_upper:\n%s", scored_stats_upper[['tier','score']])
        logger.debug("=== END DEBUG ===")
    
    # Add scores to plot_target - different score for each confidence level
    for tier in unique_tiers:
        if tier in scored_stats_mean['tier'].values:
            score_mean = scored_stats_mean[scored_stats_mean['tier'] == tier]['score'].iloc[0]
            score_lower = scored_stats_lower[scored_stats_lower['tier'] == tier]['score'].iloc[0]
            score_upper = scored_stats_upper[scored_stats_upper['tier'] == tier]['score'].iloc[0]

            optimizer_score_mean = optimizer_scored_mean[optimizer_scored_mean['tier'] == tier]['optimizer_score'].iloc[0]
            optimizer_score_lower = optimizer_scored_lower[optimizer_scored_lower['tier'] == tier]['optimizer_score'].iloc[0]
            optimizer_score_upper = optimizer_scored_upper[optimizer_scored_upper['tier'] == tier]['optimizer_score'].iloc[0]
            
            if DEBUG:
                logger.debug("Tier %s scores: mean=%.2f lower=%.2f upper=%.2f", tier, score_mean, score_lower, score_upper)
            
            # Add score based on level_1
            plot_target.loc[(plot_target['tier'] == tier) & (plot_target['level_1'] == 'mean'), 'score'] = score_mean
            plot_target.loc[(plot_target['tier'] == tier) & (plot_target['level_1'] == 'ci_lower'), 'score'] = score_lower
            plot_target.loc[(plot_target['tier'] == tier) & (plot_target['level_1'] == 'ci_upper'), 'score'] = score_upper

            plot_target.loc[(plot_target['tier'] == tier) & (plot_target['level_1'] == 'mean'), 'optimizer_score'] = optimizer_score_mean
            plot_target.loc[(plot_target['tier'] == tier) & (plot_target['level_1'] == 'ci_lower'), 'optimizer_score'] = optimizer_score_lower
            plot_target.loc[(plot_target['tier'] == tier) & (plot_target['level_1'] == 'ci_upper'), 'optimizer_score'] = optimizer_score_upper
    
    # Fill any remaining NaN values
    plot_target = plot_target.fillna(0.0)

    grouped_by_run_type_tier_df = pd.DataFrame()
    if not all_runs_time_series_df.empty:
        run_type_tier_df = all_runs_time_series_df.copy()
        run_type_tier_df['run_type'] = run_type_tier_df['run_type'].astype(str).str.lower()

        def _tier_base(value: object) -> str:
            try:
                return str(int(float(str(value).replace('+', '').strip())))
            except Exception:
                return str(value)

        run_type_tier_df['tier_base'] = run_type_tier_df['tier'].apply(_tier_base)
        run_type_tier_df['run_type_tier'] = run_type_tier_df['run_type'] + '|' + run_type_tier_df['tier_base']

        stats_by_run_type_tier = TimeSeriesStats(run_type_tier_df, 'run_type_tier')
        wide_stats_by_run_type_tier = stats_by_run_type_tier.compute_latest_stats([
            'coins_earned', 'cells_earned', 'reroll_shards_earned', 'waves_per_tier', 'real_time',
            'coins_per_hour', 'cells_per_hour', 'reroll_shards_per_hour', 'waves_per_hour'
        ])
        long_stats_by_run_type_tier = stats_by_run_type_tier.reshape_to_long_format(wide_stats_by_run_type_tier)
        grouped_by_run_type_tier_df = _build_plot_target_from_long(long_stats_by_run_type_tier, 'run_type_tier')

        if not grouped_by_run_type_tier_df.empty:
            grouped_by_run_type_tier_df[['run_type', 'tier_str']] = grouped_by_run_type_tier_df['run_type_tier'].str.split('|', n=1, expand=True)
            grouped_by_run_type_tier_df['tier'] = pd.to_numeric(grouped_by_run_type_tier_df['tier_str'], errors='coerce').fillna(0.0)
            grouped_by_run_type_tier_df = grouped_by_run_type_tier_df.drop(columns=['run_type_tier', 'tier_str'])

            for col in required_plot_cols:
                if col not in grouped_by_run_type_tier_df.columns:
                    grouped_by_run_type_tier_df[col] = 0.0

            scored_stats_by_run_type_tier = stats_by_run_type_tier.compute_score(wide_stats_by_run_type_tier)
            optimizer_scored_by_run_type_tier = compute_optimizer_score(wide_stats_by_run_type_tier)
            ci_lower_by_run_type_tier = wide_stats_by_run_type_tier.copy()
            ci_upper_by_run_type_tier = wide_stats_by_run_type_tier.copy()
            for metric in ['coins_earned', 'cells_earned', 'reroll_shards_earned', 'coins_per_hour', 'cells_per_hour', 'reroll_shards_per_hour']:
                if f'{metric}_ci_lower' in ci_lower_by_run_type_tier.columns:
                    ci_lower_by_run_type_tier[f'{metric}_mean'] = ci_lower_by_run_type_tier[f'{metric}_ci_lower']
                if f'{metric}_ci_upper' in ci_upper_by_run_type_tier.columns:
                    ci_upper_by_run_type_tier[f'{metric}_mean'] = ci_upper_by_run_type_tier[f'{metric}_ci_upper']

            scored_lower_by_run_type_tier = stats_by_run_type_tier.compute_score(ci_lower_by_run_type_tier)
            scored_upper_by_run_type_tier = stats_by_run_type_tier.compute_score(ci_upper_by_run_type_tier)
            optimizer_lower_by_run_type_tier = compute_optimizer_score(ci_lower_by_run_type_tier)
            optimizer_upper_by_run_type_tier = compute_optimizer_score(ci_upper_by_run_type_tier)

            unique_run_groups = sorted(wide_stats_by_run_type_tier['run_type_tier'].unique()) if not wide_stats_by_run_type_tier.empty else []
            for run_group in unique_run_groups:
                if run_group in scored_stats_by_run_type_tier['run_type_tier'].values:
                    score_mean = scored_stats_by_run_type_tier[scored_stats_by_run_type_tier['run_type_tier'] == run_group]['score'].iloc[0]
                    score_lower = scored_lower_by_run_type_tier[scored_lower_by_run_type_tier['run_type_tier'] == run_group]['score'].iloc[0]
                    score_upper = scored_upper_by_run_type_tier[scored_upper_by_run_type_tier['run_type_tier'] == run_group]['score'].iloc[0]
                    optimizer_score_mean = optimizer_scored_by_run_type_tier[optimizer_scored_by_run_type_tier['run_type_tier'] == run_group]['optimizer_score'].iloc[0]
                    optimizer_score_lower = optimizer_lower_by_run_type_tier[optimizer_lower_by_run_type_tier['run_type_tier'] == run_group]['optimizer_score'].iloc[0]
                    optimizer_score_upper = optimizer_upper_by_run_type_tier[optimizer_upper_by_run_type_tier['run_type_tier'] == run_group]['optimizer_score'].iloc[0]

                    grouped_by_run_type_tier_df.loc[(grouped_by_run_type_tier_df['run_type'] + '|' + grouped_by_run_type_tier_df['tier'].astype(int).astype(str) == run_group) & (grouped_by_run_type_tier_df['level_1'] == 'mean'), 'score'] = score_mean
                    grouped_by_run_type_tier_df.loc[(grouped_by_run_type_tier_df['run_type'] + '|' + grouped_by_run_type_tier_df['tier'].astype(int).astype(str) == run_group) & (grouped_by_run_type_tier_df['level_1'] == 'ci_lower'), 'score'] = score_lower
                    grouped_by_run_type_tier_df.loc[(grouped_by_run_type_tier_df['run_type'] + '|' + grouped_by_run_type_tier_df['tier'].astype(int).astype(str) == run_group) & (grouped_by_run_type_tier_df['level_1'] == 'ci_upper'), 'score'] = score_upper
                    grouped_by_run_type_tier_df.loc[(grouped_by_run_type_tier_df['run_type'] + '|' + grouped_by_run_type_tier_df['tier'].astype(int).astype(str) == run_group) & (grouped_by_run_type_tier_df['level_1'] == 'mean'), 'optimizer_score'] = optimizer_score_mean
                    grouped_by_run_type_tier_df.loc[(grouped_by_run_type_tier_df['run_type'] + '|' + grouped_by_run_type_tier_df['tier'].astype(int).astype(str) == run_group) & (grouped_by_run_type_tier_df['level_1'] == 'ci_lower'), 'optimizer_score'] = optimizer_score_lower
                    grouped_by_run_type_tier_df.loc[(grouped_by_run_type_tier_df['run_type'] + '|' + grouped_by_run_type_tier_df['tier'].astype(int).astype(str) == run_group) & (grouped_by_run_type_tier_df['level_1'] == 'ci_upper'), 'optimizer_score'] = optimizer_score_upper

            grouped_by_run_type_tier_df = grouped_by_run_type_tier_df.fillna(0.0)
    
    filter_3_days = pd.Timestamp.now(tz='UTC') - pd.Timedelta(days=3)
    three_days_df = filtered_df[filtered_df['timestamp'] >= filter_3_days]

    # Compute 3-day statistics
    stats_3_days = TimeSeriesStats(three_days_df, 'tier')
    wide_stats_3_days = stats_3_days.compute_latest_stats([
        'coins_earned', 'cells_earned', 'reroll_shards_earned', 'real_time',
        'coins_per_hour', 'cells_per_hour', 'reroll_shards_per_hour'
    ])
    
    # Debug: Check if wide_stats has data
    if DEBUG:
        logger.debug("cleanupJSON 3-days shape: %s", wide_stats_3_days.shape)
        logger.debug("cleanupJSON 3-days columns: %s", wide_stats_3_days.columns.tolist())
        if wide_stats_3_days.empty:
            logger.debug("wide_stats_3_days is empty - no data in last 3 days")
    
    long_stats_3_days = stats_3_days.reshape_to_long_format(wide_stats_3_days)
    
    # Process for scoring
    means_df_3_days = long_stats_3_days.copy()
    means_df_3_days = means_df_3_days.rename(columns={'mean': 'value'})
    means_df_3_days['metric'] = means_df_3_days['metric'].str.replace('_mean', '')
    scored_stats_3_days = stats_3_days.compute_score(means_df_3_days)

    return {
        'grouped_by_tier_df': plot_target,
        'grouped_by_run_type_tier_df': grouped_by_run_type_tier_df,
        'filtered_df': filtered_df,  # Store filtered data for on-demand clustering in optimizer
        'time_series_df': time_series_df,  # Full time series data (farming/overnight only)
        'all_runs_time_series_df': all_runs_time_series_df,  # Time series including tournament, quit, milestone
        'max_income_baseline_df': max_income_baseline_df,  # Max per-hour and per-day baselines
        'daily_metrics_df': daily_metrics_df,  # Daily sums/means with weighted CIs
        'bot_daily_df': bot_daily_df  # Bot supporter data aggregated by day
        }

#cleanedJSON=cleanupJSON(ParsedJSON)
#print("Prepared JSON:")
#print(cleanedJSON)
#pprint.pprint(df.columns.tolist)


def ToDo_Lists(path: str):    
    

    return None

if __name__ == "__main__":
    df_all=Import_JSON_record('C:\\Users\\thors\\AppData\\Roaming\\rendapp\\userData.json','gameStats')
    cleaned_data=cleanupJSON(df_all)
    if DEBUG:
        print(type(cleaned_data))
        print_df=cleaned_data['last_three_days_df']    
        print(print_df.keys())
    
    
def load_full_json(path: str) -> Dict[str, Any]:
    """Load the entire user JSON (not only gameStats) as a Python dict.
    Falls back to empty dict on error.
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        if DEBUG:
            print(f"Failed to load full JSON from {path}: {e}")
        return {}


def _get_case_insensitive(d: Dict[str, Any], key: str) -> Optional[Any]:
    for k, v in d.items():
        if k.lower() == key.lower():
            return v
    return None


def _scan_json_for_targets_and_costs(obj: Any, path: str = "") -> Dict[str, List[Dict[str, Any]]]:
    """Recursively scan JSON for structures containing target/actual and cost-like fields.

    Returns a dict with lists for 'todos' and 'costs'. Each element is a flat dict
    including a 'path' key showing where it was found.
    """
    found = {"todos": [], "costs": []}

    def _merge(a: Dict[str, List[Dict[str, Any]]], b: Dict[str, List[Dict[str, Any]]]) -> None:
        a["todos"].extend(b.get("todos", []))
        a["costs"].extend(b.get("costs", []))

    if isinstance(obj, dict):
        keys_lower = {k.lower() for k in obj.keys()}

        # Detect todo-like with target/actual (or current/value) pairs
        if ("target" in keys_lower) and ("actual" in keys_lower or "current" in keys_lower or "value" in keys_lower):
            target_val = _get_case_insensitive(obj, "target")
            actual_val = _get_case_insensitive(obj, "actual")
            if actual_val is None:
                actual_val = _get_case_insensitive(obj, "current")
            if actual_val is None:
                actual_val = _get_case_insensitive(obj, "value")
            name = _get_case_insensitive(obj, "name") or _get_case_insensitive(obj, "id") or path.split("/")[-1]
            unit = _get_case_insensitive(obj, "unit") or _get_case_insensitive(obj, "units")
            try:
                target_f = float(target_val) if target_val is not None else None
                actual_f = float(actual_val) if actual_val is not None else None
            except Exception:
                # Skip non-numeric pairs
                target_f, actual_f = None, None
            found["todos"].append({
                "path": path or "/",
                "name": name,
                "target": target_val,
                "actual": actual_val,
                "target_num": target_f,
                "actual_num": actual_f,
                "remaining": (target_f - actual_f) if (target_f is not None and actual_f is not None) else None,
                "pct": (actual_f / target_f * 100.0) if (target_f not in (None, 0) and actual_f is not None) else None,
                "unit": unit,
            })

        # Detect cost-like entries
        for k, v in obj.items():
            if re.search(r"cost|price|upgrade_cost|costs|prices", k, flags=re.IGNORECASE):
                # If dict (e.g., {"coins": 1000, "cells": 50}) flatten to rows
                if isinstance(v, dict):
                    for ck, cv in v.items():
                        try:
                            cv_num = float(cv) if cv is not None else None
                        except Exception:
                            cv_num = None
                        found["costs"].append({
                            "path": f"{path}/{k}" if path else k,
                            "name": _get_case_insensitive(obj, "name") or _get_case_insensitive(obj, "id") or path.split("/")[-1],
                            "cost_key": ck,
                            "amount": cv,
                            "amount_num": cv_num,
                        })
                else:
                    try:
                        v_num = float(v) if v is not None else None
                    except Exception:
                        v_num = None
                    found["costs"].append({
                        "path": f"{path}/{k}" if path else k,
                        "name": _get_case_insensitive(obj, "name") or _get_case_insensitive(obj, "id") or path.split("/")[-1],
                        "cost_key": k,
                        "amount": v,
                        "amount_num": v_num,
                    })

        # Recurse
        for k, v in obj.items():
            sub = _scan_json_for_targets_and_costs(v, f"{path}/{k}" if path else str(k))
            _merge(found, sub)

    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            sub = _scan_json_for_targets_and_costs(v, f"{path}/{i}" if path else str(i))
            found["todos"].extend(sub.get("todos", []))
            found["costs"].extend(sub.get("costs", []))

    return found


def analyze_full_json_file(path: str) -> Dict[str, pd.DataFrame]:
    """Analyze the full user JSON for target/actual pairs and costs.

    Returns DataFrames:
    - todo_items_df: path, name, target, actual, remaining, pct, unit
    - costs_df: path, name, cost_key, amount
    - sections_df: top-level keys with type and size
    - raw_keys_df: flattened unique keys for quick exploration
    """
    data = load_full_json(path)
    if not data:
        return {
            "todo_items_df": pd.DataFrame(),
            "costs_df": pd.DataFrame(),
            "sections_df": pd.DataFrame(),
            "raw_keys_df": pd.DataFrame(),
        }

    # Build sections overview
    rows = []
    for k, v in data.items() if isinstance(data, dict) else []:
        t = type(v).__name__
        size = len(v) if hasattr(v, "__len__") else 1
        rows.append({"top_key": k, "type": t, "size": size})
    sections_df = pd.DataFrame(rows)

    # Recursively scan for todo-like and costs
    scanned = _scan_json_for_targets_and_costs(data, "")
    todo_items_df = pd.DataFrame(scanned.get("todos", []))
    costs_df = pd.DataFrame(scanned.get("costs", []))

    # Flatten unique key paths for quick exploration
    key_paths = set()

    def _collect_paths(o: Any, p: str = ""):
        if isinstance(o, dict):
            for kk, vv in o.items():
                npth = f"{p}/{kk}" if p else kk
                key_paths.add(npth)
                _collect_paths(vv, npth)
        elif isinstance(o, list):
            for i, vv in enumerate(o):
                npth = f"{p}/{i}" if p else str(i)
                key_paths.add(npth)
                _collect_paths(vv, npth)

    _collect_paths(data, "")
    raw_keys_df = pd.DataFrame({"path": sorted(key_paths)})

    # Post-process: sort and compute simple ranks
    if not todo_items_df.empty:
        todo_items_df = todo_items_df.sort_values(by=["remaining", "pct"], ascending=[True, False], na_position='last')
    if not costs_df.empty:
        costs_df = costs_df.sort_values(by=["amount_num"], ascending=False, na_position='last')

    return {
        "todo_items_df": todo_items_df,
        "costs_df": costs_df,
        "sections_df": sections_df,
        "raw_keys_df": raw_keys_df,
    }


def save_json_analysis_to_assets(path: str, out_dir: Optional[str] = None) -> Dict[str, str]:
    """Run analysis and save CSVs into assets/analysis (or given out_dir). Returns map of artifact names to paths."""
    import os
    from pathlib import Path

    results = analyze_full_json_file(path)
    if out_dir is None:
        out_dir = str(Path(__file__).resolve().parent.parent / 'assets' / 'analysis')
    Path(out_dir).mkdir(parents=True, exist_ok=True)

    artifacts: Dict[str, str] = {}
    for name, df in results.items():
        if isinstance(df, pd.DataFrame):
            fp = Path(out_dir) / f"{name}.csv"
            df.to_csv(fp, index=False)
            artifacts[name] = str(fp)
    return artifacts


def extract_workshop_todos(json_data: Dict[str, Any]) -> pd.DataFrame:
    """Extract workshop upgrade todos from workshopData section.
    
    Returns DataFrame with columns:
    - category (attack/defense/utility/bots/ultimateWeapons)
    - index (item index within category)
    - name (item name)
    - level (current level)
    - targetLevel (target level, or targetLevels for bots/ultimateWeapons)
    - remaining_levels (targetLevel - level, only if level < targetLevel)
    - is_todo (True if level < targetLevel)
    """
    workshop_data = json_data.get('workshopData', {})
    if not isinstance(workshop_data, dict):
        return pd.DataFrame()
    
    rows = []

    def _coerce_target_level(val: Any) -> Optional[int]:
        """Coerce a target level that may be scalar, string, list or dict to an int.
        Rules:
        - int/float/str -> int if possible
        - list/tuple -> max integer value found
        - dict -> try common keys ('max','target','level'), else max of numeric values
        """
        if val is None:
            return None
        # Direct scalar
        if isinstance(val, (int,)):
            return int(val)
        if isinstance(val, float):
            try:
                return int(val)
            except Exception:
                return None
        if isinstance(val, str):
            try:
                return int(val)
            except Exception:
                try:
                    return int(float(val))
                except Exception:
                    return None
        # List/tuple -> take max of numeric entries
        if isinstance(val, (list, tuple)):
            nums: List[int] = []
            for x in val:
                try:
                    nums.append(int(x))
                except Exception:
                    try:
                        nums.append(int(float(x)))
                    except Exception:
                        continue
            return max(nums) if nums else None
        # Dict -> try common keys, else numeric values
        if isinstance(val, dict):
            for key in ('max', 'target', 'level'):
                if key in val:
                    try:
                        return int(val[key])
                    except Exception:
                        try:
                            return int(float(val[key]))
                        except Exception:
                            pass
            nums: List[int] = []
            for v in val.values():
                try:
                    nums.append(int(v))
                except Exception:
                    try:
                        nums.append(int(float(v)))
                    except Exception:
                        continue
            return max(nums) if nums else None
        return None
    for category, items in workshop_data.items():
        if not isinstance(items, dict):
            continue
        
        for idx_str, item in items.items():
            if not isinstance(item, dict):
                continue
            
            name = item.get('name', f"{category}_{idx_str}")
            level = item.get('level')
            target_level = item.get('targetLevel')
            target_levels = item.get('targetLevels')  # Some categories use plural form

            # Handle both targetLevel and targetLevels, with coercion
            if target_level is None and target_levels is not None:
                target_level = _coerce_target_level(target_levels)
            
            # Convert to numeric
            try:
                level_num = int(level) if level is not None else None
            except (ValueError, TypeError):
                level_num = None
            # target may have been coerced above; coerce again if needed
            target_num = _coerce_target_level(target_level) if target_level is not None else None
            
            # Only include if targetLevel exists and level < targetLevel
            is_todo = False
            remaining = None
            if target_num is not None:
                if level_num is None:
                    # Missing level means not started, so it's a todo
                    is_todo = True
                    remaining = target_num
                elif level_num < target_num:
                    is_todo = True
                    remaining = target_num - level_num
            
            # Always add row for reference, mark todos
            rows.append({
                'category': category,
                'index': idx_str,
                'name': name,
                'level': level_num,
                'targetLevel': target_num,
                'remaining_levels': remaining,
                'is_todo': is_todo,
            })
    
    df = pd.DataFrame(rows)
    if not df.empty:
        # Sort by todos first, then by remaining levels descending (prioritize closer to completion)
        df = df.sort_values(by=['is_todo', 'remaining_levels'], ascending=[False, True], na_position='last')
    
    return df


def extract_labs_todos(json_data: Dict[str, Any]) -> pd.DataFrame:
    """Extract labs upgrade todos from labsProgress section.
    
    Returns DataFrame with columns:
    - lab_id (index within labs array)
    - name (lab name)
    - level (current level)
    - targetLevel (target level)
    - remaining_levels (targetLevel - level, only if level < targetLevel)
    - is_todo (True if level < targetLevel)
    """
    labs_progress = json_data.get('labsProgress', {})
    if not isinstance(labs_progress, dict):
        return pd.DataFrame()
    
    labs = labs_progress.get('labs', {})
    if not isinstance(labs, dict):
        return pd.DataFrame()
    
    rows = []
    for lab_id_str, lab in labs.items():
        if not isinstance(lab, dict):
            continue
        
        name = lab.get('name', f"Lab_{lab_id_str}")
        level = lab.get('level')
        target_level = lab.get('targetLevel')
        
        # Convert to numeric
        try:
            level_num = int(level) if level is not None else None
            target_num = int(target_level) if target_level is not None else None
        except (ValueError, TypeError):
            level_num = None
            target_num = None
        
        # Only include if targetLevel exists and level < targetLevel
        is_todo = False
        remaining = None
        if target_num is not None:
            if level_num is None:
                # Missing level means not started, so it's a todo
                is_todo = True
                remaining = target_num
            elif level_num < target_num:
                is_todo = True
                remaining = target_num - level_num
        
        # Always add row for reference, mark todos
        rows.append({
            'lab_id': lab_id_str,
            'name': name,
            'level': level_num,
            'targetLevel': target_num,
            'remaining_levels': remaining,
            'is_todo': is_todo,
        })
    
    df = pd.DataFrame(rows)
    if not df.empty:
        # Sort by todos first, then by remaining levels ascending (prioritize closer to completion)
        df = df.sort_values(by=['is_todo', 'remaining_levels'], ascending=[False, True], na_position='last')
    
    return df


def load_todos_and_costs(path: str) -> Dict[str, pd.DataFrame]:
    """Load workshop and labs todos from JSON file.
    
    Returns dict with:
    - workshop_todos_df: Workshop upgrade todos
    - labs_todos_df: Labs upgrade todos
    - workshop_all_df: All workshop items (with is_todo flag)
    - labs_all_df: All labs items (with is_todo flag)
    """
    json_data = load_full_json(path)
    if not json_data:
        return {
            'workshop_todos_df': pd.DataFrame(),
            'labs_todos_df': pd.DataFrame(),
            'workshop_all_df': pd.DataFrame(),
            'labs_all_df': pd.DataFrame(),
        }
    
    workshop_all = extract_workshop_todos(json_data)
    labs_all = extract_labs_todos(json_data)
    
    # Filter to only todos
    workshop_todos = workshop_all[workshop_all['is_todo'] == True].copy() if not workshop_all.empty else pd.DataFrame()
    labs_todos = labs_all[labs_all['is_todo'] == True].copy() if not labs_all.empty else pd.DataFrame()
    
    return {
        'workshop_todos_df': workshop_todos,
        'labs_todos_df': labs_todos,
        'workshop_all_df': workshop_all,
        'labs_all_df': labs_all,
    }


def extract_relics_data(json_data: Dict[str, Any]) -> Dict[str, float]:
    """Extract relic bonuses from relicsData section.
    
    Returns:
        Dict with bonus names as keys and values as floats.
        Keys of interest:
        - Bot Range Bonus
        - Free Attack Upgrade Bonus
        - Free Defense Upgrade Bonus
        - Free Utility Upgrade Bonus
    """
    relics_data = json_data.get('relicsData', {})
    bonuses_list = relics_data.get('bonuses', [])
    
    # Convert list of {name, value} to dict
    bonuses = {}
    for bonus in bonuses_list:
        if isinstance(bonus, dict) and 'name' in bonus and 'value' in bonus:
            bonuses[bonus['name']] = float(bonus['value'])
    
    return bonuses


   

