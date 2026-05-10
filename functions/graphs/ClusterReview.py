"""Cluster Review - Analyze tier/cluster contributions to metrics."""

import pandas as pd
import plotly.graph_objs as go
import numpy as np

from functions.data.ConvertNumbers import format_display_value, generate_abbreviation_ticks
from functions.data.ci_utils import get_ci_triplet
from .subplot_builders import create_subplots_grid


def cluster_review_figure(df: pd.DataFrame, weighted: bool = True) -> go.Figure:
    """Create cluster review charts with optional weighting."""
    if df is None or df.empty:
        return go.Figure()

    required_cols = ['tier', 'level_1', 'coins_earned', 'cells_earned', 'reroll_shards_earned', 'real_time']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        # Upstream clustering can return schema-light/empty frames; fail soft for UI stability.
        return go.Figure()

    df = df.copy()
    for col in ['coins_earned', 'cells_earned', 'reroll_shards_earned', 'real_time', 'score']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    if 'base_tier' not in df.columns:
        def _to_base_tier(value: object) -> int | None:
            try:
                token = str(value).strip().replace('+', '')
                return int(float(token))
            except Exception:
                return None

        df['base_tier'] = df['tier'].apply(_to_base_tier)
        df = df[df['base_tier'].notna()].copy()
        if df.empty:
            return go.Figure()
        df['base_tier'] = df['base_tier'].astype(int)

    if 'cluster_pct' not in df.columns:
        df['cluster_pct'] = np.nan

    df = df.dropna(subset=['coins_earned', 'cells_earned', 'reroll_shards_earned', 'real_time'])

    mean_df = df[df['level_1'] == 'mean'].copy()
    if mean_df.empty:
        return go.Figure()

    # Fill missing cluster_pct within each tier if needed
    if mean_df['cluster_pct'].isna().any():
        cluster_counts = mean_df.groupby('base_tier')['tier'].nunique().to_dict()
        mean_df['cluster_pct'] = mean_df.apply(
            lambda r: 1.0 / max(cluster_counts.get(r['base_tier'], 1), 1), axis=1
        )

    tiers = sorted(mean_df['base_tier'].unique().tolist())
    cluster_labels = sorted(mean_df['tier'].unique().tolist())
    
    # Build positioning for raw (unweighted) view so modalities share tier width evenly
    tier_cluster_map: dict[int, list[str]] = {}
    for t in tiers:
        tier_cluster_map[int(t)] = sorted(mean_df[mean_df['base_tier'] == t]['tier'].unique().tolist())
    
    def _cluster_position(base_tier: int, cluster_label: str) -> tuple[float, float]:
        """Return (x_position, bar_width) for a cluster within a tier category (raw view)."""
        clusters = tier_cluster_map.get(int(base_tier), [cluster_label])
        n = max(len(clusters), 1)
        full_width = 0.8
        if n == 1:
            return float(base_tier), full_width
        # Evenly spread clusters within category width
        step = full_width / n
        start = float(base_tier) - (full_width / 2.0) + (step / 2.0)
        idx = clusters.index(cluster_label) if cluster_label in clusters else 0
        return start + idx * step, step

    metrics = [
        ('coins_earned', 'Coins Earned', 'Coins'),
        ('cells_earned', 'Cells Earned', 'Cells'),
        ('reroll_shards_earned', 'Reroll Shards Earned', 'Reroll Shards'),
        ('real_time', 'Duration', 'Hours')
    ]

    fig = create_subplots_grid(
        rows=2, cols=2,
        subplot_titles=[m[1] for m in metrics],
        specs=[[{'type': 'bar'}, {'type': 'bar'}],
               [{'type': 'bar'}, {'type': 'bar'}]],
        vertical_spacing=0.15,
        horizontal_spacing=0.12
    )

    colors_list = [
        '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf'
    ]
    
    metric_ranges = {}  # Track y-value ranges for each metric subplot

    def _lookup_ci_triplet(tier_label: str, metric: str, default: float) -> tuple[float, float, float]:
        tier_rows = df[df['tier'] == tier_label]
        ci_values = get_ci_triplet(tier_rows, metric, level_col='level_1', clamp_lower_zero=False)
        if ci_values is None:
            return default, default, default
        return ci_values

    for metric_idx, (metric, title, y_label) in enumerate(metrics, 1):
        row = 1 if metric_idx <= 2 else 2
        col = 1 if metric_idx in (1, 3) else 2
        
        # Track y-value range for this metric subplot
        y_values = []

        # Cluster segments with per-cluster error bars
        segment_error_points = []
        cumulative_by_tier: dict[int, float] = {}

        for c_idx, cluster_label in enumerate(cluster_labels):
            cluster_rows = mean_df[mean_df['tier'] == cluster_label]
            if cluster_rows.empty:
                continue

            for _, r in cluster_rows.iterrows():
                base_tier = r['base_tier']
                pct = float(r['cluster_pct']) if weighted else 1.0
                raw_mean = float(r.get(metric, 0.0))
                _, raw_lower, raw_upper = _lookup_ci_triplet(cluster_label, metric, raw_mean)
                mean_val = raw_mean * pct
                lower_val = raw_lower * pct
                upper_val = raw_upper * pct
                
                # Track y-values for custom tick formatting
                y_values.extend([lower_val, mean_val, upper_val])
                
                if metric == 'real_time':
                    raw_fmt = f"{raw_mean:.2f} h"
                    weighted_fmt = f"{mean_val:.2f} h"
                else:
                    raw_fmt = format_display_value(raw_mean)
                    weighted_fmt = format_display_value(mean_val)
                pct_fmt = f"{pct * 100:.1f}%" if weighted else "100.0%"

                if weighted:
                    cum_before = cumulative_by_tier.get(int(base_tier), 0.0)
                    cum_after = cum_before + mean_val
                    cumulative_by_tier[int(base_tier)] = cum_after
                    segment_error_points.append({
                        'x': str(int(base_tier)),
                        'y': cum_after,
                        'err_plus': max(0.0, upper_val - mean_val),
                        'err_minus': max(0.0, mean_val - lower_val)
                    })

                x_pos, bar_width = _cluster_position(int(base_tier), cluster_label) if not weighted else (str(int(base_tier)), None)
                fig.add_trace(
                    go.Bar(
                        x=[x_pos],
                        y=[mean_val],
                        name=f"Cluster {cluster_label}",
                        marker_color=colors_list[c_idx % len(colors_list)],
                        legendgroup=f"cluster_{cluster_label}",
                        showlegend=False,
                        width=[bar_width] if (not weighted and bar_width is not None) else None,
                        error_y=None if weighted else dict(
                            type='data',
                            symmetric=False,
                            array=[max(0.0, upper_val - mean_val)],
                            arrayminus=[max(0.0, mean_val - lower_val)],
                            color='#e5e7eb',
                            thickness=1.5,
                            width=3
                        ),
                        hovertemplate=(
                            f"Cluster {cluster_label}<br>"
                            f"Tier: {int(base_tier)}<br>"
                            f"Raw {y_label}: {raw_fmt}<br>"
                            f"Weighted {y_label}: {weighted_fmt}<br>"
                            f"Cluster % of tier: {pct_fmt}<extra></extra>"
                        )
                    ),
                    row=row, col=col
                )

        if weighted and segment_error_points:
            fig.add_trace(
                go.Scatter(
                    x=[p['x'] for p in segment_error_points],
                    y=[p['y'] for p in segment_error_points],
                    mode='markers',
                    marker=dict(color='#e5e7eb', size=1, opacity=0.0),
                    error_y=dict(
                        type='data',
                        symmetric=False,
                        array=[p['err_plus'] for p in segment_error_points],
                        arrayminus=[p['err_minus'] for p in segment_error_points],
                        color='#e5e7eb',
                        thickness=1.5,
                        width=3
                    ),
                    hoverinfo='skip',
                    showlegend=False
                ),
                row=row, col=col
            )

        # Tier-level (big) error bars over the stacked totals
        total_means = []
        total_err_plus = []
        total_err_minus = []
        x_tiers = [str(int(t)) for t in tiers] if weighted else [float(int(t)) for t in tiers]

        for t in tiers:
            tier_rows = mean_df[mean_df['base_tier'] == t]
            total_mean = 0.0
            total_lower = 0.0
            total_upper = 0.0
            for _, r in tier_rows.iterrows():
                pct = float(r['cluster_pct']) if weighted else 1.0
                cluster_label = r['tier']
                mean_val, lower_val, upper_val = _lookup_ci_triplet(cluster_label, metric, float(r.get(metric, 0.0)))
                total_mean += mean_val * pct
                total_lower += lower_val * pct
                total_upper += upper_val * pct
            total_means.append(total_mean)
            total_err_plus.append(max(0.0, total_upper - total_mean))
            total_err_minus.append(max(0.0, total_mean - total_lower))
            
            # Track y-values for custom tick formatting (include error bars)
            y_values.extend([total_lower, total_mean, total_upper])

        if metric == 'real_time':
            total_hover = [f"{v:.2f} h" for v in total_means]
        else:
            total_hover = [format_display_value(v) for v in total_means]

        fig.add_trace(
            go.Scatter(
                x=x_tiers,
                y=total_means,
                mode='markers',
                marker=dict(color='#ffffff', size=7, symbol='line-ns-open'),
                error_y=dict(
                    type='data',
                    symmetric=False,
                    array=total_err_plus,
                    arrayminus=total_err_minus,
                    color='#ffffff',
                    thickness=2,
                    width=4
                ),
                showlegend=False,
                legendgroup='tier_total',
                name='Tier Total CI',
                customdata=total_hover,
                hovertemplate=(
                    f"Tier Total<br>Tier: %{{x}}<br>{y_label}: %{{customdata}}<extra></extra>"
                )
            ),
            row=row, col=col
        )

        # Apply custom abbreviated ticks for non-real_time metrics
        if metric != 'real_time' and y_values:
            min_val = min([v for v in y_values if v is not None and not np.isnan(v)])
            max_val = max([v for v in y_values if v is not None and not np.isnan(v)])
            if min_val < max_val:
                tickvals, ticktext = generate_abbreviation_ticks(min_val, max_val, num_ticks=5)
                fig.update_yaxes(
                    tickvals=tickvals,
                    ticktext=ticktext,
                    row=row, col=col
                )
            else:
                fig.update_yaxes(title_text=y_label, row=row, col=col)
        elif metric == 'real_time':
            fig.update_yaxes(title_text=y_label, row=row, col=col, tickformat='.2f')
        else:
            fig.update_yaxes(title_text=y_label, row=row, col=col)

    fig.update_layout(
        barmode='stack' if weighted else 'group',
        height=700,
        plot_bgcolor='#000000',
        paper_bgcolor='#000000',
        font_color='#FAFAFA',
        title_text='Cluster Review - Weighted Cluster Contributions with CI' if weighted else 'Cluster Review - Raw Cluster Contributions with CI',
        title_font_size=16,
        showlegend=False,
        margin=dict(l=80, r=40, t=80, b=60)
    )

    fig.update_yaxes(showgrid=True, gridcolor='darkgrey', zeroline=False)
    if weighted:
        fig.update_xaxes(showgrid=False, title_text='Tier')
    else:
        fig.update_xaxes(showgrid=False, title_text='Tier', tickvals=[float(int(t)) for t in tiers], ticktext=[str(int(t)) for t in tiers])

    return fig
