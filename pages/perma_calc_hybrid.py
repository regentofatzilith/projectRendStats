
# --- Phase 3 Refactored Page: Uses DataManager + Computation Layer ---
import pandas as pd
import numpy as np
import dash
from dash import dcc, html, Input, Output, callback, ctx
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dataclasses import dataclass, field
from typing import Dict, Any, Optional

# Import from Phase 1 (Data) and Phase 2 (Computation)
from functions.data import DataManager, config
from functions.computation.simulation import (
    simulate_package_reductions,
    calculate_uw_uptime,
    calculate_uptime_stats,
    downsample_simulation_df,
)


# --- Centralized static constants via DataManager ---
WA_Card = config.WA_CARD
Farming_Perks = config.FARMING_PERKS
GC_EFFECTS = config.GC_EFFECTS
MVN_EFFECTS = config.MVN_EFFECTS
TIER_CONFIG = config.TIER_CONFIG
UW_CONFIG = config.UW_CONFIG

# --- UI Defaults ---
fb_default_tier = "Tier 14"
fb_pkg_chance = 78
fb_wa_card_default = "7 Star"
fb_package_after_boss_default = "Unlocked"
fb_uw_cooldown_bc_default = "Inactive"
fb_gc_tier_default = "Mythic"
fb_mvn_default = "None"
fb_detail_selector_default = "Golden Bot"
fb_show_cooldown_default = []

# Simulation constants
total_time = 3600
fb_max_uw_plot_points = 900

# Physics/mechanics constants (used in callback)
fb_default_boss_waves = 10
fb_bc_cooldown_bonus = 10
fb_gc_pkg_reduction = GC_EFFECTS.get("Legendary", 13.0)
fb_pkg_chance_float = fb_pkg_chance / 100.0
Wave_Basetime = config.WAVE_BASETIME
fb_wave_duration = 26.0
fb_default_wave_cooldown = 9
fb_base_wave_time = fb_wave_duration + fb_default_wave_cooldown
fb_default_play_mode = "Farming"
fb_default_perks_status = "active"

# Build DataFrames from imported TIER_CONFIG and UW_CONFIG
Tier_DF = pd.DataFrame([
    {"name": tier, **config, "wave_time": config["wave_time"], "wave_cooldown": config["wave_cooldown"], "perks": "active" if config["type"] == "Farming" else "none", "Boss_Waves": config["boss_waves"]}
    for tier, config in TIER_CONFIG.items()
])

# Convert UW_CONFIG dict to DataFrame for UI components
UW_CONFIG_DF = pd.DataFrame([
    {"name": name, **config}
    for name, config in UW_CONFIG.items()
])


def _coerce_uw_value(value: Any, fallback: float) -> float:
    """Return a numeric UW value, falling back when Dash/analyzer provides None."""
    try:
        if value is None or pd.isna(value):
            return float(fallback)
        return float(value)
    except Exception:
        return float(fallback)

def get_tier_info(tier_name: str) -> Dict[str, Any]:
    """Extract tier information from Tier_DF."""
    tier_row = Tier_DF[Tier_DF['name'] == tier_name]
    if tier_row.empty:
        return {}
    result = tier_row.iloc[0].to_dict()
    return {str(k): v for k, v in result.items()}

def _make_uw_figure(df: pd.DataFrame, title: str, uw_color: str = "#00B0F6", show_cooldown: bool = True) -> go.Figure:
    df_plot = downsample_simulation_df(df, max_points=800)
    package_mask = df_plot["package_reduction"].to_numpy() > 0
    package_times = df_plot.loc[package_mask, "t"].to_numpy()
    package_values = df_plot.loc[package_mask, "package_reduction"].to_numpy()
    uptime_y = np.where(df_plot["is_active"], df_plot["remaining_active_time"], 0)
    downtime_y = -df_plot["cooldown_remaining"]
    stats = calculate_uptime_stats(df)
    y_top = float(df_plot["remaining_active_time"].max())
    package_y = np.full_like(package_times, y_top, dtype=float)
    fig = go.Figure()
    if isinstance(uw_color, str) and uw_color.startswith("#") and len(uw_color) == 7:
        r = int(uw_color[1:3], 16)
        g = int(uw_color[3:5], 16)
        b = int(uw_color[5:7], 16)
        fill_color = f"rgba({r},{g},{b},0.3)"
    else:
        fill_color = uw_color
    fig.add_trace(go.Scatter(x=df_plot["t"], y=uptime_y, mode="lines", name="Uptime", fill="tozeroy", line=dict(color=uw_color, width=1), fillcolor=fill_color, hovertemplate="t=%{x}s<br>time=%{y}s<extra></extra>"))
    if show_cooldown:
        fig.add_trace(go.Scatter(x=df_plot["t"], y=downtime_y, mode="lines", name="Downtime", line=dict(color="#888", width=1), hovertemplate="t=%{x}s<br>time=%{y}s<extra></extra>"))
    inactive_mask = ~df_plot["is_active"].to_numpy()
    if inactive_mask.any():
        t_vals = df_plot["t"].to_numpy()
        y_zeros = np.zeros(len(t_vals))
        inactive_y = np.where(inactive_mask, y_zeros, np.nan)
        fig.add_trace(go.Scatter(x=t_vals, y=inactive_y, mode="lines", name="No Activation", line=dict(color="#DC2626", width=4), hovertemplate="t=%{x}s<br>NO ACTIVATION<extra></extra>"))
    if show_cooldown:
        for i, pkg_time in enumerate(package_times):
            pkg_idx = np.where(df_plot["t"] == pkg_time)[0]
            if len(pkg_idx) > 0:
                idx = pkg_idx[0]
                pkg_reduction = package_values[i]
                cooldown_after = df_plot.iloc[idx]["cooldown_remaining"]
                cooldown_before = cooldown_after + pkg_reduction
                y_after = -cooldown_after
                y_before = -cooldown_before
                fig.add_trace(go.Scatter(x=[pkg_time, pkg_time], y=[y_before, y_after], mode="lines", line=dict(color="#90EE90", width=2), showlegend=False, hoverinfo="skip"))
    is_boss_at_packages = df_plot.loc[package_mask, "is_boss_package"].to_numpy()
    regular_mask = ~is_boss_at_packages
    if regular_mask.any():
        fig.add_trace(go.Scatter(x=package_times[regular_mask], y=package_y[regular_mask], mode="markers", name="Package", marker=dict(size=6, color="#6495ED"), customdata=package_values[regular_mask], hovertemplate="t=%{x}s<br>reduction=%{customdata}s<extra></extra>"))
    boss_mask = is_boss_at_packages
    if boss_mask.any():
        fig.add_trace(go.Scatter(x=package_times[boss_mask], y=package_y[boss_mask], mode="markers", name="Boss Package", marker=dict(size=10, color="#FFD700", symbol="star"), customdata=package_values[boss_mask], hovertemplate="t=%{x}s<br>Boss Package<br>reduction=%{customdata}s<extra></extra>"))
    fig.update_layout(template="plotly_dark", title=title, xaxis_title="t (seconds)", xaxis=dict(range=[0, df["t"].max()]), yaxis_title="Time (s, +active/-cooldown)", legend=dict(orientation="h", yanchor="top", y=-0.15, xanchor="center", x=0.5), margin=dict(l=50, r=100, t=50, b=80))
    return fig

def _make_sync_figure(results: Dict[str, pd.DataFrame], selected_uw: str | None = None) -> go.Figure:
    fig = go.Figure()
    uw_positions = {uw_name: i for i, uw_name in enumerate(UW_ORDER)}
    bar_height = 0.8
    color_map = {row['name']: row['color_hex'] for _, row in UW_CONFIG_DF.iterrows()}

    def _rgba(hex_color: str, alpha: float) -> str:
        if isinstance(hex_color, str) and hex_color.startswith("#") and len(hex_color) == 7:
            r = int(hex_color[1:3], 16)
            g = int(hex_color[3:5], 16)
            b = int(hex_color[5:7], 16)
            return f"rgba({r},{g},{b},{alpha})"
        return hex_color

    def _compute_segments(t_values: np.ndarray, is_active: np.ndarray) -> list[tuple[float, float]]:
        if t_values.size == 0:
            return []
        is_active_padded = np.concatenate([np.array([False]), is_active, np.array([False])])
        diff = np.diff(is_active_padded.astype(int))
        starts = np.where(diff == 1)[0]
        ends = np.where(diff == -1)[0]
        segments = []
        for start_idx, end_idx in zip(starts, ends):
            t_start = float(t_values[start_idx]) if hasattr(t_values[start_idx], 'item') else t_values[start_idx]
            t_end = float(t_values[end_idx - 1]) + 1 if hasattr(t_values[end_idx - 1], 'item') else t_values[end_idx - 1] + 1
            if t_end > t_start:
                segments.append((t_start, t_end))
        return segments

    def _subtract_intervals(seg_start: float, seg_end: float, overlaps: list[tuple[float, float]]) -> list[tuple[float, float]]:
        if not overlaps:
            return [(seg_start, seg_end)]
        gaps = []
        cursor = seg_start
        for o_start, o_end in overlaps:
            if o_start > cursor:
                gaps.append((cursor, o_start))
            cursor = max(cursor, o_end)
            if cursor >= seg_end:
                break
        if cursor < seg_end:
            gaps.append((cursor, seg_end))
        return gaps

    def _segment_duration(segments: list[tuple[float, float]]) -> float:
        return float(sum(end - start for start, end in segments)) if segments else 0.0

    selected_segments: list[tuple[float, float]] = []
    if selected_uw and selected_uw in results:
        selected_df = results[selected_uw]
        if "is_active" in selected_df.columns and "t" in selected_df.columns:
            selected_t = np.asarray(selected_df["t"].values, dtype=float).flatten()
            selected_active = np.asarray(selected_df["is_active"].values, dtype=bool)
            selected_segments = _compute_segments(selected_t, selected_active)

    selected_total = _segment_duration(selected_segments)
    sync_pct_by_uw: dict[str, float] = {}

    max_t = 0.0
    shapes = []  # Build shapes list instead of calling add_shape in loops
    for uw_name in UW_ORDER:
        if uw_name in results:
            df = results[uw_name]
            if df.empty or "t" not in df.columns or "is_active" not in df.columns:
                continue
            y_position = uw_positions[uw_name]
            is_active = np.asarray(df["is_active"].values, dtype=bool)
            t_values = np.asarray(df["t"].values, dtype=float).flatten()
            if t_values.size == 0:
                continue
            max_t = max(max_t, float(t_values.max()))
            uw_color = color_map.get(uw_name, "#00B0F6")
            uw_segments = _compute_segments(t_values, is_active)
            uw_overlap_total = 0.0
            for t_start, t_end in uw_segments:
                if selected_segments:
                    overlaps = []
                    for sel_start, sel_end in selected_segments:
                        overlap_start = max(t_start, sel_start)
                        overlap_end = min(t_end, sel_end)
                        if overlap_end > overlap_start:
                            overlaps.append((overlap_start, overlap_end))
                    overlaps.sort()
                    if overlaps:
                        uw_overlap_total += _segment_duration(overlaps)
                    for seg_start, seg_end in overlaps:
                        shapes.append(dict(type="rect", x0=seg_start, x1=seg_end, y0=y_position - bar_height/2, y1=y_position + bar_height/2, fillcolor=uw_color, opacity=1.0, line=dict(width=0)))
                    for seg_start, seg_end in _subtract_intervals(t_start, t_end, overlaps):
                        shapes.append(dict(type="rect", x0=seg_start, x1=seg_end, y0=y_position - bar_height/2, y1=y_position + bar_height/2, fillcolor=_rgba(uw_color, 0.3), opacity=1.0, line=dict(width=0)))
                else:
                    shapes.append(dict(type="rect", x0=t_start, x1=t_end, y0=y_position - bar_height/2, y1=y_position + bar_height/2, fillcolor=uw_color, opacity=1.0, line=dict(width=0)))
            if selected_segments and selected_total > 0:
                sync_pct_by_uw[uw_name] = (uw_overlap_total / selected_total) * 100.0
    if max_t > 0:
        fig.add_trace(
            go.Scatter(
                x=[0, max_t],
                y=[-1, -1],
                mode="lines",
                line=dict(width=0),
                showlegend=False,
                hoverinfo="skip"
            )
        )
    ticktext = []
    for uw_name in UW_ORDER:
        if selected_segments and selected_total > 0 and uw_name in sync_pct_by_uw:
            ticktext.append(f"{uw_name} (Sync: {sync_pct_by_uw[uw_name]:.1f}%)")
        else:
            ticktext.append(uw_name)

    fig.update_layout(
        template="plotly_dark",
        title="Sync Chart: UWs sync with {}".format(selected_uw if selected_uw else "(None)"),
        xaxis_title="t (seconds)",
        xaxis=dict(range=[0, max_t] if max_t > 0 else None),
        yaxis=dict(tickvals=list(uw_positions.values()), ticktext=ticktext, range=[-0.5, len(UW_ORDER)-0.5]),
        yaxis_title="Ultimate Weapon",
        showlegend=False,
        margin=dict(l=50, r=100, t=50, b=80),
        shapes=shapes  # Batch assign all shapes at once
    )
    return fig

# Now that UW_CONFIG_DF is defined, define UW_ORDER
UW_ORDER = list(UW_CONFIG_DF['name'])


def _get_derived_uw_values() -> Dict[str, Dict[str, float]]:
    """
    Get derived (effective) UW values from DataManager.
    
    Returns a dict mapping weapon name to {"cooldown": value, "duration": value}.
    Falls back to base values from UW_CONFIG if analyzer is unavailable.
    """
    derived_values = {}
    try:
        dm = DataManager.get_instance()
        analyzer = dm.get_analyzer()
        if analyzer:
            for uw_name in UW_ORDER:
                consolidated = analyzer.get_consolidated(uw_name)
                row = UW_CONFIG_DF[UW_CONFIG_DF['name'] == uw_name]
                base_cooldown = float(row['base_cooldown'].values[0]) if not row.empty else 0.0
                base_duration = float(row['base_duration'].values[0]) if not row.empty else 0.0
                derived_values[uw_name] = {
                    "cooldown": _coerce_uw_value(consolidated.get("Cooldown", None), base_cooldown),
                    "duration": _coerce_uw_value(consolidated.get("Duration", None), base_duration),
                }
    except Exception as e:
        # Silently fall back to base values if analyzer fails
        pass
    
    # For any weapons not found in analyzer, use base values
    for uw_name in UW_ORDER:
        if uw_name not in derived_values:
            row = UW_CONFIG_DF[UW_CONFIG_DF['name'] == uw_name]
            if not row.empty:
                derived_values[uw_name] = {
                    "cooldown": float(row['base_cooldown'].values[0]),
                    "duration": float(row['base_duration'].values[0]),
                }
    
    return derived_values


# Global cache for derived values (will be invalidated when data source changes)
_derived_uw_cache_key: Optional[tuple] = None
_derived_uw_cache_data: Dict[str, Dict[str, float]] = {}


def _get_derived_uw_values_cached() -> Dict[str, Dict[str, float]]:
    """
    Get derived values with automatic cache invalidation.
    
    Cache is invalidated when DataManager's load_info changes (indicating new userData).
    This mirrors the pattern used in uw_overview.py.
    """
    global _derived_uw_cache_key, _derived_uw_cache_data
    
    try:
        dm = DataManager.get_instance()
        load_info = dm.get_load_info()
        cache_key = (load_info.get("json_path"), load_info.get("load_timestamp"))
        
        # Check if we need to recompute
        if _derived_uw_cache_data and _derived_uw_cache_key == cache_key:
            return _derived_uw_cache_data
        
        # Cache miss or data changed, recompute
        _derived_uw_cache_data = _get_derived_uw_values()
        _derived_uw_cache_key = cache_key
        return _derived_uw_cache_data
    except Exception:
        # Fallback if load_info unavailable
        if _derived_uw_cache_data:
            return _derived_uw_cache_data
        return _get_derived_uw_values()


# Initialize cache at module load time
_DERIVED_UW_VALUES = _get_derived_uw_values_cached()


dash.register_page(
    __name__,
    path="/perma-calc-hybrid",
    name="UW PermaCalc (Hybrid)",
    order=8,
)


def get_uw_param_ids():
    ids = []
    for _, row in UW_CONFIG_DF.iterrows():
        uw = row['name']
        uw_id = uw.lower().replace(' ', '-')
        ids.append(f"uw-{uw_id}-cooldown")
        ids.append(f"uw-{uw_id}-duration")
    return ids


@callback(
    *(Output(i, "value") for i in get_uw_param_ids()),
    Input("user-json-store", "data"),
)
def refresh_uw_param_defaults(_user_json_store):
    """Refresh UW parameter inputs when Settings imports a new JSON source."""
    derived_values = _get_derived_uw_values_cached()
    values = []
    for _, row in UW_CONFIG_DF.iterrows():
        uw = row["name"]
        derived = derived_values.get(uw, {})
        values.append(_coerce_uw_value(derived.get("cooldown", row["base_cooldown"]), float(row["base_cooldown"])))
        values.append(_coerce_uw_value(derived.get("duration", row["base_duration"]), float(row["base_duration"])))
    return values

# --- Simulation callback ---
@callback(
    Output("uw-hybrid-simulation-store", "data"),
    Input("uw-hybrid-tier-selector", "value"),
    Input("uw-hybrid-wa-card", "value"),
    Input("uw-hybrid-package-after-boss", "value"),
    Input("uw-hybrid-cooldown-bc", "value"),
    Input("uw-hybrid-package-chance", "value"),
    Input("uw-hybrid-galaxy-compressor", "value"),
    Input("uw-hybrid-mvn", "value"),
    Input("uw-hybrid-random-seed", "data"),
    *(Input(i, "value") for i in get_uw_param_ids()),
)

def hybrid_calculate_simulations(
    tier_name, wa_card_level, package_after_boss_state, cooldown_bc_state, pkg_chance_pct, gc_tier, mvn_state,
    random_seed,
    *uw_param_values
):
    # Map UW param values to names
    uw_param_ids = get_uw_param_ids()
    uw_param_map = dict(zip(uw_param_ids, uw_param_values))

    # Get tier information from Tier_DF
    tier_info = get_tier_info(tier_name or fb_default_tier)
    play_mode = tier_info.get("type", fb_default_play_mode)
    boss_waves = tier_info.get("Boss_Waves", fb_default_boss_waves)
    perks_tier_status = tier_info.get("perks", fb_default_perks_status)
    base_wave_cooldown = tier_info.get("wave_cooldown", fb_default_wave_cooldown)
    
    # Apply WA card reduction to tier's base wave cooldown
    wa_reduction = WA_Card.get(wa_card_level, 0.54)
    wave_cooldown = base_wave_cooldown * (1 - wa_reduction)
    wave_time = Wave_Basetime + wave_cooldown

    package_after_boss = package_after_boss_state == "Unlocked"
    bc_cooldown = fb_bc_cooldown_bonus if cooldown_bc_state == "Active" else 0
    gc_bonus = GC_EFFECTS.get(gc_tier, 0.0) if gc_tier else 0.0
    pkg_chance = (pkg_chance_pct or fb_pkg_chance) / 100.0

    # Perks logic: controlled by tier, but can be overridden
    perks_on = perks_tier_status == "active"
    bh_perk_duration = Farming_Perks["Black_Hole_Duration"] if perks_on else 0
    dw_perk_duration = Farming_Perks["Death_Wave_Duration"] if perks_on else 0
    cf_perk_duration = Farming_Perks["Chrono_Field_Duration"] if perks_on else 0

    # Multiverse Nexus
    # Use the dropdown value directly (e.g., "Epic", "Mythic") rather than parsing label text.
    mvn_offset = None
    if mvn_state and mvn_state != "None":
        mvn_offset = MVN_EFFECTS.get(mvn_state, None)

    # Create UW objects
    uws = create_uw_objects()

    # Set effective cooldown/duration for each UW (fix: set per-UW, not via locals)
    for uw in uws:
        uw_id = uw.name.lower().replace(' ', '-')
        cooldown = _coerce_uw_value(uw_param_map.get(f"uw-{uw_id}-cooldown", uw.base_cooldown), uw.base_cooldown)
        duration = _coerce_uw_value(uw_param_map.get(f"uw-{uw_id}-duration", uw.base_duration), uw.base_duration)
        # Apply BC bonus
        cooldown = cooldown + bc_cooldown
        # Apply perks
        if uw.name == "Black Hole":
            duration = duration + bh_perk_duration
        elif uw.name == "Death Wave":
            duration = duration + dw_perk_duration
        elif uw.name == "Chrono Field":
            duration = duration + cf_perk_duration
        # Set effective values directly
        uw.effective_cooldown = cooldown
        uw.effective_duration = duration

    # Apply MVN sync (after all effective_cooldown are set)
    # Only sync if mvn_offset was set (not None)
    if mvn_offset is not None:
        bh = next(u for u in uws if u.name == "Black Hole")
        gt = next(u for u in uws if u.name == "Golden Tower")
        dw = next(u for u in uws if u.name == "Death Wave")
        avg_cooldown = (bh.effective_cooldown + gt.effective_cooldown + dw.effective_cooldown) / 3
        synced_cooldown = avg_cooldown + mvn_offset
        bh.effective_cooldown = synced_cooldown
        gt.effective_cooldown = synced_cooldown
        dw.effective_cooldown = synced_cooldown

    # Simulate package reductions (shared for all UWs)
    reductions, is_boss = simulate_package_reductions(
        total_time=total_time,
        pkg_chance=pkg_chance,
        pkg_reduction=gc_bonus,
        wave_time=wave_time,
        boss_every_x=boss_waves or 10,
        seed=random_seed or 0,
        boss_package_enabled=package_after_boss,
    )

    # Run simulation for each UW
    for uw in uws:
        # Golden Bot and Summon Guardian: no GC bonus
        pkg_red = 0 if uw.name in ["Golden Bot", "Summon Guardian"] else gc_bonus
        pr_series = reductions if pkg_red > 0 else np.zeros(total_time, dtype=float)
        is_boss_arr = np.asarray(is_boss, dtype=bool)
        uw_df = calculate_uw_uptime(
            uw.effective_cooldown,
            uw.effective_duration,
            total_time=total_time,
            return_df=True,
            package_reduction_series=pr_series,
            is_boss_package_series=is_boss_arr,
            wave_time=wave_time,
            can_queue=uw.can_queue,
        )
        # Ensure uw_df is a DataFrame (for Pylance type checking)
        if not isinstance(uw_df, pd.DataFrame):
            uw_df = pd.DataFrame(uw_df)
        uw.set_stats(calculate_uptime_stats(uw_df))
        uw_plot_df = downsample_simulation_df(uw_df, max_points=fb_max_uw_plot_points)
        uw.set_df(uw_plot_df)

    # Prepare serializable results for UI
    results = {}
    for uw in uws:
        results[uw.name] = {
            "params": {
                "base_cooldown": uw.base_cooldown,
                "effective_cooldown": uw.effective_cooldown,
                "base_duration": uw.base_duration,
                "effective_duration": uw.effective_duration,
            },
            "stats": uw.stats,
            "df": uw.df.to_dict('list'),
        }
    return results

# --- Stat card outputs (one Output per stat card) ---
def make_stat_card_outputs():
    outputs = []
    for _, row in UW_CONFIG_DF.iterrows():
        uw = row['name']
        uw_id = uw.lower().replace(' ', '-')
        outputs.extend([
            Output(f'stats-{uw_id}-params', 'children'),
            Output(f'stats-{uw_id}-uptime', 'children'),
            Output(f'stats-{uw_id}-downtime', 'children'),
            Output(f'stats-{uw_id}-interval', 'children'),
            Output(f'stats-{uw_id}-card', 'style'),
        ])
    return outputs

@callback(
    *make_stat_card_outputs(),
    Output("uw-hybrid-detail-graph", "figure"),
    Output("uw-hybrid-graph-sync", "figure"),
    Input("uw-hybrid-simulation-store", "data"),
    Input("uw-hybrid-detail-selector", "value"),
    Input("uw-hybrid-show-cooldown", "value"),
)
def update_all_outputs(sim_data, selected_uw, show_cooldown):
    """Single callback that returns all stat cards + detail graph + sync chart."""
    # Default outputs if no data
    if not sim_data:
        empty_cards = ["", "", "", "", {}] * len(UW_CONFIG_DF)
        empty_fig = go.Figure()
        return empty_cards + [empty_fig, empty_fig]

    def _format_seconds(value: float) -> str:
        if value is None:
            return "N/A"
        try:
            float_val = float(value)
        except (TypeError, ValueError):
            return "N/A"
        if float_val.is_integer():
            return f"{int(float_val)}s"
        return f"{float_val:.1f}s"
    
    # Get UltimateWeapons analyzer from DataManager (Phase 1)
    dm = DataManager.get_instance()
    uw_analyzer = dm.get_analyzer()  # Already cached and thread-safe
    
    # --- Stat cards outputs ---
    card_outputs = []
    for _, row in UW_CONFIG_DF.iterrows():
        uw = row['name']
        uw_id = uw.lower().replace(' ', '-')
        params = sim_data[uw]["params"]
        stats = sim_data[uw]["stats"]
        
        # Get detailed breakdown from UltimateWeapons if available
        # NOTE: Breakdown is not displayed in cards anymore - see UW Overview page for component details
        breakdown_info = ""
        if uw_analyzer:
            try:
                detailed = uw_analyzer.get_detailed(uw)
                # Breakdown calculation kept for reference, but not displayed here
                # Users interested in composition can check the UW Overview page
            except Exception as e:
                pass  # Fall back to default display if analyzer fails
        
        # Format final values only (not the base → effective progression)
        # The input controls now default to derived values, so we only show the effective value
        eff_cd = _format_seconds(params.get('effective_cooldown'))
        eff_dur = _format_seconds(params.get('effective_duration'))
        cd_text = f"CD: {eff_cd}"
        dur_text = f"Dur: {eff_dur}"
        
        params_text = [
            html.Div(
                f"{cd_text} | {dur_text}",
                style={'color': '#999', 'fontSize': '0.85rem', 'marginBottom': '0.25rem'}
            )
        ]
        
        # Format stats
        uptime_text = f"Uptime: {stats['uptime_pct']:.1f}%" if stats['uptime_pct'] is not None else "Uptime: N/A"
        downtime_text = f"Downtime: Avg: {stats['avg_downtime']:.1f}s" if stats['avg_downtime'] is not None else "Downtime: N/A"
        interval_text = f"Activation Interval: {stats['avg_activation_interval']:.1f}s" if stats['avg_activation_interval'] is not None else "Activation Interval: perma"
        card_style = {'borderLeft': f'4px solid {row["color_hex"]}'}
        card_outputs.extend([params_text, uptime_text, downtime_text, interval_text, card_style])
    
    # --- Detail graph ---
    detail_fig = go.Figure()
    if selected_uw and selected_uw in sim_data:
        df_dict = sim_data[selected_uw]["df"]
        df = pd.DataFrame(df_dict)
        uw_row = UW_CONFIG_DF[UW_CONFIG_DF['name'] == selected_uw]
        uw_color = uw_row['color_hex'].values[0] if not uw_row.empty else "#00B0F6"
        show_cd = 'show' in show_cooldown if show_cooldown else False
        detail_fig = _make_uw_figure(df, selected_uw, uw_color, show_cooldown=show_cd)
    
    # --- Sync chart (deserialize once) ---
    results = {uw: pd.DataFrame(sim_data[uw]["df"]) for uw in sim_data if "df" in sim_data[uw]}
    sync_fig = _make_sync_figure(results, selected_uw=selected_uw)
    
    return card_outputs + [detail_fig, sync_fig]


# --- Dynamic UW class ---
@dataclass
class UltimateWeapon:
    name: str
    # Only dynamic fields are stored; all static metadata is always looked up from UW_CONFIG_DF
    effective_cooldown: float = 0.0
    effective_duration: float = 0.0
    stats: Dict[str, Any] = field(default_factory=dict)
    df: pd.DataFrame = field(default_factory=pd.DataFrame)

    @property
    def base_cooldown(self) -> float:
        row = UW_CONFIG_DF[UW_CONFIG_DF['name'] == self.name]
        return float(row['base_cooldown'].values[0]) if not row.empty else 0.0

    @property
    def base_duration(self) -> float:
        row = UW_CONFIG_DF[UW_CONFIG_DF['name'] == self.name]
        return float(row['base_duration'].values[0]) if not row.empty else 0.0

    @property
    def color_hex(self) -> str:
        row = UW_CONFIG_DF[UW_CONFIG_DF['name'] == self.name]
        return str(row['color_hex'].values[0]) if not row.empty else "#00B0F6"

    @property
    def can_queue(self) -> bool:
        row = UW_CONFIG_DF[UW_CONFIG_DF['name'] == self.name]
        return bool(row['can_queue'].values[0]) if not row.empty else False

    def update_effective(self, cooldown, duration):
        self.effective_cooldown = cooldown
        self.effective_duration = duration

    def set_stats(self, stats: Dict[str, Any]):
        self.stats = stats

    def set_df(self, df: pd.DataFrame):
        self.df = df

# --- Utility to create UW objects from config ---
def create_uw_objects():
    return [UltimateWeapon(name=row['name']) for _, row in UW_CONFIG_DF.iterrows()]


# --- Static config and class from above ---
# (UW_CONFIG_DF, UltimateWeapon, create_uw_objects)

# --- Layout (dynamically generated from UW_CONFIG_DF) ---
def make_uw_param_controls():
    controls = []
    # Refresh derived values on each render to pick up newly uploaded userData
    derived_values = _get_derived_uw_values_cached()
    
    for _, row in UW_CONFIG_DF.iterrows():
        uw = row['name']
        # Use derived values from analyzer, falling back to base values if unavailable
        derived = derived_values.get(uw, {})
        cooldown_value = _coerce_uw_value(derived.get("cooldown", row['base_cooldown']), float(row['base_cooldown']))
        duration_value = _coerce_uw_value(derived.get("duration", row['base_duration']), float(row['base_duration']))
        
        controls.append(
            dbc.Col([
                dbc.Label(f"{uw} Cooldown (s)"),
                dbc.Input(id=f"uw-{uw.lower().replace(' ', '-')}-cooldown", type="number", value=cooldown_value, step=1),
            ], width=2)
        )
        controls.append(
            dbc.Col([
                dbc.Label(f"{uw} Duration (s)"),
                dbc.Input(id=f"uw-{uw.lower().replace(' ', '-')}-duration", type="number", value=duration_value, step=1),
            ], width=2)
        )
    return controls

def make_uw_stat_cards():
    cards = []
    for _, row in UW_CONFIG_DF.iterrows():
        uw = row['name']
        uw_id = uw.lower().replace(' ', '-')
        cards.append(
            dbc.Col([
                dbc.Card([dbc.CardBody([
                    html.H6(uw, className='card-title', style={'marginBottom': '0.5rem'}),
                    html.Div(id=f'stats-{uw_id}-params', style={'color': '#6c757d', 'fontSize': '0.8rem', 'marginBottom': '0.5rem'}),
                    html.Div(id=f'stats-{uw_id}-uptime', style={'fontSize': '1rem', 'marginBottom': '0.25rem'}),
                    html.Div(id=f'stats-{uw_id}-downtime', style={'color': '#999', 'fontSize': '0.85rem', 'marginBottom': '0.25rem'}),
                    html.Div(id=f'stats-{uw_id}-interval', style={'color': '#999', 'fontSize': '0.85rem'}),
                ])], id=f'stats-{uw_id}-card', className='mb-2'),
            ], width=12, md=6, lg=4)
        )
    return cards

layout = html.Div([
    html.H1("UW PermaCalc Hybrid", className="page-title"),
    dcc.Store(id="uw-hybrid-simulation-store"),
    dcc.Store(id="uw-hybrid-random-seed", data=0),

    dbc.Card(
        dbc.CardBody([
            html.H4("Global Settings", className="mb-3"),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Tier Selector"),
                    dcc.Dropdown(
                        id="uw-hybrid-tier-selector",
                        options=[{"label": tier_name, "value": tier_name} for tier_name in Tier_DF['name']],
                        value=fb_default_tier, clearable=False),
                ], width=2),
                dbc.Col([
                    dbc.Label("Wave Accelerator Card"),
                    dcc.Dropdown(
                        id="uw-hybrid-wa-card",
                        options=[{"label": s, "value": s} for s in ["None", "1 Star", "2 Star", "3 Star", "4 Star", "5 Star", "6 Star", "7 Star"]],
                        value=fb_wa_card_default, clearable=False),
                ], width=2),
                dbc.Col([
                    dbc.Label("Package After Boss"),
                    dcc.Dropdown(
                        id="uw-hybrid-package-after-boss",
                        options=[{"label": "None", "value": "None"}, {"label": "Unlocked", "value": "Unlocked"}],
                        value=fb_package_after_boss_default, clearable=False),
                ], width=2),
                dbc.Col([
                    dbc.Label("UW Cooldown BC"),
                    dcc.Dropdown(
                        id="uw-hybrid-cooldown-bc",
                        options=[{"label": "Inactive", "value": "Inactive"}, {"label": "Active (+10s)", "value": "Active"}],
                        value=fb_uw_cooldown_bc_default, clearable=False),
                ], width=2),
                dbc.Col([
                    dbc.Label("Package Chance (%)"),
                    dbc.Input(id="uw-hybrid-package-chance", type="number", value=fb_pkg_chance, min=0, max=100, step=1),
                ], width=2),
                dbc.Col([
                    dbc.Label("Galaxy Compressor"),
                    dcc.Dropdown(
                        id="uw-hybrid-galaxy-compressor",
                        options=[
                            {"label": "None", "value": "None"},
                            {"label": "Epic (+10s)", "value": "Epic"},
                            {"label": "Legendary (+13s)", "value": "Legendary"},
                            {"label": "Mythic (+17s)", "value": "Mythic"},
                            {"label": "Ancestral (+20s)", "value": "Ancestral"},
                        ],
                        value=fb_gc_tier_default, clearable=False),
                ], width=2),
            ]),
            dbc.Row([
                dbc.Col([
                    dbc.Label("Multiverse Nexus"),
                    dcc.Dropdown(
                        id="uw-hybrid-mvn",
                        options=[
                            {"label": "None", "value": "None"},
                            {"label": "Epic (+20s)", "value": "Epic"},
                            {"label": "Legendary (+10s)", "value": "Legendary"},
                            {"label": "Mythic (+1s)", "value": "Mythic"},
                            {"label": "Ancestral (-10s)", "value": "Ancestral"},
                        ],
                        value=fb_mvn_default, clearable=False),
                ], width=2),
            ], className="mt-3"),
        ]), className="mb-4"
    ),

    dbc.Card(
        dbc.CardBody([
            html.H4("Tier Information", className="mb-3"),
            dcc.Loading(
                id="tier-info-loading",
                type="default",
                children=html.Div(id="uw-hybrid-tier-info-display")
            ),
        ]), className="mb-4"
    ),

    dbc.Card(
        dbc.CardBody([
            html.H4("UW Parameters", className="mb-3"),
            dbc.Row(make_uw_param_controls()),
        ]), className="mb-4"
    ),

    html.H4("UW Statistics", className="mb-3 mt-4"),
    dbc.Row(make_uw_stat_cards(), className="mb-4"),


    # Display Options, Re-randomize
    dbc.Row([
        dbc.Col([
            html.Label('Display Options:', className='mb-2'),
            dbc.Checklist(
                id='uw-hybrid-show-cooldown',
                options=[{'label': ' Show Cooldown', 'value': 'show'}],
                value=fb_show_cooldown_default,
                switch=True,
                className='mt-4'
            ),
        ], width=12, md=3, lg=2),
        dbc.Col([
            html.Label('Re-randomize Packages:', className='mb-2'),
            dbc.Button(
                "Re-randomize",
                id="uw-hybrid-rerandomize-btn",
                color="primary",
                size="sm",
                className="mt-4"
            ),
        ], width=12, md=2, lg=2),
    ], className="mb-2"),

    # Graphs
    dcc.Dropdown(
        id='uw-hybrid-detail-selector',
        options=[{'label': uw, 'value': uw} for uw in UW_CONFIG_DF['name']],
        value=fb_detail_selector_default,
        clearable=False,
        className='mb-3',
    ),
    dcc.Graph(id="uw-hybrid-detail-graph", config={"displayModeBar": False}, className="mb-4"),

    html.H2("Sync Chart"),
    html.P("E.g., [Golden Tower (Sync: 30%)] means Golden Tower is active 30% of the time when the selected UW is active."),
    dcc.Graph(id="uw-hybrid-graph-sync", config={"displayModeBar": False}),
])

# --- Tier info display callback ---
@callback(
    Output("uw-hybrid-tier-info-display", "children"),
    Input("uw-hybrid-tier-selector", "value"),
)
def update_tier_info_display(tier_name):
    """Update the tier information display card."""
    tier_info = get_tier_info(tier_name or fb_default_tier)
    
    if not tier_info:
        return html.Div("No tier selected")
    
    return dbc.Row([
        dbc.Col([
            html.B("Play Mode:"),
            html.Div(tier_info.get("type", "Unknown"), className="ms-2")
        ], width=6, className="mb-2"),
        dbc.Col([
            html.B("Boss Every X Waves:"),
            html.Div(str(tier_info.get("Boss_Waves", "N/A")), className="ms-2")
        ], width=6, className="mb-2"),
        dbc.Col([
            html.B("Perks:"),
            html.Div(tier_info.get("perks", "Unknown").capitalize(), className="ms-2")
        ], width=6, className="mb-2"),
        dbc.Col([
            html.B("Wave Time:"),
            html.Div(f"{tier_info.get('wave_time', 0):.2f}s", className="ms-2")
        ], width=6, className="mb-2"),
        dbc.Col([
            html.B("Wave Cooldown:"),
            html.Div(f"{tier_info.get('wave_cooldown', 0):.1f}s", className="ms-2")
        ], width=6, className="mb-2"),
    ])


# --- Re-randomize callback (for completeness, but not used in sim yet) ---
@callback(
    Output("uw-hybrid-random-seed", "data"),
    Input("uw-hybrid-rerandomize-btn", "n_clicks"),
    prevent_initial_call=True,
)
def update_random_seed(n_clicks):
    import time
    return int(time.time() * 1000000) % 1000000


