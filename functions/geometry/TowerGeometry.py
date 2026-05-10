from functions.data import ImportJSON
from functions import user_data_store
from functions.graphs.Graphs import simple_table
import pandas as pd
# Function to load and display Golden Bot info as a table
def get_golden_bot_info_table(json_path: str | None = None):
    """Return Golden Bot components table figure with Component / Level / TargetLevel."""
    try:
        if json_path:
            user_data_store.load_from_path(str(json_path))
        df = ImportJSON.extract_golden_bot_info(user_data_store.full_json if user_data_store.full_json else ImportJSON.load_full_json(str(json_path)))
        df = df.reset_index(drop=True)
        return simple_table(df, title="Golden Bot Components") if not df.empty else simple_table(df, title="Golden Bot Components (empty)")
    except Exception:
        return simple_table(pd.DataFrame(), title="Golden Bot Components (error)")

# Function to load and display Ultimate Weapon Upgrades as a styled table
def get_ultimate_weapon_upgrades_table(json_path: str | None = None):
    """Return Ultimate Weapon upgrades as a 2x2 grid of tables (one per weapon)."""
    import dash_bootstrap_components as dbc
    from dash import html
    
    try:
        if json_path:
            user_data_store.load_from_path(str(json_path))
        df = ImportJSON.extract_ultimate_weapon_upgrades(user_data_store.full_json if user_data_store.full_json else ImportJSON.load_full_json(str(json_path)))
        
        if df.empty:
            return html.Div("No Ultimate Weapon upgrades found.")
        
        # Sort and group by weapon
        df = df.sort_values(["Ultimate Weapon", "Upgrade"]).reset_index(drop=True)
        weapons = df["Ultimate Weapon"].unique()
        
        # Create individual tables for each weapon
        weapon_tables = []
        for weapon in weapons:
            weapon_df = df[df["Ultimate Weapon"] == weapon][["Upgrade", "Level", "TargetLevel"]].copy()
            fig = simple_table(weapon_df, title=weapon)
            weapon_tables.append(fig)
        
        # Pad to ensure we have 4 items for 2x2 grid
        while len(weapon_tables) < 4:
            weapon_tables.append(simple_table(pd.DataFrame(), title=""))
        
        # Create 2x2 grid layout
        from dash import dcc
        row1 = dbc.Row([
            dbc.Col(dcc.Graph(figure=weapon_tables[0], config={'displayModeBar': False}), width=6),
            dbc.Col(dcc.Graph(figure=weapon_tables[1], config={'displayModeBar': False}), width=6)
        ], className="mb-3")
        
        row2 = dbc.Row([
            dbc.Col(dcc.Graph(figure=weapon_tables[2], config={'displayModeBar': False}), width=6),
            dbc.Col(dcc.Graph(figure=weapon_tables[3], config={'displayModeBar': False}), width=6)
        ], className="mb-3")
        
        return html.Div([row1, row2])
        
    except Exception as e:
        import traceback
        return html.Div(f"Error: {e}\n{traceback.format_exc()}")


def get_relevant_modules_table(json_path: str | None = None):
    """Return modules with relevant ultimate weapon upgrades in a single table."""
    from dash import html, dcc
    
    try:
        if json_path:
            user_data_store.load_from_path(str(json_path))
        df = ImportJSON.extract_relevant_module_upgrades(user_data_store.full_json if user_data_store.full_json else ImportJSON.load_full_json(str(json_path)))
        
        if df.empty:
            return html.Div("No relevant module upgrades found.")
        
        # Format the display - combine value and unit
        df_display = df.copy()
        df_display["Effect"] = df_display.apply(
            lambda row: f"{row['Effect Value']}{row['Effect Unit']}" if pd.notna(row['Effect Unit']) and row['Effect Unit'] else str(row['Effect Value']),
            axis=1
        )
        
        # Select and reorder columns for display
        display_cols = ["Module Name", "Type", "Rarity", "Level", "Effect Name", "Effect", "Effect Rarity"]
        df_display = df_display[display_cols]
        
        fig = simple_table(df_display, title="Modules with Ultimate Weapon Upgrades")
        return dcc.Graph(figure=fig, config={'displayModeBar': False})
        
    except Exception as e:
        import traceback
        return html.Div(f"Error: {e}\n{traceback.format_exc()}")

def get_relevant_labs_table(json_path: str | None = None):
    """Return labs progress for Golden Tower, Golden Bot, Black Hole, and Spotlight research."""
    from dash import html, dcc
    
    try:
        if json_path:
            user_data_store.load_from_path(str(json_path))
        df = ImportJSON.extract_relevant_labs_progress(user_data_store.full_json if user_data_store.full_json else ImportJSON.load_full_json(str(json_path)))
        
        if df.empty:
            return html.Div("No relevant labs progress found.")
        
        fig = simple_table(df, title="Labs Progress - Ultimate Weapons & Bots")
        return dcc.Graph(figure=fig, config={'displayModeBar': False})
        
    except Exception as e:
        import traceback
        return html.Div(f"Error: {e}\n{traceback.format_exc()}")

def get_combined_ultimate_weapons_table(
    json_path: str | None = None,
    armor_module: str = "Primordial Collapse",
    armor_rarity: str = "Epic",
    generator_module: str = "Galaxy Compressor",
    generator_rarity: str = "Epic",
    package_chance: float = 40.0,
    game_mode: str = "farming",
):
    """Return combined table for all ultimate weapons with module & rarity context.

    Displays each weapon type with: Parameter | Level | Target Level | Module Effect | Labs Level | Total Value
    Applies module special effects based on selected module & rarity:
      - Multiverse Nexus: synchronize Death Wave, Golden Tower, Black Hole cooldowns to avg +/- rarity value
      - Primordial Collapse: add Black Hole Damage Reduction and Extra Black Hole rows
      - Galaxy Compressor: add Cooldown Reduction per Package rows for all ultimate weapons (except Poison Swamp which is not listed)
      - Black Hole Digestor: add Coins/Kill Bonus per Free Upgrade row (mapped here to Golden Bot)
    """
    from dash import html, dcc
    import dash_bootstrap_components as dbc
    
    try:
        if json_path:
            user_data_store.load_from_path(str(json_path))
        
        combined_data = ImportJSON.extract_combined_ultimate_weapons_data(
            user_data_store.full_json if user_data_store.full_json else ImportJSON.load_full_json(str(json_path)),
            selected_module=armor_module
        )

        # Inject Relics column for Golden Bot and fold Bot Range Bonus into Total Value
        try:
            if "Golden Bot" in combined_data:
                gb_df = combined_data["Golden Bot"].copy()
                # Ensure a 'Relics' column exists
                if 'Relics' not in gb_df.columns:
                    gb_df['Relics'] = ""

                bot_range_bonus = float(user_data_store.relics_data.get('Bot Range Bonus', 0.0) or 0.0)
                if bot_range_bonus != 0.0:
                    import re as _re
                    # Find the Range row and add the relic bonus to Total Value
                    mask_range = gb_df["Parameter"].str.contains("Range", case=False, na=False)
                    for idx in gb_df[mask_range].index:
                        current_tv = str(gb_df.loc[idx, "Total Value"]) if "Total Value" in gb_df.columns else ""
                        m = _re.search(r"(\d+(?:\.\d+)?)", current_tv)
                        if m:
                            base_val = float(m.group(1))
                            new_val = base_val + bot_range_bonus
                            # Preserve unit if present (assume meters)
                            suffix = current_tv.replace(m.group(1), "").strip()
                            suffix = suffix if suffix else "m"
                            gb_df.loc[idx, "Total Value"] = f"{new_val:.0f}{suffix}"
                            gb_df.loc[idx, "Relics"] = f"+{bot_range_bonus:.0f}m"
                        else:
                            # If no numeric value present, just set Relics column for visibility
                            gb_df.loc[idx, "Relics"] = f"+{bot_range_bonus:.0f}m"

                combined_data["Golden Bot"] = gb_df
        except Exception:
            # Non-fatal if relic injection fails
            pass

        # Apply perks if in farming mode
        if game_mode == "farming":
            # Perk definitions
            perks = {
                "+1 Wave on Death Wave": {
                    "weapon": "Death Wave",
                    "parameter": "Number of Waves",
                    "effect_type": "additive",
                    "value": 1
                },
                "Black Hole Duration +12.0s": {
                    "weapon": "Black Hole",
                    "parameter": "Duration",
                    "effect_type": "additive",
                    "value": 12.0
                },
                "Spotlight Damage Bonus x1.5": {
                    "weapon": "Spotlight",
                    "parameter": "Damage Mult",
                    "effect_type": "multiplicative",
                    "value": 1.5
                },
                "Golden Tower Bonus x1.5": {
                    "weapon": "Golden Bot",
                    "parameter": "Bonus Multiplier",
                    "effect_type": "multiplicative",
                    "value": 1.5
                },
                "Swamp Radius x1.5": {
                    "weapon": "Poison Swamp",
                    "parameter": "Radius",
                    "effect_type": "multiplicative",
                    "value": 1.5
                }
            }
            
            for perk_name, perk_def in perks.items():
                weapon = perk_def["weapon"]
                param = perk_def["parameter"]
                effect_type = perk_def["effect_type"]
                value = perk_def["value"]
                
                if weapon in combined_data:
                    df = combined_data[weapon].copy()
                    # Find rows matching the parameter
                    mask = df["Parameter"].str.contains(param, case=False, na=False)
                    if mask.any():
                        for idx in df[mask].index:
                            # Parse current Total Value
                            current = df.loc[idx, "Total Value"]
                            try:
                                # Extract numeric part
                                import re
                                numeric_match = re.search(r"(\d+(?:\.\d+)?)", str(current))
                                if numeric_match:
                                    base_val = float(numeric_match.group(1))
                                    if effect_type == "additive":
                                        new_val = base_val + value
                                    else:  # multiplicative
                                        new_val = base_val * value
                                    
                                    # Preserve unit/suffix
                                    suffix = str(current).replace(numeric_match.group(1), "").strip()
                                    df.loc[idx, "Total Value"] = f"{new_val:.1f}{suffix}"
                                    # Add perk indicator in Module Effect column
                                    df.loc[idx, "Module Effect"] = f"Perk: {perk_name.split(' ', 1)[0]}"
                            except Exception:
                                pass
                    combined_data[weapon] = df

        # Module ability values (duplicate minimal mapping to avoid circular import of app)
        ability_values = {
            "Multiverse Nexus": {"Epic": 20, "Legendary": 10, "Mythic": 1, "Ancestral": -10},
            "Primordial Collapse": {"Epic": 50, "Legendary": 55, "Mythic": 65, "Ancestral": 80},
            "Galaxy Compressor": {"Epic": 10, "Legendary": 13, "Mythic": 17, "Ancestral": 20},
            "Black Hole Digestor": {"Epic": 3, "Legendary": 5, "Mythic": 7, "Ancestral": 10},
        }

        # Helper to safely parse cooldown numeric portion (e.g., "100s")
        def _parse_seconds(val: str) -> float:
            if not isinstance(val, str):
                return 0.0
            import re as _re
            m = _re.search(r"(\d+(?:\.\d+)?)s", val)
            return float(m.group(1)) if m else 0.0

        # Apply Multiverse Nexus cooldown synchronization
        if armor_module == "Multiverse Nexus" and all(w in combined_data for w in ["Death Wave", "Golden Tower", "Black Hole"]):
            offset = ability_values.get(armor_module, {}).get(armor_rarity, 0)
            # Collect current cooldowns
            cds = []
            for w in ["Death Wave", "Golden Tower", "Black Hole"]:
                dfw = combined_data[w]
                cooldown_rows = dfw[dfw["Parameter"].str.lower() == "cooldown"].copy()
                if not cooldown_rows.empty:
                    # Assume first row is current level
                    val = cooldown_rows.iloc[0]["Total Value"]
                    cds.append(_parse_seconds(str(val)))
            if cds:
                avg_cd = sum(cds) / len(cds) + offset
                for w in ["Death Wave", "Golden Tower", "Black Hole"]:
                    dfw = combined_data[w]
                    mask = dfw["Parameter"].str.lower() == "cooldown"
                    dfw.loc[mask, "Total Value"] = f"{avg_cd:.0f}s (sync)"
                    dfw.loc[mask, "Module Effect"] = f"Avg±{offset}s"
                    combined_data[w] = dfw

        # Primordial Collapse effects
        if armor_module == "Primordial Collapse" and "Black Hole" in combined_data:
            reduction_val = ability_values.get(armor_module, {}).get(armor_rarity, 0)
            bh_df = combined_data["Black Hole"].copy()
            extra_rows = [
                {
                    "Parameter": "Total Black Holes",
                    "Level": "",
                    "Target Level": "",
                    # Base 1 BH + Primordial Collapse (+1) + Additional BH synergy (+1) = 3
                    "Module Effect": "+2",
                    "Labs Level": "",
                    "Total Value": "3 BH"
                }
            ]
            bh_df = pd.concat([bh_df, pd.DataFrame(extra_rows)], ignore_index=True)
            combined_data["Black Hole"] = bh_df

        # Black Hole Digestor bonus per free upgrade (map to Golden Bot for display)
        if generator_module == "Black Hole Digestor" and "Golden Bot" in combined_data:
            bd_val = ability_values.get(generator_module, {}).get(generator_rarity, 0)
            gb_df = combined_data["Golden Bot"].copy()
            row = {
                "Parameter": "Coins/Kill Bonus per Free Upgrade",
                "Level": "",
                "Target Level": "",
                "Module Effect": f"+{bd_val}%",
                "Labs Level": "",
                "Total Value": f"+{bd_val}% per upgrade"
            }
            gb_df = pd.concat([gb_df, pd.DataFrame([row])], ignore_index=True)
            combined_data["Golden Bot"] = gb_df
        
        if not combined_data:
            return html.Div("No combined data found.")
        # Filter out unwanted rows
        if "Death Wave" in combined_data:
            dw_df = combined_data["Death Wave"]
            combined_data["Death Wave"] = dw_df[~dw_df["Parameter"].str.contains("Damage Mult", case=False, na=False)]
        
        # Add Perk column for ultimate weapons (exclude Golden Bot)
        for w in ["Death Wave", "Golden Tower", "Black Hole", "Spotlight"]:
            if w in combined_data:
                dfw = combined_data[w].copy()
                if 'Perk' not in dfw.columns:
                    dfw['Perk'] = ""
                # Populate Perk from Module Effect entries like 'Perk: Black'
                if 'Module Effect' in dfw.columns:
                    import re as _re
                    perk_mask = dfw['Module Effect'].astype(str).str.startswith('Perk:')
                    for idx in dfw[perk_mask].index:
                        text = str(dfw.loc[idx, 'Module Effect'])
                        m = _re.search(r'Perk:\s*(.+)', text)
                        if m:
                            dfw.loc[idx, 'Perk'] = m.group(1).strip()
                combined_data[w] = dfw

        
        # Create tables for each weapon type in a grid layout
        weapon_tables = []
        weapon_order = ["Death Wave", "Golden Tower", "Black Hole", "Spotlight", "Golden Bot"]
        
        for weapon_type in weapon_order:
            if weapon_type in combined_data:
                df = combined_data[weapon_type]
                
                if df.empty:
                    table_content = html.Div(f"No data for {weapon_type}")
                else:
                    fig = simple_table(df, title=weapon_type)
                    table_content = dcc.Graph(figure=fig, config={'displayModeBar': False})
                
                weapon_tables.append(
                    dbc.Col([table_content], width=12, lg=6, className="mb-3")
                )
        
        # Create layout with rows of 2 columns each
        rows = []
        for i in range(0, len(weapon_tables), 2):
            row_cols = weapon_tables[i:i+2]
            rows.append(dbc.Row(row_cols))
        
        return html.Div(rows)
        
    except Exception as e:
        import traceback
        return html.Div(f"Error: {e}\n{traceback.format_exc()}")

import numpy as np
import plotly.graph_objs as go

# Minimal color palette to avoid circular imports
colors = {
    'background': '#000000',
    'text': '#FAFAFA',
}

# Common colors for schematic elements
SCHEME_COLORS = {
    'tower_range_line': '#7DA6C7',
    'tower_range_fill': 'rgba(255, 68, 68, 0.08)',
    'wall_line': '#7DA6C7',
    'black_hole_line': '#C060FF',
    'black_hole_fill': 'rgba(192, 96, 255, 0.3)',
    'gold_bot_line': '#FFD54A',
    'gold_bot_fill': 'rgba(255, 213, 74, 0.1)'
}

def circle_circle_intersection_area(r1: float, r2: float, d: float) -> float:
    """Calculate intersection area of two circles.
    
    Args:
        r1: radius of first circle
        r2: radius of second circle
        d: distance between centers
    
    Returns:
        intersection area (0 if no overlap)
    """
    # No intersection
    if d >= r1 + r2:
        return 0.0
    
    # One circle completely inside the other
    if d <= abs(r1 - r2):
        return np.pi * min(r1, r2)**2
    
    # Partial intersection
    # Using formula: A = r1²·arccos((d²+r1²-r2²)/(2dr1)) + r2²·arccos((d²+r2²-r1²)/(2dr2)) - 0.5·sqrt((r1+r2-d)(r1-r2+d)(-r1+r2+d)(r1+r2+d))
    part1 = r1**2 * np.arccos((d**2 + r1**2 - r2**2) / (2 * d * r1))
    part2 = r2**2 * np.arccos((d**2 + r2**2 - r1**2) / (2 * d * r2))
    part3 = 0.5 * np.sqrt((r1 + r2 - d) * (r1 - r2 + d) * (-r1 + r2 + d) * (r1 + r2 + d))
    return part1 + part2 - part3

def tower_layout_figure(
    tower_range: float = 69.5,
    black_hole_diameter: float = 48.0,
    black_hole_count: int = 3,
    inner_orb_range: float = 60.0,
) -> go.Figure:
    """Create a stylized tower layout schematic (square 1:1 aspect).

    Elements:
    - Tower range: light blue circle (diameter = tower_range meters).
    - Black holes: purple filled circles distributed evenly around orbit at 0.85× tower range.
      - Count: 2 (180°) or 3 (120°).
      - Diameter: black_hole_diameter × 1.33 x SQRT(tower_range / 69.5) for scaling.

    All circles centered at (0,0).
    """
    # Wall diameter calculation: 0.2158 * range_tower + 10.798
    wall_diameter = 0.2158 * tower_range + 10.798
    wall_r = wall_diameter / 2.0

    # Tower radius (red circle in screenshot)
    tower_r = tower_range / 2.0

    # Black hole orbit radius (center of black holes is 0.85× tower range)
    bh_orbit_r = 0.85 * tower_range / 2.0

    # Black hole circle radius (scaled with tower range)
    bh_radius = (black_hole_diameter / 2.0) * 1.33 * np.sqrt(tower_range / 69.5)

    # === KPI Calculations ===
    # 1. Tower range covered (angular coverage per black hole in degrees)
    # Formula: 2*ACOS((RangeTower² + DistBH² - RangeBH²) / (2*RangeTower*DistBH)) * 180/π
    numerator = tower_r**2 + bh_orbit_r**2 - bh_radius**2
    denominator = 2 * tower_r * bh_orbit_r
    # Clamp to [-1, 1] to avoid domain errors in arccos
    cos_value = np.clip(numerator / denominator, -1.0, 1.0)
    angle_coverage_per_bh_deg = 2 * np.arccos(cos_value) * 180 / np.pi
    total_angle_coverage_pct = (angle_coverage_per_bh_deg * black_hole_count) / 360.0 * 100

    # 2. Tower area covered (union of all black holes / area covered by tower range)
    tower_area = np.pi * tower_r**2
    # Use grid sampling for union area estimation
    grid_N = 400  # 400x400 grid for good accuracy
    xg = np.linspace(-tower_r, tower_r, grid_N)
    yg = np.linspace(-tower_r, tower_r, grid_N)
    xx, yy = np.meshgrid(xg, yg)
    # Mask: inside tower circle
    # Use elementwise multiplication instead of exponent for better type compatibility
    mask_tower = ((xx * xx) + (yy * yy)) <= (tower_r * tower_r)
    # Mask: inside any black hole
    mask_bh = np.zeros_like(xx, dtype=bool)
    angle_step = 360.0 / black_hole_count
    for i in range(black_hole_count):
        theta = np.radians(angle_step * i)
        cx = bh_orbit_r * np.cos(theta)
        cy = bh_orbit_r * np.sin(theta)
        mask_bh |= (((xx - cx) * (xx - cx)) + ((yy - cy) * (yy - cy))) <= (bh_radius * bh_radius)
    # Only count points inside both tower and any black hole
    mask_union = mask_tower & mask_bh
    area_covered = np.sum(mask_union) / np.sum(mask_tower) * 100 if np.sum(mask_tower) > 0 else 0.0
    
    # 3. Wall coverage (percentage of wall circumference covered by black holes)
    # Check intersection between black holes and wall circle
    mask_wall = ((xx * xx) + (yy * yy)) <= (wall_r * wall_r)
    mask_wall_bh = mask_wall & mask_bh
    wall_coverage_pct = np.sum(mask_wall_bh) / np.sum(mask_wall) * 100 if np.sum(mask_wall) > 0 else 0.0

    fig = go.Figure()

    # Hexagon (center, width = 1/3 of wall diameter)
    hex_width = wall_diameter / 3.0
    hex_radius = hex_width / 2.0  # distance from center to flat side
    # For a regular hexagon, the distance from center to vertex is hex_radius / cos(pi/6)
    hex_vertex_r = hex_radius / np.cos(np.pi / 6)
    hex_angles = np.linspace(0, 2 * np.pi, 7)
    hex_x = hex_vertex_r * np.cos(hex_angles)
    hex_y = hex_vertex_r * np.sin(hex_angles)
    fig.add_trace(go.Scatter(
        x=hex_x, y=hex_y,
        mode='lines',
        line=dict(color='#7DA6C7', width=3),
        name='Tower (Hexagon)',
        hoverinfo='skip',
        showlegend=False
    ))

    # Circle helper
    def circle_xy(r: float, steps: int = 360):
        ang = np.linspace(0, 2 * np.pi, steps)
        return r * np.cos(ang), r * np.sin(ang)

    # Wall (inner blue thick circle)
    x_wall, y_wall = circle_xy(wall_r)
    fig.add_trace(go.Scatter(
        x=x_wall, y=y_wall,
        mode='lines',
        line=dict(color='#7DA6C7', width=7),
        name='Wall',
        hovertemplate=f"Wall (diameter: {wall_diameter:.1f}m)<extra></extra>",
        showlegend=True
    ))

    # Tower range circle (red, matches screenshot)
    x_tr, y_tr = circle_xy(tower_r)
    fig.add_trace(go.Scatter(
        x=x_tr, y=y_tr,
        mode='lines',
        line=dict(color='#7DA6C7', width=3),
        name='Tower Range',
        fill='toself',
        fillcolor='rgba(255, 68, 68, 0.08)',
        hovertemplate=f"Tower Range: {tower_range:.1f}m<extra></extra>"
    ))

    # Black holes (distributed evenly) with kill zones
    angle_step = 360.0 / black_hole_count
    for i in range(black_hole_count):
        theta = np.radians(angle_step * i)
        # Center position of this black hole
        cx = bh_orbit_r * np.cos(theta)
        cy = bh_orbit_r * np.sin(theta)
        
        ang = np.linspace(0, 2 * np.pi, 360)
        
        # Black hole kill zone at 40% range (dotted purple line with fill)
        kill_zone_radius = bh_radius * 0.4
        kill_x = cx + kill_zone_radius * np.cos(ang)
        kill_y = cy + kill_zone_radius * np.sin(ang)
        fig.add_trace(go.Scatter(
            x=kill_x, y=kill_y,
            mode='lines',
            line=dict(color='#C060FF', width=2, dash='dot'),
            fill='toself',
            fillcolor='rgba(192, 96, 255, 0.3)',
            name=f'BH Kill Zone' if i == 0 else f'Kill Zone {i+1}',
            hovertemplate=f"Black Hole {i+1} Kill Zone (~40% range)<br>Enemies killed here<extra></extra>",
            showlegend=(i == 0)
        ))
        
        # Black hole outer range (solid purple line with same fill as kill zone)
        bh_x = cx + bh_radius * np.cos(ang)
        bh_y = cy + bh_radius * np.sin(ang)
        scaled_bh_diameter = black_hole_diameter * 1.33 * np.sqrt(tower_range / 69.5)
        fig.add_trace(go.Scatter(
            x=bh_x, y=bh_y,
            mode='lines',
            line=dict(color='#C060FF', width=2),
            fill='toself',
            fillcolor='rgba(192, 96, 255, 0.3)',
            name=f'Black Hole {i+1}' if i == 0 else f'BH {i+1}',
            hovertemplate=f"Black Hole {i+1}<br>Scaled Diameter: {scaled_bh_diameter:.1f}m<extra></extra>",
            showlegend=(i == 0)
        ))
        
        # Black hole center marker (light purple X for contrast)
        fig.add_trace(go.Scatter(
            x=[cx], y=[cy],
            mode='markers',
            marker=dict(color='#E8D4FF', size=8, symbol='x', line=dict(width=2)),
            name=f'BH Center' if i == 0 else f'BH Center {i+1}',
            hovertemplate=f"Black Hole {i+1} Center<extra></extra>",
            showlegend=False
        ))

    # Center marker
    fig.add_trace(go.Scatter(
        x=[0], y=[0],
        mode='markers',
        marker=dict(color='#FFFFFF', size=8, symbol='x'),
        name='Tower Center',
        hoverinfo='skip'
    ))
    
    # Inner Orbs - red dotted circle with 3 orbs at 60°, 180°, 300°
    # The dropdown provides the base range, formula scales it with tower range and wall diameter
    # Formula: 0.3471 * range_tower * (value_wall / 60) + 41.853
    # where the dropdown value represents the scaling factor
    inner_orb_diameter = 0.3471 * tower_range * (inner_orb_range / 60.0) + 41.853
    inner_orb_r = inner_orb_diameter / 2.0
    orb_x, orb_y = circle_xy(inner_orb_r)
    fig.add_trace(go.Scatter(
        x=orb_x, y=orb_y,
        mode='lines',
        line=dict(color='#FF4444', width=2, dash='dot'),
        name='Inner Orb Range',
        hovertemplate=f"Inner Orb Range: {inner_orb_diameter:.2f}m<extra></extra>",
        showlegend=True
    ))
    
    # Three inner orbs positioned at 60°, 180°, 300°
    orb_angles = [60, 180, 300]
    inner_orb_positions_x = []
    inner_orb_positions_y = []
    for angle in orb_angles:
        theta = np.radians(angle)
        ox = inner_orb_r * np.cos(theta)
        oy = inner_orb_r * np.sin(theta)
        inner_orb_positions_x.append(ox)
        inner_orb_positions_y.append(oy)
    
    fig.add_trace(go.Scatter(
        x=inner_orb_positions_x, y=inner_orb_positions_y,
        mode='markers',
        marker=dict(color='#FF4444', size=10, symbol='circle'),
        name='Inner Orbs',
        hovertemplate='Inner Orb<extra></extra>',
        showlegend=True
    ))
    
    # Regular Orbs - lighter red dotted circle with 6 orbs offset by 15°
    # Diameter calculation: 0.3828 * range_tower + 47.699
    regular_orb_diameter = 0.3828 * tower_range + 47.699
    regular_orb_r = regular_orb_diameter / 2.0
    reg_orb_x, reg_orb_y = circle_xy(regular_orb_r)
    fig.add_trace(go.Scatter(
        x=reg_orb_x, y=reg_orb_y,
        mode='lines',
        line=dict(color='#FF8888', width=2, dash='dot'),
        name='Regular Orb Range',
        hovertemplate=f"Regular Orb Range: {regular_orb_diameter:.2f}m<extra></extra>",
        showlegend=True
    ))
    
    # Six regular orbs positioned at 30°, 90°, 150°, 210°, 270°, 330° (60° spacing with 30° offset)
    regular_orb_angles = [30, 90, 150, 210, 270, 330]
    regular_orb_positions_x = []
    regular_orb_positions_y = []
    for angle in regular_orb_angles:
        theta = np.radians(angle)
        ox = regular_orb_r * np.cos(theta)
        oy = regular_orb_r * np.sin(theta)
        regular_orb_positions_x.append(ox)
        regular_orb_positions_y.append(oy)
    
    fig.add_trace(go.Scatter(
        x=regular_orb_positions_x, y=regular_orb_positions_y,
        mode='markers',
        marker=dict(color='#FF8888', size=10, symbol='circle'),
        name='Regular Orbs',
        hovertemplate='Regular Orb<extra></extra>',
        showlegend=True
    ))

    # Square aspect, equal axes
    # Increase span for more black space around the tower (matches screenshot)
    span = tower_r * 1.5
    fig.update_xaxes(visible=True, range=[-span, span], showgrid=True, gridcolor='#333333', zeroline=True, zerolinecolor='#555555')
    fig.update_yaxes(visible=True, range=[-span, span], scaleanchor='x', scaleratio=1, showgrid=True, gridcolor='#333333', zeroline=True, zerolinecolor='#555555')
    
    # Build title without KPIs (KPIs will be in cards)
    title_text = f"Tower Layout (Range: {tower_range:.1f}m, Black Holes: {black_hole_count}, BH Diameter: {black_hole_diameter:.1f}m base)"
    fig.update_layout(
        title=title_text,
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text'],
        showlegend=False,
        margin=dict(l=10, r=10, t=50, b=10)
    )
    return fig


def tower_layout_figure_with_kpis(
    tower_range: float = 69.5,
    black_hole_diameter: float = 48.0,
    black_hole_count: int = 3,
    inner_orb_range: float = 60.0,
):
    """Wrapper that returns both figure and KPI dict."""
    # Call the main function to get all calculations
    tower_r = tower_range / 2.0
    # Wall diameter calculation: 0.2158 * range_tower + 10.798
    wall_diameter = 0.2158 * tower_range + 10.798
    wall_r = wall_diameter / 2.0
    bh_orbit_r = 0.85 * tower_range / 2.0
    bh_radius = (black_hole_diameter / 2.0) * 1.33 * np.sqrt(tower_range / 69.5)
    
    # Calculate KPIs
    numerator = tower_r**2 + bh_orbit_r**2 - bh_radius**2
    denominator = 2 * tower_r * bh_orbit_r
    cos_value = np.clip(numerator / denominator, -1.0, 1.0)
    angle_coverage_per_bh_deg = 2 * np.arccos(cos_value) * 180 / np.pi
    total_angle_coverage_pct = (angle_coverage_per_bh_deg * black_hole_count) / 360.0 * 100
    
    # Area coverage calculation
    tower_area = np.pi * tower_r**2
    grid_N = 400
    xg = np.linspace(-tower_r, tower_r, grid_N)
    yg = np.linspace(-tower_r, tower_r, grid_N)
    xx, yy = np.meshgrid(xg, yg)
    # Use elementwise multiplication instead of exponent for better type compatibility
    mask_tower = ((xx * xx) + (yy * yy)) <= (tower_r * tower_r)
    mask_bh = np.zeros_like(xx, dtype=bool)
    angle_step = 360.0 / black_hole_count
    for i in range(black_hole_count):
        theta = np.radians(angle_step * i)
        cx = bh_orbit_r * np.cos(theta)
        cy = bh_orbit_r * np.sin(theta)
        mask_bh |= (((xx - cx) * (xx - cx)) + ((yy - cy) * (yy - cy))) <= (bh_radius * bh_radius)
    mask_union = mask_tower & mask_bh
    area_covered = np.sum(mask_union) / np.sum(mask_tower) * 100 if np.sum(mask_tower) > 0 else 0.0
    
    # Calculate wall coverage (angular/circumference coverage)
    # Check what portion of the wall circumference is within any black hole
    # Sample points along the wall circumference
    wall_sample_angles = np.linspace(0, 2 * np.pi, 360)
    wall_sample_x = wall_r * np.cos(wall_sample_angles)
    wall_sample_y = wall_r * np.sin(wall_sample_angles)
    
    covered_count = 0
    for j in range(len(wall_sample_angles)):
        wx, wy = wall_sample_x[j], wall_sample_y[j]
        # Check if this wall point is inside any black hole
        for i in range(black_hole_count):
            theta = np.radians(angle_step * i)
            cx = bh_orbit_r * np.cos(theta)
            cy = bh_orbit_r * np.sin(theta)
            dist_to_bh = np.sqrt((wx - cx)**2 + (wy - cy)**2)
            if dist_to_bh <= bh_radius:
                covered_count += 1
                break  # Count each wall point only once
    
    wall_coverage_pct = (covered_count / len(wall_sample_angles)) * 100
    
    # Calculate additional KPIs for cards
    # 1. BH center range (orbit radius where BH centers are placed)
    bh_center_range = bh_orbit_r * 2.0  # diameter
    # 2. Primary kill zone diameter (inner dotted ring shown in figure)
    primary_kill_zone_diameter = (bh_radius * 0.4) * 2.0
    
    # 2. Effective regular orbs range
    regular_orb_diameter = 0.3828 * tower_range + 47.699
    
    # 3. Effective inner orbs range
    inner_orb_diameter = 0.3471 * tower_range * (inner_orb_range / 60.0) + 41.853
    
    # 4. Effective tower range (just the tower_range parameter itself)
    effective_tower_range = tower_range
    
    # Get figure
    fig = tower_layout_figure(tower_range, black_hole_diameter, black_hole_count, inner_orb_range)
    
    # Return figure and KPIs
    kpis = {
        'tower_range_coverage': total_angle_coverage_pct,
        'tower_area_coverage': area_covered,
        'wall_coverage': wall_coverage_pct,
        'bh_center_range': bh_center_range,
        'primary_kill_zone': primary_kill_zone_diameter,
        'effective_orbs_range': regular_orb_diameter,
        'effective_inner_orbs_range': inner_orb_diameter,
        'effective_tower_range': effective_tower_range
    }
    return fig, kpis


def golden_bot_figure(
    tower_range: float = 69.5,
    bot_range: float = 56.0,
    samples: int = 10,
    seed: int | None = 42,
    black_hole_diameter: float = 48.0,
    black_hole_count: int = 2,
) -> go.Figure:
    """Golden bot schematic with random positions and KPIs.

    - Average radial distance at 50% of tower range
    - Bot size scales as: RangeBot × 1.33 × (RangeTower / 69.5)
    - Includes context: wall, tower range, hexagon, and black holes
    - KPIs: tower range coverage, black hole intersection, wall coverage
    """
    rng = np.random.default_rng(seed)

    # Geometry
    tower_r = tower_range / 2.0
    wall_fraction = 0.40
    wall_r = (tower_range * wall_fraction) / 2.0

    # Bot radius scaled in data units (meters)
    bot_radius = (bot_range / 2.0) * 1.33 * (tower_range / 69.5)
    
    # Bot can move up to 1.5× tower range radius
    max_r = 1.5 * tower_r

    # Sample angles uniformly and radii from clipped normal centered at 0.5*tower_r
    # with std dev allowing spread to 1.5× tower range
    angles = rng.uniform(0, 2 * np.pi, size=samples)
    radii = rng.normal(loc=0.5 * tower_r, scale=0.4 * tower_r, size=samples)
    radii = np.clip(radii, 0.0, max_r)

    xs = radii * np.cos(angles)
    ys = radii * np.sin(angles)

    # Black hole geometry for intersection calculation
    bh_orbit_r = 0.85 * tower_range / 2.0
    bh_radius = (black_hole_diameter / 2.0) * 1.33 * np.sqrt(tower_range / 69.5)
    kill_zone_radius = bh_radius * 0.4
    angle_step = 360.0 / black_hole_count

    # === KPI Calculations ===
    # For each bot sample, check coverage
    tower_coverage_count = 0
    bh_intersection_count = 0
    wall_coverage_count = 0

    for i in range(samples):
        bot_x, bot_y = float(xs[i]), float(ys[i])
        bot_dist_from_center = np.sqrt(bot_x**2 + bot_y**2)
        
        # 1. Tower range coverage: bot center + bot radius intersects tower circle
        if bot_dist_from_center + bot_radius >= tower_r:
            # Bot extends beyond or touches tower range
            tower_coverage_count += 1
        
        # 2. Black hole intersection: check if bot overlaps any black hole
        for j in range(black_hole_count):
            theta = np.radians(angle_step * j)
            bh_x = bh_orbit_r * np.cos(theta)
            bh_y = bh_orbit_r * np.sin(theta)
            dist_to_bh = np.sqrt((bot_x - bh_x)**2 + (bot_y - bh_y)**2)
            if dist_to_bh < (bot_radius + bh_radius):
                bh_intersection_count += 1
                break  # Count each bot only once
        
        # 3. Wall coverage: bot center + bot radius intersects wall circle
        if bot_dist_from_center - bot_radius <= wall_r:
            # Bot overlaps with wall
            wall_coverage_count += 1

    avg_tower_coverage_pct = (tower_coverage_count / samples) * 100 if samples > 0 else 0.0
    avg_bh_intersection_pct = (bh_intersection_count / samples) * 100 if samples > 0 else 0.0
    avg_wall_coverage_pct = (wall_coverage_count / samples) * 100 if samples > 0 else 0.0

    fig = go.Figure()

    # helper for drawing a circle at center (cx, cy) with radius r in data units
    def circle_xy_center(cx: float, cy: float, r: float, steps: int = 180):
        ang = np.linspace(0, 2 * np.pi, steps)
        return cx + r * np.cos(ang), cy + r * np.sin(ang)

    # Hexagon (center, width = 1/3 of wall diameter) - same as tower layout
    hex_width = wall_fraction * tower_range / 3.0
    hex_radius = hex_width / 2.0
    hex_vertex_r = hex_radius / np.cos(np.pi / 6)
    hex_angles = np.linspace(0, 2 * np.pi, 7)
    hex_x = hex_vertex_r * np.cos(hex_angles)
    hex_y = hex_vertex_r * np.sin(hex_angles)
    fig.add_trace(go.Scatter(
        x=hex_x, y=hex_y,
        mode='lines',
        line=dict(color=SCHEME_COLORS['wall_line'], width=3),
        name='Tower (Hexagon)',
        hoverinfo='skip',
        showlegend=False
    ))

    # Wall
    wall_x, wall_y = circle_xy_center(0.0, 0.0, wall_r)
    fig.add_trace(go.Scatter(
        x=wall_x, y=wall_y, mode='lines',
        line=dict(color=SCHEME_COLORS['wall_line'], width=7), name='Wall'
    ))

    # Tower range (red, matching tower layout)
    tr_x, tr_y = circle_xy_center(0.0, 0.0, tower_r)
    fig.add_trace(go.Scatter(
        x=tr_x, y=tr_y, mode='lines',
        line=dict(color=SCHEME_COLORS['tower_range_line'], width=3), name='Tower Range',
        fill='toself', fillcolor=SCHEME_COLORS['tower_range_fill'],
        hovertemplate=f"Tower Range: {tower_range:.1f}m<extra></extra>"
    ))

    # Black holes (distributed evenly, same as tower layout)
    for j in range(black_hole_count):
        theta = np.radians(angle_step * j)
        bh_x = bh_orbit_r * np.cos(theta)
        bh_y = bh_orbit_r * np.sin(theta)
        bh_circle_x, bh_circle_y = circle_xy_center(bh_x, bh_y, bh_radius)
        fig.add_trace(go.Scatter(
            x=bh_circle_x, y=bh_circle_y, mode='lines',
            line=dict(color=SCHEME_COLORS['black_hole_line'], width=2),
            fill='toself', fillcolor=SCHEME_COLORS['black_hole_fill'],
            name=f'Black Hole {j+1}' if j == 0 else None,
            showlegend=(j == 0),
            hoverinfo='skip'
        ))
        # Add kill zone ring (purple, dotted)
        kz_x, kz_y = circle_xy_center(bh_x, bh_y, kill_zone_radius)
        fig.add_trace(go.Scatter(
            x=kz_x, y=kz_y, mode='lines',
            line=dict(color='#C060FF', width=2, dash='dot'),
            name='BH Kill Zone' if j == 0 else None,
            showlegend=(j == 0),
            hoverinfo='skip'
        ))
        # Add BH center marker
        fig.add_trace(go.Scatter(
            x=[bh_x], y=[bh_y], mode='markers',
            marker=dict(color='#C060FF', size=10, symbol='circle'),
            name='BH Center' if j == 0 else None,
            showlegend=(j == 0),
            hovertemplate=f"BH Center<extra></extra>"
        ))

    # Add tower center marker (white 'x')
    fig.add_trace(go.Scatter(
        x=[0], y=[0], mode='markers',
        marker=dict(color='#FFFFFF', size=14, symbol='x'),
        name='Tower Center',
        showlegend=True,
        hovertemplate=f"Tower Center<extra></extra>"
    ))

    # Golden bot samples as filled circles
    for i in range(samples):
        cx, cy = float(xs[i]), float(ys[i])
        gx, gy = circle_xy_center(cx, cy, bot_radius)
        fig.add_trace(go.Scatter(
            x=gx, y=gy, mode='lines',
            line=dict(color=SCHEME_COLORS['gold_bot_line'], width=1),
            fill='toself', fillcolor=SCHEME_COLORS['gold_bot_fill'],
            name='Golden Bot' if i == 0 else None,
            showlegend=(i == 0),
            hovertemplate=f"Golden Bot<br>Range (base): {bot_range:.1f}m<br>Scaled diameter: {bot_range * 1.33 * (tower_range/69.5):.1f}m<extra></extra>"
        ))

    # Axes and layout to match tower schematic
    # Extend span to accommodate 1.5× tower range positions (matching tower layout)
    span = tower_r * 1.5
    fig.update_xaxes(visible=True, range=[-span, span], showgrid=True, gridcolor='#333333', zeroline=True, zerolinecolor='#555555')
    fig.update_yaxes(visible=True, range=[-span, span], scaleanchor='x', scaleratio=1, showgrid=True, gridcolor='#333333', zeroline=True, zerolinecolor='#555555')
    
    # Build title without KPIs (KPIs will be in cards)
    title_text = f"Golden Bot Positions (samples={samples})"
    
    fig.update_layout(
        title=title_text,
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text'],
        showlegend=False,
        margin=dict(l=10, r=10, t=50, b=10),
        width=600,
        height=600
    )
    return fig


def golden_bot_figure_with_kpis(
    tower_range: float = 69.5,
    bot_range: float = 40.0,
    bot_range_bonus: float = 0.0,
    samples: int = 10,
    seed: int | None = 42,
    black_hole_diameter: float = 48.0,
    black_hole_count: int = 2,
):
    """Wrapper that returns both figure and KPI dict.

    bot_range_bonus is an absolute additive bonus (e.g. +6) applied before scaling.
    """
    # Geometry remains based on the input bot_range; relic bonus is for display only
    effective_bot_range = bot_range

    # Get the figure
    fig = golden_bot_figure(tower_range, bot_range, samples, seed, black_hole_diameter, black_hole_count)
    
    # Recalculate KPIs for the card display
    # KPIs represent the AVERAGE coverage of a single bot across all sample positions
    rng = np.random.default_rng(seed)
    tower_r = tower_range / 2.0
    wall_fraction = 0.40
    wall_r = (tower_range * wall_fraction) / 2.0
    bot_radius = (bot_range / 2.0) * 1.33 * (tower_range / 69.5)
    max_r = 1.5 * tower_r
    
    angles = rng.uniform(0, 2 * np.pi, size=samples)
    radii = rng.normal(loc=0.5 * tower_r, scale=0.4 * tower_r, size=samples)
    radii = np.clip(radii, 0.0, max_r)
    
    xs = radii * np.cos(angles)
    ys = radii * np.sin(angles)
    
    bh_orbit_r = 0.85 * tower_range / 2.0
    bh_radius = (black_hole_diameter / 2.0) * 1.33 * np.sqrt(tower_range / 69.5)
    angle_step = 360.0 / black_hole_count
    
    # Helper function: calculate arc length where bot circle intersects target circle's circumference
    def calc_circumference_coverage(bot_x, bot_y, bot_r, target_r):
        """Calculate percentage of target circle's circumference covered by bot circle."""
        d = np.sqrt(bot_x**2 + bot_y**2)  # Distance from origin to bot center
        
        # If bot doesn't reach the target circumference, return 0
        if d > target_r + bot_r or d + bot_r < target_r:
            return 0.0
        
        # If bot contains the entire target circle, return 100
        if d + target_r <= bot_r:
            return 100.0
        
        # Calculate intersection points using circle-circle intersection formula
        # The angle subtended at target center by intersection arc
        if abs(d - target_r) < bot_r < d + target_r:
            # Using law of cosines: cos(half_angle) = (target_r^2 + d^2 - bot_r^2) / (2 * target_r * d)
            cos_half_angle = (target_r**2 + d**2 - bot_r**2) / (2.0 * target_r * d)
            cos_half_angle = np.clip(cos_half_angle, -1.0, 1.0)
            half_angle = np.arccos(cos_half_angle)
            arc_angle = 2.0 * half_angle
            # Percentage of circumference
            return (arc_angle / (2.0 * np.pi)) * 100.0
        
        return 0.0
    
    # For each sample position, calculate KPIs
    tower_coverage_samples = []
    bh_intersection_samples = []
    wall_coverage_samples = []
    kill_zone_coverage_samples = []

    # Kill zone radius and area
    kill_zone_radius = bh_radius * 0.4
    kill_zone_area = np.pi * kill_zone_radius ** 2

    for i in range(samples):
        bot_x, bot_y = float(xs[i]), float(ys[i])

        # 1. Tower range coverage: % of tower range circumference covered by bot
        tower_coverage = calc_circumference_coverage(bot_x, bot_y, bot_radius, tower_r)
        tower_coverage_samples.append(tower_coverage)

        # 2. Black hole intersection: union area of bot with all black holes
        grid_size = 50
        x_min = bot_x - bot_radius - bh_radius
        x_max = bot_x + bot_radius + bh_radius
        y_min = bot_y - bot_radius - bh_radius
        y_max = bot_y + bot_radius + bh_radius

        gx = np.linspace(x_min, x_max, grid_size)
        gy = np.linspace(y_min, y_max, grid_size)
        gx, gy = np.meshgrid(gx, gy)

        mask_bot = (((gx - bot_x) * (gx - bot_x)) + ((gy - bot_y) * (gy - bot_y))) <= (bot_radius * bot_radius)

        mask_any_bh = np.zeros_like(gx, dtype=bool)
        mask_any_kz = np.zeros_like(gx, dtype=bool)
        for j in range(black_hole_count):
            theta = np.radians(angle_step * j)
            bh_x = bh_orbit_r * np.cos(theta)
            bh_y = bh_orbit_r * np.sin(theta)
            mask_any_bh |= (((gx - bh_x) * (gx - bh_x)) + ((gy - bh_y) * (gy - bh_y))) <= (bh_radius * bh_radius)
            mask_any_kz |= (((gx - bh_x) * (gx - bh_x)) + ((gy - bh_y) * (gy - bh_y))) <= (kill_zone_radius * kill_zone_radius)

        intersection_points = np.sum(mask_bot & mask_any_bh)
        bot_points = np.sum(mask_bot)
        if bot_points > 0:
            bh_intersection_pct = (intersection_points / bot_points) * 100.0
        else:
            bh_intersection_pct = 0.0
        bh_intersection_samples.append(bh_intersection_pct)

        # 3. Wall coverage: % of wall circumference covered by bot
        wall_coverage = calc_circumference_coverage(bot_x, bot_y, bot_radius, wall_r)
        wall_coverage_samples.append(wall_coverage)

        # 4. Kill zone coverage: % of kill zone area covered by bot
        kill_zone_intersection_points = np.sum(mask_bot & mask_any_kz)
        total_kz_points = np.sum(mask_any_kz)
        if total_kz_points > 0:
            kill_zone_coverage = (kill_zone_intersection_points / total_kz_points) * 100.0
        else:
            kill_zone_coverage = 0.0
        kill_zone_coverage_samples.append(kill_zone_coverage)

    def conf_interval(data):
        if len(data) < 2:
            return 0.0
        import scipy.stats as stats
        mean = np.mean(data)
        sem = stats.sem(data)
        ci = stats.t.interval(0.95, len(data)-1, loc=mean, scale=sem)
        return ci[1] - mean  # upper bound distance from mean

    avg_tower_coverage_pct = np.mean(tower_coverage_samples) if samples > 0 else 0.0
    ci_tower_coverage = conf_interval(tower_coverage_samples)
    avg_bh_intersection_pct = np.mean(bh_intersection_samples) if samples > 0 else 0.0
    ci_bh_intersection = conf_interval(bh_intersection_samples)
    avg_wall_coverage_pct = np.mean(wall_coverage_samples) if samples > 0 else 0.0
    ci_wall_coverage = conf_interval(wall_coverage_samples)
    avg_kill_zone_coverage_pct = np.mean(kill_zone_coverage_samples) if samples > 0 else 0.0
    ci_kill_zone_coverage = conf_interval(kill_zone_coverage_samples)

    kpis = {
        'tower_range_coverage': avg_tower_coverage_pct,
        'tower_range_coverage_ci': ci_tower_coverage,
        'black_hole_intersection': avg_bh_intersection_pct,
        'black_hole_intersection_ci': ci_bh_intersection,
        'wall_coverage': avg_wall_coverage_pct,
        'wall_coverage_ci': ci_wall_coverage,
        'kill_zone_coverage': avg_kill_zone_coverage_pct,
        'kill_zone_coverage_ci': ci_kill_zone_coverage
    }
    return fig, kpis

