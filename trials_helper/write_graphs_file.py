from pathlib import Path
p = Path(r"\\mycloudex2ultra\Thorsten\_python\ProjectAtzi\myproject\Graphs.py")
backup = p.with_suffix('.pre_errorbar.py')
if p.exists():
    p.replace(str(backup))
content = '''import pandas as pd
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import numpy as np

from .Optimizer import optimize_runs
from .ConvertNumbers import apply_abbreviation, abbreviate_value

from typing import Tuple

# Color scheme
colors = {
    'background': '#000000',  # dark background
    'text': '#FFFFFF',        # white text
    'coins': 'green',
    'cells': 'purple',
    'reroll': 'orange',
    'score': 'lightgrey',
    'time': 'lightgrey'
}

def get_color_for_metric(metric: str) -> str:
    metric_lower = metric.lower()
    if 'coins' in metric_lower:
        return colors['coins']
    elif 'cells' in metric_lower:
        return colors['cells']
    elif 'reroll' in metric_lower:
        return colors['reroll']
    elif 'score' in metric_lower or 'time' in metric_lower:
        return colors['score']
    else:
        return 'white'


def error_bar_trace(df: pd.DataFrame, metric: str, group_col: str, color: str) -> list[go.Scatter]:
    """
    Creates error bar traces for each group in the data, showing mean values with CI bounds.
    
    Parameters:
    - df: DataFrame with level_1 containing 'mean', 'ci_lower', 'ci_upper'
    - metric: Column name for the metric to plot
    - group_col: Column to group by (e.g., 'tier' or 'scenario')
    - color: Color for the traces
    
    Returns:
    - List of Plotly traces (one per group)
    """
    if group_col not in df.columns or 'level_1' not in df.columns or metric not in df.columns:
        return []

    traces = []
    for group_label, group_data in df.groupby(group_col):
        # Get mean/CI values for this group
        try:
            mean_vals = group_data[group_data['level_1'] == 'mean'][metric].values
            lower_vals = group_data[group_data['level_1'] == 'ci_lower'][metric].values
            upper_vals = group_data[group_data['level_1'] == 'ci_upper'][metric].values
            
            if len(mean_vals) == 0:
                continue

            # Calculate error bar magnitude (symmetric up/down from mean)
            err_minus = mean_vals - lower_vals
            err_plus = upper_vals - mean_vals

            trace = go.Scatter(
                x=[group_label],  # Single point for this group
                y=mean_vals,
                name=str(group_label),
                mode='markers',
                marker=dict(
                    color=color,
                    size=10,
                ),
                error_y=dict(
                    type='data',
                    symmetric=False,
                    array=err_plus,        # distance from mean to upper CI
                    arrayminus=err_minus,  # distance from mean to lower CI
                    color=color,
                    width=3,
                    visible=True
                ),
                showlegend=True
            )
            traces.append(trace)
        except (KeyError, IndexError):
            continue  # Skip if we can't get all required values

    return traces


def combined_metrics_figure(filtered_df: pd.DataFrame) -> go.Figure:
    sub_graphs = [
        'coins_earned', 'cells_earned', 'reroll_shards_earned', 'real_time',
        'coins_per_hour', 'cells_per_hour', 'reroll_shards_per_hour', 'score'
    ]

    fig = make_subplots(rows=2, cols=4, subplot_titles=sub_graphs)

    row, col = 1, 1
    for metric in sub_graphs:
        color = get_color_for_metric(metric)
        traces = error_bar_trace(filtered_df, metric, 'tier', color)
        for trace in traces:
            fig.add_trace(trace, row=row, col=col)

        col += 1
        if col > 4:
            col = 1
            row += 1

    fig.update_layout(
        height=800,
        title_text="Metrics Overview",
        showlegend=True,
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text'],
        margin=dict(l=10, r=10, t=40, b=10)
    )

    # Y-axis: dark grey gridlines, start at zero
    fig.update_yaxes(showgrid=True, gridcolor='darkgrey', zeroline=True, zerolinecolor='white', range=[0, None])
    # X-axis: no gridlines
    fig.update_xaxes(showgrid=False, type='category')  # Treat x as categories

    return fig


def makeTable(df: pd.DataFrame) -> go.Figure:
    """
    Converts a DataFrame with confidence levels (ci_lower, mean, ci_upper)
    stored in 'level_1' into a Plotly Table where each metric is combined:
    'mean<br>(ci_lower ... ci_upper)'.
    """

    def format_metric(group, column, suffix_format="{unit}"):
        try:
            mean = float(group.loc[group['level_1'] == 'mean', column].values[0])
            lower = float(group.loc[group['level_1'] == 'ci_lower', column].values[0])
            upper = float(group.loc[group['level_1'] == 'ci_upper', column].values[0])
            formatted_mean = abbreviate_value(mean, suffix_format)
            formatted_lower = abbreviate_value(lower, suffix_format)
            formatted_upper = abbreviate_value(upper, suffix_format)
            return f"{formatted_mean}<br>({formatted_lower} ...<br>{formatted_upper})"
        except (IndexError, ValueError, TypeError):
            return "N/A"

    formatted_rows = []
    for tier, group in df.groupby('tier'):
        formatted_rows.append({
            'Tier': tier,
            'Coins Earned': format_metric(group, 'coins_earned'),
            'Cells Earned': format_metric(group, 'cells_earned'),
            'Reroll Shards Earned': format_metric(group, 'reroll_shards_earned'),
            'Coins per Hour': format_metric(group, 'coins_per_hour'),
            'Cells per Hour': format_metric(group, 'cells_per_hour'),
            'Reroll Shards per Hour': format_metric(group, 'reroll_shards_per_hour'),
            'Real Time': format_metric(group, 'real_time', suffix_format=" {unit} h"),
            'Score': format_metric(group, 'score')
        })

    formatted_df = pd.DataFrame(formatted_rows)

    return go.Figure(data=[go.Table(
        header=dict(values=list(formatted_df.columns), fill_color='lightgrey', align='left'),
        cells=dict(values=[formatted_df[col] for col in formatted_df.columns], fill_color='white', align='center')
    )])


def generate_optimize_df(df: pd.DataFrame, daytime: int) -> dict[str, pd.DataFrame]:
    # Get raw DataFrames for three scenarios
    summary_dt, breakdown_dt = optimize_runs(df, daytime)
    summary_nt, breakdown_nt = optimize_runs(df, 24 - daytime)
    summary_24, breakdown_24 = optimize_runs(df, 24)
    return {
        'summary_daytime': summary_dt,
        'breakdown_daytime': breakdown_dt,
        'summary_nighttime': summary_nt,
        'breakdown_nighttime': breakdown_nt,
        'summary_24h': summary_24,
        'breakdown_24h': breakdown_24
        }


def optimize_table(df: pd.DataFrame, daytime: int) -> Tuple[go.Figure, go.Figure]:
    # Get raw DataFrames for three scenarios

    result = generate_optimize_df(df, daytime)

    summary_df = pd.concat(
        [result['summary_daytime'], result['summary_nighttime'], result['summary_24h']],
        keys=['daytime', 'nighttime', '24h']
    ).reset_index().rename(columns={'level_0': 'scenario'})

    breakdown_df = pd.concat([
        result['breakdown_daytime'], result['breakdown_nighttime'], result['breakdown_24h']],
        keys=['daytime', 'nighttime', '24h']
    ).reset_index().rename(columns={'level_0': 'scenario'})


    # Combine them with keys
    summary_df = apply_abbreviation(summary_df, ['coins_earned', 'cells_earned', 'reroll_shards_earned'])
    breakdown_df = apply_abbreviation(breakdown_df, ['duration_per_run', 'total_duration'], suffix_format=" {unit} h")

    # ✅ Transform summary_df to formatted style
    formatted_rows = []
    for scenario, group in summary_df.groupby('scenario'):
        mean_row = group[group['confidence'] == 'mean'].iloc[0]
        lower_row = group[group['confidence'] == 'ci_lower'].iloc[0]
        upper_row = group[group['confidence'] == 'ci_upper'].iloc[0]

        coins_summary = f"{mean_row['coins_earned']} <br> ({lower_row['coins_earned']} ... {upper_row['coins_earned']})"
        cells_summary = f"{mean_row['cells_earned']} <br> ({lower_row['cells_earned']} ... {upper_row['cells_earned']})"
        shards_summary = f"{mean_row['reroll_shards_earned']} <br> ({lower_row['reroll_shards_earned']} ... {upper_row['reroll_shards_earned']})"

        formatted_rows.append({
            'scenario': scenario,
            'coins_earned': coins_summary,
            'cells_earned': cells_summary,
            'reroll_shards_earned': shards_summary
        })

    formatted_summary_df = pd.DataFrame(formatted_rows)

    # ✅ Create Plotly tables
    summary_fig = go.Figure(data=[go.Table(
        header=dict(values=list(formatted_summary_df.columns), align='center'),
        cells=dict(values=[formatted_summary_df[col] for col in formatted_summary_df.columns], align='center')
    )])

    breakdown_fig = go.Figure(data=[go.Table(
        header=dict(values=list(breakdown_df.columns)),
        cells=dict(values=[breakdown_df[col] for col in breakdown_df.columns])
    )])

    optimize_df = pd.merge(formatted_summary_df, breakdown_df, left_on='scenario', right_on='scenario', how='outer')
    # Only drop 'level_1' if it exists (some breakdowns may not include it)
    if 'level_1' in optimize_df.columns:
        optimize_df = optimize_df.drop(columns=['level_1'])
    optimize_df = optimize_df.set_index('scenario').transpose().reset_index()
    optimize_figure = go.Figure(data=[go.Table(
        header=dict(values=list(optimize_df.columns)),
        cells=dict(values=[optimize_df[col] for col in optimize_df.columns])
    )])

    return summary_fig, optimize_figure


def optimize_figure(df: pd.DataFrame, daytime: int) -> go.Figure:
    result = generate_optimize_df(df, daytime)

    summary_df = pd.concat(
        [result['summary_daytime'], result['summary_nighttime'], result['summary_24h']],
        keys=['daytime', 'nighttime', '24h']
    ).reset_index().rename(columns={'level_0': 'scenario'})

    breakdown_df = pd.concat([
        result['breakdown_daytime'], result['breakdown_nighttime'], result['breakdown_24h']],
        keys=['daytime', 'nighttime', '24h']
    ).reset_index().rename(columns={'level_0': 'scenario'})

    sub_graphs = [
        'coins_earned', 'cells_earned', 'reroll_shards_earned',
        'coins_per_hour', 'cells_per_hour', 'reroll_shards_per_hour',
    ]

    fig = make_subplots(rows=2, cols=3, subplot_titles=sub_graphs)

    row, col = 1, 1
    for metric in sub_graphs:
        color = get_color_for_metric(metric)
        traces = error_bar_trace(summary_df, metric, 'scenario', color)
        for trace in traces:
            fig.add_trace(trace, row=row, col=col)

        col += 1
        # wrap columns for a 3-column layout
        if col > 3:
            col = 1
            row += 1

    fig.update_layout(
        height=800,
        title_text="Metrics Overview",
        showlegend=True,
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text'],
        margin=dict(l=10, r=10, t=40, b=10)
    )

    # Y-axis: dark grey gridlines, start at zero
    fig.update_yaxes(showgrid=True, gridcolor='darkgrey', zeroline=True, zerolinecolor='white', range=[0, None])
    # X-axis: no gridlines
    fig.update_xaxes(showgrid=False, type='category')  # Treat x as categories

    return fig
'''
p.write_text(content, encoding='utf-8')
print('Wrote', p)
print('Backup saved as', backup)