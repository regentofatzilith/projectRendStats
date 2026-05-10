"""Dissonance analysis page."""

import dash
from dash import html, dcc, callback, Input, Output, ALL
import dash_bootstrap_components as dbc
import pandas as pd
import math
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from functions import user_data_store
from functions.analysis import (
    format_dissonance_for_table,
    summarize_dissonance,
    compute_disco_boost_columns,
    build_maxed_disco_columns,
)
from functions.data import build_disco_tier_table, config
from functions.data.disco_import import NOTE_MARKER_ALIASES
from functions.ui import warning_banner


dash.register_page(__name__, path="/dissonance", name="Dissonance", order=2)


layout = html.Div([
    html.H1("Dissonance", className="page-title"),
    html.P("Dissonance overview acccounts for the Dissonance Boost (Disco Boost) and the boost echoing from other Tiers with Disco Boost."),
    html.Ul("- Optimized scenario assumes you can achieve your current max Disco Boost on every Tier easier than the Tier you achieved the max Disco Boost."),
    html.Ul("- Lab Target shows you the effect of your chosen Dissonant Echo lab level compared to your current Disco + Echo boosts."),
    html.H2("Overview"),    
    html.Div(id="dissonance-warning"),
    dbc.Row(id="dissonance-summary", className="mb-3 g-2"),    
    html.Div(id="dissonance-matrix-graph"),
    html.H2("Tabular view"),
    html.P("Target Labs are fetched from the Simulator Card lab level selectors. If no selection is made, current lab levels are used for all calculations."),
    dbc.Row([
        dbc.Col([
            html.Label("Select View / Toggle Display Options:", style={"fontWeight": "600", "marginBottom": "0.35rem"}),
            html.Div([
                dcc.RadioItems(
                    id="dissonance-display-mode",
                    options=[
                        {"label": "Echo Boost per Tier", "value": "echo_per_tier"},
                        {"label": "Disco + Echo Boost", "value": "disco_echo_boost"},
                        {"label": "Match Best Tier Coin Multiplier", "value": "match_best_tier_coin_multiplier"},
                    ],
                    value="disco_echo_boost",
                    labelStyle={"display": "inline-block", "marginRight": "1rem"},
                    inputStyle={"marginRight": "0.35rem"},
                    style={"display": "inline-block", "marginRight": "1rem"},
                ),
                dcc.Checklist(
                    id="dissonance-display-options",
                    options=[
                        {"label": "Target Labs", "value": "target_labs"},
                        {"label": "Disco / +Echo", "value": "show_detail"},
                        {"label": "Optimized Scenario", "value": "optimized_scenario"},
                    ],
                    value=[],
                    labelStyle={"display": "inline-block", "marginRight": "0.75rem"},
                    inputStyle={"marginRight": "0.35rem"},
                    style={"display": "inline-block"},
                ),
            ], style={"display": "flex", "alignItems": "center", "gap": "0.75rem", "flexWrap": "wrap"}),
        ], width=12),
    ], className="mb-2"),
    html.Div(id="dissonance-tier-table"),
    html.Hr(),
    html.H2("Identified Dissonance Runs"),
    html.P([
        "Identification is based on Run Notes in 'UserData.json'. ",
        "Dissonance runs are identified at import based on ",
        html.Strong("\"disco\", \"dissonance\" or \"disso\""),
        " in the run notes (feature available from 2026-04-07 onwards). ",
        "The dissonance type is then determined by ",
        html.Strong("\"attack\", \"defense\", \"utility\", \"uw\" or \"ultimate weapon\""),
        " also found in the notes.",
    ]),
    html.Div(id="dissonance-table"),
])


_DISCO_ECHO_LAB_NAMES = {
    "attack":  "Dissonant Echo - Attack",
    "defense": "Dissonant Echo - Defense",
    "utility": "Dissonant Echo - Utility",
    "uw":      "Dissonant Echo - Ultimate Weapons",
}

_BASE_ECHO_LAB_MULT = 0.005


@callback(
    Output("dissonance-warning", "children"),
    Output("dissonance-summary", "children"),
    Output("dissonance-matrix-graph", "children"),
    Output("dissonance-tier-table", "children"),
    Output("dissonance-table", "children"),
    Input("user-json-store", "data"),
    Input("dissonance-display-mode", "value"),
    Input("dissonance-display-options", "value"),
    Input({"type": "dissonance-optimize-row", "category": ALL}, "value"),
    Input({"type": "dissonance-optimize-row", "category": ALL}, "id"),
    Input({"type": "dissonance-lab-select", "category": ALL, "slot": ALL}, "value"),
    Input({"type": "dissonance-lab-select", "category": ALL, "slot": ALL}, "id"),
)

def update_dissonance(_user_json_state, display_mode, display_option_values, optimize_row_values, optimize_row_ids, lab_select_values, lab_select_ids):
    # Step 1: disco runs are already tagged run_type='disco' in the datastore at import time.
    # Step 2: derive disco_type (attack/defense/utility/uw) from the notes column here.
    # Future tweak: extend NOTE_MARKER_ALIASES in disco_import.py to add more subcategory keywords.
    all_runs_df = user_data_store.cleaned.get("all_runs_time_series_df", pd.DataFrame())

    _EMPTY_COLS = ["timestamp", "tier", "wave", "duration", "waves_per_hour", "comment", "disco_type"]
    if all_runs_df is None or all_runs_df.empty or "run_type" not in all_runs_df.columns:
        df = pd.DataFrame(columns=_EMPTY_COLS)
    else:
        disco_raw = all_runs_df[all_runs_df["run_type"] == "disco"].copy()
        if disco_raw.empty:
            df = pd.DataFrame(columns=_EMPTY_COLS)
        else:
            # Duration string from real_time (numeric hours in the df).
            df = pd.DataFrame()
            df["timestamp"] = disco_raw["timestamp"].fillna("").astype(str)
            df["tier"] = disco_raw["tier"].astype(str)
            df["wave"] = pd.to_numeric(disco_raw.get("wave", disco_raw.get("waves_per_tier", pd.Series(dtype=float))), errors="coerce").fillna(0).astype(int)
            df["waves_per_hour"] = pd.to_numeric(disco_raw["waves_per_hour"], errors="coerce")
            df["duration"] = pd.to_numeric(disco_raw["real_time"], errors="coerce").map(
                lambda x: "" if pd.isna(x) else f"{float(x):.2f}h"
            )

            # Resolve notes column (any of: notes, note, comment).
            _notes_col = next(
                (c for c in disco_raw.columns
                 if "".join(ch for ch in str(c).lower() if ch.isalnum()) in {"notes", "note", "comment"}),
                None,
            )
            df["comment"] = disco_raw[_notes_col].fillna("").astype(str) if _notes_col else ""

            # Derive disco_type from the notes text using the same aliases as disco_import.py.
            def _derive_disco_type(note: str) -> str:
                note_l = str(note).lower()
                labels = [
                    f"{label} disco"
                    for label, aliases in NOTE_MARKER_ALIASES.items()
                    if any(alias in note_l for alias in aliases)
                ]
                return ", ".join(labels)

            df["disco_type"] = df["comment"].map(_derive_disco_type)
            df = df.reset_index(drop=True)

    table_df = format_dissonance_for_table(df)
    tier_table = build_disco_tier_table(df)

    if table_df.empty:
        return (
            warning_banner("No dissonance runs found for the current userData.json."),
            [],
            html.Div("No subplot data available.", style={"color": "#9ca3af"}),
            html.Div("No tier matrix available.", style={"color": "#9ca3af"}),
            html.Div("No rows to display.", style={"color": "#9ca3af"}),
        )

    summary = summarize_dissonance(table_df)
    table_display_df = table_df.copy()
    table_display_df["waves_per_hour"] = pd.to_numeric(
        table_display_df["waves_per_hour"] if "waves_per_hour" in table_display_df.columns else pd.Series(index=table_display_df.index, dtype=float),
        errors="coerce",
    ).map(lambda x: "" if pd.isna(x) else f"{float(x):.2f}")
    table_display_df["disco_5000_waves"] = pd.to_numeric(
        table_display_df["disco_5000_waves"] if "disco_5000_waves" in table_display_df.columns else pd.Series(index=table_display_df.index, dtype=float),
        errors="coerce",
    ).map(lambda x: "" if pd.isna(x) else f"{float(x):.2f}")

    runs_header_style = {
        "background": "#1e1b4b",
        "color": "#c4b5fd",
        "textAlign": "left",
        "border": "1px solid #312e81",
        "padding": "6px 8px",
        "fontWeight": "600",
    }
    runs_cell_style = {
        "border": "1px solid #2d2b50",
        "padding": "4px 8px",
        "color": "#e5e7eb",
        "fontSize": "0.9rem",
    }
    runs_rows = []
    for i, (_, row) in enumerate(table_display_df.reset_index(drop=True).iterrows()):
        bg = "#12111f" if i % 2 == 0 else "#1a1830"
        runs_rows.append(
            html.Tr([
                html.Td(str(row.get(col, "")), style={**runs_cell_style, "background": bg})
                for col in table_display_df.columns
            ])
        )

    table = dbc.Table(
        [
            html.Thead(html.Tr([html.Th(col, style=runs_header_style) for col in table_display_df.columns])),
            html.Tbody(runs_rows),
        ],
        bordered=False,
        size="sm",
        responsive=True,
        style={"borderCollapse": "collapse", "width": "100%"},
    )

    boost_df = compute_disco_boost_columns(tier_table)
    max_df = build_maxed_disco_columns(tier_table)
    merged = tier_table.merge(
        boost_df[[
            "tier",
            "attack_disco_boost",
            "defense_disco_boost",
            "utility_disco_boost",
            "uw_disco_boost",
            "attack_echo_boost",
            "defense_echo_boost",
            "utility_echo_boost",
            "uw_echo_boost",
        ]],
        on="tier",
        how="left",
    )
    merged = merged.merge(max_df, on="tier", how="left")

    # Fetch Dissonant Echo lab levels from userData
    labs_df = user_data_store.get_labs_all()

    def _normalize_lab_name(value: object) -> str:
        txt = str(value or "").strip().lower()
        txt = txt.replace("–", "-").replace("—", "-")
        return " ".join(txt.split())

    def _lab_level(cat: str) -> int:
        target_name = _normalize_lab_name(_DISCO_ECHO_LAB_NAMES[cat])

        if not labs_df.empty and "name" in labs_df.columns:
            names_norm = labs_df["name"].map(_normalize_lab_name)
            exact_match = labs_df[names_norm == target_name]
            if not exact_match.empty:
                levels = pd.to_numeric(exact_match.get("level", pd.Series(dtype=float)), errors="coerce").dropna()
                if not levels.empty:
                    return int(levels.max())

            # Fallback: tolerant match by category keyword for data variants.
            keyword = "ultimate" if cat == "uw" else cat
            keyword_match = labs_df[names_norm.str.contains("dissonant echo", na=False) & names_norm.str.contains(keyword, na=False)]
            if not keyword_match.empty:
                levels = pd.to_numeric(keyword_match.get("level", pd.Series(dtype=float)), errors="coerce").dropna()
                if not levels.empty:
                    return int(levels.max())

        # Last resort: read directly from raw JSON so level lookup is robust to extraction-format changes.
        full_json = getattr(user_data_store, "full_json", {})
        labs_progress = full_json.get("labsProgress", {}) if isinstance(full_json, dict) else {}
        labs_raw = labs_progress.get("labs", {}) if isinstance(labs_progress, dict) else {}
        if isinstance(labs_raw, dict):
            lab_items = list(labs_raw.values())
        elif isinstance(labs_raw, list):
            lab_items = labs_raw
        else:
            lab_items = []

        max_level = None
        for item in lab_items:
            if not isinstance(item, dict):
                continue
            item_name = _normalize_lab_name(item.get("name", ""))
            if item_name != target_name:
                continue
            raw_level = item.get("level", 0)
            lvl_num = pd.to_numeric(pd.Series([raw_level]), errors="coerce").iloc[0]
            if pd.isna(lvl_num):
                continue
            lvl_int = int(float(lvl_num))
            max_level = lvl_int if max_level is None else max(max_level, lvl_int)

        if max_level is not None:
            return max_level

        raw = 0
        try:
            return int(raw) if raw is not None else 0
        except (ValueError, TypeError):
            return 0

    def _echo_sum(frame: pd.DataFrame, col: str) -> float:
        if frame is None or frame.empty or col not in frame.columns:
            return 0.0
        return float(pd.to_numeric(frame[col], errors="coerce").fillna(0.0).sum())

    def _lab_echo_multiplier(lab_level: int) -> float:
        return (int(lab_level) + 1) * _BASE_ECHO_LAB_MULT

    def _scale_echo_by_lab(echo_val: float, lab_level: int) -> float:
        # compute_*_echo_boost values are based on lab-0 multiplier (0.5%).
        current_mult = _lab_echo_multiplier(lab_level)
        if _BASE_ECHO_LAB_MULT <= 0:
            return float(echo_val)
        return float(echo_val) * (float(current_mult) / float(_BASE_ECHO_LAB_MULT))

    def _lab_plus_one_echo(echo_val: float, lab_level: int) -> float:
        # Next-level total echo from current total echo and current lab level.
        current_mult = _lab_echo_multiplier(lab_level)
        next_mult = _lab_echo_multiplier(int(lab_level) + 1)
        if current_mult <= 0:
            return float(echo_val)
        return float(echo_val) / float(current_mult) * float(next_mult)

    category_labels = {
        "attack": "Attack",
        "defense": "Defense",
        "utility": "Utility",
        "uw": "UW",
    }
    display_options = {str(v).lower() for v in list(display_option_values or [])}
    tab_use_target_labs = "target_labs" in display_options
    show_detail = "show_detail" in display_options
    tab_use_optimized_scenario = "optimized_scenario" in display_options

    current_lab_levels = {cat: _lab_level(cat) for cat in ["attack", "defense", "utility", "uw"]}
    selected_lab_levels = dict(current_lab_levels)
    id_list = list(lab_select_ids or [])
    value_list = list(lab_select_values or [])
    for comp_id, comp_val in zip(id_list, value_list):
        if not isinstance(comp_id, dict):
            continue
        comp_cat = str(comp_id.get("category", "")).lower()
        comp_slot = str(comp_id.get("slot", "primary")).lower()
        lvl_num = pd.to_numeric(pd.Series([comp_val]), errors="coerce").iloc[0]
        if pd.isna(lvl_num):
            continue
        lvl_int = max(0, int(float(lvl_num)))
        if comp_cat in selected_lab_levels and comp_slot == "primary":
            selected_lab_levels[comp_cat] = lvl_int

    # Simulator and overview charts always use the selected target labs.
    effective_lab_levels = selected_lab_levels

    def _echo_at_lab(echo_at_current_lab: float, current_lab_level: int, target_lab_level: int) -> float:
        current_mult = _lab_echo_multiplier(current_lab_level)
        target_mult = _lab_echo_multiplier(target_lab_level)
        if current_mult <= 0:
            return float(echo_at_current_lab)
        return float(echo_at_current_lab) * (float(target_mult) / float(current_mult))

    optimized_cats = {"attack", "uw", "defense", "utility"}
    for comp_id, comp_val in zip(list(optimize_row_ids or []), list(optimize_row_values or [])):
        if not isinstance(comp_id, dict):
            continue
        comp_cat = str(comp_id.get("category", "")).lower()
        if comp_cat not in {"attack", "uw", "defense", "utility"}:
            continue
        values = {str(v).lower() for v in list(comp_val or [])}
        if "enabled" in values:
            optimized_cats.add(comp_cat)
        else:
            optimized_cats.discard(comp_cat)

    category_metrics = {}
    for cat in ["attack", "defense", "utility", "uw"]:
        current_lab_lvl = int(current_lab_levels.get(cat, 0))
        lab_lvl = int(effective_lab_levels.get(cat, current_lab_lvl))
        lab_echo_pct = _lab_echo_multiplier(lab_lvl)
        current_echo_raw = _echo_sum(boost_df, f"{cat}_echo_boost")
        maxed_echo_raw = _echo_sum(max_df, f"max_{cat}_echo_boost")
        current_echo_at_current_lab = _scale_echo_by_lab(current_echo_raw, current_lab_lvl)
        maxed_echo_at_current_lab = _scale_echo_by_lab(maxed_echo_raw, current_lab_lvl)
        current_echo = _echo_at_lab(current_echo_at_current_lab, current_lab_lvl, lab_lvl)
        maxed_echo_candidate = _echo_at_lab(maxed_echo_at_current_lab, current_lab_lvl, lab_lvl)
        optimized_enabled = cat in optimized_cats
        maxed_echo = maxed_echo_candidate if optimized_enabled else current_echo
        baseline_maxed_echo = maxed_echo_at_current_lab if optimized_enabled else current_echo_at_current_lab
        category_metrics[cat] = {
            "runs": int(summary.get(cat, 0)),
            "current_echo": current_echo,
            "maxed_echo": maxed_echo,
            "baseline_current_echo": current_echo_at_current_lab,
            "baseline_maxed_echo": baseline_maxed_echo,
            "current_echo_lab1": _lab_plus_one_echo(current_echo, lab_lvl),
            "maxed_echo_lab1": _lab_plus_one_echo(maxed_echo, lab_lvl),
            "lab_level": lab_lvl,
            "selected_lab_level": int(selected_lab_levels.get(cat, current_lab_lvl)),
            "current_lab_level": current_lab_lvl,
            "lab_echo_pct": lab_echo_pct,
            "optimized_enabled": optimized_enabled,
        }

    def _cap_for_category(cat: str) -> float:
        return 3.0 if cat == "utility" else 5.0

    def _mean_5000h_for_category(cat: str) -> float | None:
        if table_df.empty or "disco_type" not in table_df.columns:
            return None
        disco_series = table_df["disco_type"].astype(str).str.lower()
        if cat == "uw":
            mask = disco_series.str.contains("uw") | disco_series.str.contains("ultimate")
        else:
            mask = disco_series.str.contains(cat)
        vals = pd.to_numeric(
            table_df.loc[mask, "disco_5000_waves"] if "disco_5000_waves" in table_df.columns else pd.Series(dtype=float),
            errors="coerce",
        )
        if vals.empty or vals.notna().sum() == 0:
            return None
        return float(vals.mean())

    # Combined UW boost in echo-space: (1 + atk_echo) * (1 + uw_echo) - 1.
    atk = category_metrics["attack"]
    uw = category_metrics["uw"]
    baseline_combined_current = (1.0 + float(atk.get("baseline_current_echo", 0.0))) * (1.0 + float(uw.get("baseline_current_echo", 0.0))) - 1.0
    combined_current = (1.0 + atk["current_echo"]) * (1.0 + uw["current_echo"]) - 1.0
    combined_current_l1 = (1.0 + atk["current_echo_lab1"]) * (1.0 + uw["current_echo_lab1"]) - 1.0
    combined_maxed = (1.0 + atk["maxed_echo"]) * (1.0 + uw["maxed_echo"]) - 1.0
    combined_maxed_l1 = (1.0 + atk["maxed_echo_lab1"]) * (1.0 + uw["maxed_echo_lab1"]) - 1.0

    # Best farming tier among tiers that actually have a utility disco run.
    coin_multiplier_by_tier = {}
    for tier_name, meta in config.TIER_CONFIG.items():
        if str(meta.get("type", "")).lower() != "farming":
            continue
        try:
            tier_num = int(str(tier_name).split(" ", 1)[1])
        except Exception:
            continue
        coin_multiplier_by_tier[f"{tier_num:02d}"] = float(meta.get("coin_multiplier", 0.0) or 0.0)

    utility_tiers = tier_table.copy()
    utility_tiers["utility_num"] = pd.to_numeric(
        utility_tiers["utility"] if "utility" in utility_tiers.columns else pd.Series(index=utility_tiers.index, dtype=float),
        errors="coerce",
    )
    utility_tiers = utility_tiers[utility_tiers["utility_num"].fillna(0) > 0].copy()
    utility_tiers["tier"] = utility_tiers["tier"].astype(str)
    utility_tiers["tier_coin_multiplier"] = utility_tiers["tier"].map(coin_multiplier_by_tier).fillna(0.0)

    best_tier_label = "N/A"
    tier_coin_mult = 0.0
    utility_disco_current = 1.0
    utility_disco_maxed = 1.0
    current_boosted_coin_mult = 0.0
    optimized_boosted_coin_mult = 0.0
    current_boosted_coin_mult_lab1 = 0.0
    optimized_boosted_coin_mult_lab1 = 0.0
    coin_increase_pct = 0.0

    utility_lab_lvl = int(category_metrics["utility"]["lab_level"])
    utility_echo_current = float(category_metrics["utility"]["current_echo"])
    utility_echo_maxed = float(category_metrics["utility"]["maxed_echo"])
    utility_echo_current_l1 = float(category_metrics["utility"]["current_echo_lab1"])
    utility_echo_maxed_l1 = float(category_metrics["utility"]["maxed_echo_lab1"])
    utility_match_by_tier = {}

    def _row_num(row: pd.Series, key: str, default: float) -> float:
        return float(pd.to_numeric(pd.Series([row.get(key)]), errors="coerce").fillna(default).iloc[0])

    def _utility_match_metrics(merged_row: pd.Series) -> dict:
        tier_code = str(merged_row.get("tier", ""))
        tier_mult = float(coin_multiplier_by_tier.get(tier_code, 0.0) or 0.0)
        wave_cur = int(_row_num(merged_row, "utility", 0.0))
        disco_cur = _row_num(merged_row, "utility_disco_boost", 1.0)
        disco_max = _row_num(merged_row, "max_utility_disco_boost", 1.0)

        tier_echo_cur = _scale_echo_by_lab(_row_num(merged_row, "utility_echo_boost", 0.0), utility_lab_lvl)
        tier_echo_max = _scale_echo_by_lab(_row_num(merged_row, "max_utility_echo_boost", 0.0), utility_lab_lvl)
        tier_echo_cur_l1 = _lab_plus_one_echo(tier_echo_cur, utility_lab_lvl)
        tier_echo_max_l1 = _lab_plus_one_echo(tier_echo_max, utility_lab_lvl)

        eff_echo_cur = max(0.0, utility_echo_current - tier_echo_cur)
        eff_echo_cur_l1 = max(0.0, utility_echo_current_l1 - tier_echo_cur_l1)
        eff_echo_max = max(0.0, utility_echo_maxed - tier_echo_max)
        eff_echo_max_l1 = max(0.0, utility_echo_maxed_l1 - tier_echo_max_l1)

        total_boost_cur = disco_cur + eff_echo_cur
        total_boost_cur_l1 = disco_cur + eff_echo_cur_l1
        total_boost_max = disco_max + eff_echo_max
        total_boost_max_l1 = disco_max + eff_echo_max_l1

        return {
            "tier": tier_code,
            "tier_mult": tier_mult,
            "wave_cur": wave_cur,
            "disco_cur": disco_cur,
            "disco_max": disco_max,
            "tier_echo_cur": tier_echo_cur,
            "tier_echo_cur_l1": tier_echo_cur_l1,
            "eff_echo_cur": eff_echo_cur,
            "eff_echo_cur_l1": eff_echo_cur_l1,
            "eff_echo_max": eff_echo_max,
            "eff_echo_max_l1": eff_echo_max_l1,
            "total_boost_cur": total_boost_cur,
            "total_boost_cur_l1": total_boost_cur_l1,
            "total_boost_max": total_boost_max,
            "total_boost_max_l1": total_boost_max_l1,
            "cur_total_mult": total_boost_cur * tier_mult,
            "cur_total_mult_l1": total_boost_cur_l1 * tier_mult,
            "opt_total_mult": total_boost_max * tier_mult,
            "opt_total_mult_l1": total_boost_max_l1 * tier_mult,
        }

    for _, merged_row in merged.iterrows():
        tier_code = str(merged_row.get("tier", ""))
        utility_match_by_tier[tier_code] = _utility_match_metrics(merged_row)

    if not utility_tiers.empty:
        candidates = []
        for _, cand in utility_tiers.iterrows():
            tier_code = str(cand.get("tier", ""))
            metrics = utility_match_by_tier.get(tier_code)
            if not metrics:
                continue
            tier_num = pd.to_numeric(tier_code, errors="coerce")

            candidates.append({
                "tier": tier_code,
                "tier_num": float(tier_num) if pd.notna(tier_num) else -1.0,
                "tier_mult": float(metrics["tier_mult"]),
                "disco_cur": float(metrics["disco_cur"]),
                "disco_max": float(metrics["disco_max"]),
                "cur_total_mult": float(metrics["cur_total_mult"]),
                "cur_total_mult_l1": float(metrics["cur_total_mult_l1"]),
                "opt_total_mult": float(metrics["opt_total_mult"]),
                "opt_total_mult_l1": float(metrics["opt_total_mult_l1"]),
            })

        if candidates:
            best = max(candidates, key=lambda x: (x["cur_total_mult"], x["tier_num"]))
            best_tier_label = f"T{int(best['tier_num'])}" if best["tier_num"] >= 0 else str(best["tier"])
            tier_coin_mult = float(best["tier_mult"])
            utility_disco_current = float(best["disco_cur"])
            utility_disco_maxed = float(best["disco_max"])
            current_boosted_coin_mult = float(best["cur_total_mult"])
            current_boosted_coin_mult_lab1 = float(best["cur_total_mult_l1"])
            optimized_boosted_coin_mult = float(best["opt_total_mult"])
            optimized_boosted_coin_mult_lab1 = float(best["opt_total_mult_l1"])
            if current_boosted_coin_mult > 0:
                coin_increase_pct = (optimized_boosted_coin_mult / current_boosted_coin_mult - 1.0) * 100.0

    total_tiers = int(len(tier_table.index))
    category_card_stats = {}
    optimization_progress_by_cat = {}
    for cat in ["attack", "defense", "utility", "uw"]:
        cap = _cap_for_category(cat)
        cur_wave_col = cat
        cur_disco_col = f"{cat}_disco_boost"
        max_wave_col = f"max_{cat}_wave"
        max_disco_col = f"max_{cat}_disco_boost"

        cur_wave = pd.to_numeric(
            merged[cur_wave_col] if cur_wave_col in merged.columns else pd.Series(index=merged.index, dtype=float),
            errors="coerce",
        ).fillna(0.0)
        cur_disco = pd.to_numeric(
            merged[cur_disco_col] if cur_disco_col in merged.columns else pd.Series(index=merged.index, dtype=float),
            errors="coerce",
        ).fillna(1.0)
        max_wave = pd.to_numeric(
            merged[max_wave_col] if max_wave_col in merged.columns else pd.Series(index=merged.index, dtype=float),
            errors="coerce",
        ).fillna(0.0)
        max_disco = pd.to_numeric(
            merged[max_disco_col] if max_disco_col in merged.columns else pd.Series(index=merged.index, dtype=float),
            errors="coerce",
        ).fillna(1.0)

        maxed_runs = int(((cur_wave > 0) & (cur_disco >= (cap - 0.005))).sum())
        optimized_runs = int(((max_wave > 0) & (max_disco >= (cap - 0.005))).sum())
        avg_5000_h = _mean_5000h_for_category(cat)

        category_card_stats[cat] = {
            "maxed_runs": maxed_runs,
            "optimized_runs": optimized_runs,
            "avg_5000_h": avg_5000_h,
        }

        # Optimization progress is parity against the optimized highest disco multiplier.
        # Example: if optimized highest is set on tiers 1..12, progress is current tiers at that same
        # multiplier over 12 (e.g., 1/12), even when the multiplier is below absolute cap.
        opt_disco = max_disco.copy()
        cur_disco_for_progress = cur_disco.copy()
        highest_opt_disco = float(opt_disco.max()) if not opt_disco.empty else 1.0
        eps = 1e-9
        if highest_opt_disco <= (1.0 + eps):
            optimization_progress_by_cat[cat] = {"current": 0, "target": 0}
        else:
            target_tiers = int((opt_disco >= (highest_opt_disco - eps)).sum())
            current_tiers = int((cur_disco_for_progress >= (highest_opt_disco - eps)).sum())
            optimization_progress_by_cat[cat] = {
                "current": current_tiers,
                "target": target_tiers,
            }

    combined_maxed_runs = int(category_card_stats["attack"]["maxed_runs"] + category_card_stats["uw"]["maxed_runs"])
    combined_optimized_runs = int(category_card_stats["attack"]["optimized_runs"] + category_card_stats["uw"]["optimized_runs"])
    combined_total_tiers = total_tiers * 2

    attack_uw_mask = pd.Series(False, index=table_df.index)
    if "disco_type" in table_df.columns:
        dtypes = table_df["disco_type"].astype(str).str.lower()
        attack_uw_mask = dtypes.str.contains("attack") | dtypes.str.contains("uw") | dtypes.str.contains("ultimate")
    combined_avg_5000 = pd.to_numeric(
        table_df.loc[attack_uw_mask, "disco_5000_waves"] if "disco_5000_waves" in table_df.columns else pd.Series(dtype=float),
        errors="coerce",
    )
    combined_avg_5000_h = float(combined_avg_5000.mean()) if not combined_avg_5000.empty and combined_avg_5000.notna().sum() > 0 else None

    utility_lab1_echo_pct = ((utility_lab_lvl + 2) * 0.5)

    summary_cards = []

    def _fmt_hours(val: float | None) -> str:
        return f"{val:.2f} h" if val is not None else "n/a"

    def _fmt_tourney(echo_val: float) -> str:
        return f"x{(1.0 + float(echo_val)):.3f}"

    def _fmt_pct_delta(new_val: float, old_val: float) -> str:
        old = float(old_val)
        if old <= 0:
            return "(n/a)"
        pct = (float(new_val) / old - 1.0) * 100.0
        return f"({pct:+.0f}%)"

    def _best_current_disco(cat: str) -> float:
        col = f"{cat}_disco_boost"
        vals = pd.to_numeric(
            merged[col] if col in merged.columns else pd.Series(index=merged.index, dtype=float),
            errors="coerce",
        ).fillna(1.0)
        return float(vals.max()) if not vals.empty else 1.0

    def _delta_aware_cell(text: str):
        s = str(text or "")
        idx = s.rfind(" (")
        if idx > 0 and s.endswith(")"):
            return [
                html.Span(s[:idx], style={"color": "#e7e7e7"}),
                html.Span(s[idx:], style={"color": "#9ca3af"}),
            ]
        return s

    card_style = {
        "background": "#565656",
        "border": "2px solid #9ca3af",
        "borderRadius": "26px",
        "height": "100%",
    }
    card_body_style = {"padding": "1rem 1.3rem"}
    title_style = {"fontSize": "1.95rem", "fontWeight": "700", "color": "#e7e7e7", "marginBottom": "0.9rem"}
    section_title_style = {"fontSize": "1.05rem", "fontWeight": "600", "color": "#e7e7e7", "marginBottom": "0.45rem"}
    table_style = {"width": "100%", "marginTop": "0.25rem", "marginBottom": "0", "borderCollapse": "collapse"}
    key_style = {"color": "#e7e7e7", "padding": "0.05rem 0.5rem 0.05rem 0", "whiteSpace": "nowrap", "fontWeight": "500"}
    val_style = {"color": "#e7e7e7", "padding": "0.05rem 0.75rem 0.05rem 0", "whiteSpace": "nowrap"}
    accent_style = {"color": "#ffca2b", "fontWeight": "700"}
    lab_select_style = {
        "minWidth": "7.5rem",
        "color": "#0f172a",
        "fontSize": "0.85rem",
    }

    current_echo_rows = [
        ("Attack:", f"+{category_metrics['attack']['current_echo']:.3f}", _fmt_tourney(category_metrics["attack"]["current_echo"])),
        ("UW:", f"+{category_metrics['uw']['current_echo']:.3f}", _fmt_tourney(category_metrics["uw"]["current_echo"])),
        ("Atk x UW:", f"+{combined_current:.3f}", _fmt_tourney(combined_current)),
        ("Defense:", f"+{category_metrics['defense']['current_echo']:.3f}", _fmt_tourney(category_metrics["defense"]["current_echo"])),
        ("Utility:", f"+{category_metrics['utility']['current_echo']:.3f}", _fmt_tourney(category_metrics["utility"]["current_echo"])),
    ]

    progress_rows = [
        ("Attack:", f"{category_card_stats['attack']['maxed_runs']}/{total_tiers} ({(category_card_stats['attack']['maxed_runs'] / max(total_tiers, 1) * 100):.0f}%)"),
        ("UW:", f"{category_card_stats['uw']['maxed_runs']}/{total_tiers} ({(category_card_stats['uw']['maxed_runs'] / max(total_tiers, 1) * 100):.0f}%)"),
        ("Defense:", f"{category_card_stats['defense']['maxed_runs']}/{total_tiers} ({(category_card_stats['defense']['maxed_runs'] / max(total_tiers, 1) * 100):.0f}%)"),
        ("Utility:", f"{category_card_stats['utility']['maxed_runs']}/{total_tiers} ({(category_card_stats['utility']['maxed_runs'] / max(total_tiers, 1) * 100):.0f}%)"),
    ]

    duration_rows = [
        ("Attack:", _fmt_hours(category_card_stats["attack"]["avg_5000_h"])),
        ("UW:", _fmt_hours(category_card_stats["uw"]["avg_5000_h"])),
        ("Defense:", _fmt_hours(category_card_stats["defense"]["avg_5000_h"])),
        ("Utility:", _fmt_hours(category_card_stats["utility"]["avg_5000_h"])),
    ]

    _LAB_MAX_LEVEL = 100

    def _lab_selector(category: str, slot: str, value: int) -> dcc.Dropdown:
        return dcc.Dropdown(
            id={"type": "dissonance-lab-select", "category": category, "slot": slot},
            options=tuple(range(_LAB_MAX_LEVEL + 1)),
            value=max(0, int(value)),
            clearable=False,
            searchable=False,
            style=lab_select_style,
        )

    def _optimize_selector(category: str, enabled: bool) -> dcc.Checklist:
        return dcc.Checklist(
            id={"type": "dissonance-optimize-row", "category": category},
            options=[{"label": "", "value": "enabled"}],
            value=["enabled"] if enabled else [],
            inputStyle={"marginRight": "0"},
            style={"display": "inline-block", "margin": "0"},
        )

    def _fmt_max_disco_echo(cat: str) -> str:
        best_disco = _best_current_disco(cat)
        baseline_total = best_disco + float(category_metrics[cat]["baseline_current_echo"])
        max_total = best_disco + float(category_metrics[cat]["maxed_echo"])
        return f"x{max_total:.3f}  {_fmt_pct_delta(max_total, baseline_total)}"

    def _progress_label(cat: str) -> str:
        if not bool(category_metrics.get(cat, {}).get("optimized_enabled", False)):
            return "off"
        return f"{optimization_progress_by_cat[cat]['current']}/{optimization_progress_by_cat[cat]['target']}"

    optimization_rows = [
        (
            "Attack:",
            f"x{_best_current_disco('attack'):.3f}",
            _progress_label("attack"),
            f"+{category_metrics['attack']['maxed_echo']:.3f}  {_fmt_pct_delta(category_metrics['attack']['maxed_echo'], category_metrics['attack']['baseline_current_echo'])}",
            f"{_fmt_tourney(category_metrics['attack']['maxed_echo'])}  {_fmt_pct_delta(1.0 + category_metrics['attack']['maxed_echo'], 1.0 + category_metrics['attack']['baseline_current_echo'])}",
            _fmt_max_disco_echo("attack"),
            _optimize_selector("attack", bool(category_metrics["attack"]["optimized_enabled"])),
            _lab_selector("attack", "primary", category_metrics["attack"]["selected_lab_level"]),
        ),
        (
            "UW:",
            f"x{_best_current_disco('uw'):.3f}",
            _progress_label("uw"),
            f"+{category_metrics['uw']['maxed_echo']:.3f}  {_fmt_pct_delta(category_metrics['uw']['maxed_echo'], category_metrics['uw']['baseline_current_echo'])}",
            f"{_fmt_tourney(category_metrics['uw']['maxed_echo'])}  {_fmt_pct_delta(1.0 + category_metrics['uw']['maxed_echo'], 1.0 + category_metrics['uw']['baseline_current_echo'])}",
            _fmt_max_disco_echo("uw"),
            _optimize_selector("uw", bool(category_metrics["uw"]["optimized_enabled"])),
            _lab_selector("uw", "primary", category_metrics["uw"]["selected_lab_level"]),
        ),
        (
            "Atk x UW:",
            "---",
            "---",
            f"+{combined_maxed:.3f}  {_fmt_pct_delta(combined_maxed, baseline_combined_current)}",
            f"{_fmt_tourney(combined_maxed)}  {_fmt_pct_delta(1.0 + combined_maxed, 1.0 + baseline_combined_current)}",
            "---",
            html.Span("via Attack + UW", style={"color": "#9ca3af", "fontSize": "0.85rem"}),
            html.Span("uses Attack + UW lab targets", style={"color": "#9ca3af", "fontSize": "0.85rem"}),
        ),
        (
            "Defense:",
            f"x{_best_current_disco('defense'):.3f}",
            _progress_label("defense"),
            f"+{category_metrics['defense']['maxed_echo']:.3f}  {_fmt_pct_delta(category_metrics['defense']['maxed_echo'], category_metrics['defense']['baseline_current_echo'])}",
            f"{_fmt_tourney(category_metrics['defense']['maxed_echo'])}  {_fmt_pct_delta(1.0 + category_metrics['defense']['maxed_echo'], 1.0 + category_metrics['defense']['baseline_current_echo'])}",
            _fmt_max_disco_echo("defense"),
            _optimize_selector("defense", bool(category_metrics["defense"]["optimized_enabled"])),
            _lab_selector("defense", "primary", category_metrics["defense"]["selected_lab_level"]),
        ),
        (
            "Utility:",
            f"x{_best_current_disco('utility'):.3f}",
            _progress_label("utility"),
            f"+{category_metrics['utility']['maxed_echo']:.3f}  {_fmt_pct_delta(category_metrics['utility']['maxed_echo'], category_metrics['utility']['baseline_current_echo'])}",
            f"{_fmt_tourney(category_metrics['utility']['maxed_echo'])}  {_fmt_pct_delta(1.0 + category_metrics['utility']['maxed_echo'], 1.0 + category_metrics['utility']['baseline_current_echo'])}",
            _fmt_max_disco_echo("utility"),
            _optimize_selector("utility", bool(category_metrics["utility"]["optimized_enabled"])),
            _lab_selector("utility", "primary", category_metrics["utility"]["selected_lab_level"]),
        ),
    ]

    summary_cards.extend([
        dbc.Col(
            dbc.Card(dbc.CardBody([
                html.Div("Current Echo Boosts", style=title_style),
                html.Table([
                    html.Thead(html.Tr([
                        html.Th("", style=key_style),
                        html.Th("Echo", style=section_title_style),
                        html.Th("Tournament Multiplier", style=section_title_style),
                    ])),
                    html.Tbody([
                        html.Tr([
                            html.Td(lbl, style=key_style),
                            html.Td(echo, style=val_style),
                            html.Td(mult, style=val_style),
                        ])
                        for lbl, echo, mult in current_echo_rows
                    ]),
                ], style=table_style),
            ], style=card_body_style), style=card_style),
            width=12,
            lg=4,
        ),
        dbc.Col(
            dbc.Card(dbc.CardBody([
                html.Div("Progress", style=title_style),
                html.Div("Maxed Dissonance Tiers:", style={"color": "#e7e7e7", "fontSize": "1.05rem", "marginBottom": "0.25rem"}),
                html.Table(
                    html.Tbody([
                        html.Tr([
                            html.Td(lbl, style=key_style),
                            html.Td(_delta_aware_cell(val), style=val_style),
                        ])
                        for lbl, val in progress_rows
                    ]),
                    style=table_style,
                ),
                html.Div(f"Best Coin Multiplier: {best_tier_label}", style={**accent_style, "fontSize": "1.55rem", "marginTop": "0.8rem"}),
            ], style=card_body_style), style=card_style),
            width=12,
            lg=4,
        ),
        dbc.Col(
            dbc.Card(dbc.CardBody([
                html.Div("Duration", style=title_style),
                html.Div("Avg. 5000 Wave Duration", style={"color": "#e7e7e7", "fontSize": "1.05rem", "marginBottom": "0.35rem"}),
                html.Table(
                    html.Tbody([
                        html.Tr([
                            html.Td(lbl, style=key_style),
                            html.Td(val, style=val_style),
                        ])
                        for lbl, val in duration_rows
                    ]),
                    style=table_style,
                ),
            ], style=card_body_style), style=card_style),
            width=12,
            lg=4,
        ),
        dbc.Col(
            dbc.Card(dbc.CardBody([
                html.Div("Simulator (Echo Boost, Lab Target)", style=title_style),
                html.Div("Optimize Echo Boost: All easier Tiers maxed to current best Disco Boost.", style={"color": "#e7e7e7", "fontSize": "1rem", "marginBottom": "0.25rem"}),
                html.Div("Lab Target: Simulate the impact of Echo Labs.", style={"color": "#e7e7e7", "fontSize": "1rem", "marginBottom": "0.35rem"}),
                html.Table([
                    html.Thead(html.Tr([
                        html.Th("", style=key_style),
                        html.Th("Max. Disco Boost", style=section_title_style),
                        html.Th("Progress", style=section_title_style),
                        html.Th("Echo Boost", style=section_title_style),
                        html.Th("Tourney Mult", style=section_title_style),
                        html.Th("Max. Disco + Echo Boost", style=section_title_style),
                        html.Th("Optimize", style=section_title_style),
                        html.Th("Lab Target", style=section_title_style),
                    ])),
                    html.Tbody([
                        html.Tr([
                            html.Td(lbl, style=key_style),
                            html.Td(max_disco, style={**val_style, **(accent_style if lbl in {"Attack:", "Utility:"} else {})}),
                            html.Td(progress, style=val_style),
                            html.Td(_delta_aware_cell(opt_echo), style=val_style),
                            html.Td(_delta_aware_cell(opt_mult), style=val_style),
                            html.Td(_delta_aware_cell(max_disco_echo), style=val_style),
                            html.Td(optimize_toggle, style=val_style),
                            html.Td(lab_target, style=val_style),
                        ])
                        for lbl, max_disco, progress, opt_echo, opt_mult, max_disco_echo, optimize_toggle, lab_target in optimization_rows
                    ]),
                ], style=table_style),
            ], style=card_body_style), style=card_style),
            width=12,
            lg=12,
        ),
    ])

    def _to_tier_code(value: object) -> str:
        raw = str(value or "").strip().lower().replace("tier", "").replace("t", "")
        num = pd.to_numeric(pd.Series([raw]), errors="coerce").iloc[0]
        if pd.isna(num):
            return ""
        return f"{int(float(num)):02d}"

    def _match_wave_from_disco(disco_val: float) -> int:
        d = float(disco_val)
        if d <= 1.0:
            return 0
        if d >= 3.0:
            return 5000
        wave_est = 5000.0 * (((d - 1.0) / (3.0 - 1.0)) ** (1.0 / 1.75))
        return int(math.ceil(wave_est))

    def _solve_match_iteration(
        *,
        target_best_coin_mult: float,
        tier_mult: float,
        other_echo: float,
        source_disco_current: float,
        is_best_tier: bool,
        best_tier_mult: float,
        lab_mult: float,
    ) -> dict:
        result = {
            "required_disco": float("nan"),
            "required_total_boost": float("nan"),
            "required_coin_mult": float("nan"),
            "required_wave": "",
            "impossible": False,
            "updated_best_boost": float("nan"),
            "updated_best_coin_mult": float("nan"),
            "max_possible_coin_mult": float("nan"),
        }
        if tier_mult <= 0 or target_best_coin_mult <= 0 or best_tier_mult <= 0:
            return result

        current_best_boost = target_best_coin_mult / best_tier_mult
        max_possible_boost = 3.0 + float(other_echo)
        max_possible_coin_mult = max_possible_boost * float(tier_mult)

        if is_best_tier:
            req = max(1.0, float(source_disco_current))
            if req > 3.0:
                result["impossible"] = True
                result["required_disco"] = req
                result["required_total_boost"] = req + float(other_echo)
                result["required_coin_mult"] = (req + float(other_echo)) * float(tier_mult)
                result["max_possible_coin_mult"] = max_possible_coin_mult
                return result
            required_total_boost = req + float(other_echo)
            required_coin_mult = required_total_boost * float(tier_mult)
            result.update({
                "required_disco": req,
                "required_total_boost": required_total_boost,
                "required_coin_mult": required_coin_mult,
                "required_wave": f"{_match_wave_from_disco(req):04d}",
                "updated_best_boost": current_best_boost,
                "updated_best_coin_mult": target_best_coin_mult,
                "max_possible_coin_mult": max_possible_coin_mult,
            })
            return result

        req = max(1.0, (target_best_coin_mult / float(tier_mult)) - float(other_echo))
        prev_wave = _match_wave_from_disco(min(req, 3.0))
        for _ in range(50):
            if req > 3.0:
                result["impossible"] = True
                result["required_disco"] = req
                result["required_total_boost"] = req + float(other_echo)
                result["required_coin_mult"] = (req + float(other_echo)) * float(tier_mult)
                result["max_possible_coin_mult"] = max_possible_coin_mult
                return result

            delta_disco = req - float(source_disco_current)
            updated_best_boost = current_best_boost + (float(lab_mult) * delta_disco)
            updated_best_coin_mult = updated_best_boost * float(best_tier_mult)
            required_total_boost = updated_best_coin_mult / float(tier_mult)
            next_req = max(1.0, required_total_boost - float(other_echo))

            if next_req > 3.0:
                result["impossible"] = True
                result["required_disco"] = next_req
                result["required_total_boost"] = next_req + float(other_echo)
                result["required_coin_mult"] = (next_req + float(other_echo)) * float(tier_mult)
                result["max_possible_coin_mult"] = max_possible_coin_mult
                return result

            next_wave = _match_wave_from_disco(next_req)
            req = next_req
            if abs(next_wave - prev_wave) <= 1:
                result.update({
                    "required_disco": req,
                    "required_total_boost": req + float(other_echo),
                    "required_coin_mult": (req + float(other_echo)) * float(tier_mult),
                    "required_wave": f"{next_wave:04d}",
                    "updated_best_boost": updated_best_boost,
                    "updated_best_coin_mult": updated_best_coin_mult,
                    "max_possible_coin_mult": max_possible_coin_mult,
                })
                return result
            prev_wave = next_wave

        result["impossible"] = True
        result["required_disco"] = req
        result["required_total_boost"] = req + float(other_echo)
        result["required_coin_mult"] = (req + float(other_echo)) * float(tier_mult)
        result["max_possible_coin_mult"] = max_possible_coin_mult
        return result

    # Keep chart tier order stable and numeric-first.
    merged["_tier_num"] = pd.to_numeric(merged["tier"], errors="coerce")
    merged = merged.sort_values(["_tier_num", "tier"], na_position="last").reset_index(drop=True)

    selected_mode = str(display_mode or "disco_echo_boost")
    if selected_mode == "current_boost":
        selected_mode = "disco_echo_boost"
    CATEGORIES = ["attack", "defense", "utility", "uw"]

    def _series_value(row: pd.Series, key: str, default: float) -> float:
        return float(pd.to_numeric(pd.Series([row.get(key)]), errors="coerce").fillna(default).iloc[0])

    def _wave_label(row: pd.Series, key: str) -> str:
        w = pd.to_numeric(pd.Series([row.get(key)]), errors="coerce").fillna(0.0).iloc[0]
        w_int = int(float(w))
        return f"{w_int:04d}" if w_int > 0 else "0000"

    # Build chart data per category.
    tiers = merged["tier"].astype(str).tolist()
    chart_series = {}
    for cat in CATEGORIES:
        lab_level = int(category_metrics.get(cat, {}).get("lab_level", 0))
        total_current_echo = float(category_metrics.get(cat, {}).get("current_echo", 0.0))
        total_maxed_echo = float(category_metrics.get(cat, {}).get("maxed_echo", 0.0))
        total_current_echo_l1 = _lab_plus_one_echo(total_current_echo, lab_level)
        total_maxed_echo_l1 = _lab_plus_one_echo(total_maxed_echo, lab_level)

        act_disco = []
        act_echo = []
        act_echo_l1 = []
        max_disco = []
        max_echo = []
        max_echo_l1 = []
        act_wave = []
        max_wave = []

        for _, row in merged.iterrows():
            d_cur = _series_value(row, f"{cat}_disco_boost", 1.0)
            d_max = _series_value(row, f"max_{cat}_disco_boost", 1.0)

            # Effective echo = total echo - this tier's own echo (a tier's echo doesn't boost itself).
            tier_echo_cur = _scale_echo_by_lab(_series_value(row, f"{cat}_echo_boost", 0.0), lab_level)
            tier_echo_max = _scale_echo_by_lab(_series_value(row, f"max_{cat}_echo_boost", 0.0), lab_level)
            eff_echo = max(0.0, total_current_echo - tier_echo_cur)
            eff_echo_l1 = _lab_plus_one_echo(eff_echo, lab_level)
            eff_maxed_echo = max(0.0, total_maxed_echo - tier_echo_max)
            eff_maxed_echo_l1 = _lab_plus_one_echo(eff_maxed_echo, lab_level)

            act_disco.append(d_cur)
            act_echo.append(eff_echo)
            act_echo_l1.append(eff_echo_l1)
            max_disco.append(d_max)
            max_echo.append(eff_maxed_echo)
            max_echo_l1.append(eff_maxed_echo_l1)
            act_wave.append(_wave_label(row, cat))
            max_wave.append(_wave_label(row, f"max_{cat}_wave"))

        chart_series[cat] = {
            "actual_disco": act_disco,
            "actual_echo": act_echo,
            "actual_echo_lab1": act_echo_l1,
            "maxed_disco": max_disco,
            "maxed_echo": max_echo,
            "maxed_echo_lab1": max_echo_l1,
            "actual_wave": act_wave,
            "maxed_wave": max_wave,
        }

    fig = make_subplots(
        rows=2,
        cols=3,
        subplot_titles=(
            "Attack Boost",
            "UW Boost",
            "Combined Attack & UW Boost",
            "Defense Boost",
            "Utility Boost",
            "Utility Boost - Match Best Farming Tier",
        ),
        specs=[[{}, {}, {}], [{}, {}, {}]],
        horizontal_spacing=0.06,
        vertical_spacing=0.16,
    )

    subplot_positions = {
        "attack": (1, 1),
        "uw": (1, 2),
        "attack_uw": (1, 3),
        "defense": (2, 1),
        "utility": (2, 2),
        "best_farming_match": (2, 3),
    }
    trace_colors = {
        "actual_disco": "#0ea5e9",
        "actual_echo": "#22c55e",
        "actual_echo_lab1": "#ec4899",
        "maxed_disco": "#1e3a8a",
        "maxed_echo": "#166534",
        "maxed_echo_lab1": "#ec4899",
        "best_match": "#fbbf24",
        "best_match_impossible": "#7f1d1d",
    }

    y_axis_ceiling = {}

    def _snap_ceil(max_val: float) -> float:
        """Round max_val up to the next logarithmic tick mark."""
        mval = max(float(max_val), 1.0)
        k = int(math.floor(math.log10(mval)))
        decade = 10.0 ** k
        normalized = mval / decade
        mul = 0.1 if normalized <= 1.0 else (0.5 if normalized <= 5.0 else 1.0)
        step = mul * decade
        return max(2.0, step * math.ceil(mval / step))

    # Add derived combined subplot: attack x uw with per-tier echo products.
    attack_series = chart_series.get("attack", {})
    uw_series = chart_series.get("uw", {})

    def _combined_product_delta(d_a, e_a, d_u, e_u):
        """Return (disco_product, echo_delta) so they stack to full product."""
        disco_prod = d_a * d_u
        full_prod = (d_a + e_a) * (d_u + e_u)
        return disco_prod, max(0.0, full_prod - disco_prod)

    _atk_d = attack_series.get("actual_disco", [1.0] * len(tiers))
    _atk_e = attack_series.get("actual_echo", [0.0] * len(tiers))
    _atk_e_l1 = attack_series.get("actual_echo_lab1", [0.0] * len(tiers))
    _atk_md = attack_series.get("maxed_disco", [1.0] * len(tiers))
    _atk_me = attack_series.get("maxed_echo", [0.0] * len(tiers))
    _atk_me_l1 = attack_series.get("maxed_echo_lab1", [0.0] * len(tiers))
    _uw_d = uw_series.get("actual_disco", [1.0] * len(tiers))
    _uw_e = uw_series.get("actual_echo", [0.0] * len(tiers))
    _uw_e_l1 = uw_series.get("actual_echo_lab1", [0.0] * len(tiers))
    _uw_md = uw_series.get("maxed_disco", [1.0] * len(tiers))
    _uw_me = uw_series.get("maxed_echo", [0.0] * len(tiers))
    _uw_me_l1 = uw_series.get("maxed_echo_lab1", [0.0] * len(tiers))

    _comb_act = [_combined_product_delta(a, ea, u, eu) for a, ea, u, eu in zip(_atk_d, _atk_e, _uw_d, _uw_e)]
    _comb_act_l1 = [_combined_product_delta(a, ea, u, eu) for a, ea, u, eu in zip(_atk_d, _atk_e_l1, _uw_d, _uw_e_l1)]
    _comb_max = [_combined_product_delta(a, ea, u, eu) for a, ea, u, eu in zip(_atk_md, _atk_me, _uw_md, _uw_me)]
    _comb_max_l1 = [_combined_product_delta(a, ea, u, eu) for a, ea, u, eu in zip(_atk_md, _atk_me_l1, _uw_md, _uw_me_l1)]

    chart_series["attack_uw"] = {
        "actual_disco": [x[0] for x in _comb_act],
        "actual_echo": [x[1] for x in _comb_act],
        "actual_echo_lab1": [x[1] for x in _comb_act_l1],
        "maxed_disco": [x[0] for x in _comb_max],
        "maxed_echo": [x[1] for x in _comb_max],
        "maxed_echo_lab1": [x[1] for x in _comb_max_l1],
    }

    # Build best farming matching subplot series.
    utility_series = chart_series.get("utility", {})
    utility_actual_disco = utility_series.get("actual_disco", [1.0] * len(tiers))
    utility_maxed_disco = utility_series.get("maxed_disco", [1.0] * len(tiers))
    coin_mult_per_tier = [coin_multiplier_by_tier.get(t, 0.0) for t in tiers]
    best_tier_code = ""
    if str(best_tier_label).startswith("T"):
        best_tier_code = _to_tier_code(best_tier_label)
    _chart_lab_mult = _lab_echo_multiplier(utility_lab_lvl)
    required_match_disco = []
    required_match_total_boost = []
    required_match_impossible_disco = []
    required_match_wave = []
    required_match_impossible_wave = []
    best_tier_highlight = []
    match_target_coin_mult = optimized_boosted_coin_mult if tab_use_optimized_scenario else current_boosted_coin_mult
    source_disco_key = "disco_max" if tab_use_optimized_scenario else "disco_cur"
    source_echo_key = "eff_echo_max" if tab_use_optimized_scenario else "eff_echo_cur"
    for tier_code, tier_mult in zip(tiers, coin_mult_per_tier):
        metrics = utility_match_by_tier.get(str(tier_code), {})
        source_disco_cur = float(metrics.get(source_disco_key, 1.0))
        eff_echo_cur = float(metrics.get(source_echo_key, utility_echo_current))
        if tier_mult > 0 and match_target_coin_mult > 0:
            solved = _solve_match_iteration(
                target_best_coin_mult=match_target_coin_mult,
                tier_mult=float(tier_mult),
                other_echo=eff_echo_cur,
                source_disco_current=source_disco_cur,
                is_best_tier=str(tier_code) == best_tier_code,
                best_tier_mult=tier_coin_mult,
                lab_mult=_chart_lab_mult,
            )
            req = float(solved.get("required_disco", float("nan")))
            required_total_boost = float(solved.get("required_total_boost", float("nan")))
            req_impossible = bool(solved.get("impossible", False)) or (pd.notna(req) and req > 3.0)
            if req_impossible:
                required_match_disco.append(float("nan"))
                required_match_total_boost.append(float("nan"))
                required_match_impossible_disco.append(req if pd.notna(req) else float("nan"))
                required_match_wave.append(">5000" if pd.notna(req) and req > 3.0 else "")
                required_match_impossible_wave.append("")
            else:
                req_clamped = max(1.0, req)
                required_match_disco.append(req_clamped)
                required_match_total_boost.append(required_total_boost)
                required_match_impossible_disco.append(float("nan"))
                required_match_wave.append(str(solved.get("required_wave", f"{_match_wave_from_disco(req_clamped):04d}")))
                required_match_impossible_wave.append("")
        else:
            required_match_disco.append(float("nan"))
            required_match_total_boost.append(float("nan"))
            required_match_impossible_disco.append(float("nan"))
            required_match_wave.append("")
            required_match_impossible_wave.append("")
        best_tier_highlight.append((utility_disco_maxed if tab_use_optimized_scenario else utility_disco_current) if tier_code == best_tier_code else 0.0)

    chart_series["best_farming_match"] = {
        "actual_disco": utility_actual_disco,
        "maxed_disco": utility_maxed_disco,
        "required_match_disco": required_match_disco,
        "required_match_total_boost": required_match_total_boost,
        "required_match_impossible_disco": required_match_impossible_disco,
        "required_match_wave": required_match_wave,
        "required_match_impossible_wave": required_match_impossible_wave,
        "best_tier_highlight": best_tier_highlight,
    }

    CHART_KEYS = ["attack", "defense", "utility", "uw", "attack_uw", "best_farming_match"]
    for cat in CHART_KEYS:
        r, c = subplot_positions[cat]
        is_base_subplots = cat in CATEGORIES
        if cat == "uw":
            cap = "UW"
        elif cat == "attack_uw":
            cap = "Combined Attack & UW"
        elif cat == "best_farming_match":
            cap = "Utility Boost - Match Best Farming Tier"
        else:
            cap = cat.capitalize()

        # Build four visual levels:
        # L1 front  : Actual Disco (solid)
        # L2 behind : Actual Total Echo (solid)
        # L3 behind : Maxed Disco (outline only)
        # L4 back   : Maxed Total Echo (outline only)
        # Lab+1     : dotted lines
        if cat == "best_farming_match":
            level0_coin_mult = None
            level1_actual = chart_series[cat]["actual_disco"]
            level2_actual = chart_series[cat]["best_tier_highlight"]
            level3_maxed = chart_series[cat]["maxed_disco"]
            level4_maxed = [0.0] * len(tiers)
            level5_actual_lab1 = [0.0] * len(tiers)
            line_maxed_lab1 = chart_series[cat]["required_match_disco"]
            level_required_impossible = chart_series[cat]["required_match_impossible_disco"]
            achieved_wave_labels = chart_series.get("utility", {}).get("actual_wave", [""] * len(tiers))
            needed_wave_labels = chart_series.get("utility", {}).get("maxed_wave", [""] * len(tiers))
            line_required_wave = chart_series[cat]["required_match_wave"]
            line_required_impossible_wave = chart_series[cat]["required_match_impossible_wave"]
            level_required_impossible_base = [
                max(a, m) for a, m in zip(level1_actual, level3_maxed)
            ]
        else:
            level0_coin_mult = None
            level1_actual = chart_series[cat]["actual_disco"]
            level2_actual = [
                d + e for d, e in zip(
                    chart_series[cat]["actual_disco"],
                    chart_series[cat]["actual_echo"],
                )
            ]
            level3_maxed = chart_series[cat]["maxed_disco"]
            level4_maxed = [
                d + e for d, e in zip(
                    chart_series[cat]["maxed_disco"],
                    chart_series[cat]["maxed_echo"],
                )
            ]
            level5_actual_lab1 = [
                d + e for d, e in zip(
                    chart_series[cat]["actual_disco"],
                    chart_series[cat]["actual_echo_lab1"],
                )
            ]
            line_maxed_lab1 = [
                d + e for d, e in zip(
                    chart_series[cat]["maxed_disco"],
                    chart_series[cat]["maxed_echo_lab1"],
                )
            ]
            level_required_impossible = [float("nan")] * len(tiers)
            line_required_wave = [""] * len(tiers)
            line_required_impossible_wave = [""] * len(tiers)
            level_required_impossible_base = [float("nan")] * len(tiers)
            achieved_wave_labels = chart_series.get(cat, {}).get("actual_wave", [""] * len(tiers))
            needed_wave_labels = chart_series.get(cat, {}).get("maxed_wave", [""] * len(tiers))

        wave_achieved_suffix = "<br>Wave Achieved: %{customdata}" if is_base_subplots else ""
        wave_needed_suffix = "<br>Wave Needed: %{customdata}" if is_base_subplots else ""

        max_candidates = [
            float(v)
            for v in (level1_actual + level2_actual + level3_maxed + level4_maxed + level5_actual_lab1 + line_maxed_lab1)
            if pd.notna(v)
        ]
        max_val = max(max_candidates) if max_candidates else 1.0
        ceil_val = 3.5 if cat == "best_farming_match" else _snap_ceil(max_val)
        y_axis_ceiling[cat] = ceil_val

        if level0_coin_mult is not None:
            fig.add_trace(
                go.Bar(
                    x=tiers,
                    y=level0_coin_mult,
                    name="Tier Coin Multiplier",
                    marker={"color": "rgba(148,163,184,0.35)"},
                    hovertemplate=f"{cap} Tier %{{x}}<br>Tier Coin Multiplier: %{{y:.3f}}<extra></extra>",
                    legendgroup="coin_mult_only",
                    showlegend=False,
                    opacity=1.0,
                ),
                row=r,
                col=c,
            )

        if cat != "best_farming_match":
            # Level 5 back-most: actual total echo Lab+1 (muted theoretical)
            fig.add_trace(
                go.Bar(
                    x=tiers,
                    y=level5_actual_lab1,
                    customdata=(achieved_wave_labels if is_base_subplots else None),
                    name="Current Disco + Echo Boost (Lab+1)",
                    marker={"color": trace_colors["actual_echo_lab1"]},
                    hovertemplate=f"{cap} Tier %{{x}}<br>Current Disco + Echo Boost (Lab+1): %{{y:.3f}}<extra></extra>",
                    legendgroup="actual_echo_lab1",
                    showlegend=(cat == "attack"),
                    legendrank=3,
                    opacity=0.25,
                ),
                row=r,
                col=c,
            )

        if cat != "best_farming_match":
            # Level 4: maxed total echo (muted theoretical)
            fig.add_trace(
                go.Bar(
                    x=tiers,
                    y=level4_maxed,
                    customdata=(needed_wave_labels if is_base_subplots else None),
                    name="Maxed Disco + Echo Boost",
                    marker={"color": trace_colors["maxed_echo"]},
                    hovertemplate=f"{cap} Tier %{{x}}<br>Maxed Disco + Echo Boost: %{{y:.3f}}<extra></extra>",
                    legendgroup="maxed_echo",
                    showlegend=(cat == "attack"),
                    legendrank=5,
                    opacity=0.35,
                ),
                row=r,
                col=c,
            )
        # Level 3: maxed disco (muted theoretical)
        fig.add_trace(
            go.Bar(
                x=tiers,
                y=level3_maxed,
                customdata=(needed_wave_labels if (is_base_subplots or cat == "best_farming_match") else None),
                name=("Maxed Disco Boost" if cat != "best_farming_match" else "Maxed Utility Boost"),
                marker={"color": trace_colors["maxed_disco"]},
                hovertemplate=(
                    f"{cap} Tier %{{x}}<br>"
                    f"{'Maxed Disco Boost' if cat != 'best_farming_match' else 'Maxed Utility Boost'}: %{{y:.3f}}"
                    f"{wave_needed_suffix if cat != 'best_farming_match' else '<br>Wave Needed: %{customdata}'}"
                    "<extra></extra>"
                ),
                legendgroup="maxed_disco",
                showlegend=(cat == "attack"),
                legendrank=4,
                opacity=0.45,
            ),
            row=r,
            col=c,
        )
        if cat == "best_farming_match":
            required_custom = [
                [boost, wave]
                for boost, wave in zip(line_maxed_lab1, line_required_wave)
            ]
            fig.add_trace(
                go.Bar(
                    x=tiers,
                    y=line_maxed_lab1,
                    customdata=required_custom,
                    name="Boost Needed To Match Best Farming Tier",
                    marker={"color": trace_colors["best_match"]},
                    hovertemplate=(
                        f"{cap} Tier %{{x}}<br>"
                        f"Target (Utility Total Boost x Tier Difficulty): {match_target_coin_mult:.3f}"
                        "<br>Required Boost: %{customdata[0]:.3f}"
                        "<br>Required Wave: %{customdata[1]}<extra></extra>"
                    ),
                    legendgroup="best_match_req",
                    showlegend=False,
                    opacity=0.28,
                ),
                row=r,
                col=c,
            )
            impossible_cap_height = [
                max(0.0, 3.5 - b) if pd.notna(v) else float("nan")
                for v, b in zip(level_required_impossible, level_required_impossible_base)
            ]
            impossible_custom = [
                [boost, wave]
                for boost, wave in zip(level_required_impossible, line_required_impossible_wave)
            ]
            fig.add_trace(
                go.Bar(
                    x=tiers,
                    y=impossible_cap_height,
                    base=level_required_impossible_base,
                    customdata=impossible_custom,
                    name="Parity to Best Farming Tier not possible",
                    marker={"color": trace_colors["best_match_impossible"]},
                    hovertemplate=(
                        f"{cap} Tier %{{x}}<br>"
                        f"Target (Utility Total Boost x Tier Difficulty): {match_target_coin_mult:.3f}"
                        "<br>Required Boost: %{customdata[0]:.3f}"
                        "<br>Required Wave: not possible (max 3.00x Disco Boost)<extra></extra>"
                    ),
                    legendgroup="best_match_impossible",
                    showlegend=False,
                    opacity=0.30,
                ),
                row=r,
                col=c,
            )
        if cat != "best_farming_match":
            # Level 2: actual total echo (solid factual)
            fig.add_trace(
                go.Bar(
                    x=tiers,
                    y=level2_actual,
                    customdata=(achieved_wave_labels if is_base_subplots else None),
                    name="Current Disco + Echo Boost",
                    marker={"color": trace_colors["actual_echo"]},
                    hovertemplate=f"{cap} Tier %{{x}}<br>Current Disco + Echo Boost: %{{y:.3f}}<extra></extra>",
                    legendgroup="actual_echo",
                    showlegend=(cat == "attack"),
                    legendrank=2,
                    opacity=0.85,
                ),
                row=r,
                col=c,
            )
        # Level 1 front: actual disco (solid factual)
        fig.add_trace(
            go.Bar(
                x=tiers,
                y=level1_actual,
                customdata=(achieved_wave_labels if (is_base_subplots or cat == "best_farming_match") else None),
                name=("Current Disco Boost" if cat != "best_farming_match" else "Current Utility Boost"),
                marker={"color": trace_colors["actual_disco"]},
                hovertemplate=(
                    f"{cap} Tier %{{x}}<br>"
                    f"{'Current Disco Boost' if cat != 'best_farming_match' else 'Current Utility Boost'}: %{{y:.3f}}"
                    f"{wave_achieved_suffix if cat != 'best_farming_match' else '<br>Wave Achieved: %{customdata}'}"
                    "<extra></extra>"
                ),
                legendgroup="actual_disco",
                showlegend=(cat == "attack" if cat != "best_farming_match" else False),
                legendrank=1,
                opacity=0.95,
            ),
            row=r,
            col=c,
        )

        if cat == "best_farming_match":
            fig.add_trace(
                go.Bar(
                    x=tiers,
                    y=level2_actual,
                    name="Best Farming Tier",
                    marker={"color": trace_colors["best_match"]},
                    customdata=(achieved_wave_labels if cat == "best_farming_match" else None),
                    hovertemplate=(
                        f"{cap} Tier %{{x}}<br>"
                        f"Best Tier Multiplier (Utility Total Boost x Tier Difficulty): {match_target_coin_mult:.3f}"
                        "<br>Current Disco Boost: %{y:.3f}"
                        "<br>Wave Achieved: %{customdata}<extra></extra>"
                    ),
                    legendgroup="best_farming_tier",
                    showlegend=False,
                    opacity=0.95,
                ),
                row=r,
                col=c,
            )

        # Maxed Lab+1 as dotted hull line
        if cat != "best_farming_match":
            fig.add_trace(
                go.Scatter(
                    x=tiers,
                    y=line_maxed_lab1,
                    customdata=(needed_wave_labels if is_base_subplots else None),
                    mode="lines",
                    name="Maxed Disco + Echo Boost (Lab+1)",
                    line={"color": trace_colors["maxed_echo_lab1"], "width": 2, "dash": "dot"},
                    hovertemplate=f"{cap} Tier %{{x}}<br>Maxed Disco + Echo Boost (Lab+1): %{{y:.3f}}<extra></extra>",
                    legendgroup="maxed_echo_lab1",
                    showlegend=(cat == "attack"),
                    legendrank=6,
                ),
                row=r,
                col=c,
            )

    def _tick_step_from_max(max_val: float) -> float:
        """Dynamic step size from max value.

        Formula:
          step = m * 10^k
          where k = floor(log10(max_val))
          and m in {0.1, 0.5, 1.0} chosen by normalized max in that decade.

        This yields:
          max<=5 -> 0.5, max<=10 -> 1, max<=50 -> 5, max<=100 -> 10, ...
        """
        mval = max(float(max_val), 1.0)
        k = int(math.floor(math.log10(mval)))
        decade = 10.0 ** k
        normalized = mval / decade
        if normalized <= 1.0:
            mul = 0.1
        elif normalized <= 5.0:
            mul = 0.5
        else:
            mul = 1.0
        return mul * decade

    def _log_ticks_from_max(max_val: float):
        step = _tick_step_from_max(max_val)
        mval = max(float(max_val), 1.0)
        lower = 1.0

        ticks = [lower]
        v = step
        while v <= mval:
            ticks.append(round(v, 10))
            v += step
        ticks.append(mval)

        ticks = sorted({t for t in ticks if t > 0})
        labels = [str(int(t)) if abs(t - round(t)) < 1e-9 else f"{t:.2f}".rstrip("0").rstrip(".") for t in ticks]
        return ticks, labels, lower

    # Logarithmic scale with variable-resolution ticks per subplot.
    for cat in CHART_KEYS:
        r, c = subplot_positions[cat]
        max_tick = float(y_axis_ceiling.get(cat, 10))
        tick_vals, tick_text, lower_tick = _log_ticks_from_max(max_tick)
        axis_range = [0, math.log10(3.5)] if cat == "best_farming_match" else [0, math.log10(max_tick)]

        fig.update_yaxes(
            type="log",
            tickmode="array",
            tickvals=tick_vals,
            ticktext=tick_text,
            range=axis_range,
            gridcolor="rgba(255,255,255,0.16)",
            zeroline=False,
            title_text=("Boost from Disco + Echo" if c == 1 else None),
            row=r,
            col=c,
        )
        fig.update_xaxes(
            title_text="Tier",
            showgrid=False,
            tickangle=-40,
            row=r,
            col=c,
        )

    fig.update_layout(
        template="plotly_dark",
        barmode="overlay",
        paper_bgcolor="#0b0f19",
        plot_bgcolor="#0f172a",
        margin={"l": 30, "r": 20, "t": 56, "b": 30},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.08, "x": 0.0},
        height=860,
        title=None,
    )

    # Dark theme colour palette
    _C = {
        "bg_header":  "#1e1b4b",   # deep indigo header
        "bg_even":    "#12111f",   # very dark row (even tiers)
        "bg_odd":     "#1a1830",   # slightly lighter row (odd tiers)
        "border":     "#312e81",   # indigo border between tiers
        "cell_border":"#2d2b50",   # faint inner border
        "label":      "#6b7280",   # muted grey for "Tier/Wave/Boost" labels
        "tier_num":   "#e5e7eb",   # bright white-grey for tier number
        "wave":       "#a78bfa",   # purple for wave values
        "boost":      "#f9fafb",   # near-white for boost values
        "boost_max":  "#fbbf24",   # gold for capped boosts
        "dash":       "#4b5563",   # dim dash for empty cells
        "sim_wave":   "#9ca3af",   # light grey for simulated wave values
        "sim_boost":  "#d1d5db",   # light grey for simulated boost values
        "simulated":  "#38bdf8",   # bright blue for simulated maxed values
        "sheet_title_bg": "#2b2416",
        "sheet_title_fg": "#ece1bf",
        "sheet_subtitle_bg": "#201c14",
        "sheet_left_bg": "#243124",
        "sheet_tier_bg": "#1c261c",
        "sheet_grid": "#4d4738",
        "sheet_text": "#ebe7db",
        "sheet_muted": "#8f9188",
        "sheet_attack": "#352420",
        "sheet_attack_max": "#472b24",
        "sheet_defense": "#223126",
        "sheet_defense_max": "#2b3d2d",
        "sheet_utility": "#342d1c",
        "sheet_utility_max": "#473b22",
        "sheet_uw": "#1d2b37",
        "sheet_uw_max": "#22384a",
        "sheet_combined": "#2f2037",
        "sheet_combined_max": "#41284a",
        "sheet_tournament": "#2a2b30",
    }

    def _mode_subtitle() -> str:
        if selected_mode == "match_best_tier_coin_multiplier":
            if show_detail:
                return "Utility Boost (Disco / +Echo) vs Tier Coin Multiplier Parity"
            return "Utility Boost vs Tier Coin Multiplier Parity"
        if selected_mode == "echo_per_tier":
            return "Wave / Echo Boost per Tier"
        if show_detail:
            return "Wave / Disco + Carried Echo (Detailed)"
        return "Wave / Total Boost"

    def _category_colors(category: str) -> dict:
        return {
            "attack": {"bg": _C["sheet_attack"], "bg_max": _C["sheet_attack_max"], "accent": "#f09a7f"},
            "defense": {"bg": _C["sheet_defense"], "bg_max": _C["sheet_defense_max"], "accent": "#9bcea0"},
            "utility": {"bg": _C["sheet_utility"], "bg_max": _C["sheet_utility_max"], "accent": "#f1cd6a"},
            "uw": {"bg": _C["sheet_uw"], "bg_max": _C["sheet_uw_max"], "accent": "#8ec4e8"},
            "attack_uw": {"bg": _C["sheet_combined"], "bg_max": _C["sheet_combined_max"], "accent": "#d49eff"},
        }[category]

    def _category_header(category: str) -> str:
        if category == "uw":
            return "Ultimate Weapon"
        if category == "attack_uw":
            return "Combined Attack x UW"
        return category.capitalize()

    def _category_values(category: str, row: pd.Series, tournament: bool = False) -> dict:
        is_optimized = tab_use_optimized_scenario
        cat_meta = category_metrics.get(category, {})
        lab_level = int(cat_meta.get("selected_lab_level", cat_meta.get("lab_level", 0))) if tab_use_target_labs else int(cat_meta.get("current_lab_level", 0))
        use_max = is_optimized

        if tab_use_target_labs:
            total_echo_key = "maxed_echo" if use_max else "current_echo"
        else:
            total_echo_key = "baseline_maxed_echo" if use_max else "baseline_current_echo"
        total_echo_val = float(cat_meta.get(total_echo_key, 0.0))

        if tournament:
            return {
                "wave_int": 0,
                "has_data": False,
                "has_logged_run": False,
                "is_simulated": False,
                "disco_val": 1.0,
                "tier_echo_val": 0.0,
                "effective_echo_val": total_echo_val,
                "at_cap": False,
            }

        actual_wave_raw = row.get(category)
        actual_wave_num = pd.to_numeric(pd.Series([actual_wave_raw]), errors="coerce").fillna(0.0).iloc[0]
        has_logged_run = int(float(actual_wave_num)) > 0

        wave_col = category if not (is_optimized and not has_logged_run) else f"max_{category}_wave"
        wave_raw = row.get(wave_col)
        wave_num = pd.to_numeric(pd.Series([wave_raw]), errors="coerce").fillna(0.0).iloc[0]
        wave_int = int(float(wave_num))
        has_data = wave_int > 0

        disco_key = f"max_{category}_disco_boost" if use_max else f"{category}_disco_boost"
        disco_raw = row.get(disco_key)
        disco_val = float(pd.to_numeric(pd.Series([disco_raw]), errors="coerce").fillna(1.0).iloc[0])
        if not has_data:
            disco_val = 1.0

        echo_key = f"max_{category}_echo_boost" if use_max else f"{category}_echo_boost"
        echo_raw = row.get(echo_key)
        tier_echo_val = _scale_echo_by_lab(
            float(pd.to_numeric(pd.Series([echo_raw]), errors="coerce").fillna(0.0).iloc[0]),
            lab_level,
        )

        effective_echo_val = max(0.0, total_echo_val - tier_echo_val)
        bonus_cap = 3.0 if category == "utility" else 5.0
        at_cap = disco_val >= bonus_cap - 0.005

        return {
            "wave_int": wave_int,
            "has_data": has_data,
            "has_logged_run": has_logged_run,
            "is_simulated": is_optimized and not has_logged_run,
            "disco_val": disco_val,
            "tier_echo_val": tier_echo_val,
            "effective_echo_val": effective_echo_val,
            "at_cap": at_cap,
        }

    def _boost_text(values: dict, tournament: bool = False) -> str:
        if selected_mode == "echo_per_tier" and not tournament:
            return f"x{values['tier_echo_val']:.3f}"
        if show_detail and selected_mode == "disco_echo_boost":
            return f"x{values['disco_val']:.3f} / +{values['effective_echo_val']:.3f}"
        return f"x{(values['disco_val'] + values['effective_echo_val']):.3f}"

    def _category_cells(category: str, values: dict, tournament: bool = False) -> list[html.Td]:
        colors = _category_colors(category)
        wave_text = "---" if (tournament or not values["has_data"]) else str(values["wave_int"])

        wave_color = _C["sheet_muted"] if values["is_simulated"] or not values["has_data"] else colors["accent"]
        boost_color = _C["boost_max"] if values["at_cap"] and values["has_data"] else _C["sheet_text"]
        if values["is_simulated"]:
            boost_color = _C["sheet_muted"]

        cell_bg = _C["sheet_tournament"] if tournament else (colors["bg_max"] if values["at_cap"] and values["has_data"] else colors["bg"])

        wave_td = html.Td(wave_text, style={
            "textAlign": "center",
            "verticalAlign": "middle",
            "background": cell_bg,
            "border": f"1px solid {_C['sheet_grid']}",
            "padding": "0.35rem 0.45rem",
            "minWidth": "4.8rem",
            "fontSize": "1rem",
            "fontWeight": "700",
            "lineHeight": "1.1",
            "color": wave_color,
        })
        boost_td = html.Td(_boost_text(values, tournament=tournament), style={
            "textAlign": "center",
            "verticalAlign": "middle",
            "background": cell_bg,
            "border": f"1px solid {_C['sheet_grid']}",
            "padding": "0.35rem 0.55rem",
            "minWidth": "8.8rem",
            "fontSize": "0.84rem",
            "fontWeight": "700" if values["at_cap"] and values["has_data"] else "500",
            "lineHeight": "1.2",
            "color": boost_color,
            "whiteSpace": "nowrap",
        })
        return [wave_td, boost_td]

    def _combined_cell(atk_values: dict, uw_values: dict, tournament: bool = False) -> html.Td:
        colors = _category_colors("attack_uw")
        atk_total = float(atk_values["disco_val"] + atk_values["effective_echo_val"])
        uw_total = float(uw_values["disco_val"] + uw_values["effective_echo_val"])
        combined_total = atk_total * uw_total

        combined_at_cap = bool(atk_values["at_cap"] and uw_values["at_cap"] and atk_values["has_data"] and uw_values["has_data"])
        combined_simulated = bool(atk_values["is_simulated"] or uw_values["is_simulated"])

        bg = _C["sheet_tournament"] if tournament else (colors["bg_max"] if combined_at_cap else colors["bg"])
        fg = _C["boost_max"] if combined_at_cap else _C["sheet_text"]
        if combined_simulated:
            fg = _C["sheet_muted"]

        return html.Td(f"x{combined_total:.3f}", style={
            "textAlign": "center",
            "verticalAlign": "middle",
            "background": bg,
            "border": f"1px solid {_C['sheet_grid']}",
            "padding": "0.35rem 0.55rem",
            "minWidth": "8.8rem",
            "fontSize": "0.88rem",
            "fontWeight": "700",
            "lineHeight": "1.2",
            "color": fg,
            "whiteSpace": "nowrap",
        })

    def _tournament_row() -> html.Tr:
        tournament_values = {c: _category_values(c, pd.Series(dtype=object), tournament=True) for c in CATEGORIES}
        return html.Tr(
            [
                html.Td(
                    "Tournament",
                    style={
                        "background": _C["sheet_tournament"],
                        "border": f"1px solid {_C['sheet_grid']}",
                        "padding": "0.35rem 0.5rem",
                        "textAlign": "center",
                        "whiteSpace": "nowrap",
                        "fontSize": "0.95rem",
                        "fontWeight": "700",
                        "lineHeight": "1.1",
                        "color": _C["sheet_text"],
                    },
                )
            ]
            + [cell for c in CATEGORIES for cell in _category_cells(c, tournament_values[c], tournament=True)]
            + [_combined_cell(tournament_values["attack"], tournament_values["uw"], tournament=True)]
        )

    body_rows = []
    tournament_inserted = False
    for _, row in merged.iterrows():
        tier_label = str(row.get("tier", ""))
        cat_values = {c: _category_values(c, row, tournament=False) for c in CATEGORIES}
        body_rows.append(html.Tr(
            [
                html.Td(
                    tier_label,
                    style={
                        "background": _C["sheet_tier_bg"],
                        "border": f"1px solid {_C['sheet_grid']}",
                        "padding": "0.35rem 0.5rem",
                        "textAlign": "center",
                        "whiteSpace": "nowrap",
                        "minWidth": "4.4rem",
                        "fontSize": "1.15rem",
                        "fontWeight": "700",
                        "lineHeight": "1.1",
                        "color": _C["sheet_text"],
                    },
                )
            ]
            + [cell for c in CATEGORIES for cell in _category_cells(c, cat_values[c])]
            + [_combined_cell(cat_values["attack"], cat_values["uw"])]
        ))
        tier_num = pd.to_numeric(pd.Series([tier_label]), errors="coerce").iloc[0]
        if not tournament_inserted and pd.notna(tier_num) and int(float(tier_num)) == 21:
            body_rows.append(_tournament_row())
            tournament_inserted = True

    if not tournament_inserted:
        body_rows.append(_tournament_row())

    footer_label_style = {
        "background": _C["sheet_left_bg"],
        "border": f"1px solid {_C['sheet_grid']}",
        "padding": "0.35rem 0.5rem",
        "fontWeight": "700",
        "color": _C["sheet_text"],
        "textAlign": "left",
    }

    footer_cells = [html.Td("Echo Lab", style=footer_label_style)]
    for category in CATEGORIES:
        cat_meta = category_metrics.get(category, {})
        lab_level = int(cat_meta.get("selected_lab_level", cat_meta.get("lab_level", 0))) if tab_use_target_labs else int(cat_meta.get("current_lab_level", 0))
        lab_pct = _lab_echo_multiplier(lab_level) * 100.0
        colors = _category_colors(category)
        footer_cells.append(html.Td([
            html.Div(f"Lvl {lab_level}", style={"fontWeight": "700", "color": colors["accent"]}),
            html.Div(f"{lab_pct:.1f}% multiplier", style={"fontSize": "0.82rem", "color": _C["sheet_text"]}),
        ], style={
            "background": colors["bg"],
            "border": f"1px solid {_C['sheet_grid']}",
            "padding": "0.35rem 0.45rem",
            "textAlign": "center",
        }, colSpan=2))
    footer_cells.append(html.Td("", style={
        "background": _C["sheet_combined"],
        "border": f"1px solid {_C['sheet_grid']}",
        "padding": "0.35rem 0.45rem",
    }))

    title_row = html.Tr([
        html.Th("Tier", style={
            "background": _C["sheet_left_bg"],
            "color": _C["sheet_text"],
            "border": f"1px solid {_C['sheet_grid']}",
            "padding": "0.45rem 0.5rem",
            "width": "4.4rem",
        }),
        html.Th("Dissonant Runs", colSpan=len(CATEGORIES) * 2 + 1, style={
            "background": _C["sheet_title_bg"],
            "color": _C["sheet_title_fg"],
            "border": f"1px solid {_C['sheet_grid']}",
            "padding": "0.45rem 0.5rem",
            "fontWeight": "700",
            "textAlign": "center",
            "fontSize": "1rem",
        }),
    ])

    subtitle_row = html.Tr([
        html.Th("", style={
            "background": _C["sheet_left_bg"],
            "border": f"1px solid {_C['sheet_grid']}",
            "padding": "0.2rem",
        }),
        html.Th(_mode_subtitle(), colSpan=len(CATEGORIES) * 2 + 1, style={
            "background": _C["sheet_subtitle_bg"],
            "color": _C["sheet_title_fg"],
            "border": f"1px solid {_C['sheet_grid']}",
            "padding": "0.2rem 0.5rem",
            "textAlign": "center",
            "fontSize": "0.82rem",
            "fontStyle": "italic",
        }),
    ])

    header_row = html.Tr([
        html.Th("Tier", style={
            "background": _C["sheet_left_bg"],
            "color": _C["sheet_text"],
            "border": f"1px solid {_C['sheet_grid']}",
            "padding": "0.35rem 0.5rem",
            "textAlign": "left",
        })
    ] + [
        html.Th(_category_header(category), style={
            "background": _category_colors(category)["bg"],
            "color": _C["sheet_text"],
            "border": f"1px solid {_C['sheet_grid']}",
            "padding": "0.35rem 0.5rem",
            "textAlign": "center",
            "fontWeight": "700",
            "fontSize": "0.9rem",
        }, colSpan=2)
        for category in CATEGORIES
    ] + [
        html.Th(_category_header("attack_uw"), style={
            "background": _category_colors("attack_uw")["bg"],
            "color": _C["sheet_text"],
            "border": f"1px solid {_C['sheet_grid']}",
            "padding": "0.35rem 0.5rem",
            "textAlign": "center",
            "fontWeight": "700",
            "fontSize": "0.9rem",
        })
    ])

    subheader_row = html.Tr([
        html.Th("", style={
            "background": _C["sheet_left_bg"],
            "color": _C["sheet_text"],
            "border": f"1px solid {_C['sheet_grid']}",
            "padding": "0.2rem 0.35rem",
        })
    ] + [
        cell
        for category in CATEGORIES
        for cell in (
            html.Th("Wave", style={
                "background": _category_colors(category)["bg"],
                "color": _C["sheet_muted"],
                "border": f"1px solid {_C['sheet_grid']}",
                "padding": "0.2rem 0.35rem",
                "textAlign": "center",
                "fontWeight": "600",
                "fontSize": "0.72rem",
                "textTransform": "uppercase",
                "letterSpacing": "0.03em",
            }),
            html.Th("Boost", style={
                "background": _category_colors(category)["bg"],
                "color": _C["sheet_muted"],
                "border": f"1px solid {_C['sheet_grid']}",
                "padding": "0.2rem 0.35rem",
                "textAlign": "center",
                "fontWeight": "600",
                "fontSize": "0.72rem",
                "textTransform": "uppercase",
                "letterSpacing": "0.03em",
            }),
        )
    ] + [
        html.Th("Multiplier", style={
            "background": _category_colors("attack_uw")["bg"],
            "color": _C["sheet_muted"],
            "border": f"1px solid {_C['sheet_grid']}",
            "padding": "0.2rem 0.35rem",
            "textAlign": "center",
            "fontWeight": "600",
            "fontSize": "0.72rem",
            "textTransform": "uppercase",
            "letterSpacing": "0.03em",
        })
    ])

    if selected_mode == "match_best_tier_coin_multiplier":
        match_target_mult = optimized_boosted_coin_mult if tab_use_optimized_scenario else current_boosted_coin_mult
        match_body_rows = []
        _match_lab_mult = _lab_echo_multiplier(utility_lab_lvl)
        for _, row in merged.iterrows():
            tier_label = str(row.get("tier", ""))
            row_is_best_tier = tier_label == best_tier_code
            metrics = utility_match_by_tier.get(tier_label, {})
            utility_wave = int(float(metrics.get("wave_cur", 0.0) or 0.0)) if not tab_use_optimized_scenario else int(float(row.get("max_utility_wave", 0.0) or 0.0))
            utility_total_boost = float(metrics.get("total_boost_max" if tab_use_optimized_scenario else "total_boost_cur", 1.0))
            source_disco_cur = float(metrics.get("disco_max" if tab_use_optimized_scenario else "disco_cur", 1.0))
            tier_mult = float(metrics.get("tier_mult", 0.0) or 0.0)
            coin_mult = utility_total_boost * tier_mult if tier_mult > 0 else float("nan")
            other_echo = float(metrics.get("eff_echo_max" if tab_use_optimized_scenario else "eff_echo_cur", 0.0))

            solved = _solve_match_iteration(
                target_best_coin_mult=match_target_mult,
                tier_mult=tier_mult,
                other_echo=other_echo,
                source_disco_current=source_disco_cur,
                is_best_tier=tier_label == best_tier_code,
                best_tier_mult=tier_coin_mult,
                lab_mult=_match_lab_mult,
            )
            required_disco = float(solved.get("required_disco", float("nan")))
            required_total_boost = float(solved.get("required_total_boost", float("nan")))
            required_coin_mult = float(solved.get("required_coin_mult", float("nan")))
            req_wave_raw = str(solved.get("required_wave", ""))
            updated_best_boost = float(solved.get("updated_best_boost", float("nan")))
            updated_best_coin_mult = float(solved.get("updated_best_coin_mult", float("nan")))
            req_impossible = bool(solved.get("impossible", False)) or (pd.notna(required_disco) and required_disco > 3.0)
            utility_boost_text = (
                f"x{source_disco_cur:.3f} / +{other_echo:.3f}"
                if show_detail
                else f"x{utility_total_boost:.3f}"
            )

            max_possible_coin = float(solved.get("max_possible_coin_mult", float("nan")))
            req_estimated = False
            if pd.notna(required_disco) and not req_impossible:
                req_wave_text = req_wave_raw if req_wave_raw and req_wave_raw != "0000" else "---"
                req_boost_text = (
                    f"x{required_disco:.3f} / +{other_echo:.3f}"
                    if show_detail
                    else f"x{required_total_boost:.3f}"
                )
                req_coin_text = f"x{required_coin_mult:.3f}"
                updated_best_boost_text = f"x{updated_best_boost:.3f}" if pd.notna(updated_best_boost) else "---"
                updated_best_coin_text = f"x{updated_best_coin_mult:.3f}" if pd.notna(updated_best_coin_mult) else "---"
            elif req_impossible:
                req_estimated = True
                req_disco = float(solved.get("required_disco", float("nan")))
                req_boost = float(solved.get("required_total_boost", float("nan")))
                req_wave_text = ">5000" if pd.notna(req_disco) and req_disco > 3.0 else "---"
                req_boost_text = (
                    (f"x{req_disco:.3f} / +{other_echo:.3f}" if pd.notna(req_disco) else "---")
                    if show_detail
                    else (f"x{req_boost:.3f}" if pd.notna(req_boost) and req_boost > 3.0 else "---")
                )
                req_coin_text = f"Max. x{max_possible_coin:.3f}" if pd.notna(max_possible_coin) else "---"
                updated_best_boost_text = "---"
                updated_best_coin_text = "---"
            else:
                req_wave_text = "---"
                req_boost_text = "---"
                req_coin_text = "---"
                updated_best_boost_text = "---"
                updated_best_coin_text = "---"

            if row_is_best_tier:
                req_wave_text = "Best Tier"
                req_boost_text = "Best Tier"
                req_coin_text = "Best Tier"
                updated_best_boost_text = "Best Tier"
                updated_best_coin_text = "Best Tier"

            match_body_rows.append(html.Tr([
                html.Td(tier_label, style={
                    "background": _C["sheet_tier_bg"],
                    "border": f"1px solid {_C['sheet_grid']}",
                    "padding": "0.35rem 0.5rem",
                    "textAlign": "center",
                    "whiteSpace": "nowrap",
                    "minWidth": "4.4rem",
                    "fontSize": "1.15rem",
                    "fontWeight": "700",
                    "color": _C["sheet_text"],
                }),
                html.Td(f"x{tier_mult:.2f}" if tier_mult > 0 else "---", style={
                    "background": _C["sheet_tier_bg"],
                    "border": f"1px solid {_C['sheet_grid']}",
                    "padding": "0.35rem 0.45rem",
                    "textAlign": "center",
                    "minWidth": "5.2rem",
                    "fontWeight": "600",
                    "color": _C["sheet_text"],
                }),
                html.Td("---" if utility_wave <= 0 else str(utility_wave), style={
                    "background": _C["sheet_utility"],
                    "border": f"1px solid {_C['sheet_grid']}",
                    "padding": "0.35rem 0.45rem",
                    "textAlign": "center",
                    "minWidth": "4.8rem",
                    "fontWeight": "700",
                    "color": _C["sheet_muted"] if utility_wave <= 0 else _category_colors("utility")["accent"],
                }),
                html.Td(utility_boost_text, style={
                    "background": _C["sheet_utility_max"] if utility_total_boost >= 2.995 else _C["sheet_utility"],
                    "border": f"1px solid {_C['sheet_grid']}",
                    "padding": "0.35rem 0.55rem",
                    "textAlign": "center",
                    "minWidth": "8.8rem",
                    "fontWeight": "700" if utility_total_boost >= 2.995 else "500",
                    "color": _C["boost_max"] if utility_total_boost >= 2.995 else _C["sheet_text"],
                    "whiteSpace": "nowrap",
                }),
                html.Td(f"x{coin_mult:.3f}" if pd.notna(coin_mult) else "---", style={
                    "background": _C["sheet_utility"],
                    "border": f"1px solid {_C['sheet_grid']}",
                    "padding": "0.35rem 0.55rem",
                    "textAlign": "center",
                    "minWidth": "8.8rem",
                    "fontWeight": "600",
                    "color": _C["sheet_text"],
                    "whiteSpace": "nowrap",
                }),
                html.Td(req_wave_text, style={
                    "background": _C["sheet_combined"],
                    "border": f"1px solid {_C['sheet_grid']}",
                    "padding": "0.35rem 0.45rem",
                    "textAlign": "center",
                    "minWidth": "6.2rem",
                    "fontWeight": "400" if req_estimated else "600",
                    "color": _C["sheet_muted"] if req_estimated or req_wave_text == "---" else _category_colors("attack_uw")["accent"],
                }),
                html.Td(req_boost_text, style={
                    "background": _C["sheet_combined"],
                    "border": f"1px solid {_C['sheet_grid']}",
                    "padding": "0.35rem 0.55rem",
                    "textAlign": "center",
                    "minWidth": "8.8rem",
                    "fontWeight": "400" if req_estimated else "600",
                    "color": _C["sheet_muted"] if req_estimated or req_boost_text == "---" else _C["sheet_text"],
                    "whiteSpace": "nowrap",
                }),
                html.Td(req_coin_text, style={
                    "background": _C["sheet_combined"],
                    "border": f"1px solid {_C['sheet_grid']}",
                    "padding": "0.35rem 0.55rem",
                    "textAlign": "center",
                    "minWidth": "8.8rem",
                    "fontWeight": "400" if req_estimated else "600",
                    "color": _C["sheet_muted"] if req_estimated or req_coin_text == "---" else _C["sheet_text"],
                    "whiteSpace": "nowrap",
                }),
                html.Td(updated_best_boost_text, style={
                    "background": _C["sheet_defense"],
                    "border": f"1px solid {_C['sheet_grid']}",
                    "padding": "0.35rem 0.55rem",
                    "textAlign": "center",
                    "minWidth": "8.8rem",
                    "fontWeight": "600",
                    "color": _C["sheet_muted"] if updated_best_boost_text in {"---", "not possible"} else _C["sheet_text"],
                    "whiteSpace": "nowrap",
                }),
                html.Td(updated_best_coin_text, style={
                    "background": _C["sheet_defense"],
                    "border": f"1px solid {_C['sheet_grid']}",
                    "padding": "0.35rem 0.55rem",
                    "textAlign": "center",
                    "minWidth": "8.8rem",
                    "fontWeight": "600",
                    "color": _C["sheet_muted"] if updated_best_coin_text in {"---", "not possible"} else _C["sheet_text"],
                    "whiteSpace": "nowrap",
                }),
            ]))

        match_title_row = html.Tr([
            html.Th("Tier", colSpan=2, style={
                "background": _C["sheet_left_bg"],
                "color": _C["sheet_text"],
                "border": f"1px solid {_C['sheet_grid']}",
                "padding": "0.45rem 0.5rem",
                "width": "4.4rem",
            }),
            html.Th("Match Best Tier Coin Multiplier", colSpan=8, style={
                "background": _C["sheet_title_bg"],
                "color": _C["sheet_title_fg"],
                "border": f"1px solid {_C['sheet_grid']}",
                "padding": "0.45rem 0.5rem",
                "fontWeight": "700",
                "textAlign": "center",
                "fontSize": "1rem",
            }),
        ])

        match_subtitle_row = html.Tr([
            html.Th("", colSpan=2, style={
                "background": _C["sheet_left_bg"],
                "border": f"1px solid {_C['sheet_grid']}",
                "padding": "0.2rem",
            }),
            html.Th(_mode_subtitle(), colSpan=8, style={
                "background": _C["sheet_subtitle_bg"],
                "color": _C["sheet_title_fg"],
                "border": f"1px solid {_C['sheet_grid']}",
                "padding": "0.2rem 0.5rem",
                "textAlign": "center",
                "fontSize": "0.82rem",
                "fontStyle": "italic",
            }),
        ])

        match_header_row = html.Tr([
            html.Th("Tier", colSpan=2, style={
                "background": _C["sheet_left_bg"],
                "color": _C["sheet_text"],
                "border": f"1px solid {_C['sheet_grid']}",
                "padding": "0.35rem 0.5rem",
                "textAlign": "left",
            }),
            html.Th("Current Utility Boost", colSpan=3, style={
                "background": _C["sheet_utility"], "color": _C["sheet_text"], "border": f"1px solid {_C['sheet_grid']}",
                "padding": "0.35rem 0.5rem", "textAlign": "center", "fontWeight": "700", "fontSize": "0.9rem",
            }),
            html.Th("Match", colSpan=3, style={
                "background": _C["sheet_combined"], "color": _C["sheet_text"], "border": f"1px solid {_C['sheet_grid']}",
                "padding": "0.35rem 0.5rem", "textAlign": "center", "fontWeight": "700", "fontSize": "0.9rem",
            }),
            html.Th("Updated Best Farming Tier", colSpan=2, style={
                "background": _C["sheet_defense"], "color": _C["sheet_text"], "border": f"1px solid {_C['sheet_grid']}",
                "padding": "0.35rem 0.5rem", "textAlign": "center", "fontWeight": "700", "fontSize": "0.9rem",
            }),
        ])

        match_subheader_row = html.Tr([
            html.Th("Tier", style={"background": _C["sheet_left_bg"], "color": _C["sheet_muted"], "border": f"1px solid {_C['sheet_grid']}", "padding": "0.2rem 0.35rem", "textAlign": "center", "fontWeight": "600", "fontSize": "0.72rem", "textTransform": "uppercase", "letterSpacing": "0.03em"}),
            html.Th("Tier Difficulty", style={"background": _C["sheet_left_bg"], "color": _C["sheet_muted"], "border": f"1px solid {_C['sheet_grid']}", "padding": "0.2rem 0.35rem", "textAlign": "center", "fontWeight": "600", "fontSize": "0.72rem", "textTransform": "uppercase", "letterSpacing": "0.03em"}),
            html.Th("Wave", style={"background": _C["sheet_utility"], "color": _C["sheet_muted"], "border": f"1px solid {_C['sheet_grid']}", "padding": "0.2rem 0.35rem", "textAlign": "center", "fontWeight": "600", "fontSize": "0.72rem", "textTransform": "uppercase", "letterSpacing": "0.03em"}),
            html.Th("Boost", style={"background": _C["sheet_utility"], "color": _C["sheet_muted"], "border": f"1px solid {_C['sheet_grid']}", "padding": "0.2rem 0.35rem", "textAlign": "center", "fontWeight": "600", "fontSize": "0.72rem", "textTransform": "uppercase", "letterSpacing": "0.03em"}),
            html.Th("Coin Multiplier", style={"background": _C["sheet_utility"], "color": _C["sheet_muted"], "border": f"1px solid {_C['sheet_grid']}", "padding": "0.2rem 0.35rem", "textAlign": "center", "fontWeight": "600", "fontSize": "0.72rem", "textTransform": "uppercase", "letterSpacing": "0.03em"}),
            html.Th("Required Waves", style={"background": _C["sheet_combined"], "color": _C["sheet_muted"], "border": f"1px solid {_C['sheet_grid']}", "padding": "0.2rem 0.35rem", "textAlign": "center", "fontWeight": "600", "fontSize": "0.72rem", "textTransform": "uppercase", "letterSpacing": "0.03em"}),
            html.Th("Required Boost", style={"background": _C["sheet_combined"], "color": _C["sheet_muted"], "border": f"1px solid {_C['sheet_grid']}", "padding": "0.2rem 0.35rem", "textAlign": "center", "fontWeight": "600", "fontSize": "0.72rem", "textTransform": "uppercase", "letterSpacing": "0.03em"}),
            html.Th("Coin Multiplier", style={"background": _C["sheet_combined"], "color": _C["sheet_muted"], "border": f"1px solid {_C['sheet_grid']}", "padding": "0.2rem 0.35rem", "textAlign": "center", "fontWeight": "600", "fontSize": "0.72rem", "textTransform": "uppercase", "letterSpacing": "0.03em"}),
            html.Th("Boost", style={"background": _C["sheet_defense"], "color": _C["sheet_muted"], "border": f"1px solid {_C['sheet_grid']}", "padding": "0.2rem 0.35rem", "textAlign": "center", "fontWeight": "600", "fontSize": "0.72rem", "textTransform": "uppercase", "letterSpacing": "0.03em"}),
            html.Th("Coin Multiplier", style={"background": _C["sheet_defense"], "color": _C["sheet_muted"], "border": f"1px solid {_C['sheet_grid']}", "padding": "0.2rem 0.35rem", "textAlign": "center", "fontWeight": "600", "fontSize": "0.72rem", "textTransform": "uppercase", "letterSpacing": "0.03em"}),
        ])

        combined_table = dbc.Table(
            [
                html.Thead([match_title_row, match_subtitle_row, match_header_row, match_subheader_row]),
                html.Tbody(match_body_rows),
            ],
            bordered=False,
            size="sm",
            responsive=True,
            style={
                "borderCollapse": "collapse",
                "width": "100%",
                "background": _C["sheet_subtitle_bg"],
                "fontFamily": '"Trebuchet MS", "Segoe UI", sans-serif',
                "boxShadow": "0 10px 24px rgba(0, 0, 0, 0.28)",
            },
        )
    else:
        combined_table = dbc.Table(
            [
                html.Thead([title_row, subtitle_row, header_row, subheader_row]),
                html.Tbody(body_rows + [html.Tr(footer_cells)]),
            ],
            bordered=False,
            size="sm",
            responsive=True,
            style={
                "borderCollapse": "collapse",
                "width": "100%",
                "background": _C["sheet_subtitle_bg"],
                "fontFamily": '"Trebuchet MS", "Segoe UI", sans-serif',
                "boxShadow": "0 10px 24px rgba(0, 0, 0, 0.28)",
            },
        )

    matrix_graph = html.Div([
        dcc.Graph(
            id="dissonance-echo-subplots",
            figure=fig,
            config={"displaylogo": False},
            style={"marginBottom": "1rem"},
        ),
    ])

    return None, summary_cards, matrix_graph, combined_table, table
