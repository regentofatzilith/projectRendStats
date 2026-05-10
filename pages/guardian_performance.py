"""Guardian Performance - Bot supporter statistics and analytics."""

import dash
from dash import dcc, html, callback, Input, Output
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import pandas as pd
import numpy as np
import logging

from functions import user_data_store
from functions.graphs.subplot_builders import create_subplots_grid
from functions.ui import empty_figure, graph_row, stat_card, warning_banner

logger = logging.getLogger(__name__)

dash.register_page(__name__, path="/guardian-performance", name="Guardian Performance", order=4)


# Fetch Guardian Drop Table (from userData.json card stats)
FETCH_DROP_TABLE = {
    'gems': {'chance': 0.04, 'daily_cap': 20},
    'medals': {'chance': 0.02, 'daily_cap': 10},
    'reroll_shards': {'chance': 0.03, 'daily_cap': None},
    'cannon_shards': {'chance': 0.01, 'daily_cap': None},
    'armor_shards': {'chance': 0.01, 'daily_cap': None},
    'generator_shards': {'chance': 0.01, 'daily_cap': None},
    'core_shards': {'chance': 0.01, 'daily_cap': None},
    'common_modules': {'chance': 0.004, 'daily_cap': 3},
    'rare_modules': {'chance': 0.001, 'daily_cap': 2},
    'coins': {'chance': 0.865, 'daily_cap': None}
}


def get_fetch_guardian_stats() -> dict:
    """Get Fetch Guardian card stats from userData.json.
    
    Returns:
        Dict with keys: cooldown (seconds), find_chance (0-1), double_find_chance (0-1)
        Returns defaults if card data not available.
    """
    # Try to get card stats from full_json
    try:
        full_json = user_data_store.full_json
        if not full_json:
            return {'cooldown': 80, 'find_chance': 0.32, 'double_find_chance': 0.05}
        
        card_tracker = full_json.get('cardTracker', {})
        card_slots = card_tracker.get('cardSlots', [])
        
        # Find Fetch Guardian (card id 31)
        fetch_card = None
        for slot in card_slots:
            if isinstance(slot, dict) and slot.get('id') == 31:
                fetch_card = slot
                break
        
        if fetch_card:
            # Extract stats - use get() for safety with defaults
            cooldown = fetch_card.get('cooldown', 80)
            find_chance = fetch_card.get('findChance', 0.32)
            double_find_chance = fetch_card.get('doubleChance', 0.05)
            
            # Normalize percentages if they're in 0-100 range
            if find_chance > 1:
                find_chance = find_chance / 100
            if double_find_chance > 1:
                double_find_chance = double_find_chance / 100
            
            return {
                'cooldown': cooldown,
                'find_chance': find_chance,
                'double_find_chance': double_find_chance
            }
    except Exception as e:
        logger.warning(f"Error getting fetch guardian stats: {e}")
    
    # Return defaults
    return {'cooldown': 80, 'find_chance': 0.32, 'double_find_chance': 0.05}


def _safe_probability(value: float) -> float:
    """Clamp a numeric value to [0, 1]."""
    return max(0.0, min(1.0, float(value)))


def _build_fetch_runs_df(game_stats_df: pd.DataFrame, cooldown_seconds: float) -> pd.DataFrame:
    """Build per-run durations and integer activation counts for Fetch Guardian.

    Uses user requirement formula:
    n = ROUND_TO_INT(duration_1 / cooldown) + ... + ROUND_TO_INT(duration_n / cooldown)
    """
    if game_stats_df.empty or 'timestamp' not in game_stats_df.columns or 'real_time' not in game_stats_df.columns:
        return pd.DataFrame()

    runs_df = game_stats_df.copy()
    runs_df['timestamp'] = pd.to_datetime(runs_df['timestamp'], errors='coerce')
    runs_df['real_time_hours'] = pd.to_numeric(runs_df['real_time'], errors='coerce').fillna(0)
    runs_df = runs_df.dropna(subset=['timestamp'])
    runs_df = runs_df[runs_df['real_time_hours'] > 0]

    if runs_df.empty:
        return pd.DataFrame()

    runs_df['duration_seconds'] = runs_df['real_time_hours'] * 3600
    runs_df['activations'] = np.rint(runs_df['duration_seconds'] / cooldown_seconds).astype(int)
    runs_df['activations'] = runs_df['activations'].clip(lower=0)
    runs_df['date'] = runs_df['timestamp'].dt.date
    return runs_df


def _expected_capped_drops(total_activations: int, find_chance: float, double_find_chance: float) -> dict:
    """Compute expected capped rewards with conditional double-drop behavior.

    Model per activation:
    - Regular drop probability: p_reg = find_chance
    - Double-drop event probability: p_double_evt = find_chance * double_find_chance
    - Expected reward units multiplier: p_reg * (1 + double_find_chance)

    Cap redistribution rule:
    - When a capped reward reaches cap, its chance is removed.
    - Removed chance is redistributed equally to the five shard-type uncapped rewards
      (reroll, cannon, generator, armor, core) per user specification example.
    """
    tracked_items = ('gems', 'medals', 'common_modules', 'rare_modules')
    caps = {k: FETCH_DROP_TABLE[k]['daily_cap'] for k in tracked_items}
    base_probs = {k: float(FETCH_DROP_TABLE[k]['chance']) for k in FETCH_DROP_TABLE.keys()}
    redistribution_items = ('reroll_shards', 'cannon_shards', 'generator_shards', 'armor_shards', 'core_shards')

    p_find = _safe_probability(find_chance)
    p_double = _safe_probability(double_find_chance)
    expected_reward_multiplier = p_find * (1.0 + p_double)

    expected = {k: 0.0 for k in tracked_items}
    active_probs = base_probs.copy()

    for _ in range(max(0, int(total_activations))):
        remaining_total = sum(active_probs.values())
        if remaining_total <= 0:
            break

        for item in tracked_items:
            if item not in active_probs:
                continue

            p_item_given_drop = active_probs[item] / remaining_total
            expected[item] += expected_reward_multiplier * p_item_given_drop

            cap = caps[item]
            if cap is not None and expected[item] >= cap:
                expected[item] = float(cap)
                removed_prob = active_probs.pop(item, 0.0)

                # Redistribute removed chance equally across the five uncapped shard-like rewards.
                if removed_prob > 0:
                    existing_targets = [k for k in redistribution_items if k in active_probs]
                    if existing_targets:
                        bonus = removed_prob / len(existing_targets)
                        for target in existing_targets:
                            active_probs[target] += bonus

    return expected


def calculate_fetch_binomial_stats(game_stats_df: pd.DataFrame, lookback_days: int = 7) -> dict:
    """Calculate Fetch Guardian stats using integer activations and binomial expectation."""
    guardian_stats = get_fetch_guardian_stats()
    cooldown = float(guardian_stats.get('cooldown', 80))
    find_chance = _safe_probability(guardian_stats.get('find_chance', 0.32))
    double_find_chance = _safe_probability(guardian_stats.get('double_find_chance', 0.05))

    # Conditional model requested by user:
    # regular drops = p_find
    # double drops  = p_find * p_double
    # expected reward units per activation = p_find * (1 + p_double)
    expected_regular_drops_per_activation = find_chance
    expected_double_drops_per_activation = find_chance * double_find_chance
    expected_reward_units_per_activation = find_chance * (1.0 + double_find_chance)

    runs_df = _build_fetch_runs_df(game_stats_df, cooldown)
    if runs_df.empty:
        return {}

    latest_date = runs_df['timestamp'].max().date()
    lookback_cutoff = latest_date - pd.Timedelta(days=lookback_days - 1)
    lookback_runs = runs_df[runs_df['date'] >= lookback_cutoff]
    if lookback_runs.empty:
        return {}

    daily = (
        lookback_runs.groupby('date', as_index=False)
        .agg(duration_seconds=('duration_seconds', 'sum'), activations=('activations', 'sum'))
        .sort_values('date')
    )

    daily['expected_regular_drops'] = daily['activations'] * expected_regular_drops_per_activation
    daily['expected_double_drops'] = daily['activations'] * expected_double_drops_per_activation
    daily['expected_reward_units'] = daily['activations'] * expected_reward_units_per_activation

    daily_expected_rows = []
    for _, row in daily.iterrows():
        exp_drops = _expected_capped_drops(
            int(row['activations']),
            find_chance=find_chance,
            double_find_chance=double_find_chance,
        )
        daily_expected_rows.append(exp_drops)
    expected_df = pd.DataFrame(daily_expected_rows)
    daily = pd.concat([daily.reset_index(drop=True), expected_df], axis=1)

    recent_cutoff = latest_date - pd.Timedelta(days=2)
    last_three_days = daily[daily['date'] >= recent_cutoff].sort_values('date', ascending=False)

    return {
        'guardian_stats': guardian_stats,
        'expected_regular_drops_per_activation': expected_regular_drops_per_activation,
        'expected_double_drops_per_activation': expected_double_drops_per_activation,
        'expected_reward_units_per_activation': expected_reward_units_per_activation,
        'avg_duration_hours_per_day': (daily['duration_seconds'] / 3600).mean(),
        'avg_activations_per_day': daily['activations'].mean(),
        'avg_expected_regular_drops_per_day': daily['expected_regular_drops'].mean(),
        'avg_expected_double_drops_per_day': daily['expected_double_drops'].mean(),
        'avg_expected_reward_units_per_day': daily['expected_reward_units'].mean(),
        'avg_expected_gems_per_day': daily['gems'].mean(),
        'avg_expected_medals_per_day': daily['medals'].mean(),
        'avg_expected_common_modules_per_day': daily['common_modules'].mean(),
        'avg_expected_rare_modules_per_day': daily['rare_modules'].mean(),
        'last_three_days': last_three_days,
    }


def create_fetch_pulls_cards(bot_df: pd.DataFrame, lookback_days: int) -> list:
    """Create cards showing Fetch Guardian pull statistics and expectations.
    
    Args:
        bot_df: DataFrame with bot supporter data (daily aggregated)
        lookback_days: Number of days to look back
    
    Returns:
        List of card components
    """
    if bot_df.empty:
        return [html.Div("No Fetch Guardian data available", style={'color': '#999'})]
    
    try:
        game_stats_df = user_data_store.game_stats_df
        stats = calculate_fetch_binomial_stats(game_stats_df, lookback_days)

        if not stats:
            return [html.Div("Insufficient run data to calculate Fetch binomial stats", style={'color': '#999'})]

        guardian_stats = stats['guardian_stats']
        p_find = _safe_probability(guardian_stats.get('find_chance', 0.32))
        p_double = _safe_probability(guardian_stats.get('double_find_chance', 0.05))
        p_double_event = _safe_probability(p_find * p_double)
        p_reward_units = _safe_probability(stats.get('expected_reward_units_per_activation', p_find * (1 + p_double)))
        last_three = stats['last_three_days']

        recent_rows = []
        for _, row in last_three.iterrows():
            recent_rows.append(
                html.Tr([
                    html.Td(str(row['date']), style={'padding': '0.35rem 0.45rem', 'color': '#e5e7eb', 'borderBottom': '1px solid #374151'}),
                    html.Td(f"{row['duration_seconds'] / 3600:.2f}h", style={'padding': '0.35rem 0.45rem', 'color': '#e5e7eb', 'borderBottom': '1px solid #374151'}),
                    html.Td(f"{int(row['activations'])}", style={'padding': '0.35rem 0.45rem', 'color': '#e5e7eb', 'borderBottom': '1px solid #374151'}),
                    html.Td(f"{row['expected_reward_units']:.2f}", style={'padding': '0.35rem 0.45rem', 'color': '#e5e7eb', 'borderBottom': '1px solid #374151'}),
                ])
            )

        cards = [
            dbc.Col([
                stat_card(
                    "Binomial Inputs (Lookback)",
                    [
                        html.Div([
                            html.Div(f"Cooldown: {guardian_stats['cooldown']}s"),
                            html.Div(f"Find Probability: {p_find * 100:.1f}%"),
                            html.Div(f"Double Probability: {p_double * 100:.1f}%"),
                            html.Div(f"Double Event p (find*double): {p_double_event * 100:.1f}%"),
                            html.Div(f"Expected reward units/activation: {stats['expected_reward_units_per_activation']:.3f}"),
                            html.Div(f"Avg Duration/Day: {stats['avg_duration_hours_per_day']:.2f}h"),
                            html.Div(f"Avg Activations/Day (n): {stats['avg_activations_per_day']:.1f}", style={'color': 'rgba(147, 51, 234, 1)'}),
                            html.Div(f"E[regular drops/day] = n*p_find: {stats['avg_expected_regular_drops_per_day']:.2f}", style={'color': 'rgba(147, 51, 234, 1)'}),
                            html.Div(f"E[double drops/day] = n*(p_find*p_double): {stats['avg_expected_double_drops_per_day']:.2f}", style={'color': 'rgba(147, 51, 234, 1)'}),
                            html.Div(f"E[reward units/day]: {stats['avg_expected_reward_units_per_day']:.2f}", style={'color': 'rgba(147, 51, 234, 1)'})
                        ], style={'fontSize': '0.92rem', 'lineHeight': '1.6'})
                    ],
                    border_left_color='rgba(147, 51, 234, 0.8)',
                )
            ], width=12, lg=4),
            dbc.Col([
                stat_card(
                    "Expected Capped Drops / Day",
                    [
                        html.Div([
                            html.Div(f"Gems: {stats['avg_expected_gems_per_day']:.2f}"),
                            html.Div(f"Medals: {stats['avg_expected_medals_per_day']:.2f}"),
                            html.Div(f"Common Modules: {stats['avg_expected_common_modules_per_day']:.2f}"),
                            html.Div(f"Rare Modules: {stats['avg_expected_rare_modules_per_day']:.2f}"),
                            html.Hr(style={'margin': '0.5rem 0'}),
                            html.Div("p varies as capped items drop out and the remaining drop table is re-normalized.",
                                     style={'fontSize': '0.82rem', 'color': '#a1a1aa'})
                        ], style={'fontSize': '0.92rem', 'lineHeight': '1.6'})
                    ],
                    border_left_color='rgba(34, 197, 94, 0.8)',
                )
            ], width=12, lg=4),
            dbc.Col([
                stat_card(
                    "Last 3 Days Duration -> Effective Pulls",
                    [
                        html.Div([
                            html.Table([
                                html.Thead(html.Tr([
                                    html.Th("Date", style={'padding': '0.35rem 0.45rem', 'color': '#f3f4f6', 'borderBottom': '1px solid #374151'}),
                                    html.Th("Duration", style={'padding': '0.35rem 0.45rem', 'color': '#f3f4f6', 'borderBottom': '1px solid #374151'}),
                                    html.Th("n", style={'padding': '0.35rem 0.45rem', 'color': '#f3f4f6', 'borderBottom': '1px solid #374151'}),
                                    html.Th("E(reward units)", style={'padding': '0.35rem 0.45rem', 'color': '#f3f4f6', 'borderBottom': '1px solid #374151'}),
                                ])),
                                html.Tbody(recent_rows if recent_rows else [
                                    html.Tr([html.Td("No recent runs", colSpan=4, style={'color': '#9ca3af', 'padding': '0.45rem'})])
                                ]),
                            ], style={
                                'width': '100%',
                                'fontSize': '0.9rem',
                                'backgroundColor': 'transparent',
                            }),
                        ], style={
                            'backgroundColor': 'rgba(17, 24, 39, 0.65)',
                            'border': '1px solid #374151',
                            'borderRadius': '6px',
                            'padding': '0.35rem',
                        })
                    ],
                    border_left_color='rgba(251, 146, 60, 0.8)',
                )
            ], width=12, lg=4)
        ]

        return cards

    except Exception as e:
        logger.error(f"Error creating fetch pulls cards: {e}")
        return [html.Div(f"Error calculating predictions: {str(e)}", style={'color': '#f87171'})]


def fill_interior_nan_only(series: pd.Series) -> pd.Series:
    """Fill NaN values only between first and last valid data points.
    
    Leading and trailing NaN values are preserved as NaN (will show as gaps).
    Interior NaN values are filled with 0.
    
    Args:
        series: Pandas Series with potential NaN values
    
    Returns:
        Series with interior NaN filled with 0, leading/trailing NaN preserved
    """
    if series.isna().all():
        # All NaN - return as is
        return series
    
    # Find first and last valid (non-NaN) indices
    valid_indices = series.notna()
    if not valid_indices.any():
        return series
    
    first_valid = valid_indices.idxmax()
    last_valid = valid_indices[::-1].idxmax()
    
    # Create a copy
    result = series.copy()
    
    # Only fill NaN between first_valid and last_valid
    interior_mask = (result.index >= first_valid) & (result.index <= last_valid)
    result.loc[interior_mask] = result.loc[interior_mask].fillna(0)
    
    return result


def create_capped_performance_cards(bot_df: pd.DataFrame, lookback_days: int) -> list:
    """Create performance cards for capped items showing avg performance vs cap.
    
    Args:
        bot_df: DataFrame with bot supporter data
        lookback_days: Number of days to look back
    
    Returns:
        List of card components
    """
    if bot_df.empty or 'date' not in bot_df.columns:
        return [html.Div("No data available", style={'color': '#999'})]
    
    # Filter to last X days
    bot_df = bot_df.copy()
    bot_df['date'] = pd.to_datetime(bot_df['date'])
    latest_date = bot_df['date'].max()
    cutoff_date = latest_date - pd.Timedelta(days=lookback_days)
    recent_df = bot_df[bot_df['date'] >= cutoff_date]
    
    if recent_df.empty:
        return [html.Div(f"No data in last {lookback_days} days", style={'color': '#999'})]
    
    capped_items = [
        ('fetch_gems', 10, 'Gems', 'rgba(147, 51, 234, 0.8)'),
        ('medals', 10, 'Medals', 'rgba(250, 204, 21, 0.8)'),
        ('common_modules', 5, 'Common Modules', 'rgba(34, 197, 94, 0.8)'),
        ('rare_modules', 2, 'Rare Modules', 'rgba(239, 68, 68, 0.8)')
    ]
    
    cards = []
    for field, cap, label, color in capped_items:
        if field in recent_df.columns:
            avg_value = recent_df[field].mean()
            percentage = (avg_value / cap * 100) if cap > 0 else 0
            
            cards.append(
                dbc.Col([
                    stat_card(
                        label,
                        [
                            html.Span(f"Avg: {avg_value:.1f} / {cap} cap ", 
                                     style={'fontSize': '1.1rem', 'color': '#fff'}),
                            html.Span(f"({percentage:.0f}%)", 
                                     style={'fontSize': '1.1rem', 'color': color, 'fontWeight': 'bold'})
                        ],
                        border_left_color=color,
                    )
                ], width=6, lg=3)
            )
    
    return cards


def create_fetch_area_chart(bot_df: pd.DataFrame) -> go.Figure:
    """Create area charts for capped items.
    
    Returns:
        figure
    """
    if bot_df.empty:
        fig = go.Figure()
        fig.update_layout(
            template="plotly_dark",
            title="No data available"
        )
        return fig
    
    # Ensure date column is datetime
    bot_df = bot_df.copy()
    bot_df['date'] = pd.to_datetime(bot_df['date'])
    
    # Area charts for capped items
    fig = create_subplots_grid(
        rows=2, cols=2,
        subplot_titles=('Fetch Gems (cap: 10/day)', 'Medals (cap: 10/day)', 
                        'Common Modules (cap: 5/day)', 'Rare Modules (cap: 2/day)'),
        vertical_spacing=0.12,
        horizontal_spacing=0.1
    )
    
    capped_items = [
        ('fetch_gems', 10, 1, 1, 'rgba(147, 51, 234, 0.8)'),
        ('medals', 10, 1, 2, 'rgba(250, 204, 21, 0.8)'),
        ('common_modules', 5, 2, 1, 'rgba(34, 197, 94, 0.8)'),
        ('rare_modules', 2, 2, 2, 'rgba(239, 68, 68, 0.8)')
    ]
    
    for field, cap, row, col, color in capped_items:
        if field in bot_df.columns:
            # Check if there's any valid data
            if bot_df[field].notna().sum() == 0:
                # No data at all - add annotation
                fig.add_annotation(
                    text="No run data for this guardian",
                    xref="x domain", yref="y domain",
                    x=0.5, y=0.5,
                    showarrow=False,
                    font=dict(size=12, color='#999'),
                    row=row, col=col
                )
                continue
            
            # Fill only interior NaN with 0, preserve leading/trailing NaN
            y_data = fill_interior_nan_only(bot_df[field])
            
            # Filter to only non-NaN values for proper x-axis range
            mask = y_data.notna()
            x_filtered = bot_df['date'][mask]
            y_filtered = y_data[mask].values
            
            # Add area trace
            fig.add_trace(
                go.Scatter(
                    x=x_filtered,
                    y=y_filtered,
                    name=field.replace('_', ' ').title(),
                    mode='lines',
                    line=dict(color=color, width=2),
                    fill='tozeroy',
                    fillcolor=color.replace('0.8', '0.3'),
                    showlegend=False
                ),
                row=row, col=col
            )
            
            # Add cap line (only where data exists)
            fig.add_trace(
                go.Scatter(
                    x=x_filtered,
                    y=[cap] * len(x_filtered),
                    name='Daily Cap',
                    mode='lines',
                    line=dict(color='rgba(255, 87, 51, 0.8)', dash='dash', width=2),
                    showlegend=(row == 1 and col == 1)
                ),
                row=row, col=col
            )
    
    fig.update_layout(
        template="plotly_dark",
        title="Fetch Performance: Capped Items",
        height=800,
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    # Set consistent x-axis range across all subplots for easy comparison
    fig.update_xaxes(title_text="Date", range=[bot_df['date'].min(), bot_df['date'].max()])
    fig.update_yaxes(title_text="Count")
    
    return fig


def create_fetch_line_chart(bot_df: pd.DataFrame) -> go.Figure:
    """Create line charts for uncapped fetch items (no markers).
    
    Returns:
        figure
    """
    if bot_df.empty:
        fig = go.Figure()
        fig.update_layout(template="plotly_dark", title="No data available")
        return fig
    
    # Ensure date column is datetime
    bot_df = bot_df.copy()
    bot_df['date'] = pd.to_datetime(bot_df['date'])
    
    # Line charts for uncapped items (2 columns x 3 rows)
    fig = create_subplots_grid(
        rows=3, cols=2,
        subplot_titles=(
            'Coins Fetched', 'Reroll Shards Fetched',
            'Cannon Shards', 'Generator Shards',
            'Armor Shards', 'Core Shards'
        ),
        vertical_spacing=0.12,
        horizontal_spacing=0.1
    )
    
    uncapped_items = [
        ('coins_fetched', 1, 1, 'rgba(250, 204, 21, 0.8)'),
        ('reroll_shards_fetched', 1, 2, 'rgba(147, 51, 234, 0.8)'),
        ('cannon_shards', 2, 1, 'rgba(236, 72, 153, 0.8)'),
        ('generator_shards', 2, 2, 'rgba(34, 197, 94, 0.8)'),
        ('armor_shards', 3, 1, 'rgba(59, 130, 246, 0.8)'),
        ('core_shards', 3, 2, 'rgba(251, 146, 60, 0.8)')
    ]
    
    for field, row, col, color in uncapped_items:
        if field in bot_df.columns:
            # Check if there's any valid data
            if bot_df[field].notna().sum() == 0:
                # No data at all - add annotation
                fig.add_annotation(
                    text="No run data for this guardian",
                    xref="x domain", yref="y domain",
                    x=0.5, y=0.5,
                    showarrow=False,
                    font=dict(size=12, color='#999'),
                    row=row, col=col
                )
                continue
            
            # Fill only interior NaN with 0, preserve leading/trailing NaN
            y_data = fill_interior_nan_only(bot_df[field])
            
            # Filter to only non-NaN values for proper x-axis range
            mask = y_data.notna()
            x_filtered = bot_df['date'][mask]
            y_filtered = y_data[mask].values
            
            fig.add_trace(
                go.Scatter(
                    x=x_filtered,
                    y=y_filtered,
                    name=field.replace('_', ' ').title(),
                    mode='lines',
                    line=dict(color=color, width=2),
                    showlegend=False
                ),
                row=row, col=col
            )
    
    fig.update_layout(
        template="plotly_dark",
        title="Fetch Performance: Resource Collection",
        height=800
    )
    # Set consistent x-axis range across all subplots for easy comparison
    fig.update_xaxes(title_text="Date", range=[bot_df['date'].min(), bot_df['date'].max()])
    fig.update_yaxes(title_text="Amount")
    
    return fig


def create_guardian_grid_chart(bot_df: pd.DataFrame) -> go.Figure:
    """Create 2x2 grid for Summon, Bounty, Attack, and Ally guardians.
    
    Args:
        bot_df: DataFrame with bot supporter data
    
    Returns:
        figure with 2x2 subplots
    """
    if bot_df.empty:
        fig = go.Figure()
        fig.update_layout(template="plotly_dark", title="No data available")
        return fig
    
    # Ensure date column is datetime
    bot_df = bot_df.copy()
    bot_df['date'] = pd.to_datetime(bot_df['date'])
    
    # Create 2x2 grid
    fig = create_subplots_grid(
        rows=2, cols=2,
        subplot_titles=('Summon: Enemies Summoned', 'Bounty: Coins Stolen',
                        'Attack: Guardian Damage', 'Ally: Guardian Catches'),
        vertical_spacing=0.12,
        horizontal_spacing=0.1
    )
    
    guardian_items = [
        ('summoned_enemies', 1, 1, 'rgba(239, 68, 68, 0.8)'),
        ('coins_stolen', 1, 2, 'rgba(250, 204, 21, 0.8)'),
        ('guardian_damage', 2, 1, 'rgba(236, 72, 153, 0.8)'),
        ('guardian_catches', 2, 2, 'rgba(59, 130, 246, 0.8)')
    ]
    
    for field, row, col, color in guardian_items:
        if field in bot_df.columns:
            # Check if there's any valid data
            if bot_df[field].notna().sum() == 0:
                # No data at all - add invisible trace to render subplot, then add annotation
                fig.add_trace(
                    go.Scatter(
                        x=[bot_df['date'].min(), bot_df['date'].max()],
                        y=[0, 0],
                        mode='lines',
                        line=dict(color='rgba(0,0,0,0)', width=0),
                        showlegend=False,
                        hoverinfo='skip'
                    ),
                    row=row, col=col
                )
                fig.add_annotation(
                    text="No run data for this guardian",
                    xref="x domain", yref="y domain",
                    x=0.5, y=0.5,
                    showarrow=False,
                    font=dict(size=14, color='#999'),
                    row=row, col=col
                )
                continue
            
            # Fill only interior NaN with 0, preserve leading/trailing NaN
            y_data = fill_interior_nan_only(bot_df[field])
            
            # Filter to only non-NaN values for proper x-axis range
            mask = y_data.notna()
            x_filtered = bot_df['date'][mask]
            y_filtered = y_data[mask].values
            
            fig.add_trace(
                go.Scatter(
                    x=x_filtered,
                    y=y_filtered,
                    name=field.replace('_', ' ').title(),
                    mode='lines',
                    line=dict(color=color, width=2),
                    fill='tozeroy',
                    fillcolor=color.replace('0.8', '0.3'),
                    showlegend=False
                ),
                row=row, col=col
            )
    
    fig.update_layout(
        template="plotly_dark",
        title="Guardian Performance: Daily Statistics",
        height=800
    )
    # Set consistent x-axis range across all subplots for easy comparison
    fig.update_xaxes(title_text="Date", range=[bot_df['date'].min(), bot_df['date'].max()])
    fig.update_yaxes(title_text="Amount")
    
    return fig


def create_simple_line_chart(bot_df: pd.DataFrame, field: str, title: str, color: str) -> go.Figure:
    """Create a simple line chart for a single metric.
    
    Args:
        bot_df: DataFrame with bot supporter data
        field: Field name to plot
        title: Chart title
        color: Line color
    
    Returns:
        figure
    """
    fig = go.Figure()
    
    if bot_df.empty or field not in bot_df.columns:
        fig.update_layout(
            template="plotly_dark",
            title=title,
            annotations=[{
                'text': f'No {field} data found',
                'xref': 'paper',
                'yref': 'paper',
                'showarrow': False,
                'font': {'size': 16}
            }]
        )
        return fig
    
    # Check if there's any valid data
    if bot_df[field].notna().sum() == 0:
        fig.update_layout(
            template="plotly_dark",
            title=title,
            annotations=[{
                'text': 'No run data for this guardian',
                'xref': 'paper',
                'yref': 'paper',
                'x': 0.5,
                'y': 0.5,
                'showarrow': False,
                'font': {'size': 16, 'color': '#999'}
            }]
        )
        return fig
    
    # Fill only interior NaN with 0, preserve leading/trailing NaN
    y_data = fill_interior_nan_only(bot_df[field])
    
    fig.add_trace(
        go.Scatter(
            x=bot_df['date'],
            y=y_data.values,
            name=field.replace('_', ' ').title(),
            mode='lines',
            line=dict(color=color, width=3),
            fill='tozeroy',
            fillcolor=color.replace('0.8', '0.2')
        )
    )
    
    fig.update_layout(
        template="plotly_dark",
        title=title,
        xaxis_title="Date",
        yaxis_title=field.replace('_', ' ').title(),
        height=400,
        showlegend=False
    )
    
    return fig


# Page layout
layout = html.Div([
    html.H1("Guardian Performance", className="page-title"),
    
    html.Div(id='guardian-no-data-warning'),
    
    # Lookback period slider
    dbc.Row([
        dbc.Col([
            html.Label('Performance Lookback Period (Days)'),
            dcc.Slider(
                id='lookback-days-slider',
                min=1,
                max=100,
                step=None,
                value=7,
                marks={
                    1: '1d',
                    2: '2d',
                    3: '3d',
                    5: '5d',
                    7: '7d',
                    10: '10d',
                    14: '2w',
                    30: '1m',
                    100: '100d'
                }
            )
        ], width=12)
    ], className="mb-4"),
    
    # Performance cards
    html.H3("Capped Items Performance"),
    dbc.Row(id='performance-cards', className="mb-4"),
    
    # Fetch Guardian Pulls Analysis
    html.H2("Fetch Guardian Pulls Analysis", style={'marginTop': '2rem'}),
    html.P("Luck-based pull calculations based on your Fetch Guardian stats and actual run data. "
           "These are expectations derived from cooldown, find chance, and drop table probabilities."),
    dbc.Row(id='fetch-pulls-cards', className="mb-4"),
    
    # Fetch Section
    html.H2("Fetch Performance", style={'marginTop': '2rem'}),
    html.P("Daily collection statistics from the Fetch Guardian. Capped items show maximum daily limits."),
    
    graph_row('fetch-area-chart', row_class_name='mb-5', row_style={'marginTop': '2rem'}),
    graph_row('fetch-line-chart', row_class_name='mb-5', row_style={'marginTop': '2rem'}),
    
    # Other Guardians Section
    html.H2("Other Guardian Performance", style={'marginTop': '2rem'}),
    html.P("Daily statistics from Summon, Bounty, Attack, and Ally Guardians."),
    
    graph_row('guardian-grid-chart', row_class_name='mb-5', row_style={'marginTop': '2rem'}),
])


def _apply_fetch_guardian_aliases(bot_df: pd.DataFrame) -> pd.DataFrame:
    """Apply aliasing for Fetch Guardian column names to handle legacy naming.
    
    Combines new and legacy names:
    - reroll_shards_fetched + reroll_shards → reroll_shards_fetched
    - fetch_gems + gems → fetch_gems
    
    If both exist, sums them. If only legacy exists, renames to new name.
    """
    if bot_df.empty:
        return bot_df
    
    result_df = bot_df.copy()

    def _num(series: pd.Series) -> pd.Series:
        return pd.to_numeric(series, errors='coerce')
    
    # Handle reroll shards: combine reroll_shards_fetched (new) with reroll_shards (legacy)
    has_new_reroll = 'reroll_shards_fetched' in result_df.columns
    has_legacy_reroll = 'reroll_shards' in result_df.columns
    
    if has_new_reroll and has_legacy_reroll:
        # Coerce to numeric and sum both columns.
        result_df['reroll_shards_fetched'] = _num(result_df['reroll_shards_fetched']).fillna(0)
        result_df['reroll_shards'] = _num(result_df['reroll_shards']).fillna(0)
        result_df['reroll_shards_fetched'] = result_df['reroll_shards_fetched'] + result_df['reroll_shards']
        result_df = result_df.drop(columns=['reroll_shards'])
    elif has_legacy_reroll and not has_new_reroll:
        # Rename legacy to new name and coerce numeric.
        result_df = result_df.rename(columns={'reroll_shards': 'reroll_shards_fetched'})
        result_df['reroll_shards_fetched'] = _num(result_df['reroll_shards_fetched'])
    elif has_new_reroll:
        result_df['reroll_shards_fetched'] = _num(result_df['reroll_shards_fetched'])
    
    # Handle gems: combine fetch_gems (new) with gems (legacy)
    has_new_gems = 'fetch_gems' in result_df.columns
    has_legacy_gems = 'gems' in result_df.columns
    
    if has_new_gems and has_legacy_gems:
        # Coerce to numeric and sum both columns.
        result_df['fetch_gems'] = _num(result_df['fetch_gems']).fillna(0)
        result_df['gems'] = _num(result_df['gems']).fillna(0)
        result_df['fetch_gems'] = result_df['fetch_gems'] + result_df['gems']
        result_df = result_df.drop(columns=['gems'])
    elif has_legacy_gems and not has_new_gems:
        # Rename legacy to new name and coerce numeric.
        result_df = result_df.rename(columns={'gems': 'fetch_gems'})
        result_df['fetch_gems'] = _num(result_df['fetch_gems'])
    elif has_new_gems:
        result_df['fetch_gems'] = _num(result_df['fetch_gems'])

    # Normalize fetch-related series to numeric if present.
    for col in (
        'coins_fetched',
        'reroll_shards_fetched',
        'cannon_shards',
        'generator_shards',
        'armor_shards',
        'core_shards',
        'fetch_gems',
    ):
        if col in result_df.columns:
            result_df[col] = _num(result_df[col])
    
    return result_df


@callback(
    [Output('performance-cards', 'children'),
     Output('fetch-pulls-cards', 'children'),
     Output('fetch-area-chart', 'figure'),
     Output('fetch-line-chart', 'figure'),
     Output('guardian-grid-chart', 'figure'),
     Output('guardian-no-data-warning', 'children')],
    [Input('user-json-store', 'data'),
     Input('lookback-days-slider', 'value')]
)
def update_guardian_performance(user_json_state, lookback_days):
    """Update all guardian performance visualizations."""
    # Get bot data from store
    bot_df = user_data_store.cleaned.get('bot_daily_df', pd.DataFrame())
    
    # Apply fetch guardian column name aliases (combine legacy + new names)
    bot_df = _apply_fetch_guardian_aliases(bot_df)
    
    if bot_df.empty:
        warning = warning_banner('No bot supporter data available. This data is compiled from run statistics.')
        empty_fig = empty_figure(template="plotly_dark")
        return [], [], empty_fig, empty_fig, empty_fig, warning
    
    # Create performance cards
    cards = create_capped_performance_cards(bot_df, lookback_days or 7)
    
    # Create fetch pulls prediction cards
    pulls_cards = create_fetch_pulls_cards(bot_df, lookback_days or 7)
    
    # Create figures
    area_fig = create_fetch_area_chart(bot_df)
    line_fig = create_fetch_line_chart(bot_df)
    guardian_grid_fig = create_guardian_grid_chart(bot_df)
    
    return cards, pulls_cards, area_fig, line_fig, guardian_grid_fig, None

