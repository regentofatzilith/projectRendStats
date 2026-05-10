"""Shared score utilities for optimizer and datastore flows."""

from __future__ import annotations

from typing import Mapping

import pandas as pd


DEFAULT_SCORE_WEIGHTS = {
    "coins": 1.0 / 3.0,
    "cells": 1.0 / 3.0,
    "shards": 1.0 / 3.0,
}


def normalize_weights(weights: Mapping[str, float] | None = None) -> dict[str, float]:
    """Return normalized score weights for coins/cells/shards."""
    src = dict(DEFAULT_SCORE_WEIGHTS)
    if weights:
        for key in ["coins", "cells", "shards"]:
            if key in weights:
                try:
                    src[key] = float(weights[key])
                except Exception:
                    pass
    total = src["coins"] + src["cells"] + src["shards"]
    if total <= 0:
        return dict(DEFAULT_SCORE_WEIGHTS)
    return {k: v / total for k, v in src.items()}


def compute_normalized_score_100(
    coins_value: float,
    cells_value: float,
    shards_value: float,
    max_coins_per_day: float,
    max_cells_per_day: float,
    max_shards_per_day: float,
    weights: Mapping[str, float] | None = None,
) -> float:
    """Compute normalized score in [0, 100] using per-day maxima."""
    w = normalize_weights(weights)

    def _safe_ratio(v: float, denom: float) -> float:
        try:
            val = float(v)
        except Exception:
            val = 0.0
        try:
            d = float(denom)
        except Exception:
            d = 0.0
        if d <= 0:
            return 0.0
        return max(0.0, val / d)

    score01 = (
        w["coins"] * _safe_ratio(coins_value, max_coins_per_day)
        + w["cells"] * _safe_ratio(cells_value, max_cells_per_day)
        + w["shards"] * _safe_ratio(shards_value, max_shards_per_day)
    )
    return max(0.0, min(100.0, score01 * 100.0))


def compute_max_income_baseline(df: pd.DataFrame) -> dict[str, float]:
    """Compute max per-hour and per-day baselines from a run-level dataframe."""
    if df is None or df.empty:
        return {
            "max_coins_per_hour": 0.0,
            "max_cells_per_hour": 0.0,
            "max_shards_per_hour": 0.0,
            "max_coins_per_day": 0.0,
            "max_cells_per_day": 0.0,
            "max_shards_per_day": 0.0,
        }

    baseline_df = df.copy()

    # Compute max-income baseline from standard progression runs only.
    # This excludes tournament/milestone/quit spikes from normalization anchors.
    if "run_type" in baseline_df.columns:
        allowed_run_types = {"farming", "overnight"}
        run_type_ser = baseline_df["run_type"].astype(str).str.lower()
        filtered = baseline_df[run_type_ser.isin(allowed_run_types)].copy()
        if not filtered.empty:
            baseline_df = filtered

    def _max(col: str) -> float:
        if col not in baseline_df.columns:
            return 0.0
        ser = pd.to_numeric(baseline_df[col], errors="coerce")
        val = float(ser.max()) if not ser.empty else 0.0
        if pd.isna(val):
            return 0.0
        return max(0.0, val)

    max_coins_ph = _max("coins_per_hour")
    max_cells_ph = _max("cells_per_hour")
    max_shards_ph = _max("reroll_shards_per_hour")

    return {
        "max_coins_per_hour": max_coins_ph,
        "max_cells_per_hour": max_cells_ph,
        "max_shards_per_hour": max_shards_ph,
        "max_coins_per_day": max_coins_ph * 24.0,
        "max_cells_per_day": max_cells_ph * 24.0,
        "max_shards_per_day": max_shards_ph * 24.0,
    }
