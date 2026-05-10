"""Reusable timeline/schedule chart renderers (stacked base-height bars)."""

from typing import Any

import plotly.graph_objs as go

from functions.data.ConvertNumbers import format_display_value
from functions.statistics import compute_normalized_score_100


DAY_TICK_VALUES = [0, 4, 8, 12, 16, 20, 24]


def run_color(run_type: str, tier: Any) -> str:
    """Consistent color mapping for run timeline bars."""
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
        palette = ["#f3e8ff", "#d8b4fe", "#c084fc", "#a855f7", "#7e22ce", "#581c87"]
        return palette[tier_num % len(palette)]
    if run_type == "disco":
        # Dissonance runs: teal/cyan spectrum — distinct from farming grays and tournament red.
        # Future tweak: shade by subcategory (attack/defense/utility/uw) when disco_type is available.
        palette = ["#67e8f9", "#22d3ee", "#06b6d4", "#0891b2", "#0e7490", "#155e75"]
        return palette[tier_num % len(palette)]
    if run_type == "buffer":
        return "#10b981"

    if tier_num >= 11:
        farming_palette = ["#9ca3af", "#6b7280", "#52525b", "#3f3f46", "#27272a", "#18181b", "#09090b"]
        idx = min(tier_num - 11, len(farming_palette) - 1)
        return farming_palette[idx]
    return "#9ca3af"


def build_time_allocation_figure(
    segments: list[dict[str, Any]],
    title: str,
    colors: dict[str, str],
    score_weights: dict[str, float] | None = None,
    max_per_hour: dict[str, float] | None = None,
    categoryarray: list[str] | None = None,
) -> go.Figure:
    """Render stacked base/height bars for segmented runs on a 24h day axis."""
    fig = go.Figure()
    if not segments:
        fig.update_layout(
            title='Weekly Proposal: No Results',
            plot_bgcolor=colors['background'],
            paper_bgcolor=colors['background'],
            font_color=colors['text'],
        )
        return fig

    weights = score_weights or {'coins': 1.0 / 3.0, 'cells': 1.0 / 3.0, 'shards': 1.0 / 3.0}
    max_coins_ph = max_per_hour.get('coins', 1.0) if max_per_hour else 1.0
    max_cells_ph = max_per_hour.get('cells', 1.0) if max_per_hour else 1.0
    max_shards_ph = max_per_hour.get('shards', 1.0) if max_per_hour else 1.0

    seen_legend: set[str] = set()
    for seg in segments:
        run_type = str(seg.get('run_type', 'farming'))
        if run_type == 'buffer':
            continue

        tier = seg.get('tier', '?')
        label = f"{run_type.capitalize()}, Tier {tier}"
        show_legend = label not in seen_legend
        seen_legend.add(label)

        base_hours = float(seg.get('base', 0.0) or 0.0)
        base_hours_int = int(base_hours)
        base_minutes = int((base_hours - base_hours_int) * 60)
        start_time_str = f"{base_hours_int:02d}:{base_minutes:02d}"
        finish_hours = base_hours + float(seg.get('height', 0.0) or 0.0)
        finish_hours_int = int(finish_hours)
        finish_minutes = int((finish_hours - finish_hours_int) * 60)
        finish_time_str = f"{finish_hours_int:02d}:{finish_minutes:02d}"
        duration_str = f"{float(seg.get('height', 0.0) or 0.0):.2f}h"

        coins_val = float(seg.get('coins', 0.0) or 0.0)
        cells_val = float(seg.get('cells', 0.0) or 0.0)
        shards_val = float(seg.get('shards', 0.0) or 0.0)
        waves_val = float(seg.get('waves', 0.0) or 0.0)
        full_duration = float(seg.get('full_duration', seg.get('duration', seg.get('height', 0.0))) or seg.get('height', 0.0) or 0.0)
        coins_hour = coins_val / full_duration if full_duration > 0 else 0.0
        cells_hour = cells_val / full_duration if full_duration > 0 else 0.0
        shards_hour = shards_val / full_duration if full_duration > 0 else 0.0
        waves_hour = waves_val / full_duration if full_duration > 0 else 0.0
        score = compute_normalized_score_100(
            coins_val,
            cells_val,
            shards_val,
            max_coins_ph * 24.0,
            max_cells_ph * 24.0,
            max_shards_ph * 24.0,
            weights=weights,
        )

        killed_by = str(seg.get('killed_by', '') or '')

        fig.add_trace(
            go.Bar(
                x=[seg.get('day', '')],
                y=[float(seg.get('height', 0.0) or 0.0)],
                base=[base_hours],
                marker_color=run_color(run_type, tier),
                name=label,
                legendgroup=label,
                showlegend=show_legend,
                customdata=[[run_type, str(tier), start_time_str, finish_time_str, duration_str, format_display_value(coins_val), format_display_value(cells_val), format_display_value(shards_val), format_display_value(waves_val), format_display_value(coins_hour), format_display_value(cells_hour), format_display_value(shards_hour), format_display_value(waves_hour), format_display_value(score), killed_by]],
                hovertemplate=(
                    'Day: %{x}<br>Time: %{customdata[2]} - %{customdata[3]} (Duration %{customdata[4]})'
                    '<br>Type: %{customdata[0]}<br>Tier: %{customdata[1]}'
                    + ('<br>Killed By: %{customdata[14]}' if killed_by else '')
                    + '<br>Total - Coins: %{customdata[5]}, Cells: %{customdata[6]}, Shards: %{customdata[7]}, Waves: %{customdata[8]}'
                    '<br>Per Hour - Coins: %{customdata[9]}, Cells: %{customdata[10]}, Shards: %{customdata[11]}, Waves: %{customdata[12]}'
                    '<br>Score: %{customdata[13]}'
                    '<extra></extra>'
                ),
            )
        )

    if categoryarray is None:
        seen_days: list[str] = []
        for seg in segments:
            day_label = str(seg.get('day', ''))
            if day_label and day_label not in seen_days:
                seen_days.append(day_label)
        categoryarray = seen_days

    fig.update_layout(
        title=title,
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text'],
        barmode='overlay',
        height=520,
        margin=dict(l=30, r=20, t=50, b=30),
        legend=dict(bgcolor='rgba(0,0,0,0.35)', font=dict(size=10)),
    )
    fig.update_xaxes(
        categoryorder='array',
        categoryarray=categoryarray,
        showgrid=False,
        title_text='Day',
    )
    fig.update_yaxes(
        range=[0, 24],
        tickvals=DAY_TICK_VALUES,
        title_text='Actual Time (h)',
        showgrid=True,
        gridcolor='#333',
    )
    return fig
