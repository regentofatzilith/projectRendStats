"""Weekly Optimizer page - 7-day planning with spillover-aware schedule."""

import math
import re
from datetime import datetime, timedelta
from typing import Any, cast

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, callback, dcc, html

from functions import user_data_store
from functions.data.ConvertNumbers import format_display_value
from functions.statistics import compute_normalized_score_100
from functions.graphs import (
    build_daily_income_figure,
    build_current_scenario_daily_income_figure,
    build_current_scenario_weekly_details,
    build_current_scenario_weekly_proposal_figure,
    colors,
    optimize_figure,
)
from functions.ui import standard_card, warning_banner
from functions.graphs.ClusterReview import cluster_review_figure
from functions.graphs.Graphs import generate_optimize_df
from functions.graphs.time_allocation_charts import build_time_allocation_figure
from .metrics_data import build_tier_options

# Register this page
# Keep legacy optimizer untouched and expose a parallel weekly-planning page.
dash.register_page(__name__, path="/optimizer-weekly", name="Optimizer (Weekly)", order=3)

TODAY_DATE = datetime.now().date()
TODAY_WEEKDAY = TODAY_DATE.weekday()
WEEK_MONDAY = TODAY_DATE - timedelta(days=TODAY_WEEKDAY)


def _format_day_label(dt_value: datetime | pd.Timestamp | Any, prefix: str | None = None) -> str:
    ts = pd.Timestamp(dt_value)
    base = ts.strftime('%a %b-%d')
    if prefix:
        base = f"{prefix} {ts.strftime('%b-%d')}"
    if ts.date() == TODAY_DATE:
        base = f"{base} - TODAY"
    return base


DAY_LABELS = [_format_day_label(pd.Timestamp(WEEK_MONDAY) + pd.Timedelta(days=i)) for i in range(7)]
DAY_LABELS.append(_format_day_label(pd.Timestamp(WEEK_MONDAY) + pd.Timedelta(days=7), prefix='Mon+'))

TOURNAMENT_DAYS = {2, 5}  # Wednesday, Saturday in Monday-indexed week


def _parse_sleep_window(value: str | None) -> tuple[float, float]:
    """Parse sleep window string like '22:00-07:00' into (start_h, end_h)."""
    if not value:
        return 22.0, 7.0
    m = re.match(r"\s*(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})\s*$", str(value))
    if not m:
        return 22.0, 7.0
    sh, sm, eh, em = [int(x) for x in m.groups()]
    start_h = float(max(0, min(23, sh))) + float(max(0, min(59, sm))) / 60.0
    end_h = float(max(0, min(23, eh))) + float(max(0, min(59, em))) / 60.0
    return start_h, end_h


def _duration_hours_from_run_row(row: pd.Series) -> float:
    """Extract run duration in hours from available run fields."""
    for gt_col in ["game_time", "gametime"]:
        if gt_col in row and pd.notna(row[gt_col]):
            try:
                return max(0.0, float(row[gt_col]) / 3600.0)
            except Exception:
                pass
    if "real_time" in row and pd.notna(row["real_time"]):
        try:
            return max(0.0, float(str(row["real_time"]).replace("h", "").strip()))
        except Exception:
            return 0.0
    return 0.0


def _current_run_segments(
    df_all_runs: pd.DataFrame | None,
    score_weights: dict[str, float] | None = None,
    max_per_hour: dict[str, float] | None = None,
    lookback_days: int = 7,
) -> list[dict[str, Any]]:
    """Split actual runs into day segments and attach per-segment metrics from one shared source."""
    if df_all_runs is None or df_all_runs.empty or "timestamp" not in df_all_runs.columns:
        return []

    df_runs = df_all_runs.copy()
    ts = pd.to_datetime(df_runs["timestamp"], errors="coerce", utc=True).dt.tz_localize(None)
    df_runs = df_runs.loc[ts.notna()].copy()
    if df_runs.empty:
        return []
    df_runs["timestamp"] = ts.loc[ts.notna()]

    max_ts = pd.to_datetime(df_runs["timestamp"], errors="coerce").max()
    if pd.isna(max_ts):
        return []

    today = max_ts.normalize()
    lookback_days = max(1, int(lookback_days or 7))
    window_start = today - pd.Timedelta(days=lookback_days - 1)
    window_end = today + pd.Timedelta(days=1)

    w_coins = score_weights.get('coins', 1 / 3) if score_weights else 1 / 3
    w_cells = score_weights.get('cells', 1 / 3) if score_weights else 1 / 3
    w_shards = score_weights.get('shards', 1 / 3) if score_weights else 1 / 3
    max_coins_ph = max_per_hour.get('coins', 1.0) if max_per_hour else 1.0
    max_cells_ph = max_per_hour.get('cells', 1.0) if max_per_hour else 1.0
    max_shards_ph = max_per_hour.get('shards', 1.0) if max_per_hour else 1.0

    out: list[dict[str, Any]] = []
    for _, row in df_runs.iterrows():
        row_timestamp = row.get("timestamp")
        if row_timestamp is None:
            continue
        end_ts = pd.to_datetime(row_timestamp, errors="coerce")
        if pd.isna(end_ts):
            continue

        duration_h = _duration_hours_from_run_row(row)
        if duration_h <= 0:
            continue

        start_ts = end_ts - pd.to_timedelta(duration_h, unit="h")
        seg_start = max(start_ts, window_start)
        seg_end = min(end_ts, window_end)
        if seg_end <= seg_start:
            continue

        run_type = str(row.get("run_type", "farming") or "farming")
        tier = row.get("tier", "?")
        coins_earned = float(row.get("coins_earned", 0.0) or 0.0)
        cells_earned = float(row.get("cells_earned", 0.0) or 0.0)
        shards_earned = float(row.get("reroll_shards_earned", 0.0) or 0.0)
        waves_earned = float(row.get("waves_per_tier", row.get("wave", 0.0)) or 0.0)

        if 'optimizer_score' in row and pd.notna(row.get('optimizer_score')):
            total_score = float(row.get('optimizer_score', 0.0) or 0.0)
        else:
            coins_ph = coins_earned / duration_h if duration_h > 0 else 0.0
            cells_ph = cells_earned / duration_h if duration_h > 0 else 0.0
            shards_ph = shards_earned / duration_h if duration_h > 0 else 0.0
            tier_score_coins = coins_ph / (max_coins_ph * 24) if max_coins_ph > 0 else 0.0
            tier_score_cells = cells_ph / (max_cells_ph * 24) if max_cells_ph > 0 else 0.0
            tier_score_shards = shards_ph / (max_shards_ph * 24) if max_shards_ph > 0 else 0.0
            total_score = (w_coins * tier_score_coins + w_cells * tier_score_cells + w_shards * tier_score_shards) * duration_h

        cursor = seg_start
        while cursor < seg_end:
            current_date = cursor.normalize()
            day_end = current_date + pd.Timedelta(days=1)
            chunk_end = min(seg_end, day_end)
            hours = (chunk_end - cursor).total_seconds() / 3600.0
            if hours > 1e-6:
                base_h = (cursor - current_date).total_seconds() / 3600.0
                scale = hours / duration_h if duration_h > 0 else 0.0
                out.append({
                    "day": _format_day_label(current_date),
                    "sort_date": current_date,
                    "base": base_h,
                    "height": hours,
                    "run_type": run_type,
                    "tier": tier,
                    "coins": coins_earned * scale,
                    "cells": cells_earned * scale,
                    "shards": shards_earned * scale,
                    "waves": waves_earned * scale,
                    "score": total_score * scale,
                    "duration": duration_h,
                })
            cursor = chunk_end

    out.sort(key=lambda x: x.get("sort_date", window_start))
    return out


def _current_daily_totals_from_segments(segments: list[dict[str, Any]]) -> pd.DataFrame:
    """Aggregate segmented current runs by day label in chronological order."""
    if not segments:
        return pd.DataFrame(columns=['coins', 'cells', 'shards', 'score'])

    rows = []
    seen_days: list[str] = []
    day_dates: dict[str, pd.Timestamp] = {}
    for seg in segments:
        day_label = str(seg.get('day', ''))
        if not day_label:
            continue
        if day_label not in seen_days:
            seen_days.append(day_label)
            sort_date = seg.get('sort_date')
            day_dates[day_label] = pd.to_datetime(sort_date) if sort_date is not None else pd.Timestamp.min
        rows.append({
            'day': day_label,
            'coins': float(seg.get('coins', 0.0) or 0.0),
            'cells': float(seg.get('cells', 0.0) or 0.0),
            'shards': float(seg.get('shards', 0.0) or 0.0),
            'score': float(seg.get('score', 0.0) or 0.0),
        })

    if not rows:
        return pd.DataFrame(columns=['coins', 'cells', 'shards', 'score'])

    daily_df = pd.DataFrame(rows).groupby('day', as_index=True).sum()
    ordered_days = sorted(day_dates.keys(), key=lambda label: day_dates[label])
    return daily_df.reindex(ordered_days, fill_value=0.0)


def _daily_totals_from_schedule_segments(
    segments: list[dict[str, Any]],
    day_labels: list[str],
    score_weights: dict[str, float] | None,
    max_per_hour: dict[str, float] | None,
) -> pd.DataFrame:
    """Aggregate schedule segments into daily totals (coins/cells/shards/score)."""
    out = pd.DataFrame(0.0, index=day_labels, columns=["coins", "cells", "shards", "score"])
    if not segments:
        return out

    for seg in segments:
        day = str(seg.get("day", ""))
        if day not in out.index:
            continue
        out.at[day, "coins"] = float(cast(Any, out.at[day, "coins"])) + float(seg.get("coins", 0.0) or 0.0)
        out.at[day, "cells"] = float(cast(Any, out.at[day, "cells"])) + float(seg.get("cells", 0.0) or 0.0)
        out.at[day, "shards"] = float(cast(Any, out.at[day, "shards"])) + float(seg.get("shards", 0.0) or 0.0)

    w = score_weights or {"coins": 1.0 / 3.0, "cells": 1.0 / 3.0, "shards": 1.0 / 3.0}
    max_coins_ph = max_per_hour.get("coins", 1.0) if max_per_hour else 1.0
    max_cells_ph = max_per_hour.get("cells", 1.0) if max_per_hour else 1.0
    max_shards_ph = max_per_hour.get("shards", 1.0) if max_per_hour else 1.0

    for day in out.index:
        c = float(cast(Any, out.at[day, "coins"]))
        ce = float(cast(Any, out.at[day, "cells"]))
        s = float(cast(Any, out.at[day, "shards"]))
        out.loc[day, "score"] = compute_normalized_score_100(
            c,
            ce,
            s,
            max_coins_ph * 24.0,
            max_cells_ph * 24.0,
            max_shards_ph * 24.0,
            weights=w,
        )

    return out


def _expand_breakdown_runs(breakdown_df: pd.DataFrame) -> list[dict[str, Any]]:
    """Expand breakdown rows into run-level entries with normalized durations."""
    runs: list[dict[str, Any]] = []
    if breakdown_df is None or breakdown_df.empty:
        return runs

    for _, row in breakdown_df.iterrows():
        run_type = str(row.get("run_type", "farming") or "farming")
        tier = row.get("tier", "?")

        if pd.notna(row.get("runs")) and pd.notna(row.get("duration_per_run")):
            count_val = row.get("runs")
            duration_val = row.get("duration_per_run")
            if count_val is None or duration_val is None:
                continue
            count_float = float(count_val)
            duration = float(duration_val)
            if duration <= 0:
                continue

            full_runs = int(math.floor(count_float))
            remainder = max(0.0, count_float - full_runs)
            for _ in range(full_runs):
                runs.append({"run_type": run_type, "tier": tier, "hours": duration})
            if remainder > 1e-6:
                runs.append({"run_type": run_type, "tier": tier, "hours": duration * remainder})
            continue

        desc = str(row.get("description", "") or "")
        match = re.match(r"(\d+(?:\.\d+)?) x tier ([0-9.+-]+) \(([0-9.]+) h each\)", desc)
        if match:
            count_str, tier_str, duration_str = match.groups()
            count_float = float(count_str)
            duration = float(duration_str)
            if duration <= 0:
                continue
            full_runs = int(math.floor(count_float))
            remainder = max(0.0, count_float - full_runs)
            for _ in range(full_runs):
                runs.append({"run_type": run_type, "tier": tier_str, "hours": duration})
            if remainder > 1e-6:
                runs.append({"run_type": run_type, "tier": tier_str, "hours": duration * remainder})

    return runs


def _run_color(run_type: str, tier: Any) -> str:
    tier_num = 0
    try:
        tier_num = int(float(str(tier).replace("+", "")))
    except Exception:
        tier_num = 0

    if run_type == "tournament":
        return "#991b1b"
    if run_type == "milestone":
        palette = ["#fdba74", "#fb923c", "#f97316", "#ea580c", "#c2410c", "#9a3412"]
        return palette[tier_num % len(palette)]
    if run_type == "quit":
        palette = ["#d1d5db", "#9ca3af", "#6b7280", "#4b5563", "#374151", "#1f2937"]
        return palette[tier_num % len(palette)]
    if run_type == "buffer":
        return "#10b981"

    # Farming tiers: keep tier 11 lighter, then progressively darken with tier.
    if tier_num >= 11:
        farming_palette = ["#9ca3af", "#6b7280", "#52525b", "#3f3f46", "#27272a", "#18181b", "#09090b"]
        idx = min(tier_num - 11, len(farming_palette) - 1)
        return farming_palette[idx]
    return "#9ca3af"


def _weekly_schedule_figure(
    optimize_result: dict[str, Any],
    scenario_key: str,
    sleep_window: str | None,
    all_runs_time_series_df: pd.DataFrame | None = None,
    nighttime_max_runs: int = 1,
    required_tiers: list[int] | None = None,
    forward_schedule: pd.DataFrame | None = None,
    scenario_name: str = "Day+Night",
    best_24h_run: dict[str, Any] | None = None,
    score_weights: dict[str, float] | None = None,
    max_per_hour: dict[str, float] | None = None,
    current_days: int = 7,
    tier_stats: dict[tuple[str, int], dict[str, float]] | None = None,
    return_segments: bool = False,
) -> go.Figure | tuple[go.Figure, list[dict[str, Any]]]:
    """Build a weekly (Mon->Sun + spill Mon+) allocation chart with real time on Y-axis."""
    breakdown_map = {
        "24h": "breakdown_24h",
        "daynight": "breakdown_combined",
        "tournament": "breakdown_tournament",
        "custom": "breakdown_custom",
        "current": "breakdown_current",
    }
    selected_breakdown = optimize_result.get(breakdown_map.get(scenario_key, "breakdown_combined"), pd.DataFrame())
    tournament_breakdown = optimize_result.get("breakdown_tournament", pd.DataFrame())

    selected_runs_all = _expand_breakdown_runs(selected_breakdown)
    tournament_runs_all = [
        r for r in _expand_breakdown_runs(tournament_breakdown)
        if str(r.get("run_type", "")) == "tournament"
    ]

    # Filter out fractional artifact runs (< 1h) — e.g. "2.07 runs" expands to [12h, 12h, 0.84h];
    # the 0.84h partial should never be scheduled as a discrete run.
    base_cycle = [
        r for r in selected_runs_all
        if str(r.get("run_type", "")) != "buffer"
        and float(r.get("hours", 0.0) or 0.0) >= 1.0
    ]
    if scenario_key == "24h" and best_24h_run is not None:
        # 24h scenario intentionally repeats only the top-scoring farming tier.
        base_cycle = [best_24h_run]
    if not base_cycle:
        base_cycle = [{"run_type": "buffer", "tier": "Buffer", "hours": 24.0}]

    required_set = set(int(t) for t in (required_tiers or []))
    w_coins = score_weights.get('coins', 1.0 / 3.0) if score_weights else 1.0 / 3.0
    w_cells = score_weights.get('cells', 1.0 / 3.0) if score_weights else 1.0 / 3.0
    w_shards = score_weights.get('shards', 1.0 / 3.0) if score_weights else 1.0 / 3.0
    max_coins_ph = max_per_hour.get('coins', 1.0) if max_per_hour else 1.0
    max_cells_ph = max_per_hour.get('cells', 1.0) if max_per_hour else 1.0
    max_shards_ph = max_per_hour.get('shards', 1.0) if max_per_hour else 1.0

    def _tier_int_from_run(run: dict[str, Any]) -> int | None:
        try:
            return int(float(str(run.get("tier", "")).replace("+", "").strip()))
        except Exception:
            return None

    # Build a lookup of run duration (hours) per (run_type, tier) from the breakdown runs.
    # Used by the hill-climbing pass to construct candidate higher-tier runs.
    tier_hours_lookup: dict[tuple[str, int], float] = {}
    for _r in selected_runs_all:
        _rt = str(_r.get("run_type", "farming") or "farming").lower()
        _ti = _tier_int_from_run(_r)
        _h = float(_r.get("hours", 0.0) or 0.0)
        if _ti is not None and _h >= 1.0:
            tier_hours_lookup[(_rt, _ti)] = _h

    sleep_start, sleep_end = _parse_sleep_window(sleep_window)
    wake_start = sleep_end if sleep_end != sleep_start else 7.0

    segments: list[dict[str, Any]] = []

    def _run_stats(run: dict[str, Any]) -> dict[str, float]:
        """Resolve run totals from explicit run values first, then run-type+tier stats map."""
        run_type_key = str(run.get("run_type", "farming")).lower()
        tier_key: int | None = None
        try:
            tier_key = int(float(str(run.get("tier", "")).replace("+", "").strip()))
        except Exception:
            pass

        stats_map = tier_stats or {}
        stats: dict[str, float] = {}
        if tier_key is not None:
            stats = stats_map.get((run_type_key, tier_key), {})
            # Only farming may safely fall back to same-tier farming stats.
            if not stats and run_type_key == "farming":
                stats = stats_map.get(("farming", tier_key), {})

        return {
            "coins": float(run.get("coins", stats.get("coins", 0.0)) or 0.0),
            "cells": float(run.get("cells", stats.get("cells", 0.0)) or 0.0),
            "shards": float(run.get("shards", stats.get("shards", 0.0)) or 0.0),
            "waves": float(run.get("waves", stats.get("waves", 0.0)) or 0.0),
        }

    def _run_value_density(run: dict[str, Any]) -> float:
        """Score density used for smart scheduling decisions (higher is better)."""
        dur = float(run.get("hours", 0.0) or 0.0)
        if dur <= 0:
            return -1.0
        # Prefer explicit optimizer score when present; normalize by duration so
        # longer runs are not unfairly preferred just because they are longer.
        try:
            run_score = float(run.get("score", 0.0) or 0.0)
        except Exception:
            run_score = 0.0
        if run_score > 0:
            return run_score / dur

        rs = _run_stats(run)
        coins_ph = rs["coins"] / dur if dur > 0 else 0.0
        cells_ph = rs["cells"] / dur if dur > 0 else 0.0
        shards_ph = rs["shards"] / dur if dur > 0 else 0.0

        coins_term = (coins_ph / max_coins_ph) if max_coins_ph > 0 else 0.0
        cells_term = (cells_ph / max_cells_ph) if max_cells_ph > 0 else 0.0
        shards_term = (shards_ph / max_shards_ph) if max_shards_ph > 0 else 0.0
        return (w_coins * coins_term) + (w_cells * cells_term) + (w_shards * shards_term)

    def push_segment(start_h: float, end_h: float, run: dict[str, Any]) -> None:
        """Split one continuous run into per-day segments for plotting."""
        start = float(start_h)
        end = float(end_h)
        full_run_hours = float(run.get("hours", 0.0) or (end_h - start_h))

        rs = _run_stats(run)
        run_coins = rs["coins"]
        run_cells = rs["cells"]
        run_shards = rs["shards"]
        run_waves = rs["waves"]

        while start < end and start < 192.0:
            day_idx = int(start // 24.0)
            if day_idx < 0 or day_idx >= len(DAY_LABELS):
                break
            day_end = min((day_idx + 1) * 24.0, 192.0)
            seg_end = min(end, day_end)
            if seg_end <= start:
                break
            duration = seg_end - start
            scale = duration / full_run_hours if full_run_hours > 0 else 0.0
            segments.append({
                "day": DAY_LABELS[day_idx],
                "base": start - (day_idx * 24.0),
                "height": duration,
                "run_type": str(run.get("run_type", "farming")),
                "tier": run.get("tier", "?"),
                "coins": run_coins * scale,
                "cells": run_cells * scale,
                "shards": run_shards * scale,
                "waves": run_waves * scale,
                "score": float(run.get("score", 0.0)) if "score" in run else 0.0,
                "full_duration": full_run_hours,
            })
            start = seg_end

    # Handle different scenarios
    # ── Hill-climb: try replacing lower-income runs with higher-tier versions ──────────────
    # Applies only to Day+Night / Custom (scheduling-loop scenarios, not 24h/current/forward).
    if scenario_key not in ("24h", "current", "forward") and (tier_stats or tier_hours_lookup):

        def _score_segments(segs: list[dict[str, Any]]) -> float:
            total = 0.0
            for s in segs:
                dur = s.get("height", 0.0) or 0.0
                if dur <= 0:
                    continue
                coins_ph = (s.get("coins", 0.0) or 0.0) / dur
                cells_ph = (s.get("cells", 0.0) or 0.0) / dur
                shards_ph = (s.get("shards", 0.0) or 0.0) / dur
                total += dur * (
                    w_coins * (coins_ph / max_coins_ph if max_coins_ph > 0 else 0.0)
                    + w_cells * (cells_ph / max_cells_ph if max_cells_ph > 0 else 0.0)
                    + w_shards * (shards_ph / max_shards_ph if max_shards_ph > 0 else 0.0)
                )
            return total

        def _simulate_daynight(cycle: list[dict[str, Any]]) -> list[dict[str, Any]]:
            """Run the Day+Night/Custom schedule with `cycle` and return the resulting segments.
            Used for hill-climbing comparisons before the real schedule build."""
            sim_segments: list[dict[str, Any]] = []
            sim_time = wake_start
            sim_spill_quota = max(0, int(nighttime_max_runs or 0))
            sim_required_spill = set(required_set) if scenario_key == "custom" else set()
            sim_cycle_idx = 0

            def _sim_pick_fit(remaining: float) -> dict[str, Any] | None:
                nonlocal sim_cycle_idx
                if remaining <= 1e-6 or not cycle:
                    return None
                fitting = [
                    r for r in cycle
                    if 0 < float(r.get("hours", 0.0) or 0.0) <= remaining + 1e-6
                    and not (scenario_key == "custom" and _tier_int_from_run(r) in sim_required_spill)
                ]
                if not fitting:
                    fitting = [r for r in cycle if 0 < float(r.get("hours", 0.0) or 0.0) <= remaining + 1e-6]
                if not fitting:
                    return None
                fitting.sort(key=_run_value_density, reverse=True)
                return fitting[0]

            def _sim_pick_spill() -> dict[str, Any] | None:
                nonlocal sim_cycle_idx
                if not cycle:
                    return None
                if scenario_key == "custom" and sim_required_spill:
                    for i in range(len(cycle)):
                        r = cycle[(sim_cycle_idx + i) % len(cycle)]
                        ti = _tier_int_from_run(r)
                        if ti is not None and ti in sim_required_spill:
                            sim_required_spill.discard(ti)
                            sim_cycle_idx += i + 1
                            return r
                cands = [r for r in cycle if float(r.get("hours", 0.0) or 0.0) > 0]
                if not cands:
                    return None
                cands.sort(key=_run_value_density, reverse=True)
                return cands[0]

            def _sim_push(start: float, end: float, run: dict[str, Any]) -> None:
                full_h = float(run.get("hours", 0.0) or (end - start))
                rs = _run_stats(run)
                s = start
                while s < end and s < 192.0:
                    di = int(s // 24.0)
                    if di < 0 or di >= len(DAY_LABELS):
                        break
                    se = min(end, (di + 1) * 24.0, 192.0)
                    if se <= s:
                        break
                    dur = se - s
                    scale = dur / full_h if full_h > 0 else 0.0
                    sim_segments.append({
                        "day": DAY_LABELS[di], "base": s - di * 24.0, "height": dur,
                        "run_type": str(run.get("run_type", "farming")),
                        "tier": run.get("tier", "?"),
                        "coins": rs["coins"] * scale, "cells": rs["cells"] * scale,
                        "shards": rs["shards"] * scale, "waves": rs["waves"] * scale,
                        "score": 0.0, "full_duration": full_h,
                    })
                    s = se

            for di in range(7):
                d_start = float(di * 24)
                d_wake = d_start + wake_start
                d_sleep = d_start + sleep_start
                if d_sleep <= d_wake:
                    d_sleep += 24.0

                if di in TOURNAMENT_DAYS and tournament_runs_all:
                    # Global rule: no runs start before wakeup.
                    if sim_time < d_wake:
                        sim_time = d_wake
                    for tr in tournament_runs_all:
                        td = float(tr.get("hours", 0.0) or 0.0)
                        if td > 0:
                            _sim_push(sim_time, sim_time + td, tr)
                            sim_time += td

                if sim_time < d_wake:
                    sim_time = d_wake

                dc = min(d_sleep, d_start + 24.0)
                while sim_time < dc - 1e-6:
                    run = _sim_pick_fit(dc - sim_time)
                    if run is None:
                        break
                    dur = float(run.get("hours", 0.0) or 0.0)
                    if dur <= 0:
                        break
                    _sim_push(sim_time, sim_time + dur, run)
                    sim_time += dur

                sc = 0
                while sc < sim_spill_quota and sim_time <= d_sleep + 1e-6:
                    sr = _sim_pick_spill()
                    if sr is None or sim_time > d_sleep + 1e-6:
                        break
                    dur = float(sr.get("hours", 0.0) or 0.0)
                    if dur <= 0:
                        break
                    _sim_push(sim_time, sim_time + dur, sr)
                    sim_time += dur
                    sc += 1

            return sim_segments

        # Hill-climb: replace the lowest-density run in base_cycle with next higher tier,
        # re-simulate the full week, keep if total score improves. Repeat until stable.
        best_cycle = list(base_cycle)
        best_score = _score_segments(_simulate_daynight(best_cycle))
        improved = True
        _max_passes = 10  # safety cap
        while improved and _max_passes > 0:
            improved = False
            _max_passes -= 1
            # Sort runs by density ascending so we try replacing the weakest first.
            sorted_runs = sorted(
                enumerate(best_cycle),
                key=lambda x: _run_value_density(x[1]),
            )
            for slot_idx, slot_run in sorted_runs:
                rt = str(slot_run.get("run_type", "farming") or "farming").lower()
                ti = _tier_int_from_run(slot_run)
                if ti is None:
                    continue
                # Try next tiers up (1 step at a time, up to 3 tiers higher).
                for delta in range(1, 4):
                    next_tier = ti + delta
                    if (rt, next_tier) not in (tier_stats or {}):
                        break  # no data for this tier, stop trying higher
                    next_hours = tier_hours_lookup.get((rt, next_tier), 0.0)
                    if next_hours < 1.0:
                        break  # no duration data — can't schedule it
                    # Build candidate run with the higher tier's stats.
                    next_stats = (tier_stats or {}).get((rt, next_tier), {})
                    candidate_run = dict(slot_run)
                    candidate_run["tier"] = str(next_tier)
                    candidate_run["hours"] = next_hours
                    candidate_run.update({
                        k: v for k, v in next_stats.items()
                        if k in ("coins", "cells", "shards", "waves")
                    })
                    test_cycle = list(best_cycle)
                    test_cycle[slot_idx] = candidate_run
                    test_score = _score_segments(_simulate_daynight(test_cycle))
                    if test_score > best_score + 1e-9:
                        best_cycle = test_cycle
                        best_score = test_score
                        improved = True
                        break  # restart outer while with new best_cycle
                if improved:
                    break  # restart from sorted_runs with updated cycle
        base_cycle = best_cycle

    if scenario_key == "forward" and forward_schedule is not None and not forward_schedule.empty:
        # Forward optimization: use absolute times directly
        for _, run in forward_schedule.iterrows():
            start_abs = float(run.get('start_absolute', 0.0))
            end_abs = start_abs + float(run.get('duration', 0.0))
            run_dict = dict(run)
            push_segment(start_abs, end_abs, run_dict)

    elif scenario_key == "current":
        segments = _current_run_segments(
            all_runs_time_series_df,
            score_weights=score_weights,
            max_per_hour=max_per_hour,
            lookback_days=current_days,
        )
    else:
        current_time = 0.0 if scenario_key == "24h" else wake_start
        cycle_idx = 0
        night_spill_quota = max(0, int(nighttime_max_runs or 0))
        required_for_spill_remaining = set(required_set) if scenario_key == "custom" else set()

        def _pick_fit_run(remaining_hours: float) -> dict[str, Any] | None:
            nonlocal cycle_idx
            if remaining_hours <= 1e-6:
                return None
            n = len(base_cycle)
            if n == 0:
                return None

            fitting_non_reserved: list[dict[str, Any]] = []
            fitting_any: list[dict[str, Any]] = []
            for run in base_cycle:
                h = float(run.get("hours", 0.0) or 0.0)
                if not (0 < h <= remaining_hours + 1e-6):
                    continue
                fitting_any.append(run)
                tier_i = _tier_int_from_run(run)
                if scenario_key == "custom" and tier_i is not None and tier_i in required_for_spill_remaining:
                    continue
                fitting_non_reserved.append(run)

            target = fitting_non_reserved if fitting_non_reserved else fitting_any
            if not target:
                return None
            target.sort(
                key=lambda run: (
                    _run_value_density(run),
                    float(run.get("hours", 0.0) or 0.0),
                ),
                reverse=True,
            )
            return target[0]

        def _pick_spill_run() -> dict[str, Any] | None:
            nonlocal cycle_idx
            if not base_cycle:
                return None
            if scenario_key == "custom" and required_for_spill_remaining:
                for i in range(len(base_cycle)):
                    run = base_cycle[(cycle_idx + i) % len(base_cycle)]
                    tier_i = _tier_int_from_run(run)
                    if tier_i is not None and tier_i in required_for_spill_remaining:
                        required_for_spill_remaining.discard(tier_i)
                        cycle_idx = cycle_idx + i + 1
                        return run
            candidates = [r for r in base_cycle if float(r.get("hours", 0.0) or 0.0) > 0]
            if not candidates:
                return None
            candidates.sort(
                key=lambda run: (
                    _run_value_density(run),
                    float(run.get("hours", 0.0) or 0.0),
                ),
                reverse=True,
            )
            return candidates[0]

        # ── 24h: one continuous timeline, no per-day clipping ──────────────────
        if scenario_key == "24h":
            best_run = base_cycle[0] if base_cycle else {"run_type": "buffer", "tier": "Buffer", "hours": 24.0}
            best_run_hours = float(best_run.get("hours", 0.0) or 0.0)
            if best_run_hours <= 0:
                best_run_hours = 24.0

            # Track which tournament days have had their tournaments inserted.
            _tourn_done: set[int] = set()
            _t = 0.0
            _total = 7 * 24.0

            while _t < _total - 1e-6:
                _day_idx = int(_t // 24.0)

                # Tournament days: at the first run boundary inside the tournament day,
                # insert the tournament block before the next farming run.
                if (
                    _day_idx in TOURNAMENT_DAYS
                    and _day_idx not in _tourn_done
                    and tournament_runs_all
                    and _t >= _day_idx * 24.0  # we're actually inside this day
                ):
                    _tourn_done.add(_day_idx)
                    for _tr in tournament_runs_all:
                        _td = float(_tr.get("hours", 0.0) or 0.0)
                        if _td <= 0:
                            continue
                        push_segment(_t, _t + _td, _tr)
                        _t += _td

                # Full farming run — no capping to day boundary.
                push_segment(_t, _t + best_run_hours, best_run)
                _t += best_run_hours

        else:
            # ── Day+Night / Custom / etc: per-day wake/sleep schedule ───────────
            for day_idx in range(7):
                day_start = float(day_idx * 24)
                day_end = float((day_idx + 1) * 24)
                day_wake = day_start + wake_start
                day_sleep = day_start + sleep_start
                if day_sleep <= day_wake:
                    day_sleep += 24.0

                if day_idx in TOURNAMENT_DAYS and tournament_runs_all:
                    # Global rule: no runs start before wakeup.
                    if current_time < day_wake:
                        current_time = day_wake
                    # Tournament starts right after spill, but never before wake.
                    for tr in tournament_runs_all:
                        dur = float(tr.get("hours", 0.0) or 0.0)
                        if dur <= 0:
                            continue
                        push_segment(current_time, current_time + dur, tr)
                        current_time = current_time + dur

                # Farming runs start earliest at wake time (rule 2).
                if current_time < day_wake:
                    current_time = day_wake

                daytime_cutoff = min(day_sleep, day_end)
                while current_time < daytime_cutoff - 1e-6:
                    remaining = daytime_cutoff - current_time
                    run = _pick_fit_run(remaining)
                    if run is None:
                        break
                    dur = float(run.get("hours", 0.0) or 0.0)
                    if dur <= 0:
                        break
                    start = current_time
                    end = start + dur
                    push_segment(start, end, run)
                    current_time = end

                spill_count = 0
                while spill_count < night_spill_quota and current_time <= day_sleep + 1e-6:
                    spill_run = _pick_spill_run()
                    if spill_run is None:
                        break
                    dur = float(spill_run.get("hours", 0.0) or 0.0)
                    if dur <= 0:
                        break
                    start = current_time
                    if start > day_sleep + 1e-6:
                        break
                    end = start + dur
                    push_segment(start, end, spill_run)
                    current_time = end
                    spill_count += 1

    categoryarray = None
    if scenario_key != "current":
        categoryarray = DAY_LABELS

    fig = build_time_allocation_figure(
        segments,
        title=f"Weekly Proposal ({scenario_name})",
        colors=colors,
        score_weights={'coins': w_coins, 'cells': w_cells, 'shards': w_shards},
        max_per_hour={'coins': max_coins_ph, 'cells': max_cells_ph, 'shards': max_shards_ph},
        categoryarray=categoryarray,
    )
    if return_segments:
        return fig, segments
    return fig


layout = html.Div([
    html.H1("Run Optimizer & Weekly Planning", className="page-title"),
    html.Div(id="optimizer-weekly-no-data-warning"),

    html.P([
        "This weekly optimizer projects your runs into a Monday-Sunday plan with explicit spillover into Monday+. ",
        "Configure your sleep schedule and tier preferences below.",
    ], style={"marginBottom": "1.5rem", "color": "#9ca3af"}),

    html.H3("Optimizer Score Weights"),
    dbc.Row([
        dbc.Col([
            html.Label("Coins Weight"),
            dcc.Input(
                id="optw-score-weight-coins",
                type="number",
                min=0,
                max=1,
                step=0.01,
                value=0.34,
                style={"width": "100%"},
            ),
        ], width=4),
        dbc.Col([
            html.Label("Cells Weight"),
            dcc.Input(
                id="optw-score-weight-cells",
                type="number",
                min=0,
                max=1,
                step=0.01,
                value=0.33,
                style={"width": "100%"},
            ),
        ], width=4),
        dbc.Col([
            html.Label("Reroll Shards Weight"),
            dcc.Input(
                id="optw-score-weight-shards-display",
                type="number",
                value=0.33,
                readOnly=True,
                style={"width": "100%", "backgroundColor": "#1f2937", "color": "#d1d5db"},
            ),
            html.Div("Auto: 1 - (coins + cells)", style={"fontSize": "0.8rem", "color": "#9ca3af", "marginTop": "0.35rem"}),
        ], width=4),
    ], className="mb-4"),

    html.H3("Tier Selection"),
    dbc.Row([
        dbc.Col([
            html.Label("Filter Tiers (optional)"),
            dcc.Dropdown(
                id="optw-tier-filter",
                options=[],
                value=None,
                placeholder="All tiers (or select specific tiers to exclude from optimization)",
                multi=True,
                clearable=True,
            ),
        ], width=4),
        dbc.Col([
            html.Label("Required Tiers (optional)"),
            dcc.Dropdown(
                id="optw-required-tiers",
                options=[],
                value=["Tier 12"],
                placeholder="No requirements (or select tiers that must appear at least once per day)",
                multi=True,
                clearable=True,
            ),
        ], width=4),
        dbc.Col([
            html.Label("Tournament Runs"),
            dcc.Input(
                id="optw-tournament-runs",
                type="number",
                value=2,
                min=0,
                max=10,
                step=1,
                style={"width": "100%"},
            ),
        ], width=4),
    ], className="mb-3"),

    dbc.Row([
        dbc.Col([
            html.Label("Tournament Tier"),
            dcc.Dropdown(
                id="optw-tournament-tier",
                options=[
                    {"label": "Copper: Tier 1+", "value": 1},
                    {"label": "Silver: Tier 3+", "value": 3},
                    {"label": "Gold: Tier 5+", "value": 5},
                    {"label": "Platinum: Tier 8+", "value": 8},
                    {"label": "Champion: Tier 12+", "value": 12},
                    {"label": "Legend: Tier 17+", "value": 17},
                ],
                value=12,
                clearable=False,
            ),
        ], width=4),
        dbc.Col([
            html.Label("Detailed Scenario"),
            dcc.Dropdown(
                id="optw-detailed-scenario",
                options=[
                    {"label": "Day+Night", "value": "daynight"},
                    {"label": "24h", "value": "24h"},
                    {"label": "Custom", "value": "custom"},
                    {"label": "Current", "value": "current"},
                ],
                value="daynight",
                clearable=False,
            ),
        ], width=4),
        dbc.Col([
            html.Label("Sleep Window (HH:MM-HH:MM)"),
            dcc.Input(
                id="optw-sleep-window",
                type="text",
                value="22:00-07:00",
                style={"width": "100%"},
            ),
        ], width=4),
    ], className="mb-3"),

    html.Div(id="optw-tier-warning", style={"marginBottom": "1rem"}),

    html.H3("Detailed Scenario Results", style={"marginTop": "2rem"}),
    html.P([
        "Shows daily income for the currently selected detailed scenario. ",
        "For Current, values come from recent actual runs. For optimizer scenarios, values are based on optimizer daily averages.",
    ], style={"marginBottom": "1rem", "color": "#9ca3af", "fontSize": "0.9rem"}),
    html.Div(id="optw-forward-summary", style={"marginBottom": "1rem"}),
    dbc.Row([dbc.Col(dcc.Graph(id="optw-forward-graph"), width=12)], className="mb-4"),

    html.H3("Weekly Proposal (Spillover-aware)", style={"marginTop": "2rem"}),
    html.P([
        "Shows how the selected scenario is distributed across the week (Mon-Sun) with respect to your sleep schedule. ",
        "Use the ", html.Strong("Detailed Scenario"), " dropdown to select: ",
        html.Strong("Day+Night"), ", ",
        html.Strong("24h"), ", ",
        html.Strong("Custom"), " (required tiers), or ",
        html.Strong("Current"), " (actual recent runs). ",
        "Overnight runs that exceed bedtime spill into Monday+. Tournament runs are automatically scheduled on Wed/Sat.",
    ], style={"marginBottom": "1rem", "color": "#9ca3af", "fontSize": "0.9rem"}),
    dbc.Row([dbc.Col(dcc.Graph(id="optw-weekly-graph"), width=12)], className="mb-4"),

    html.H3("Optimization Results (Daily Average Income)", style={"marginTop": "2rem"}),
    html.P([
        "Compare different optimization scenarios. ",
        html.Strong("24h"), " shows theoretical maximum income with no sleep time. ",
        html.Strong("Day+Night"), " shows realistic income accounting for your sleep schedule. ",
        html.Strong("Custom"), " appears when required tiers are selected. ",
        html.Strong("Current"), " shows your actual recent performance.",
    ], style={"marginBottom": "1rem", "color": "#9ca3af", "fontSize": "0.9rem"}),
    dbc.Row([dbc.Col(dcc.Graph(id="optw-optimizer-graph"), width=12)], className="mb-4"),

    html.H3("Cluster Review", style={"marginTop": "2rem"}),
    dbc.Row([
        dbc.Col([
            html.Label("Cluster Review Period"),
            dcc.Dropdown(
                id="optw-cluster-review-period",
                options=[
                    {"label": "1 Week", "value": 7},
                    {"label": "2 Weeks", "value": 14},
                    {"label": "3 Weeks", "value": 21},
                    {"label": "1 Month", "value": 30},
                    {"label": "2 Months", "value": 60},
                ],
                value=14,
                clearable=False,
            ),
        ], width=4),
        dbc.Col([
            html.Label("View Mode"),
            dbc.Checklist(
                id="optw-cluster-review-weighted",
                options=[{"label": "Weighted stacked bars", "value": "weighted"}],
                value=["weighted"],
                switch=True,
            ),
        ], width=4),
    ], className="mb-3"),
    dbc.Row([dbc.Col(dcc.Graph(id="optw-cluster-review-graph"), width=12)], className="mb-4"),
])


@callback(
    [
        Output("optw-score-weight-shards-display", "value"),
        Output("optw-forward-graph", "figure"),
        Output("optw-forward-summary", "children"),
        Output("optw-optimizer-graph", "figure"),
        Output("optw-weekly-graph", "figure"),
        Output("optw-cluster-review-graph", "figure"),
        Output("optw-tier-filter", "options"),
        Output("optw-required-tiers", "options"),
        Output("optw-tier-warning", "children"),
        Output("optimizer-weekly-no-data-warning", "children"),
    ],
    [
        Input("optw-score-weight-coins", "value"),
        Input("optw-score-weight-cells", "value"),
        Input("optw-tier-filter", "value"),
        Input("optw-required-tiers", "value"),
        Input("optw-tournament-runs", "value"),
        Input("optw-tournament-tier", "value"),
        Input("optw-detailed-scenario", "value"),
        Input("optw-sleep-window", "value"),
        Input("optw-cluster-review-period", "value"),
        Input("optw-cluster-review-weighted", "value"),
        Input("user-json-store", "data"),
    ],
)
def update_optimizer_weekly(
    score_weight_coins,
    score_weight_cells,
    tier_filter,
    required_tiers,
    tournament_runs,
    tournament_tier,
    detailed_scenario,
    sleep_window,
    cluster_review_days,
    cluster_review_weighted,
    user_json_state,
):
    """Update weekly optimizer and companion views."""
    
    # Use fixed values for removed parameters
    nighttime_max_runs = 1  # Always 1
    current_days = 7  # Always 7 days
    
    # Calculate daytime hours from sleep window
    sleep_start, sleep_end = _parse_sleep_window(sleep_window)
    if sleep_end > sleep_start:
        daytime_hours = int(24.0 - (sleep_end - sleep_start))
    else:
        daytime_hours = int(24.0 - (24.0 - sleep_start + sleep_end))
    daytime_hours = max(8, min(24, daytime_hours))  # Clamp between 8 and 24
    
    cluster_review_days = int(cluster_review_days or 14)

    optimizer_df = user_data_store.cleaned.get("grouped_by_tier_df", pd.DataFrame())
    grouped_by_run_type_tier_df = user_data_store.cleaned.get("grouped_by_run_type_tier_df", pd.DataFrame())
    filtered_df = user_data_store.cleaned.get("filtered_df", pd.DataFrame())
    time_series_df = user_data_store.cleaned.get("time_series_df", pd.DataFrame())
    all_runs_time_series_df = user_data_store.cleaned.get("all_runs_time_series_df", pd.DataFrame())
    max_income_baseline_df = user_data_store.cleaned.get("max_income_baseline_df", pd.DataFrame())

    from functions.statistics.ClusterDetection import detect_clusters
    if filtered_df is not None and not filtered_df.empty:
        cluster_df, _ = detect_clusters(filtered_df, cluster_review_days=cluster_review_days)
    else:
        cluster_df = pd.DataFrame()

    tier_options = build_tier_options(optimizer_df)

    if optimizer_df.empty:
        warning = warning_banner(
            "No optimizer data loaded. Please check that your userData.json contains farming/overnight run data."
        )
        return 0.33, go.Figure(), None, go.Figure(), go.Figure(), go.Figure(), tier_options, tier_options, None, warning

    df_to_optimize = optimizer_df.copy()
    if tier_filter and len(tier_filter) > 0:
        tier_filter_int = [int(t) for t in tier_filter]
        df_to_optimize = df_to_optimize[df_to_optimize["tier"].isin(tier_filter_int)]
        if df_to_optimize.empty:
            warning = warning_banner(f"No data available for filtered tiers: {tier_filter}")
            return 0.33, go.Figure(), None, go.Figure(), go.Figure(), go.Figure(), tier_options, tier_options, warning, None

    def _safe_max(series: pd.Series) -> float:
        try:
            val = float(series.max())
            return 0.0 if pd.isna(val) else val
        except Exception:
            return 0.0

    # Initialize weights with defaults. Shards is derived from coins/cells.
    coins_in = float(score_weight_coins if score_weight_coins is not None else 0.34)
    cells_in = float(score_weight_cells if score_weight_cells is not None else 0.33)
    shards_in = max(0.0, 1.0 - (coins_in + cells_in))
    weights = [coins_in, cells_in, shards_in]
    weight_sum = sum(weights)
    if weight_sum <= 0:
        weights = [0.34, 0.33, 0.33]
        weight_sum = 1.0
    w_coins, w_cells, w_shards = [w / weight_sum for w in weights]
    
    # Initialize max per-hour values with defaults
    max_coins_per_hour = 0.0
    max_cells_per_hour = 0.0
    max_shards_per_hour = 0.0

    tier_stats: dict[tuple[str, int], dict[str, float]] = {}

    # Shared duration parser used by optimizer summaries and raw run history.
    def _coerce_duration_hours(value: Any) -> float:
        if value is None or (isinstance(value, float) and pd.isna(value)):
            return 0.0
        if isinstance(value, str):
            token = value.strip().lower().replace("h", "")
            try:
                raw = float(token)
            except Exception:
                return 0.0
        else:
            try:
                raw = float(value)
            except Exception:
                return 0.0

        if raw > 72.0:
            return raw / 3600.0
        return raw

    if not df_to_optimize.empty:
        mean_rows = df_to_optimize[df_to_optimize.get("level_1") == "mean"] if "level_1" in df_to_optimize.columns else df_to_optimize

        # Derive per-hour maxima directly from absolute earnings and duration whenever possible.
        # Some imported datasets contain stale/inconsistent *_per_hour columns.
        def _derived_per_hour_max(amount_col: str, fallback_rate_col: str) -> float:
            rate_from_column = _safe_max(mean_rows.get(fallback_rate_col, pd.Series([0.0])))
            if amount_col not in mean_rows.columns or "real_time" not in mean_rows.columns:
                return rate_from_column

            durations = mean_rows["real_time"].apply(_coerce_duration_hours)
            amounts = pd.to_numeric(mean_rows[amount_col], errors="coerce")
            valid = (durations > 0) & amounts.notna()
            if not valid.any():
                return rate_from_column

            derived_rate = _safe_max(amounts[valid] / durations[valid])
            return max(rate_from_column, derived_rate)

        max_coins_per_hour = _derived_per_hour_max("coins_earned", "coins_per_hour")
        max_cells_per_hour = _derived_per_hour_max("cells_earned", "cells_per_hour")
        max_shards_per_hour = _derived_per_hour_max("reroll_shards_earned", "reroll_shards_per_hour")

        if max_income_baseline_df is not None and not max_income_baseline_df.empty:
            base_row = max_income_baseline_df.iloc[0]
            base_coins_ph = float(base_row.get("max_coins_per_hour", 0.0) or 0.0)
            base_cells_ph = float(base_row.get("max_cells_per_hour", 0.0) or 0.0)
            base_shards_ph = float(base_row.get("max_shards_per_hour", 0.0) or 0.0)
            max_coins_per_hour = max(max_coins_per_hour, base_coins_ph)
            max_cells_per_hour = max(max_cells_per_hour, base_cells_ph)
            max_shards_per_hour = max(max_shards_per_hour, base_shards_ph)

        denom_coins = max_coins_per_hour * 24 if max_coins_per_hour else _safe_max(mean_rows.get("coins_earned", pd.Series([0.0])))
        denom_cells = max_cells_per_hour * 24 if max_cells_per_hour else _safe_max(mean_rows.get("cells_earned", pd.Series([0.0])))
        denom_shards = max_shards_per_hour * 24 if max_shards_per_hour else _safe_max(mean_rows.get("reroll_shards_earned", pd.Series([0.0])))

        def _safe_norm(series: pd.Series, denom: float) -> pd.Series:
            if denom and not pd.isna(denom):
                return series / denom
            return pd.Series([0.0] * len(series), index=series.index)

        df_to_optimize = df_to_optimize.copy()
        df_to_optimize["optimizer_score"] = (
            _safe_norm(df_to_optimize.get("coins_earned", pd.Series([0.0])), denom_coins) * w_coins
            + _safe_norm(df_to_optimize.get("cells_earned", pd.Series([0.0])), denom_cells) * w_cells
            + _safe_norm(df_to_optimize.get("reroll_shards_earned", pd.Series([0.0])), denom_shards) * w_shards
        ) * 100

        # Build per-tier income lookup for weekly schedule tooltips from optimizer aggregates.
        for _, _sr in mean_rows.iterrows():
            try:
                _t = int(float(str(_sr.get("tier", "0"))))
            except Exception:
                continue
            _dur = _coerce_duration_hours(_sr.get("real_time"))
            if _dur <= 0:
                continue
            _run_type = str(_sr.get("run_type", "farming") or "farming").lower()
            tier_stats[(_run_type, _t)] = {
                "coins": float(_sr.get("coins_earned", 0.0) or 0.0),
                "cells": float(_sr.get("cells_earned", 0.0) or 0.0),
                "shards": float(_sr.get("reroll_shards_earned", 0.0) or 0.0),
                "waves": float(_sr.get("waves_per_tier", _sr.get("wave", 0.0)) or 0.0),
            }

    # Canonical all-run-type tier stats from datastore for tournament and any other non-farming rows.
    if grouped_by_run_type_tier_df is not None and not grouped_by_run_type_tier_df.empty:
        grouped_mean_rows = (
            grouped_by_run_type_tier_df[grouped_by_run_type_tier_df.get("level_1") == "mean"]
            if "level_1" in grouped_by_run_type_tier_df.columns
            else grouped_by_run_type_tier_df
        )
        for _, _sr in grouped_mean_rows.iterrows():
            try:
                _t = int(float(str(_sr.get("tier", "0"))))
            except Exception:
                continue
            _run_type = str(_sr.get("run_type", "farming") or "farming").lower()
            if _run_type == "farming" and (_run_type, _t) in tier_stats:
                continue
            tier_stats[(_run_type, _t)] = {
                "coins": float(_sr.get("coins_earned", 0.0) or 0.0),
                "cells": float(_sr.get("cells_earned", 0.0) or 0.0),
                "shards": float(_sr.get("reroll_shards_earned", 0.0) or 0.0),
                "waves": float(_sr.get("waves_per_tier", _sr.get("wave", 0.0)) or 0.0),
            }

    # Keep Tier 12 as default only when the dropdown is unset (initial load).
    if required_tiers is None:
        required_tiers_int = [12]
    elif len(required_tiers) > 0:
        required_tiers_int = [int(t) for t in required_tiers]
    else:
        required_tiers_int = None

    selected_scenario = str(detailed_scenario or "daynight").lower()

    daytime_hours_val = int(daytime_hours or 16)
    nighttime_max_runs_val = int(nighttime_max_runs or 1)
    current_days_val = int(current_days or 3)
    tournament_runs_val = int(tournament_runs or 2)
    tournament_tier_val = int(tournament_tier or 12)

    def _best_24h_run_template(df_for_choice: pd.DataFrame) -> dict[str, Any] | None:
        if df_for_choice is None or df_for_choice.empty:
            return None
        mean_rows = df_for_choice[df_for_choice.get("level_1") == "mean"] if "level_1" in df_for_choice.columns else df_for_choice
        if mean_rows.empty:
            return None

        # Prefer farming runs for pure 24h chaining; fall back to global best if needed.
        farm_rows = mean_rows[mean_rows["run_type"].astype(str).str.lower() == "farming"] if "run_type" in mean_rows.columns else mean_rows
        candidates = farm_rows if not farm_rows.empty else mean_rows

        candidates = candidates.copy()
        if "optimizer_score" not in candidates.columns or "real_time" not in candidates.columns or "tier" not in candidates.columns:
            return None
        candidates["optimizer_score"] = pd.to_numeric(candidates["optimizer_score"], errors="coerce")
        candidates["real_time"] = pd.to_numeric(candidates["real_time"], errors="coerce")
        candidates = candidates.dropna(subset=["optimizer_score", "real_time", "tier"]) 
        candidates = candidates[candidates["real_time"] > 0]
        if candidates.empty:
            return None

        best_row = candidates.sort_values(["optimizer_score", "real_time"], ascending=[False, False]).iloc[0]
        try:
            best_tier = int(float(str(best_row.get("tier"))))
        except Exception:
            best_tier = str(best_row.get("tier", "?"))
        return {
            "run_type": "farming",
            "tier": best_tier,
            "hours": float(best_row.get("real_time", 0.0) or 0.0),
            "coins": float(best_row.get("coins_earned", 0.0) or 0.0),
            "cells": float(best_row.get("cells_earned", 0.0) or 0.0),
            "shards": float(best_row.get("reroll_shards_earned", 0.0) or 0.0),
        }

    def _daily_totals_from_summary(summary_df: pd.DataFrame) -> pd.DataFrame:
        """Project one-day optimizer summary as a flat Mon-Sun profile (Mon+ set to zero)."""
        labels = DAY_LABELS.copy()
        out = pd.DataFrame(0.0, index=labels, columns=['coins', 'cells', 'shards', 'score'])
        if summary_df is None or summary_df.empty:
            return out
        mean_rows = summary_df[summary_df.get('confidence') == 'mean'] if 'confidence' in summary_df.columns else summary_df
        if mean_rows.empty:
            return out
        row = mean_rows.iloc[0]
        coins = float(row.get('coins_earned', 0.0) or 0.0)
        cells = float(row.get('cells_earned', 0.0) or 0.0)
        shards = float(row.get('reroll_shards_earned', 0.0) or 0.0)
        score = compute_normalized_score_100(
            coins,
            cells,
            shards,
            max_coins_per_hour * 24.0,
            max_cells_per_hour * 24.0,
            max_shards_per_hour * 24.0,
            weights={'coins': w_coins, 'cells': w_cells, 'shards': w_shards},
        )
        for day_label in DAY_LABELS[:7]:
            out.loc[day_label, ['coins', 'cells', 'shards', 'score']] = [coins, cells, shards, score]
        return out

    def _build_daily_income_figure(daily_totals_df: pd.DataFrame, title: str) -> go.Figure:
        return build_daily_income_figure(
            daily_totals_df,
            title=title,
            no_results_title='Detailed Scenario: No Results',
            max_per_day=max_per_day,
        )

    def _build_24h_back_to_back_outputs(best_run: dict[str, Any] | None) -> tuple[pd.DataFrame, pd.DataFrame]:
        labels = DAY_LABELS.copy()
        daily = pd.DataFrame(0.0, index=labels, columns=['coins', 'cells', 'shards', 'score'])
        if not best_run:
            return daily, pd.DataFrame()

        duration = float(best_run.get('hours', 0.0) or 0.0)
        if duration <= 0:
            return daily, pd.DataFrame()

        runs_per_day = 24.0 / duration
        coins_per_run = float(best_run.get('coins', 0.0) or 0.0)
        cells_per_run = float(best_run.get('cells', 0.0) or 0.0)
        shards_per_run = float(best_run.get('shards', 0.0) or 0.0)

        coins_day = coins_per_run * runs_per_day
        cells_day = cells_per_run * runs_per_day
        shards_day = shards_per_run * runs_per_day
        score_day = compute_normalized_score_100(
            coins_day,
            cells_day,
            shards_day,
            max_coins_per_hour * 24.0,
            max_cells_per_hour * 24.0,
            max_shards_per_hour * 24.0,
            weights={'coins': w_coins, 'cells': w_cells, 'shards': w_shards},
        )

        for day_label in DAY_LABELS[:7]:
            daily.loc[day_label, ['coins', 'cells', 'shards', 'score']] = [coins_day, cells_day, shards_day, score_day]

        summary = pd.DataFrame([
            {
                'confidence': conf,
                'coins_earned': coins_day,
                'cells_earned': cells_day,
                'reroll_shards_earned': shards_day,
                'score': score_day,
                'total_duration': 24.0,
            }
            for conf in ['ci_lower', 'mean', 'ci_upper']
        ])
        return daily, summary

    optimize_result = generate_optimize_df(
        df_to_optimize,
        daytime_hours_val,
        time_series_df,
        all_runs_time_series_df,
        current_days=current_days_val,
        nighttime_max_runs=nighttime_max_runs_val,
        required_tiers=required_tiers_int,
        tournament_runs=tournament_runs_val,
        tournament_tier=tournament_tier_val,
    )

    best_24h_run = _best_24h_run_template(df_to_optimize)
    daily_24h_back_to_back, summary_24h_back_to_back = _build_24h_back_to_back_outputs(best_24h_run)
    if not summary_24h_back_to_back.empty:
        optimize_result['summary_24h'] = summary_24h_back_to_back

    forward_fig = go.Figure()
    scenario_daily_map = {
        "daynight": "Day+Night",
        "24h": "24h",
        "custom": "Custom",
        "current": "Current",
    }
    current_details = build_current_scenario_weekly_details(
        all_runs_time_series_df,
        score_weights={'coins': w_coins, 'cells': w_cells, 'shards': w_shards},
        max_per_hour={'coins': max_coins_per_hour, 'cells': max_cells_per_hour, 'shards': max_shards_per_hour},
        current_days=current_days_val,
    )
    current_daily_complete = cast(pd.DataFrame, current_details['daily_complete'])
    max_per_day = {
        'coins': max_coins_per_hour * 24.0,
        'cells': max_cells_per_hour * 24.0,
        'shards': max_shards_per_hour * 24.0,
    }

    if selected_scenario == "current":
        forward_fig = build_current_scenario_daily_income_figure(
            current_details,
            title="Current Scenario: Daily Income",
            max_per_day=max_per_day,
        )
    elif selected_scenario == "24h":
        forward_fig = _build_daily_income_figure(
            daily_24h_back_to_back,
            "Detailed Scenario (24h): Daily Income",
        )
    else:
        summary_map_for_daily = {
            'daynight': 'summary_combined',
            '24h': 'summary_24h',
            'custom': 'summary_custom',
        }
        summary_key_for_daily = summary_map_for_daily.get(selected_scenario, 'summary_combined')
        daily_totals = _daily_totals_from_summary(optimize_result.get(summary_key_for_daily, pd.DataFrame()))
        forward_fig = _build_daily_income_figure(
            daily_totals,
            f"Detailed Scenario ({scenario_daily_map.get(selected_scenario, 'Day+Night')}): Daily Income",
        )

    # Keep Current scenario source identical across optimizer graph and comparison table.
    # Build summary_current from the same segmented-daily dataframe used below in the table.
    if not current_daily_complete.empty:
        summary_current_override = pd.DataFrame([
            {
                'confidence': 'ci_lower',
                'coins_earned': float(current_daily_complete['coins'].quantile(0.16)),
                'cells_earned': float(current_daily_complete['cells'].quantile(0.16)),
                'reroll_shards_earned': float(current_daily_complete['shards'].quantile(0.16)),
                'score': float(current_daily_complete['score'].quantile(0.16)),
            },
            {
                'confidence': 'mean',
                'coins_earned': float(current_daily_complete['coins'].mean()),
                'cells_earned': float(current_daily_complete['cells'].mean()),
                'reroll_shards_earned': float(current_daily_complete['shards'].mean()),
                'score': float(current_daily_complete['score'].mean()),
            },
            {
                'confidence': 'ci_upper',
                'coins_earned': float(current_daily_complete['coins'].quantile(0.84)),
                'cells_earned': float(current_daily_complete['cells'].quantile(0.84)),
                'reroll_shards_earned': float(current_daily_complete['shards'].quantile(0.84)),
                'score': float(current_daily_complete['score'].quantile(0.84)),
            },
        ])
    else:
        summary_current_override = pd.DataFrame([
            {
                'confidence': 'ci_lower',
                'coins_earned': 0.0,
                'cells_earned': 0.0,
                'reroll_shards_earned': 0.0,
                'score': 0.0,
            },
            {
                'confidence': 'mean',
                'coins_earned': 0.0,
                'cells_earned': 0.0,
                'reroll_shards_earned': 0.0,
                'score': 0.0,
            },
            {
                'confidence': 'ci_upper',
                'coins_earned': 0.0,
                'cells_earned': 0.0,
                'reroll_shards_earned': 0.0,
                'score': 0.0,
            },
        ])

    optimize_result['summary_current'] = summary_current_override

    optimizer_graph, opt_warning = optimize_figure(
        df_to_optimize,
        daytime_hours_val,
        time_series_df,
        all_runs_time_series_df,
        current_days=current_days_val,
        nighttime_max_runs=nighttime_max_runs_val,
        required_tiers=required_tiers_int,
        tournament_runs=tournament_runs_val,
        tournament_tier=tournament_tier_val,
        show_time_allocation=False,
        show_tournament=False,
        precomputed_result=optimize_result,
    )

    # Map scenario key to human-readable name
    scenario_name_map = {
        "daynight": "Day+Night (Realistic Schedule)",
        "24h": "24h (No Sleep)",
        "custom": "Custom (Required Tiers)",
        "current": "Current (Recent Actual Runs)"
    }
    scenario_display_name = scenario_name_map.get(selected_scenario, "Day+Night")

    if selected_scenario == "current":
        weekly_graph = build_current_scenario_weekly_proposal_figure(
            current_details,
            score_weights={'coins': w_coins, 'cells': w_cells, 'shards': w_shards},
            max_per_hour={'coins': max_coins_per_hour, 'cells': max_cells_per_hour, 'shards': max_shards_per_hour},
            title=f"Weekly Proposal ({scenario_display_name})",
        )
    else:
        weekly_graph, weekly_segments = cast(
            tuple[go.Figure, list[dict[str, Any]]],
            _weekly_schedule_figure(
            optimize_result,
            selected_scenario,
            sleep_window,
            all_runs_time_series_df,
            nighttime_max_runs=nighttime_max_runs_val,
            required_tiers=required_tiers_int,
            scenario_name=scenario_display_name,
            best_24h_run=(best_24h_run if selected_scenario == "24h" else None),
            score_weights={'coins': w_coins, 'cells': w_cells, 'shards': w_shards},
            max_per_hour={'coins': max_coins_per_hour, 'cells': max_cells_per_hour, 'shards': max_shards_per_hour},
            current_days=current_days_val,
            tier_stats=tier_stats,
            return_segments=True,
            ),
        )

        # Keep detailed income chart in sync with the actual weekly schedule placement.
        # This makes tournament/spillover days visibly differ from regular days.
        scheduled_daily_totals = _daily_totals_from_schedule_segments(
            weekly_segments,
            DAY_LABELS,
            score_weights={'coins': w_coins, 'cells': w_cells, 'shards': w_shards},
            max_per_hour={'coins': max_coins_per_hour, 'cells': max_cells_per_hour, 'shards': max_shards_per_hour},
        )
        forward_fig = _build_daily_income_figure(
            scheduled_daily_totals,
            f"Detailed Scenario ({scenario_daily_map.get(selected_scenario, 'Day+Night')}): Daily Income",
        )

    weighted_view = bool(cluster_review_weighted and "weighted" in cluster_review_weighted)
    cluster_review_graph = cluster_review_figure(cluster_df, weighted=weighted_view)

    optimizer_warning = None
    if opt_warning:
        optimizer_warning = html.Div(
            [html.Strong("Optimization Warning: "), opt_warning],
            style={"color": "#f97316", "background": "#222", "padding": "1rem", "borderRadius": "6px"},
        )
    
    # Build comparison table across all scenarios using summaries (actual income data)
    scenario_keys = ["max_income", "24h", "daynight", "custom", "current"]
    scenario_labels = ["Max Income", "24h", "Day+Night", "Custom", "Current"]
    summary_map = {
        "24h": "summary_24h",
        "daynight": "summary_combined",
        "custom": "summary_custom",
        "current": "summary_current",
    }
    scenario_summaries = {}
    
    for scenario_key, scenario_label in zip(scenario_keys, scenario_labels):
        if scenario_key == "max_income":
            max_coins_per_day = float(max_coins_per_hour * 24.0)
            max_cells_per_day = float(max_cells_per_hour * 24.0)
            max_shards_per_day = float(max_shards_per_hour * 24.0)
            scenario_summaries[scenario_label] = {
                'coins_hour': float(max_coins_per_hour),
                'cells_hour': float(max_cells_per_hour),
                'shards_hour': float(max_shards_per_hour),
                'score_hour': 100.0,
                'coins_daily': max_coins_per_day,
                'cells_daily': max_cells_per_day,
                'shards_daily': max_shards_per_day,
                'score_daily': 100.0,
                'coins_weekly': max_coins_per_day * 7.0,
                'cells_weekly': max_cells_per_day * 7.0,
                'shards_weekly': max_shards_per_day * 7.0,
                'score_weekly': 700.0,
            }
            continue
        elif scenario_key == "current":
            if not current_daily_complete.empty:
                total_coins = float(current_daily_complete['coins'].mean())
                total_cells = float(current_daily_complete['cells'].mean())
                total_shards = float(current_daily_complete['shards'].mean())
                total_score = compute_normalized_score_100(
                    total_coins,
                    total_cells,
                    total_shards,
                    max_coins_per_hour * 24.0,
                    max_cells_per_hour * 24.0,
                    max_shards_per_hour * 24.0,
                    weights={'coins': w_coins, 'cells': w_cells, 'shards': w_shards},
                )
                num_days = int(len(current_daily_complete))
            else:
                total_coins = total_cells = total_shards = total_score = 0.0
                num_days = max(1, current_days_val)
        elif scenario_key == "24h" and not summary_24h_back_to_back.empty:
            mean_row_24h = summary_24h_back_to_back[summary_24h_back_to_back['confidence'] == 'mean'].iloc[0]
            total_coins = float(mean_row_24h.get('coins_earned', 0.0) or 0.0)
            total_cells = float(mean_row_24h.get('cells_earned', 0.0) or 0.0)
            total_shards = float(mean_row_24h.get('reroll_shards_earned', 0.0) or 0.0)
            total_score = float(mean_row_24h.get('score', 0.0) or 0.0)
            num_days = 7
        else:
            summary_key = summary_map.get(scenario_key, "summary_combined")
            summary_df = optimize_result.get(summary_key, pd.DataFrame())
            if not summary_df.empty:
                mean_rows = summary_df[summary_df.get("confidence") == "mean"] if "confidence" in summary_df.columns else summary_df
                if not mean_rows.empty:
                    row = mean_rows.iloc[0]
                    total_coins = float(row.get("coins_earned", 0.0) or 0.0)
                    total_cells = float(row.get("cells_earned", 0.0) or 0.0)
                    total_shards = float(row.get("reroll_shards_earned", 0.0) or 0.0)
                    total_score = compute_normalized_score_100(
                        total_coins,
                        total_cells,
                        total_shards,
                        max_coins_per_hour * 24.0,
                        max_cells_per_hour * 24.0,
                        max_shards_per_hour * 24.0,
                        weights={'coins': w_coins, 'cells': w_cells, 'shards': w_shards},
                    )
                else:
                    total_coins = total_cells = total_shards = total_score = 0.0
            else:
                total_coins = total_cells = total_shards = total_score = 0.0
            num_days = 7  # Standard week

        # Each summary value is already a per-day total (optimizer runs for 1 day window)
        scenario_summaries[scenario_label] = {
            'coins_hour': total_coins / 24.0,
            'cells_hour': total_cells / 24.0,
            'shards_hour': total_shards / 24.0,
            'score_hour': total_score, # Score is already normalized to max per day, so it's effectively a per-hour average when divided by 24
            'coins_daily': total_coins,
            'cells_daily': total_cells,
            'shards_daily': total_shards,
            'score_daily': total_score,
            'coins_weekly': total_coins * num_days,
            'cells_weekly': total_cells * num_days,
            'shards_weekly': total_shards * num_days,
            'score_weekly': total_score * num_days,
        }
    
    separator_color = "#4b5563"
    metric_group_row_style = {
        "display": "flex",
        "gap": "0.5rem",
        "marginLeft": "0.75rem",
        "paddingLeft": "0.75rem",
        "borderLeft": f"1px solid {separator_color}",
    }
    metric_group_header_style = {
        "display": "flex",
        "flexDirection": "column",
        "marginLeft": "0.75rem",
        "paddingLeft": "0.75rem",
        "borderLeft": f"1px solid {separator_color}",
    }

    # Build comparison table HTML
    forward_summary_div = standard_card([
        html.H5("Optimization Comparison", style={"marginBottom": "0.75rem"}),
        html.Div([
            html.Div(f"Detailed Scenario: {scenario_display_name}", 
                     style={"marginBottom": "0.75rem", "fontSize": "0.9rem", "color": "#9ca3af"}),
        ]),
        # Comparison table
        html.Div([
            # Header row with column groups
            html.Div([
                html.Div("Scenario", style={"width": "100px", "fontWeight": "bold", "paddingRight": "1rem"}),
                # Per-hour group
                html.Div([
                    html.Div("Per Hour Avg", style={"fontWeight": "bold", "textAlign": "center", "marginBottom": "0.25rem"}),
                    html.Div([
                        html.Div("Coins", style={"width": "80px", "textAlign": "center", "fontWeight": "bold", "color": colors['coins']}),
                        html.Div("Cells", style={"width": "80px", "textAlign": "center", "fontWeight": "bold", "color": colors['cells']}),
                        html.Div("Shards", style={"width": "90px", "textAlign": "center", "fontWeight": "bold", "color": colors['reroll']}),
                        html.Div("Score", style={"width": "70px", "textAlign": "center", "fontWeight": "bold", "color": colors['score']}),
                    ], style={"display": "flex", "gap": "0.5rem"}),
                ], style=metric_group_header_style),
                # Daily group
                html.Div([
                    html.Div("Daily Avg", style={"fontWeight": "bold", "textAlign": "center", "marginBottom": "0.25rem"}),
                    html.Div([
                        html.Div("Coins", style={"width": "80px", "textAlign": "center", "fontWeight": "bold", "color": colors['coins']}),
                        html.Div("Cells", style={"width": "80px", "textAlign": "center", "fontWeight": "bold", "color": colors['cells']}),
                        html.Div("Shards", style={"width": "90px", "textAlign": "center", "fontWeight": "bold", "color": colors['reroll']}),
                        html.Div("Score", style={"width": "70px", "textAlign": "center", "fontWeight": "bold", "color": colors['score']}),
                    ], style={"display": "flex", "gap": "0.5rem"}),
                ], style=metric_group_header_style),
                # Weekly group
                html.Div([
                    html.Div("Weekly Total", style={"fontWeight": "bold", "textAlign": "center", "marginBottom": "0.25rem"}),
                    html.Div([
                        html.Div("Coins", style={"width": "80px", "textAlign": "center", "fontWeight": "bold", "color": colors['coins']}),
                        html.Div("Cells", style={"width": "80px", "textAlign": "center", "fontWeight": "bold", "color": colors['cells']}),
                        html.Div("Shards", style={"width": "90px", "textAlign": "center", "fontWeight": "bold", "color": colors['reroll']}),
                        html.Div("Score", style={"width": "70px", "textAlign": "center", "fontWeight": "bold", "color": colors['score']}),
                    ], style={"display": "flex", "gap": "0.5rem"}),
                ], style=metric_group_header_style),
            ], style={"display": "flex", "marginBottom": "0.5rem", "paddingBottom": "0.5rem", "borderBottom": "1px solid #374151"}),
            # Data rows
            *[
                html.Div([
                    html.Div(scenario_label, style={"width": "100px", "fontWeight": "bold", "paddingRight": "1rem"}),
                    # Per-hour values
                    html.Div([
                        html.Div(format_display_value(scenario_summaries[scenario_label]['coins_daily'] / 24.0), style={"width": "80px", "textAlign": "center"}),
                        html.Div(format_display_value(scenario_summaries[scenario_label]['cells_daily'] / 24.0), style={"width": "80px", "textAlign": "center"}),
                        html.Div(format_display_value(scenario_summaries[scenario_label]['shards_daily'] / 24.0), style={"width": "90px", "textAlign": "center"}),
                        html.Div(format_display_value(scenario_summaries[scenario_label]['score_hour']), style={"width": "70px", "textAlign": "center"}),
                    ], style=metric_group_row_style),
                    # Daily values
                    html.Div([
                        html.Div(format_display_value(scenario_summaries[scenario_label]['coins_daily']), style={"width": "80px", "textAlign": "center"}),
                        html.Div(format_display_value(scenario_summaries[scenario_label]['cells_daily']), style={"width": "80px", "textAlign": "center"}),
                        html.Div(format_display_value(scenario_summaries[scenario_label]['shards_daily']), style={"width": "90px", "textAlign": "center"}),
                        html.Div(format_display_value(scenario_summaries[scenario_label]['score_daily']), style={"width": "70px", "textAlign": "center"}),
                    ], style=metric_group_row_style),
                    # Weekly values
                    html.Div([
                        html.Div(format_display_value(scenario_summaries[scenario_label]['coins_weekly']), style={"width": "80px", "textAlign": "center"}),
                        html.Div(format_display_value(scenario_summaries[scenario_label]['cells_weekly']), style={"width": "80px", "textAlign": "center"}),
                        html.Div(format_display_value(scenario_summaries[scenario_label]['shards_weekly']), style={"width": "90px", "textAlign": "center"}),
                        html.Div(format_display_value(scenario_summaries[scenario_label]['score_weekly']), style={"width": "70px", "textAlign": "center"}),
                    ], style=metric_group_row_style),
                ], style={"display": "flex", "marginBottom": "0.25rem"})
                for scenario_label in scenario_labels
            ],
        ], style={"fontFamily": "monospace", "fontSize": "0.85rem", "lineHeight": "1.6", "overflowX": "auto"}),
    ])

    return round(shards_in, 2), forward_fig, forward_summary_div, optimizer_graph, weekly_graph, cluster_review_graph, tier_options, tier_options, optimizer_warning, None
