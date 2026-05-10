"""Dissonance (disco) run extraction from userData gameStats."""

from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

import pandas as pd

try:
    from . import config
except ImportError:
    from functions.data import config

DISCO_LAUNCH_DATE_UTC = pd.Timestamp("2026-04-07", tz="UTC")

NOTE_MARKER_ALIASES: Dict[str, List[str]] = {
    "attack": ["attack disco run", "attack disco"],
    "defense": ["defense disco run", "defense disco"],
    "utility": ["utility disco run", "utility disco"],
    "uw": ["uw disco run", "uw disco"],
}

DISCO_COLUMNS = ["attack", "defense", "utility", "uw"]
DISCO_LABEL_TO_COLUMN = {
    "attack disco": "attack",
    "defense disco": "defense",
    "utility disco": "utility",
    "uw disco": "uw",
}


CRITERIA_ALIASES: Dict[str, List[List[str]]] = {
    "attack": [
        ["Killed by Projectiles", "killed_by_projectiles"],
        ["Killed By Land Mines", "killed_by_land_mines"],
    ],
    "defense": [
        ["Defense Percent Blocked", "defense_percent_blocked"],
        ["Defense Absolute Blocked", "defense_absolute_blocked"],
    ],
    "utility": [
        ["Cash Earned", "cash_earned"],
        ["Interest Earned", "interest_earned"],
    ],
    "uw_damage": [
        ["Killed by ILM", "killed_by_ilm"],
        ["Killed by CL", "killed_by_cl"],
        ["Killed by SM", "killed_by_sm"],
        ["DW Damage", "dw_damage"],
    ],
    "uw_coin": [
        ["Coins from DW", "coins_from_dw"],
        ["Coins from GT", "coins_from_gt"],
        ["Coins from BH", "coins_from_bh"],
        ["Coins from SL", "coins_from_sl"],
    ],
}


def _norm_key(value: Any) -> str:
    return "".join(ch for ch in str(value).lower() if ch.isalnum())


def _to_numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series, errors="coerce").fillna(0.0)


def _resolve_column(df: pd.DataFrame, aliases: Iterable[str]) -> Optional[str]:
    if df.empty:
        return None
    col_map = {_norm_key(col): col for col in df.columns}
    for alias in aliases:
        hit = col_map.get(_norm_key(alias))
        if hit is not None:
            return hit
    return None


def _criterion_zero(df: pd.DataFrame, alias_groups: Iterable[Iterable[str]]) -> pd.Series:
    """Evaluate a criterion where each required field variant must resolve and be zero."""
    result = pd.Series(True, index=df.index)
    for aliases in alias_groups:
        col = _resolve_column(df, aliases)
        if col is None:
            # Missing required field -> criterion cannot be trusted/passed.
            return pd.Series(False, index=df.index)
        result &= _to_numeric(df[col]).eq(0.0)
    return result


def _build_comment(row_flags: Dict[str, bool]) -> str:
    comments: List[str] = []
    if row_flags.get("attack"):
        comments.append("attack disco")
    if row_flags.get("defense"):
        comments.append("defense disco")
    if row_flags.get("utility"):
        comments.append("utility disco")
    if row_flags.get("uw"):
        comments.append("uw disco")
    return ", ".join(comments)


def _note_masks(notes_series: pd.Series, index: pd.Index) -> Dict[str, pd.Series]:
    notes_norm = notes_series.fillna("").astype(str).str.lower()
    masks: Dict[str, pd.Series] = {}
    for label, aliases in NOTE_MARKER_ALIASES.items():
        label_mask = pd.Series(False, index=index)
        for alias in aliases:
            label_mask |= notes_norm.str.contains(alias, regex=False, na=False)
        masks[label] = label_mask
    return masks


def _normalize_run_type(series: pd.Series) -> pd.Series:
    return series.astype(str).str.strip().str.lower().replace("", "farming").fillna("farming")


def _string_or_blank(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value)


def _duration_hours(value: Any) -> float:
    if value is None or pd.isna(value):
        return float("nan")

    if isinstance(value, (int, float)):
        numeric = float(value)
        if numeric <= 0:
            return float("nan")
        # Heuristic: large values here are more likely milliseconds than seconds.
        if numeric > 86400 * 30:
            return numeric / 3600000.0
        return numeric / 3600.0

    text = str(value).strip()
    if not text:
        return float("nan")

    try:
        numeric = float(text)
        if numeric <= 0:
            return float("nan")
        if numeric > 86400 * 30:
            return numeric / 3600000.0
        return numeric / 3600.0
    except ValueError:
        pass

    td = pd.to_timedelta(text, errors="coerce")
    if pd.isna(td):
        return float("nan")
    total_seconds = float(td.total_seconds())
    if total_seconds <= 0:
        return float("nan")
    return total_seconds / 3600.0


def _apply_run_filters(df: pd.DataFrame) -> pd.DataFrame:
    # Ignore deleted runs to match other analytics pages.
    status_col = _resolve_column(df, ["status"])
    if status_col is not None:
        status_series = df[status_col].astype(str).str.lower()
        df = df[~status_series.eq("deleted")].copy()

    # Exclude tournament runs per dissonance requirements.
    run_type_col = _resolve_column(df, ["run_type", "runType"])
    if run_type_col is not None:
        run_type = _normalize_run_type(df[run_type_col])
        df = df[~run_type.eq("tournament")].copy()

    # Ignore runs before the disco feature launch date.
    timestamp_col = _resolve_column(df, ["timestamp", "timeStamp", "date", "created_at"])
    if timestamp_col is not None:
        ts = pd.to_datetime(df[timestamp_col], errors="coerce", utc=True, format="mixed")
        df = df.loc[ts.notna()].copy()
        ts = ts.loc[df.index]
        df = df.loc[ts >= DISCO_LAUNCH_DATE_UTC].copy()

    return df


def _disco_masks(df: pd.DataFrame) -> Dict[str, pd.Series]:
    attack_mask = _criterion_zero(df, CRITERIA_ALIASES["attack"])

    defense_mask = _criterion_zero(df, CRITERIA_ALIASES["defense"])

    utility_mask = _criterion_zero(df, CRITERIA_ALIASES["utility"])

    uw_damage_mask = _criterion_zero(df, CRITERIA_ALIASES["uw_damage"])

    uw_coin_mask = _criterion_zero(df, CRITERIA_ALIASES["uw_coin"])
    uw_mask = uw_damage_mask & uw_coin_mask

    return {
        "attack": attack_mask,
        "defense": defense_mask,
        "utility": utility_mask,
        "uw": uw_mask,
    }


def _resolved_columns(df: pd.DataFrame, alias_groups: Iterable[Iterable[str]]) -> Dict[str, Any]:
    resolved: List[str] = []
    missing: List[str] = []
    for aliases in alias_groups:
        col = _resolve_column(df, aliases)
        label = " | ".join(aliases)
        if col is None:
            missing.append(label)
        else:
            resolved.append(col)
    return {"resolved": resolved, "missing": missing}


def extract_dissonance_runs(game_stats_df: pd.DataFrame) -> pd.DataFrame:
    """Extract dissonance candidate runs.

    Output columns: tier, wave, comment, disco_type
    - comment: sourced from userData run notes field (notes/comment)
    - disco_type: mapped from note markers (attack/defense/utility/uw disco)
    """
    if game_stats_df is None or game_stats_df.empty:
        return pd.DataFrame(columns=["timestamp", "tier", "wave", "duration", "waves_per_hour", "comment", "disco_type"])

    df = _apply_run_filters(game_stats_df.copy())

    if df.empty:
        return pd.DataFrame(columns=["timestamp", "tier", "wave", "duration", "waves_per_hour", "comment", "disco_type"])

    masks = _disco_masks(df)
    any_mask = masks["attack"] | masks["defense"] | masks["utility"] | masks["uw"]

    notes_col = _resolve_column(df, ["notes", "note", "comment"])
    if notes_col is not None:
        note_masks = _note_masks(df[notes_col], df.index)
        note_any = note_masks["attack"] | note_masks["defense"] | note_masks["utility"] | note_masks["uw"]
        selected_mask = note_any
    else:
        note_masks = {
            "attack": pd.Series(False, index=df.index),
            "defense": pd.Series(False, index=df.index),
            "utility": pd.Series(False, index=df.index),
            "uw": pd.Series(False, index=df.index),
        }
        selected_mask = any_mask

    selected = df[selected_mask].copy()

    if selected.empty:
        return pd.DataFrame(columns=["timestamp", "tier", "wave", "duration", "waves_per_hour", "comment", "disco_type"])

    tier_col = _resolve_column(selected, ["tier", "Tier"])
    wave_col = _resolve_column(selected, ["wave", "Wave"])
    notes_col = _resolve_column(selected, ["notes", "note", "comment"])
    timestamp_col = _resolve_column(selected, ["timestamp", "timeStamp", "date", "created_at"])
    duration_col = _resolve_column(selected, ["duration", "runDuration", "run_duration", "timePlayed", "time_played", "elapsed", "elapsedTime", "durationSeconds"])

    out = pd.DataFrame(index=selected.index)
    out["timestamp"] = selected[timestamp_col].map(_string_or_blank) if timestamp_col else ""
    out["tier"] = selected[tier_col] if tier_col else ""
    out["wave"] = pd.to_numeric(selected[wave_col], errors="coerce") if wave_col else 0
    out["duration"] = selected[duration_col].map(_string_or_blank) if duration_col else ""
    out["comment"] = selected[notes_col].fillna("").astype(str) if notes_col else ""

    disco_types: List[str] = []
    for idx in selected.index:
        note_label = _build_comment(
            {
                "attack": bool(note_masks["attack"].loc[idx]),
                "defense": bool(note_masks["defense"].loc[idx]),
                "utility": bool(note_masks["utility"].loc[idx]),
                "uw": bool(note_masks["uw"].loc[idx]),
            }
        )
        if note_label:
            disco_types.append(note_label)
        else:
            # Fallback only used when note markers are unavailable.
            disco_types.append(
                _build_comment(
                    {
                        "attack": bool(masks["attack"].loc[idx]),
                        "defense": bool(masks["defense"].loc[idx]),
                        "utility": bool(masks["utility"].loc[idx]),
                        "uw": bool(masks["uw"].loc[idx]),
                    }
                )
            )
    out["disco_type"] = disco_types
    duration_hours = out["duration"].map(_duration_hours)
    out["waves_per_hour"] = out["wave"] / duration_hours

    out["wave"] = out["wave"].fillna(0).astype(int)
    out["tier_numeric"] = pd.to_numeric(out["tier"], errors="coerce")
    out = out.sort_values(["tier_numeric", "wave"], ascending=[True, False], na_position="last")
    out = out.drop(columns=["tier_numeric"]).reset_index(drop=True)
    return out[["timestamp", "tier", "wave", "duration", "waves_per_hour", "comment", "disco_type"]]


def extract_dissonance_runs_from_json(json_data: Dict[str, Any]) -> pd.DataFrame:
    """Extract dissonance runs directly from userData JSON dict."""
    game_stats = json_data.get("gameStats") if isinstance(json_data, dict) else None
    if isinstance(game_stats, list):
        return extract_dissonance_runs(pd.DataFrame(game_stats))
    if isinstance(game_stats, dict):
        rows: List[Dict[str, Any]] = []
        for run_id, payload in game_stats.items():
            if isinstance(payload, dict):
                row = dict(payload)
                row.setdefault("run_id", run_id)
                rows.append(row)
        return extract_dissonance_runs(pd.DataFrame(rows))
    return pd.DataFrame(columns=["timestamp", "tier", "wave", "duration", "waves_per_hour", "comment", "disco_type"])


def build_disco_tier_map(dissonance_df: pd.DataFrame) -> Dict[str, Dict[str, object]]:
    """Map per-tier max wave for each disco category.

    Output shape per tier:
        {
            "01": {"attack": None, "defense": None, "utility": None, "uw": None},
            ...
        }
    """
    tier_table = build_disco_tier_table(dissonance_df)
    if tier_table.empty:
        return {}

    out: Dict[str, Dict[str, object]] = {}
    for _, row in tier_table.iterrows():
        tier_code = str(row.get("tier", ""))

        def _cell(value: object) -> object:
            numeric = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
            if pd.isna(numeric):
                return None
            try:
                return int(float(numeric))
            except Exception:
                return value

        out[tier_code] = {
            "attack": _cell(row.get("attack")),
            "defense": _cell(row.get("defense")),
            "utility": _cell(row.get("utility")),
            "uw": _cell(row.get("uw")),
        }
    return out


def build_disco_tier_table(dissonance_df: pd.DataFrame) -> pd.DataFrame:
    """Build tier matrix: tier | attack | defense | utility | uw.

    Uses config.TIER_CONFIG as the master tier list. Non-filled cells are None.
    """
    farming_tiers: List[int] = []
    for tier_name, meta in config.TIER_CONFIG.items():
        if not str(tier_name).lower().startswith("tier "):
            continue
        if str(meta.get("type", "")).lower() != "farming":
            continue
        try:
            tier_num = int(str(tier_name).split(" ", 1)[1])
        except Exception:
            continue
        farming_tiers.append(tier_num)

    farming_tiers = sorted(set(farming_tiers))
    base_rows: List[Dict[str, object]] = []
    for tier_num in farming_tiers:
        base_rows.append(
            {
                "tier": f"{tier_num:02d}",
                "attack": None,
                "defense": None,
                "utility": None,
                "uw": None,
            }
        )

    table = pd.DataFrame(base_rows, columns=["tier", "attack", "defense", "utility", "uw"])
    if dissonance_df is None or dissonance_df.empty:
        return table

    df = dissonance_df.copy()
    if "tier" not in df.columns or "wave" not in df.columns or "disco_type" not in df.columns:
        return table

    df["tier_num"] = pd.to_numeric(df["tier"], errors="coerce")
    df["wave_num"] = pd.to_numeric(df["wave"], errors="coerce")
    df = df[df["tier_num"].notna() & df["wave_num"].notna()].copy()
    if df.empty:
        return table

    # Expand row-level disco labels to category columns, then keep max wave per tier/category.
    for label, col_name in DISCO_LABEL_TO_COLUMN.items():
        mask = df["disco_type"].astype(str).str.lower().str.contains(label, na=False)
        if not mask.any():
            continue
        sub = df[mask].copy()
        max_by_tier = sub.groupby("tier_num")["wave_num"].max()
        for tier_num, wave_val in max_by_tier.items():
            tier_num_val = pd.to_numeric(pd.Series([tier_num]), errors="coerce").iloc[0]
            if pd.isna(tier_num_val):
                continue
            tier_code = f"{int(float(tier_num_val)):02d}"
            row_mask = table["tier"] == tier_code
            if row_mask.any():
                table.loc[row_mask, col_name] = int(wave_val)

    return table


def verify_dissonance_logic(game_stats_df: pd.DataFrame) -> Dict[str, Any]:
    """Return a quick verification report for dissonance classification logic."""
    if game_stats_df is None or game_stats_df.empty:
        return {
            "rows_input": 0,
            "rows_after_filters": 0,
            "counts": {"attack": 0, "defense": 0, "utility": 0, "uw": 0, "any": 0},
            "note_counts": {"attack": 0, "defense": 0, "utility": 0, "uw": 0, "any": 0},
            "overlap": {"attack": 0, "defense": 0, "utility": 0, "uw": 0, "any": 0},
            "fields": {},
        }

    filtered = _apply_run_filters(game_stats_df.copy())
    if filtered.empty:
        return {
            "rows_input": int(len(game_stats_df.index)),
            "rows_after_filters": 0,
            "counts": {"attack": 0, "defense": 0, "utility": 0, "uw": 0, "any": 0},
            "note_counts": {"attack": 0, "defense": 0, "utility": 0, "uw": 0, "any": 0},
            "overlap": {"attack": 0, "defense": 0, "utility": 0, "uw": 0, "any": 0},
            "fields": {},
        }

    masks = _disco_masks(filtered)
    any_mask = masks["attack"] | masks["defense"] | masks["utility"] | masks["uw"]
    notes_col = _resolve_column(filtered, ["notes", "note", "comment"])
    if notes_col is not None:
        nm = _note_masks(filtered[notes_col], filtered.index)
    else:
        nm = {
            "attack": pd.Series(False, index=filtered.index),
            "defense": pd.Series(False, index=filtered.index),
            "utility": pd.Series(False, index=filtered.index),
            "uw": pd.Series(False, index=filtered.index),
        }
    note_any = nm["attack"] | nm["defense"] | nm["utility"] | nm["uw"]

    return {
        "rows_input": int(len(game_stats_df.index)),
        "rows_after_filters": int(len(filtered.index)),
        "counts": {
            "attack": int(masks["attack"].sum()),
            "defense": int(masks["defense"].sum()),
            "utility": int(masks["utility"].sum()),
            "uw": int(masks["uw"].sum()),
            "any": int(any_mask.sum()),
        },
        "note_counts": {
            "attack": int(nm["attack"].sum()),
            "defense": int(nm["defense"].sum()),
            "utility": int(nm["utility"].sum()),
            "uw": int(nm["uw"].sum()),
            "any": int(note_any.sum()),
        },
        "overlap": {
            "attack": int((masks["attack"] & nm["attack"]).sum()),
            "defense": int((masks["defense"] & nm["defense"]).sum()),
            "utility": int((masks["utility"] & nm["utility"]).sum()),
            "uw": int((masks["uw"] & nm["uw"]).sum()),
            "any": int((any_mask & note_any).sum()),
        },
        "fields": {
            "attack": _resolved_columns(filtered, CRITERIA_ALIASES["attack"]),
            "defense": _resolved_columns(filtered, CRITERIA_ALIASES["defense"]),
            "utility": _resolved_columns(filtered, CRITERIA_ALIASES["utility"]),
            "uw_damage": _resolved_columns(filtered, CRITERIA_ALIASES["uw_damage"]),
            "uw_coin": _resolved_columns(filtered, CRITERIA_ALIASES["uw_coin"]),
            "notes": notes_col,
            "run_type": _resolve_column(filtered, ["run_type", "runType"]),
            "timestamp": _resolve_column(filtered, ["timestamp", "timeStamp", "date", "created_at"]),
        },
    }
