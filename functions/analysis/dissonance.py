"""Dissonance page helpers."""

from __future__ import annotations

from typing import Dict

import pandas as pd

DISCO_COLUMNS = ["attack", "defense", "utility", "uw"]


def format_dissonance_for_table(df: pd.DataFrame) -> pd.DataFrame:
    """Return a stable, display-ready frame with required columns."""
    if df is None or df.empty:
        return pd.DataFrame(columns=["timestamp", "tier", "wave", "duration", "waves_per_hour", "disco_5000_waves", "disco_type", "comment"])

    out = df.copy()
    defaults = {
        "timestamp": "",
        "tier": "",
        "wave": 0,
        "duration": "",
        "waves_per_hour": pd.NA,
        "disco_5000_waves": pd.NA,
        "disco_type": "",
        "comment": "",
    }
    for col, default in defaults.items():
        if col not in out.columns:
            out[col] = default

    out["wave"] = pd.to_numeric(out["wave"], errors="coerce").fillna(0).astype(int)
    out["timestamp"] = out["timestamp"].fillna("").astype(str)
    out["duration"] = out["duration"].fillna("").astype(str)
    out["waves_per_hour"] = pd.to_numeric(out["waves_per_hour"], errors="coerce").round(2)
    out["disco_5000_waves"] = 5000.0 / pd.to_numeric(out["waves_per_hour"], errors="coerce")
    out.loc[pd.to_numeric(out["waves_per_hour"], errors="coerce") <= 0, "disco_5000_waves"] = pd.NA
    out["disco_5000_waves"] = pd.to_numeric(out["disco_5000_waves"], errors="coerce").round(2)
    out["tier_numeric"] = pd.to_numeric(out["tier"], errors="coerce")
    out = out.sort_values(["tier_numeric", "wave"], ascending=[True, False], na_position="last")
    out = out.drop(columns=["tier_numeric"]).reset_index(drop=True)
    return out[["timestamp", "tier", "wave", "duration", "waves_per_hour", "disco_5000_waves", "disco_type", "comment"]]


def summarize_dissonance(df: pd.DataFrame) -> Dict[str, int]:
    """Count rows by dissonance type using disco_type labels."""
    if df is None or df.empty or "disco_type" not in df.columns:
        return {"total": 0, "attack": 0, "defense": 0, "utility": 0, "uw": 0}

    labels = df["disco_type"].astype(str).str.lower()
    return {
        "total": int(len(df.index)),
        "attack": int(labels.str.contains("attack disco", na=False).sum()),
        "defense": int(labels.str.contains("defense disco", na=False).sum()),
        "utility": int(labels.str.contains("utility disco", na=False).sum()),
        "uw": int(labels.str.contains("uw disco", na=False).sum()),
    }


def disco_bonus(disco_type: str) -> float:
    """Return category bonus: utility=3, all others=5."""
    return 3.0 if str(disco_type).strip().lower() == "utility" else 5.0


def disco_boost(wave: float, disco_type: str) -> tuple[float, float]:
    """Compute disco_boost and echo_boost for one category wave.

    disco_boost = min(1 + (bonus - 1) * ((wave/5000)^1.75), bonus)
    echo_boost  = (disco_boost - 1) * 0.005
    """
    w = float(wave or 0.0)
    if w <= 0:
        return 1.0, 0.0

    bonus = disco_bonus(disco_type)
    growth = 1.0 + (bonus - 1.0) * ((w / 5000.0) ** 1.75)
    d_boost = min(growth, bonus)
    e_boost = (d_boost - 1.0) * 0.005
    return float(d_boost), float(e_boost)


def compute_disco_boost_columns(tier_wave_df: pd.DataFrame) -> pd.DataFrame:
    """Add per-category disco/echo boost columns from tier wave matrix.

    Expected input columns: tier, attack, defense, utility, uw
    """
    if tier_wave_df is None or tier_wave_df.empty:
        return pd.DataFrame(
            columns=[
                "tier",
                "attack", "defense", "utility", "uw",
                "attack_disco_boost", "defense_disco_boost", "utility_disco_boost", "uw_disco_boost",
                "attack_echo_boost", "defense_echo_boost", "utility_echo_boost", "uw_echo_boost",
            ]
        )

    out = tier_wave_df.copy()
    for cat in DISCO_COLUMNS:
        if cat not in out.columns:
            out[cat] = None

        disco_vals = []
        echo_vals = []
        for raw_wave in out[cat].tolist():
            wave_num = pd.to_numeric(pd.Series([raw_wave]), errors="coerce").fillna(0.0).iloc[0]
            d_boost, e_boost = disco_boost(float(wave_num), cat)
            disco_vals.append(d_boost)
            echo_vals.append(e_boost)

        out[f"{cat}_disco_boost"] = disco_vals
        out[f"{cat}_echo_boost"] = echo_vals

    return out


def total_echo_boost(boost_df: pd.DataFrame) -> Dict[str, float]:
    """Return summed echo boost per category from echo boost columns."""
    totals: Dict[str, float] = {}
    if boost_df is None or boost_df.empty:
        for cat in DISCO_COLUMNS:
            totals[cat] = 0.0
        return totals

    for cat in DISCO_COLUMNS:
        col = f"{cat}_echo_boost"
        if col in boost_df.columns:
            totals[cat] = float(pd.to_numeric(boost_df[col], errors="coerce").fillna(0.0).sum())
        else:
            totals[cat] = 0.0
    return totals


def fill_upwards_capped(data: pd.Series, cap: float) -> pd.Series:
    """Fill values upward with a running max, then cap with a running top-down min.

    This mirrors the spreadsheet behavior used for maxed dissonance expectations.
    """
    vals = pd.to_numeric(pd.Series(data), errors="coerce").fillna(0.0).astype(float).tolist()
    n = len(vals)
    if n == 0:
        return pd.Series(dtype=float)

    upward_max = [0.0] * n
    curr_max = 0.0
    for i in range(n - 1, -1, -1):
        curr_max = max(curr_max, vals[i])
        upward_max[i] = curr_max

    final_result = [0.0] * n
    curr_min = float(cap)
    for i in range(n):
        curr_min = min(curr_min, upward_max[i])
        final_result[i] = curr_min

    return pd.Series(final_result, index=pd.Series(data).index)


def build_maxed_disco_columns(tier_wave_df: pd.DataFrame) -> pd.DataFrame:
    """Build max-wave/max-boost columns per disco category.

    Wave max values are filled upward and capped at 5000.
    Boost max values are computed from max wave and capped by category bonus.
    """
    if tier_wave_df is None or tier_wave_df.empty:
        return pd.DataFrame(columns=["tier"])

    out = pd.DataFrame({"tier": tier_wave_df.get("tier", pd.Series(dtype=object))})

    for cat in DISCO_COLUMNS:
        if cat not in tier_wave_df.columns:
            wave_series = pd.Series([0.0] * len(tier_wave_df), index=tier_wave_df.index)
        else:
            wave_series = pd.to_numeric(tier_wave_df[cat], errors="coerce").fillna(0.0)

        max_wave = fill_upwards_capped(wave_series, 5000.0)
        max_disco_vals = []
        max_echo_vals = []
        for w in max_wave.tolist():
            d_boost, e_boost = disco_boost(float(w), cat)
            max_disco_vals.append(d_boost)
            max_echo_vals.append(e_boost)

        out[f"max_{cat}_wave"] = max_wave.astype(float)
        out[f"max_{cat}_disco_boost"] = pd.Series(max_disco_vals, index=max_wave.index)
        out[f"max_{cat}_echo_boost"] = pd.Series(max_echo_vals, index=max_wave.index)

    return out
