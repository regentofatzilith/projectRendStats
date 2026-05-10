"""
Ultimate Weapons Overview Page - Detailed breakdown of all UW stats.

Redesigned for:
- One weapon per row (full width)
- One block per effect/parameter
- Config-based colors from UW_PERMA_CONFIG
- Uses userData.json via DataManager
- Dynamically pulls lookup table structure from config.py

Features:
- Shows all parameters from lookup tables
- Displays which sources (Levels, Labs, Modules, Submodules, Relics) are available
- Categorizes Ultimate Weapons, Bots, and Guardian Chips
"""

import dash
from dash import html
import dash_bootstrap_components as dbc
from typing import Any, List, Dict, Optional, Tuple

from functions.data import DataManager, config
from functions.computation import get_weapon_cards

dash.register_page(
    __name__,
    path="/uw-overview",
    name="UW Overview",
    order=9,
)

_cards_cache_key: Optional[tuple] = None
_cards_cache_data: Optional[Dict[str, Dict[str, Any]]] = None


def _get_weapon_cards_cached() -> Dict[str, Dict[str, Any]]:
    """Return cached weapon cards, invalidating on data source change."""
    global _cards_cache_key, _cards_cache_data
    
    dm = DataManager.get_instance()
    load_info = dm.get_load_info()
    cache_key = (load_info.get("json_path"), load_info.get("load_timestamp"))
    
    if _cards_cache_data is not None and _cards_cache_key == cache_key:
        return _cards_cache_data
    
    all_weapons = dm.get_all_weapons(detailed=True)
    _cards_cache_data = get_weapon_cards(all_weapons) if all_weapons else {}
    _cards_cache_key = cache_key
    return _cards_cache_data


def _get_weapon_color(weapon_name: str) -> str:
    """Get color hex from config for weapon."""
    config_entry = config.UW_PERMA_CONFIG.get(weapon_name, {})
    return config_entry.get("color_hex", "#0d6efd")


def _build_category_lookup_from_datastore() -> Dict[str, str]:
    """Best-effort category lookup from raw datastore JSON.

    Looks for objects with both `name` and `category` keys.
    """
    out: Dict[str, str] = {}
    try:
        dm = DataManager.get_instance()
        json_data = dm.get_json_data()
    except Exception:
        return out

    def _walk(node: Any) -> None:
        if isinstance(node, dict):
            name = node.get("name")
            category = node.get("category")
            if isinstance(name, str) and isinstance(category, str):
                out[name] = category
            for v in node.values():
                _walk(v)
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    _walk(json_data)
    return out


def _get_all_lookups_from_config() -> Dict[str, Dict[str, Dict[str, Any]]]:
    """Extract all entity lookups from the LOOKUP_TABLE_REGISTRY in config.py.
    
    Returns:
        Dict structure from config.LOOKUP_TABLE_REGISTRY:
        {
            "Ultimate Weapons": {
                "Golden Tower": {"lut": {...}, "sources_map": {...}},
                ...
            },
            "Bots": {...},
            "Guardians": {...}
        }
    """
    if hasattr(config, 'LOOKUP_TABLE_REGISTRY'):
        return config.LOOKUP_TABLE_REGISTRY
    return {}


def _analyze_lookup_structure(entity_lookups: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze a single entity's lookup structure to extract parameters and sources.
    
    Args:
        entity_lookups: Full nested structure: {"Levels": {...}, "Labs": {...}, ...}
    
    Returns:
        Dict with keys "parameters", "has_labs", "has_modules", etc.:
        {
            "parameters": ["Duration", "Cooldown", ...],
            "has_levels": True,
            "has_labs": bool,
            "has_modules": bool,
            "has_submodules": bool,
            "has_relics": bool,
            "levels": {param: max_level},
            "labs_params": set,
            "modules_params": set,
            "relics_params": set,
        }
    """
    levels_data = entity_lookups.get("Levels", {})
    labs_data = entity_lookups.get("Labs", {})
    modules_data = entity_lookups.get("Modules", {})
    submodules_data = entity_lookups.get("Submodules", {})
    relics_data = entity_lookups.get("Relics", {})
    
    # Extract parameters from Levels
    parameters = list(levels_data.keys()) if levels_data else []
    
    # Find max levels for each parameter
    levels_info = {}
    if levels_data:
        for param, level_dict in levels_data.items():
            if isinstance(level_dict, dict):
                max_level = max(level_dict.keys()) if level_dict else 0
                levels_info[param] = max_level
    
    return {
        "parameters": sorted(parameters),
        "has_levels": bool(levels_data),
        "has_labs": bool(labs_data),
        "has_modules": bool(modules_data),
        "has_submodules": bool(submodules_data),
        "has_relics": bool(relics_data),
        "levels": levels_info,
        "labs_params": set(labs_data.keys()) if labs_data else set(),
        "modules_params": set(modules_data.keys()) if modules_data else set(),
        "submodules_params": set(submodules_data.keys()) if submodules_data else set(),
        "relics_params": set(relics_data.keys()) if relics_data else set(),
    }


def _render_source_availability(param_name: str, analysis: Dict[str, Any]) -> html.Span:
    """Render a visual indicator of which sources have data for a parameter.
    
    Shows colored badges for each source type available.
    """
    sources = []
    
    if param_name in analysis["labs_params"]:
        sources.append(html.Span("Labs", className="badge bg-success me-1", style={"fontSize": "0.75rem"}))
    
    if param_name in analysis["modules_params"]:
        sources.append(html.Span("Modules", className="badge bg-info me-1", style={"fontSize": "0.75rem"}))
    
    if param_name in analysis["submodules_params"]:
        sources.append(html.Span("Submodules", className="badge bg-warning me-1", style={"fontSize": "0.75rem"}))
    
    if param_name in analysis["relics_params"]:
        sources.append(html.Span("Relics", className="badge bg-danger me-1", style={"fontSize": "0.75rem"}))
    
    return html.Span(sources if sources else html.Span("Levels only", style={"fontSize": "0.75rem", "color": "#9ca3af"}))


def _render_lookup_table_view() -> Any:
    """Render an overview of all lookup tables with parameters and available sources."""
    try:
        all_lookups = _get_all_lookups_from_config()
        if not all_lookups:
            return dbc.Alert("No lookup tables found in config", color="warning")
        
        section_order = ["Ultimate Weapons", "Bots", "Guardians"]
        content_blocks: List[Any] = []
        
        for section_name in section_order:
            if section_name not in all_lookups:
                continue
            
            entities = all_lookups[section_name]
            content_blocks.append(html.H3(section_name, className="mt-4 mb-3"))
            
            # Create a table for this section
            rows = []
            for entity_name in sorted(entities.keys()):
                entity_registry = entities[entity_name]
                entity_data = entity_registry["lut"]
                analysis = _analyze_lookup_structure(entity_data)
                
                # Get color for entity
                color = _get_weapon_color(entity_name)
                
                # Build row with entity info
                param_list = analysis["parameters"]
                
                if not param_list:
                    rows.append(dbc.Row([
                        dbc.Col(html.Div(
                            f"{entity_name}: No parameters found",
                            style={"color": "#9ca3af", "fontSize": "0.9rem"}
                        ), width=12)
                    ], className="mb-2"))
                    continue
                
                # Create parameter list with source badges
                param_rows = []
                for param_name in param_list:
                    max_level = analysis["levels"].get(param_name, 0)
                    source_indicator = _render_source_availability(param_name, analysis)
                    
                    param_rows.append(
                        dbc.Row([
                            dbc.Col(html.Span(param_name, style={"fontSize": "0.9rem", "color": "#e2e8f0"}), width=4),
                            dbc.Col(html.Span(f"Lvl 0-{max_level}", style={"fontSize": "0.85rem", "color": "#a0aec0"}), width=2),
                            dbc.Col(source_indicator, width=6),
                        ], className="mb-2", style={"fontSize": "0.85rem"})
                    )
                
                # Wrap in card
                row = dbc.Row([
                    dbc.Col([
                        dbc.Card(
                            dbc.CardBody([
                                html.H5(
                                    entity_name,
                                    className="card-title mb-3",
                                    style={"color": color}
                                ),
                                html.Div(
                                    param_rows,
                                    style={
                                        "maxHeight": "400px",
                                        "overflowY": "auto",
                                        "paddingRight": "8px"
                                    }
                                ),
                                html.Div(
                                    html.Small(
                                        f"{len(param_list)} parameters | "
                                        f"{'Labs: ✓' if analysis['has_labs'] else ''} "
                                        f"{'Modules: ✓' if analysis['has_modules'] else ''} "
                                        f"{'Relics: ✓' if analysis['has_relics'] else ''}"
                                    ),
                                    style={"color": "#718096", "marginTop": "12px", "fontSize": "0.8rem"}
                                ),
                            ]),
                            className="shadow-sm",
                            style={
                                "borderLeft": f"6px solid {color}",
                                "borderRadius": "0.375rem"
                            }
                        ),
                    ], width=12, className="mb-3"),
                ])
                rows.append(row)
            
            content_blocks.extend(rows)
        
        return html.Div(content_blocks, className="mb-4")
        
    except Exception:
        import traceback
        return dbc.Alert([
            html.H5("Error rendering lookup table view"),
            html.Pre(traceback.format_exc()),
        ], color="danger")





def _get_entity_section_from_registry(entity_name: str) -> Optional[str]:
    """Look up which section an entity belongs to using LOOKUP_TABLE_REGISTRY.
    
    Returns the section name ("Ultimate Weapons", "Bots", "Guardians") or None if not found.
    """
    if not hasattr(config, 'LOOKUP_TABLE_REGISTRY'):
        return None
    
    registry = config.LOOKUP_TABLE_REGISTRY
    for section_name, entities in registry.items():
        if entity_name in entities:
            return section_name
    
    return None


def _classify_weapon_section(weapon_name: str, datastore_categories: Dict[str, str]) -> str:
    """Classify weapon into one of: Ultimate Weapons, Guardians, Bots.
    
    First tries LOOKUP_TABLE_REGISTRY, then falls back to datastore inference if not found.
    """
    # Primary: Check LOOKUP_TABLE_REGISTRY
    section = _get_entity_section_from_registry(weapon_name)
    if section:
        return section
    
    # Fallback: Infer from datastore categories
    category_raw = str(datastore_categories.get(weapon_name, "") or "").lower()
    if "bot" in category_raw:
        return "Bots"
    if "guardian" in category_raw:
        return "Guardians"
    if "ultimate" in category_raw:
        return "Ultimate Weapons"

    # Final fallback: Name-based inference
    name_lower = weapon_name.lower()
    if "chip" in name_lower:
        return "Guardians"
    if "bot" in name_lower:
        return "Bots"
    if "guardian" in name_lower:
        return "Guardians"
    return "Ultimate Weapons"


_COL_STYLE_BASE = {
    "overflow": "hidden",
    "textOverflow": "ellipsis",
    "whiteSpace": "nowrap",
    "paddingRight": "12px",
}

_COL_WIDTHS = {
    "total":   "80px",
    "type":    "260px",
    "Levels":  "180px",
    "labs":    "160px",
    "modules": "100px",
    "relic":   "100px",
}

def _col(content: str, key: str, extra_style: Optional[Dict[str, Any]] = None) -> html.Span:
    style = {**_COL_STYLE_BASE, "minWidth": _COL_WIDTHS[key], **(extra_style or {})}
    return html.Span(content, style=style)


def _render_table_header(weapon_color: str) -> html.Div:
    """Single shared header row for the parameter table."""
    header_style: Dict[str, Any] = {"color": "#718096", "fontSize": "0.78rem", "fontWeight": "600",
                                     "textTransform": "uppercase", "letterSpacing": "0.05em"}
    return html.Div([
        _col("Total",   "total",   header_style),
        _col("Type",    "type",    header_style),
        _col("Levels",  "Levels",  header_style),
        _col("Labs",    "labs",    header_style),
        _col("Modules", "modules", header_style),
        _col("Relic",   "relic",   header_style),
    ], className="d-flex align-items-center mb-1 pb-1",
       style={"borderBottom": f"1px solid {weapon_color}33", "fontSize": "0.78rem"})


def _render_effect_block(param_name: str, param_data: Dict[str, Any], weapon_color: str) -> html.Div:
    """Render one parameter as a table row."""
    total_value = param_data.get("total_display", "—")
    levels_val = param_data.get("levels_display", "—")
    lab_val    = param_data.get("labs_display",  "—")
    module_val = param_data.get("module_display","—")
    relic_val  = param_data.get("relic_display", "—")
    labs_supported = bool(param_data.get("labs_supported", False))
    module_supported = bool(param_data.get("module_supported", False))
    relic_supported = bool(param_data.get("relic_supported", False))

    labs_style = {"color": "#68d391" if labs_supported else "#718096"}
    module_style = {"color": "#f6ad55" if module_supported else "#718096"}
    relic_style = {"color": "#76e4f7" if relic_supported else "#718096"}

    return html.Div([
        _col(total_value, "total",   {"color": weapon_color, "fontWeight": "600"}),
        _col(param_name,  "type",    {"color": "#a0aec0"}),
        _col(levels_val,  "Levels",  {"color": "#e2e8f0"}),
        _col(lab_val,     "labs",    labs_style),
        _col(module_val,  "modules", module_style),
        _col(relic_val,   "relic",   relic_style),
    ], className="d-flex align-items-center mb-1", style={"fontSize": "0.92rem"})


def _render_uw_overview_content() -> Any:
    """Generate UW overview with one weapon per row, one block per effect."""
    try:
        dm = DataManager.get_instance()
        weapon_cards = _get_weapon_cards_cached()
        if not weapon_cards:
            return dbc.Alert("No weapons to display", color="info")

        entry_catalog = config.get_data_view_entry_catalog()

        catalog_sections: Dict[str, str] = {}
        catalog_entries_by_entity: Dict[str, List[str]] = {}
        for section_name, entities in entry_catalog.items():
            for entity_name, info in entities.items():
                catalog_sections[entity_name] = section_name
                entries = info.get("entries", [])
                catalog_entries_by_entity[entity_name] = [str(e) for e in entries] if isinstance(entries, list) else []

        datastore_categories = _build_category_lookup_from_datastore()
        section_order = ["Ultimate Weapons", "Guardians", "Bots"]
        section_rows: Dict[str, List[dbc.Row]] = {k: [] for k in section_order}

        entity_order: List[str] = []
        for section_name in section_order:
            entity_order.extend(sorted(entry_catalog.get(section_name, {}).keys()))

        for weapon_name in entity_order:
            card_data = weapon_cards.get(weapon_name, {"parameters": []})
            weapon_color = _get_weapon_color(weapon_name)
            parameters = card_data.get("parameters", [])

            # Reorder and complete rows using config-driven entry catalog.
            parameters_by_name: Dict[str, Dict[str, Any]] = {}
            for p in parameters:
                if isinstance(p, dict):
                    name = str(p.get("name", "Parameter"))
                    parameters_by_name[name] = p

            expected_entries = catalog_entries_by_entity.get(weapon_name, [])
            if expected_entries:
                ordered_parameters: List[Dict[str, Any]] = []
                for entry_name in expected_entries:
                    if entry_name in parameters_by_name:
                        ordered_parameters.append(parameters_by_name[entry_name])
                    else:
                        ordered_parameters.append(
                            {
                                "name": entry_name,
                                "total_display": "—",
                                "levels_display": "N/A",
                                "labs_display": "N/A",
                                "module_display": "N/A",
                                "relic_display": "N/A",
                                "levels_supported": False,
                                "labs_supported": False,
                                "module_supported": False,
                                "relic_supported": False,
                            }
                        )

                parameters = ordered_parameters
            
            # Build parameter rows
            param_rows = [_render_table_header(weapon_color)]
            for param_data in parameters:
                param_name = str(param_data.get("name", "Parameter"))
                param_rows.append(_render_effect_block(param_name, param_data, weapon_color))

            # One row per weapon
            weapon_row = dbc.Row([
                dbc.Col([
                    dbc.Card(
                        dbc.CardBody([
                            html.H4(
                                weapon_name,
                                className="card-title mb-3",
                                style={"color": weapon_color}
                            ),
                            html.Div(param_rows),
                        ]),
                        className="shadow-sm",
                        style={
                            "borderLeft": f"6px solid {weapon_color}",
                            "borderRadius": "0.375rem"
                        }
                    ),
                ], width=12, className="mb-4"),
            ])

            section_name = catalog_sections.get(weapon_name) or _classify_weapon_section(weapon_name, datastore_categories)
            section_rows.setdefault(section_name, []).append(weapon_row)

        content_blocks: List[Any] = []
        for section_name in section_order:
            rows = section_rows.get(section_name, [])
            content_blocks.append(html.H3(section_name, className="mt-3 mb-3"))
            if rows:
                content_blocks.extend(rows)
            else:
                content_blocks.append(
                    html.Div(
                        "No entries in this section.",
                        style={"color": "#9ca3af", "marginBottom": "1rem"}
                    )
                )

        return html.Div(content_blocks, className="mb-4")
        
    except Exception:
        import traceback
        return dbc.Alert([
            html.H5("Error generating weapons overview"),
            html.Pre(traceback.format_exc()),
        ], color="danger")


def layout() -> html.Div:
    """Layout for UW Overview page."""
    return html.Div([
        html.H1("UW Overview", className="page-title mb-4"),
        
        # Tabs for switching between views
        dbc.Tabs([
            dbc.Tab(
                label="Lookup Tables (Config)",
                children=[
                    html.Div(className="p-3", children=[
                        html.P(
                            "Dynamic view of all lookup tables from config.py, showing available parameters and sources.",
                            style={"color": "#718096", "fontSize": "0.9rem"}
                        ),
                        _render_lookup_table_view(),
                    ])
                ],
                tab_id="lookups"
            ),
            dbc.Tab(
                label="Data-Driven View",
                children=[
                    html.Div(className="p-3", children=[
                        html.P(
                            "Detailed breakdown of weapons from userData.json via DataManager.",
                            style={"color": "#718096", "fontSize": "0.9rem"}
                        ),
                        _render_uw_overview_content(),
                    ])
                ],
                tab_id="data-driven"
            ),
        ], id="uw-overview-tabs", active_tab="lookups"),
    ], className="p-3")
