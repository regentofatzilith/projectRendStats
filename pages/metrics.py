"""Metrics & Optimizer page - displays run statistics and optimization recommendations."""

import dash
from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
from typing import cast

from functions import user_data_store
from functions.graphs import (
    build_current_scenario_daily_income_figure,
    build_current_scenario_weekly_details,
    build_current_scenario_weekly_proposal_figure,
)
from functions.ui import empty_figure, graph_row, section_with_graph, warning_banner
from .metrics_data import build_tier_options, prepare_metrics_data, create_metrics_figures

# Register this page
dash.register_page(__name__, path="/metrics-overview", name="Metrics & Overview", order=1)


# Page layout
layout = html.Div([
    html.H1('Metrics Overview', className="page-title"),
    html.P([
        'This section provides an overview of your runs and performance metrics. Use the controls below to filter by tier and adjust the time window for continuous metrics.   \n'
        ' The confidence intervals show the variability of your income per Tier and can help you understand the consistency of your runs.'
        ' Hover over the graphs to see exact values.'
    ]),
    html.Div(id='metrics-no-data-warning'),
    # Controls row for tier and window selection
    dbc.Row([
        dbc.Col([
            html.Label('Select Tier'),
            dcc.Dropdown(
                id='tier-selector',
                # Build options from grouped stats; if empty, fall back to time series to include new tiers
                options=cast(list, build_tier_options(
                    pd.concat(
                        [
                            user_data_store.cleaned.get('grouped_by_tier_df', pd.DataFrame()),
                            user_data_store.cleaned.get('time_series_df', pd.DataFrame())
                        ], ignore_index=True
                    )
                )),
                value=[],
                placeholder="Select Tiers",
                multi=True,
                clearable=True
            )
        ], width=3),
        dbc.Col([
            html.Label('Smoothing Window Size (Window size accounts for 67 percent of calculated average)'),
            dcc.Slider(
                id='window-days-slider',
                min=0.5,
                max=7,
                step=0.5,
                value=2,
                marks={
                    0.5: '12h',
                    1: '1d',
                    2: '2d',
                    3: '3d',
                    5: '5d',
                    7: '1w'
                }
            ),
            html.Div(
                [
                    html.Span('Displayed Timeline:', style={'marginRight': '0.5rem', 'color': '#9ca3af'}),
                    dcc.RadioItems(
                        id='metrics-timeline-scope',
                        options=[
                            {'label': '3 months', 'value': '3m'},
                            {'label': 'All data', 'value': 'all'},
                        ],
                        value='3m',
                        inline=True,
                        labelStyle={'marginRight': '1rem'},
                        style={'display': 'inline-block'},
                    ),
                ],
                style={'marginTop': '0.65rem'}
            ),
        ], width=5)
    ], className="mb-4"),
    
    *section_with_graph('Metrics Overview per Farming Run', 'metrics-overview-graph', description='This graph shows the coins, cells, and shards earned per run per tier, along with the real time duration.  This section is limited to farming / overnight runs to avoid fluctuations introduced by milestone, dissonance tournament or quit runs. \n Use the tier selector above to filter runs by tier.'),
    *section_with_graph('Daily Results (average and confidence intervals)', 'continuous-metrics-graph', description='This graph shows the daily results with average values and confidence intervals for your farming / overnight runs.   \n Use the tier selector above to filter runs by tier.'),

    html.H2('Last week details'),
    html.P([
        'To see how to optimize your weekly income please visit the ',
        dcc.Link('Optimizer (weekly)', href='/optimizer-weekly'),
        ' page. The graphs below show the daily income for coins, cells, and shards earned based on your recent runs. The Max Income lines show your current best per hour income run for 24h per day as a benchmark.'
    ], style={'color': '#9ca3af'}),
    graph_row('last-week-daily-income-graph'),
    graph_row('last-week-weekly-proposal-graph')
])



@callback(
     [Output('metrics-overview-graph', 'figure'),
      Output('continuous-metrics-graph', 'figure'),
      Output('last-week-daily-income-graph', 'figure'),
      Output('last-week-weekly-proposal-graph', 'figure'),
      Output('tier-selector', 'options'),
      Output('metrics-no-data-warning', 'children')],
     [Input('tier-selector', 'value'),
      Input('window-days-slider', 'value'),
      Input('metrics-timeline-scope', 'value'),
      Input('user-json-store', 'data')]
)
def update_metrics(selected_tier, window_days, timeline_scope, user_json_state):
    """Update all metrics visualizations based on selections."""
    # Get data from store
    filtered_df = user_data_store.cleaned.get('grouped_by_tier_df', pd.DataFrame())
    time_series_df = user_data_store.cleaned.get('time_series_df', pd.DataFrame())
    
    # Initialize empty figures if no data
    if filtered_df.empty and time_series_df.empty:
        tier_options = build_tier_options(filtered_df)
        warning = warning_banner(
            'No data loaded. Please check that your userData.json is present, contains runs, and is being loaded by the app.'
        )
        return empty_figure(), empty_figure(), empty_figure(), empty_figure(), tier_options, warning
    
    # Prepare all metrics data
    window_days_val = float(window_days or 2.0)
    
    metrics_df, ts_filtered, all_runs_filtered, optimizer_df, tier_options = prepare_metrics_data(
        selected_tier=selected_tier,
        window_days=window_days_val,
        timeline_scope=str(timeline_scope or '3m'),
        current_days=3  # Not used anymore on this page
    )
    
    # Create figures (metrics and continuous only)
    from functions.graphs import combined_metrics_figure, continuous_metrics_figure
    
    metrics_graph = combined_metrics_figure(metrics_df, metric_type='real_time') if not metrics_df.empty else go.Figure()
    continuous_graph = continuous_metrics_figure(ts_filtered, window_days=window_days_val) if not ts_filtered.empty else go.Figure()

    max_income_baseline_df = user_data_store.cleaned.get('max_income_baseline_df', pd.DataFrame())

    # Read max-income reference values directly from the pre-computed baseline
    max_coins_per_hour = 0.0
    max_cells_per_hour = 0.0
    max_shards_per_hour = 0.0
    if max_income_baseline_df is not None and not max_income_baseline_df.empty:
        base_row = max_income_baseline_df.iloc[0]
        max_coins_per_hour = float(base_row.get('max_coins_per_hour', 0.0) or 0.0)
        max_cells_per_hour = float(base_row.get('max_cells_per_hour', 0.0) or 0.0)
        max_shards_per_hour = float(base_row.get('max_shards_per_hour', 0.0) or 0.0)

    max_per_day = {
        'coins': max_coins_per_hour * 24.0,
        'cells': max_cells_per_hour * 24.0,
        'shards': max_shards_per_hour * 24.0,
    }

    current_details = build_current_scenario_weekly_details(
        all_runs_filtered,
        score_weights={'coins': 0.34, 'cells': 0.33, 'shards': 0.33},
        max_per_hour={'coins': max_coins_per_hour, 'cells': max_cells_per_hour, 'shards': max_shards_per_hour},
        current_days=7,
    )
    last_week_daily_graph = build_current_scenario_daily_income_figure(
        current_details,
        title='Daily Income of Recent Runs (Last 7 Days)',
        max_per_day=max_per_day,
    )
    last_week_weekly_graph = build_current_scenario_weekly_proposal_figure(
        current_details,
        score_weights={'coins': 0.34, 'cells': 0.33, 'shards': 0.33},
        max_per_hour={'coins': max_coins_per_hour, 'cells': max_cells_per_hour, 'shards': max_shards_per_hour},
        title='Calendar view of Recent Runs (Last 7 Days)',
    )
    
    # Return outputs (no optimizer)
    return metrics_graph, continuous_graph, last_week_daily_graph, last_week_weekly_graph, tier_options, None
