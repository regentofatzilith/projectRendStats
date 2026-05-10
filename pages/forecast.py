"""Forecast page - predicts future metrics based on historical trends."""

import dash
from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import numpy as np
from typing import cast, Optional
import logging

from functions import user_data_store
from functions.graphs.subplot_builders import create_subplots_grid
from functions.statistics import forecast_metric, TimeSeriesStats
from functions.graphs import get_color_for_metric, display_name, colors, continuous_metrics_figure
from functions.ui import empty_figure, graph_row, no_data_text, stat_card, warning_banner
from .metrics_data import build_tier_options, prepare_metrics_data

logger = logging.getLogger(__name__)


def _stats_card_col(title: str, content_id: str) -> dbc.Col:
    return dbc.Col(
        [
            stat_card(
                title,
                [html.Div(id=content_id, style={'fontSize': '0.9rem'})],
                class_name='mb-2',
            )
        ],
        width=12,
        md=6,
        lg=2,
    )

# Register this page
dash.register_page(__name__, path="/forecast", name="Forecast", order=7)


# Page layout
layout = html.Div([
    html.H1('Metric Forecasting', className="page-title"),
    html.P('Predict future performance based on historical trends using exponential, sigmoidal, or linear models.'),
    
    html.Div(id='forecast-no-data-warning'),
    
    # Controls row
    dbc.Row([
        dbc.Col([
            html.Label('Select Tier'),
            dcc.Dropdown(
                id='forecast-tier-selector',
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
        ], width=2),
        dbc.Col([
            html.Label('Daily Results Window (Days)'),
            dcc.Slider(
                id='forecast-daily-window-slider',
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
            )
        ], width=2)
    ], className="mb-4"),
    
    # Daily Results chart (shows the historical data used for forecasting)
    html.H4('Daily Results (average and confidence intervals)', className="mb-3"),
    html.P('This chart shows the weighted average and confidence intervals, matching the Daily Results chart from the Metrics page.', 
           style={'fontSize': '0.9rem', 'color': '#999'}),
    graph_row('forecast-daily-results'),
    
    # Forecast controls row
    html.H4('Forecast Configuration', className="mb-3 mt-4"),
    dbc.Row([
        dbc.Col([
            html.Label('Historical Data Lookback (Days)'),
            dcc.Slider(
                id='forecast-lookback-slider',
                min=14,
                max=365,
                step=30,
                value=180,
                marks={                    
                    30: '1mo',
                    60: '2mo',
                    90: '3mo',
                    180: '6mo',
                    270: '9mo',
                    365: '1y'
                }
            )
        ], width=3),
        dbc.Col([
            html.Label('Forecast Smoothing Window (Days)'),
            dcc.Slider(
                id='forecast-smoothing-slider',
                min=7,
                max=60,
                step=7,
                value=14,
                marks={
                    7: '1w',
                    14: '2w',
                    21: '3w',
                    30: '1mo',
                    60: '2mo'
                }
            )
        ], width=3),
        dbc.Col([
            html.Label('Forecast Horizon (Days)'),
            dcc.Slider(
                id='forecast-days-slider',
                min=7,
                max=90,
                step=7,
                value=30,
                marks={
                    7: '1w',
                    14: '2w',
                    30: '1mo',
                    60: '2mo',
                    90: '3mo'
                }
            )
        ], width=2),
        dbc.Col([
            html.Label('Model Type'),
            dcc.Dropdown(
                id='forecast-model-selector',
                options=[
                    {'label': 'Auto-select (Best Fit)', 'value': 'auto'},
                    {'label': 'Ensemble (Hybrid)', 'value': 'ensemble'},
                    {'label': 'Exponential Growth', 'value': 'exponential'},
                    {'label': 'Sigmoidal (S-curve)', 'value': 'sigmoidal'},
                    {'label': 'Polynomial (Quadratic)', 'value': 'polynomial'},
                    {'label': 'Linear Growth', 'value': 'linear'}
                ],
                value='auto',
                clearable=False
            )
        ], width=3),
        dbc.Col([
            html.Label('Detect Upgrade Jumps'),
            dbc.Checklist(
                id='forecast-detect-jumps',
                options=[{'label': ' Auto-segment', 'value': 'detect'}],
                value=[],
                switch=True,
                className='mt-4'
            )
        ], width=1)
    ], className="mb-4"),
    
    # Model statistics cards
    html.H4('Model Statistics', className="mb-3"),
    dbc.Row([
        _stats_card_col('Coins Earned', 'forecast-coins-stats'),
        _stats_card_col('Cells Earned', 'forecast-cells-stats'),
        _stats_card_col('Reroll Shards', 'forecast-reroll-stats'),
        _stats_card_col('Coins/Hour', 'forecast-coins-hour-stats'),
        _stats_card_col('Cells/Hour', 'forecast-cells-hour-stats'),
        _stats_card_col('Reroll/Hour', 'forecast-reroll-hour-stats'),
    ], className="mb-4"),
    
    # Forecast charts
    html.H4('Forecast Visualizations', className="mb-3"),
    graph_row('forecast-graph'),
])


def _format_model_stats(result: dict) -> list:
    """Format model statistics for display in cards."""
    if not result:
        return [html.Div('No data', style={'color': '#999'})]
    
    model_type = result.get('model_type', 'unknown').title()
    r_squared = result.get('r_squared', 0)
    metadata = result.get('metadata', {})
    
    stats = [
        html.Div([
            html.Strong('Model: '),
            html.Span(model_type)
        ], style={'marginBottom': '0.5rem'}),
        html.Div([
            html.Strong('R²: '),
            html.Span(f'{r_squared:.4f}')
        ], style={'marginBottom': '0.5rem', 'color': '#4ade80' if r_squared > 0.9 else '#fb923c' if r_squared > 0.7 else '#f87171'})
    ]
    
    # Add model-specific parameters
    if model_type == 'Ensemble':
        dominant = metadata.get('dominant_model', 'unknown')
        weights = metadata.get('weights', [])
        if weights:
            weight_str = f"{weights[0]:.0%} exp, {weights[1]:.0%} sig, {weights[2]:.0%} lin, {weights[3]:.0%} poly"
            stats.append(html.Div([
                html.Strong('Dominant: '),
                html.Span(dominant.title())
            ], style={'fontSize': '0.85rem', 'color': '#999'}))
            stats.append(html.Div([
                html.Strong('Weights: '),
                html.Span(weight_str)
            ], style={'fontSize': '0.75rem', 'color': '#666'}))
    elif model_type == 'Exponential':
        growth_rate = metadata.get('growth_rate', 0)
        stats.append(html.Div([
            html.Strong('Growth Rate: '),
            html.Span(f'{growth_rate:.4f}/day')
        ], style={'fontSize': '0.85rem', 'color': '#999'}))
    elif model_type == 'Sigmoidal':
        capacity = metadata.get('carrying_capacity', 0)
        stats.append(html.Div([
            html.Strong('Capacity: '),
            html.Span(f'{capacity:.2f}')
        ], style={'fontSize': '0.85rem', 'color': '#999'}))
    elif model_type == 'Linear':
        slope = metadata.get('slope', 0)
        stats.append(html.Div([
            html.Strong('Slope: '),
            html.Span(f'{slope:.2f}/day')
        ], style={'fontSize': '0.85rem', 'color': '#999'}))
    elif model_type == 'Polynomial':
        degree = metadata.get('degree', 2)
        stats.append(html.Div([
            html.Strong('Degree: '),
            html.Span(f'{degree}')
        ], style={'fontSize': '0.85rem', 'color': '#999'}))
    
    return stats


def _create_forecast_figure(results: dict, metrics: list, daily_aggregated: dict) -> go.Figure:
    """Create subplot figure with forecasts for all metrics.
    
    Args:
        results: Forecast results dictionary
        metrics: List of metrics to plot (should be 6 metrics for 2x3 grid)
        daily_aggregated: Dict of daily aggregated DataFrames for each metric (for grey bars)
    """
    titles = [display_name(m) for m in metrics]
    fig = create_subplots_grid(
        rows=2, cols=3,
        subplot_titles=titles,
        vertical_spacing=0.12,
        horizontal_spacing=0.06
    )
    
    positions = [(1, 1), (1, 2), (1, 3), (2, 1), (2, 2), (2, 3)]
    
    for idx, metric in enumerate(metrics):
        result = results.get(metric, {})
        row, col = positions[idx]
        color = get_color_for_metric(metric)
        
        # Raw daily aggregated data (grey bars)
        if metric in daily_aggregated and not daily_aggregated[metric].empty:
            daily_df = daily_aggregated[metric]
            fig.add_trace(
                go.Bar(
                    x=daily_df['timestamp'],
                    y=daily_df[metric],
                    name='Daily Total',
                    marker=dict(color='#666', opacity=0.3),
                    showlegend=(idx == 0),
                    hovertemplate='%{x|%Y-%m-%d}<br>%{y:.2f}<extra></extra>'
                ),
                row=row, col=col
            )
        
        # Skip the rest if no forecast result
        if not result:
            continue
        
        # Smoothed historical data (colored line)
        timestamps_hist = result.get('timestamps_historical', [])
        y_fitted = result.get('y_fitted', [])
        
        if len(timestamps_hist) > 0 and len(y_fitted) > 0:
            fig.add_trace(
                go.Scatter(
                    x=timestamps_hist,
                    y=y_fitted,
                    mode='lines',
                    name='Smoothed',
                    line=dict(color=color, width=2),
                    showlegend=(idx == 0),
                    hovertemplate='%{x|%Y-%m-%d}<br>%{y:.2f}<extra></extra>'
                ),
                row=row, col=col
            )
        
        # Forecast
        timestamps_forecast = result.get('timestamps_forecast', [])
        y_forecast = result.get('y_forecast', [])
        lower_bound = result.get('lower_bound', [])
        upper_bound = result.get('upper_bound', [])
        
        if len(timestamps_forecast) > 0 and len(y_forecast) > 0:
            # Forecast line
            fig.add_trace(
                go.Scatter(
                    x=timestamps_forecast,
                    y=y_forecast,
                    mode='lines',
                    name='Forecast',
                    line=dict(color=color, width=2, dash='dash'),
                    showlegend=(idx == 0),
                    hovertemplate='%{x|%Y-%m-%d}<br>%{y:.2f}<extra></extra>'
                ),
                row=row, col=col
            )
            
            # Prediction interval - transparent fill with boundary lines
            if lower_bound is not None and upper_bound is not None:
                # Upper bound line
                fig.add_trace(
                    go.Scatter(
                        x=timestamps_forecast,
                        y=upper_bound,
                        mode='lines',
                        line=dict(color=color, width=1, dash='dot'),
                        name='Upper 95%',
                        showlegend=(idx == 0),
                        hovertemplate='%{x|%Y-%m-%d}<br>%{y:.2f}<extra></extra>'
                    ),
                    row=row, col=col
                )
                # Lower bound line
                fig.add_trace(
                    go.Scatter(
                        x=timestamps_forecast,
                        y=lower_bound,
                        mode='lines',
                        line=dict(color=color, width=1, dash='dot'),
                        name='Lower 95%',
                        showlegend=(idx == 0),
                        fill='tonexty',
                        fillcolor=color.replace('rgb', 'rgba').replace(')', ', 0.2)'),
                        hovertemplate='%{x|%Y-%m-%d}<br>%{y:.2f}<extra></extra>'
                    ),
                    row=row, col=col
                )
    
    fig.update_layout(
        height=800,
        showlegend=True,
        plot_bgcolor=colors['background'],
        paper_bgcolor=colors['background'],
        font_color=colors['text'],
        margin=dict(l=50, r=50, t=50, b=50),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.15,
            xanchor="center",
            x=0.5
        )
    )
    
    fig.update_yaxes(showgrid=True, gridcolor='#333', zeroline=False)
    fig.update_xaxes(showgrid=True, gridcolor='#333')
    
    return fig


@callback(
    [Output('forecast-tier-selector', 'options'),
     Output('forecast-no-data-warning', 'children')],
    [Input('user-json-store', 'data')]
)
def update_tier_options(user_json_state):
    """Initialize tier selector with available tiers."""
    filtered_df = user_data_store.cleaned.get('grouped_by_tier_df', pd.DataFrame())
    time_series_df = user_data_store.cleaned.get('time_series_df', pd.DataFrame())
    
    if filtered_df.empty and time_series_df.empty:
        warning = warning_banner('No data loaded. Please load your userData.json from the Settings page.')
        return [], warning
    
    # Build tier options (same as metrics.py)
    tier_options = build_tier_options(
        pd.concat([filtered_df, time_series_df], ignore_index=True)
    )
    
    return tier_options, None


@callback(
    [Output('forecast-daily-results', 'figure'),
     Output('forecast-graph', 'figure'),
     Output('forecast-coins-stats', 'children'),
     Output('forecast-cells-stats', 'children'),
     Output('forecast-reroll-stats', 'children'),
     Output('forecast-coins-hour-stats', 'children'),
     Output('forecast-cells-hour-stats', 'children'),
     Output('forecast-reroll-hour-stats', 'children')],
    [Input('forecast-tier-selector', 'value'),
     Input('forecast-daily-window-slider', 'value'),
     Input('forecast-lookback-slider', 'value'),
     Input('forecast-smoothing-slider', 'value'),
     Input('forecast-days-slider', 'value'),
     Input('forecast-model-selector', 'value'),
     Input('forecast-detect-jumps', 'value')]
)
def update_forecast(selected_tier, daily_window_days, lookback_days, smoothing_days, forecast_days, model_type, detect_jumps):
    """Generate forecasts for all metrics."""
    # Use prepare_metrics_data to get consistent data preparation (same as metrics.py)
    # daily_window_days is for the Daily Results chart display (matches metrics.py window-days-slider)
    daily_window_val = float(daily_window_days or 2.0)
    
    # Prepare data using the same function as metrics.py
    _, ts_filtered, _, _, _ = prepare_metrics_data(
        selected_tier=selected_tier,
        window_days=daily_window_val,  # Use daily window for data preparation
        current_days=3  # Not used for forecast, but required parameter
    )
    
    if ts_filtered.empty:
        empty_fig = empty_figure(background=colors['background'], text_color=colors['text'])
        no_data = no_data_text('No data')
        return empty_fig, empty_fig, no_data, no_data, no_data, no_data, no_data, no_data
    
    # Generate Daily Results chart - EXACT same as metrics.py continuous_metrics_figure
    # Uses daily_window_val (2 days default) matching metrics.py behavior
    daily_results_fig = continuous_metrics_figure(ts_filtered, window_days=daily_window_val)
    
    # Generate forecasts for each metric using DAILY AGGREGATED data (actual income per day)
    # lookback_days controls how far back in history to look
    # smoothing_days controls the smoothing window for the forecast model
    metrics_to_forecast = ['coins_earned', 'cells_earned', 'reroll_shards_earned', 
                           'coins_per_hour', 'cells_per_hour', 'reroll_shards_per_hour']
    results = {}
    
    detect_segments = 'detect' in (detect_jumps or [])
    lookback_val = float(lookback_days or 60.0)
    smoothing_val = float(smoothing_days or 14.0)
    
    # Filter ts_filtered to only include data within lookback_days
    if 'timestamp' in ts_filtered.columns:
        ts_filtered_copy = ts_filtered.copy()
        ts_filtered_copy['timestamp'] = pd.to_datetime(ts_filtered_copy['timestamp'])
        max_date = ts_filtered_copy['timestamp'].max()
        cutoff_date = max_date - pd.Timedelta(days=lookback_val)
        ts_forecast_filtered = ts_filtered_copy[ts_filtered_copy['timestamp'] >= cutoff_date]
    else:
        ts_forecast_filtered = ts_filtered.copy()
    
    # Create daily aggregated data for each metric (actual income per day)
    daily_aggregated = {}
    abs_metrics = {'coins_earned', 'cells_earned', 'reroll_shards_earned'}
    rate_metrics = {'coins_per_hour', 'cells_per_hour', 'reroll_shards_per_hour'}
    
    for metric in metrics_to_forecast:
        if metric not in ts_forecast_filtered.columns:
            continue
            
        ts = pd.to_datetime(ts_forecast_filtered['timestamp'], errors='coerce').dt.tz_localize(None)
        vals = pd.to_numeric(ts_forecast_filtered[metric], errors='coerce')
        
        if metric in abs_metrics:
            # Sum for absolute metrics
            daily_df = pd.DataFrame({'timestamp': ts.dt.normalize(), metric: vals})
            daily_df = daily_df.dropna().groupby('timestamp', as_index=False)[metric].sum()
        elif metric in rate_metrics:
            # Weighted average for rate metrics
            if 'real_time' in ts_forecast_filtered.columns:
                weights = pd.to_numeric(ts_forecast_filtered['real_time'], errors='coerce')
                tmp = pd.DataFrame({'timestamp': ts.dt.normalize(), metric: vals, 'w': weights})
                tmp = tmp.dropna()
                daily_df = tmp.groupby('timestamp', as_index=False).apply(
                    lambda g: pd.Series({
                        metric: np.average(g[metric], weights=g['w']) if g['w'].sum() > 0 else g[metric].mean()
                    })
                ).reset_index()
            else:
                daily_df = pd.DataFrame({'timestamp': ts.dt.normalize(), metric: vals})
                daily_df = daily_df.dropna().groupby('timestamp', as_index=False)[metric].mean()
        else:
            continue
            
        daily_aggregated[metric] = daily_df
    
    for metric in metrics_to_forecast:
        try:
            # Check if we have daily aggregated data
            if metric not in daily_aggregated or daily_aggregated[metric].empty:
                logger.warning(f"No daily aggregated data for {metric}")
                results[metric] = {}
                continue
            
            daily_df = daily_aggregated[metric]
            
            # Check if we have enough data points
            if len(daily_df) < 3:
                logger.warning(f"Insufficient daily data for {metric}: {len(daily_df)} days")
                results[metric] = {}
                continue
            
            # Generate forecast using daily aggregated data
            # forecast_metric expects data with 'mean' column, so rename metric to 'mean'
            forecast_input = daily_df.rename(columns={metric: 'mean'})
            
            result = forecast_metric(
                forecast_input,  # Pass data with 'mean' column
                metric,
                model_type=model_type,
                forecast_days=forecast_days or 30,
                detect_segments=detect_segments
            )
            results[metric] = result
        except Exception as e:
            logger.error(f"Error forecasting {metric}: {e}", exc_info=True)
            results[metric] = {}
    
    # Create figure with daily aggregated data
    fig = _create_forecast_figure(results, metrics_to_forecast, daily_aggregated)
    
    # Format stats for cards (6 metrics matching Daily Results layout)
    coins_stats = _format_model_stats(results.get('coins_earned', {}))
    cells_stats = _format_model_stats(results.get('cells_earned', {}))
    reroll_stats = _format_model_stats(results.get('reroll_shards_earned', {}))
    coins_hour_stats = _format_model_stats(results.get('coins_per_hour', {}))
    cells_hour_stats = _format_model_stats(results.get('cells_per_hour', {}))
    reroll_hour_stats = _format_model_stats(results.get('reroll_shards_per_hour', {}))
    
    return daily_results_fig, fig, coins_stats, cells_stats, reroll_stats, coins_hour_stats, cells_hour_stats, reroll_hour_stats
