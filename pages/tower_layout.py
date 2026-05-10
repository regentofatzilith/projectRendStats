"""Tower Layout page - visualization of tower range, black holes, and golden bot positions."""

import dash
from dash import dcc, html, callback, Input, Output, State
import dash_bootstrap_components as dbc
import logging

from functions import user_data_store
from functions.geometry import tower_layout_figure_with_kpis, golden_bot_figure_with_kpis

logger = logging.getLogger(__name__)

# Register this page
dash.register_page(__name__, path="/tower-layout", name="Tower Layout", order=3)

# Page layout
layout = html.Div([
    html.H1('Tower Layout Schematic', className="page-title"),
    
    dbc.Row([
        dbc.Col([
            html.Label('Black Hole Diameter (m base)'),
            dcc.Slider(
                id='bh-diameter-slider',
                min=30,
                max=82,
                step=1,
                value=48,
                marks={30: '30m', 40: '40m', 50: '50m', 60: '60m', 70: '70m', 82: '82m'}
            ),
            html.Div(id='bh-diameter-display', style={'fontSize': '0.85rem', 'marginTop': '4px', 'color': '#C060FF'})
        ], width=4),
        dbc.Col([
            html.Label('Tower Range (m)'),
            dbc.Input(
                id='tower-range-input',
                type='number',
                min=30.5,
                max=262,
                step=0.5,
                value=69.5,
                style={
                    'width': '90px',
                    'backgroundColor': '#222',
                    'color': '#fff',
                    'border': '1px solid #fff',
                    'borderRadius': '4px',
                    'fontWeight': 'bold'
                }
            ),
            html.Div(id='tower-range-warn', style={'fontSize': '0.7rem', 'color': '#FF6B6B'})
        ], width=2),
        dbc.Col([
            html.Label('Black Hole Count'),
            dcc.Dropdown(
                id='bh-count-dropdown',
                options=[
                    {'label': '1', 'value': 1},
                    {'label': '2 (180°)', 'value': 2},
                    {'label': '3 (120°)', 'value': 3}
                ],
                value=3,
                clearable=False,
                style={'width': '100%'}
            )
        ], width=2),
        dbc.Col([
            html.Label('Inner Orb Range (m)'),
            dcc.Dropdown(
                id='inner-orb-range-dropdown',
                options=[
                    {'label': f'{val:.2f}m', 'value': val}
                    for val in [60.00, 63.04, 66.07, 69.11, 72.14, 75.18, 78.21, 81.25, 84.28, 87.32, 90.35]
                ],
                value=60.00,
                clearable=False,
                style={'width': '100%'}
            )
        ], width=2)
    ], className="mb-4"),
    
    dbc.Row([
        dbc.Col(dcc.Graph(
            id='tower-layout-graph',
            config={'displayModeBar': False, 'displaylogo': False},
            style={'marginRight': '0', 'width': '600px', 'height': '600px'}
        ), width=6, className='p-0'),
        dbc.Col(html.Div(id='tower-layout-kpis', style={'paddingLeft': '0', 'marginLeft': '0'}), width=4, className='p-0')
    ], className="mb-3 g-0"),
    
    html.H2('Golden Bot Positions'),
    dbc.Row([
        dbc.Col([
            html.Label('Golden Bot Range (m)'),
            dcc.Slider(
                id='golden-bot-range-slider',
                min=20,
                max=60,
                step=1,
                value=40,
                marks={20: '20m', 30: '30m', 40: '40m', 50: '50m', 60: '60m'},
                className='golden-slider'
            )
        ], width=6),
    ], className="mb-4"),
    
    # Removed cooldown and uptime controls
    
    dbc.Row([
        dbc.Col([
            dbc.Button(
                "Resample Positions",
                id='resample-button',
                color="warning",
                className="mb-3",
                style={'backgroundColor': '#FFD54A', 'color': '#000000', 'border': 'none'}
            ),
            dcc.Store(id='resample-counter', data=0)
        ], width=12)
    ], justify="center", className="mb-2"),
    
    dbc.Row([
        dbc.Col(dcc.Graph(
            id='golden-bot-graph',
            config={'displayModeBar': False, 'displaylogo': False}
        ), width=6),
        dbc.Col(html.Div(id='golden-bot-kpis'), width=3),
        dbc.Col(html.Div(id='cooldown-per-package-panel'), width=3)
    ], justify="center", className="mb-4")
])


@callback(
    [Output('tower-layout-graph', 'figure'),
     Output('tower-layout-kpis', 'children'),
     Output('bh-diameter-display', 'children')],
    [Input('tower-range-input', 'value'),
     Input('bh-diameter-slider', 'value'),
     Input('bh-count-dropdown', 'value'),
     Input('inner-orb-range-dropdown', 'value')]
)
def update_tower_layout(tower_range, bh_diameter, bh_count, inner_orb_range):
    """Update the tower layout schematic and KPIs."""
    # Clamp tower range from manual entry
    try:
        tower_range = float(tower_range)
    except (TypeError, ValueError):
        tower_range = 69.5
    if tower_range < 30.5:
        tower_range = 30.5
    elif tower_range > 262:
        tower_range = 262
    fig, kpis = tower_layout_figure_with_kpis(
        tower_range=tower_range,
        black_hole_diameter=bh_diameter,
        black_hole_count=bh_count,
        inner_orb_range=inner_orb_range
    )
    # KPI cards
    try:
        angle_cov = kpis.get('tower_range_coverage', 0.0)
        area_cov = kpis.get('tower_area_coverage', 0.0)
        wall_cov = kpis.get('wall_coverage', 0.0)
        bh_center = kpis.get('bh_center_range', 0.0)
        eff_orbs = kpis.get('effective_orbs_range', 0.0)
        eff_inner_orbs = kpis.get('effective_inner_orbs_range', 0.0)
        eff_tower = kpis.get('effective_tower_range', 0.0)
        wall_diameter = 0.2158 * tower_range + 10.798
        # Scaled BH diameter used in drawing
        scaled_bh_diameter = bh_diameter * 1.33 * (tower_range / 69.5) ** 0.5
        
        primary_kill_zone = kpis.get('primary_kill_zone', 0.0)
        cards = html.Div([
            # Tower section
            html.H6('Tower', className='mt-2 mb-2', style={'fontWeight': 'bold'}),
            dbc.Row([
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.H6('Range', className='mb-1', style={'fontSize': '0.85rem'}),
                    html.Div(f"{eff_tower:.1f}m", className='metric-value', style={'fontSize': '1.2rem'})
                ]), className='mb-2', style={'borderLeft': '4px solid #7DA6C7'}), width=6),
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.H6('Displayed Wall Range', className='mb-1', style={'fontSize': '0.85rem'}),
                    html.Div(f"{wall_diameter:.1f}m", className='metric-value', style={'fontSize': '1.2rem'})
                ]), className='mb-2', style={'borderLeft': '4px solid #7DA6C7'}), width=6),
            ]),
            
            # Orbs vs. BH Center section
            html.H6('Orbs vs. BH Center', className='mt-3 mb-2', style={'fontWeight': 'bold'}),
            dbc.Row([
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.H6('Displayed Orbs Range', className='mb-1', style={'fontSize': '0.9rem'}),
                    html.Div(f"{eff_orbs:.1f}m", className='metric-value', style={'fontSize': '1.3rem'})
                ]), className='mb-2', style={'borderLeft': '4px solid #FF8888'}), width=4),
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.H6('Displayed Inner Orbs Range', className='mb-1', style={'fontSize': '0.9rem'}),
                    html.Div(f"{eff_inner_orbs:.1f}m", className='metric-value', style={'fontSize': '1.3rem'})
                ]), className='mb-2', style={'borderLeft': '4px solid #FF4444'}), width=4),
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.H6('BH Center', className='mb-1', style={'fontSize': '0.9rem'}),
                    html.Div(f"{bh_center:.1f}m", className='metric-value', style={'fontSize': '1.3rem'})
                ]), className='mb-2', style={'borderLeft': '4px solid #C060FF'}), width=4),
            ]),
            
            # Black Hole section
            html.H6('Black Hole', className='mt-3 mb-2', style={'fontWeight': 'bold'}),
            dbc.Row([
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.H6('Count', className='mb-1', style={'fontSize': '0.9rem'}),
                    html.Div(f"{bh_count}", className='metric-value', style={'fontSize': '1.3rem'})
                ]), className='mb-2', style={'borderLeft': '4px solid #C060FF'}), width=4),
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.H6('Displayed Diameter', className='mb-1', style={'fontSize': '0.9rem'}),
                    html.Div(f"{scaled_bh_diameter:.1f}m", className='metric-value', style={'fontSize': '1.3rem'})
                ]), className='mb-2', style={'borderLeft': '4px solid #C060FF'}), width=4),
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.H6('Primary Kill Zone', className='mb-1', style={'fontSize': '0.9rem', 'borderBottom': '2px dashed #C060FF', 'paddingBottom': '2px'}),
                    html.Div(f"{primary_kill_zone:.1f}m", className='metric-value', style={'fontSize': '1.3rem'})
                ]), className='mb-2', style={'borderLeft': '4px solid #C060FF'}), width=4),
            ]),
            
            # BH Coverage section
            html.H6('BH Coverage', className='mt-3 mb-2', style={'fontWeight': 'bold'}),
            dbc.Row([
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.H6('Tower Range Coverage', className='mb-1', style={'fontSize': '0.85rem'}),
                    html.Div(f"{angle_cov:.1f}%", className='metric-value', style={'fontSize': '1.2rem'})
                ]), className='mb-2', style={'borderLeft': '4px solid #7DA6C7'}), width=4),
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.H6('Tower Area Coverage', className='mb-1', style={'fontSize': '0.85rem'}),
                    html.Div(f"{area_cov:.1f}%", className='metric-value', style={'fontSize': '1.2rem'})
                ]), className='mb-2', style={'borderLeft': '4px solid #C060FF'}), width=4),
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.H6('Wall Coverage', className='mb-1', style={'fontSize': '0.85rem'}),
                    html.Div(f"{wall_cov:.1f}%", className='metric-value', style={'fontSize': '1.2rem'})
                ]), className='mb-2', style={'borderLeft': '4px solid #7DA6C7'}), width=4),
            ])
        ])
    except Exception:
        cards = []
    
    # Display current BH diameter value under slider
    bh_diameter_text = f"{bh_diameter:.1f}m"
    
    return fig, cards, bh_diameter_text


@callback(
    Output('resample-counter', 'data'),
    Input('resample-button', 'n_clicks'),
    State('resample-counter', 'data'),
    prevent_initial_call=True
)
def increment_resample_counter(n_clicks, current_counter):
    """Increment the resample counter to trigger new random positions."""
    if n_clicks is None:
        return current_counter
    return current_counter + 1


@callback(
    [Output('golden-bot-graph', 'figure'),
     Output('golden-bot-kpis', 'children'),
     Output('cooldown-per-package-panel', 'children')],
    [Input('tower-range-input', 'value'),
     Input('golden-bot-range-slider', 'value'),
     Input('bh-diameter-slider', 'value'),
     Input('bh-count-dropdown', 'value'),
     Input('resample-counter', 'data')]
)
def update_golden_bot_graph(tower_range, bot_range, bh_diameter, bh_count, resample_counter):
    """Update golden bot scatter of random positions and KPIs."""
    # Input validation and defaults
    if tower_range is None:
        tower_range = 69.5
    if bot_range is None:
        bot_range = 40.0
    if bh_diameter is None:
        bh_diameter = 48.0
    if bh_count is None:
        bh_count = 3
    if resample_counter is None:
        resample_counter = 0
    seed = 42 + resample_counter
    # 1. Graph uses 10 samples
    fig, _ = golden_bot_figure_with_kpis(
        tower_range=tower_range,
        bot_range=bot_range,
        bot_range_bonus=user_data_store.relics_data.get('Bot Range Bonus', 0.0),
        samples=10,
        seed=seed,
        black_hole_diameter=bh_diameter,
        black_hole_count=bh_count
    )
    # 2. Cards use 30 samples
    _, kpis = golden_bot_figure_with_kpis(
        tower_range=tower_range,
        bot_range=bot_range,
        bot_range_bonus=user_data_store.relics_data.get('Bot Range Bonus', 0.0),
        samples=30,
        seed=seed,
        black_hole_diameter=bh_diameter,
        black_hole_count=bh_count
    )
    
    # Build cooldown reduction panel for Galaxy Compressor
    # Omit generator-based panel here to avoid cross-page dependencies
    panel = html.Div()

    # Golden bot KPI cards
    try:
        gb_range_cov = kpis.get('tower_range_coverage', 0.0)
        gb_range_ci = kpis.get('tower_range_coverage_ci', 0.0)
        gb_bh_int = kpis.get('black_hole_intersection', 0.0)
        gb_bh_ci = kpis.get('black_hole_intersection_ci', 0.0)
        gb_wall_cov = kpis.get('wall_coverage', 0.0)
        gb_wall_ci = kpis.get('wall_coverage_ci', 0.0)
        gb_kill_zone = kpis.get('kill_zone_coverage', 0.0)
        gb_kill_zone_ci = kpis.get('kill_zone_coverage_ci', 0.0)
        # Format CI as effective range
        gb_range_low = gb_range_cov - gb_range_ci
        gb_range_high = gb_range_cov + gb_range_ci
        gb_bh_low = gb_bh_int - gb_bh_ci
        gb_bh_high = gb_bh_int + gb_bh_ci
        gb_wall_low = gb_wall_cov - gb_wall_ci
        gb_wall_high = gb_wall_cov + gb_wall_ci
        gb_kz_low = gb_kill_zone - gb_kill_zone_ci
        gb_kz_high = gb_kill_zone + gb_kill_zone_ci
        gb_cards = html.Div([
            html.H6('Golden Bot KPIs (computed with samples = 30)', className='mb-2', style={'fontWeight': 'bold'}),
            dbc.Row([
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.H6('Avg. Range Covered', className='mb-1'),
                    html.Div(f"{gb_range_cov:.1f}%", className='metric-value'),
                    html.Div(f"({gb_range_low:.1f}% ... {gb_range_high:.1f}%)", className='metric-ci', style={'fontSize': '0.85rem', 'color': '#7DA6C7'}),
                ]), className='mb-2', style={'borderLeft': '4px solid #7DA6C7'}), width=6),
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.H6('Avg. Wall Coverage', className='mb-1'),
                    html.Div(f"{gb_wall_cov:.1f}%", className='metric-value'),
                    html.Div(f"({gb_wall_low:.1f}% ... {gb_wall_high:.1f}%)", className='metric-ci', style={'fontSize': '0.85rem', 'color': '#7DA6C7'}),
                ]), className='mb-2', style={'borderLeft': '4px solid #7DA6C7'}), width=6),
            ]),
            dbc.Row([
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.H6('Avg. BH Covered', className='mb-1'),
                    html.Div(f"{gb_bh_int:.1f}%", className='metric-value'),
                    html.Div(f"({gb_bh_low:.1f}% ... {gb_bh_high:.1f}%)", className='metric-ci', style={'fontSize': '0.85rem', 'color': '#C060FF'}),
                ]), className='mb-2', style={'borderLeft': '4px solid #C060FF'}), width=6),
                dbc.Col(dbc.Card(dbc.CardBody([
                    html.H6('Avg. BH Kill Zone Covered', className='mb-1'),
                    html.Div(f"{gb_kill_zone:.1f}%", className='metric-value'),
                    html.Div(f"({gb_kz_low:.1f}% ... {gb_kz_high:.1f}%)", className='metric-ci', style={'fontSize': '0.85rem', 'color': '#C060FF'}),
                ]), className='mb-2', style={'borderLeft': '4px solid #C060FF'}), width=6),
            ]),
        ])
    except Exception:
        gb_cards = []
    return fig, gb_cards, panel


@callback(
    [Output('golden-bot-range-slider', 'value')],
    [Input('user-json-store', 'data')]
)
def initialize_gb_sliders(user_json_state):
    """Initialize Golden Bot sliders from JSON data."""
    try:
        if user_data_store.full_json is None or not isinstance(user_data_store.full_json, dict):
            return [dash.no_update]
        
        # Use Primordial Collapse as default armor module for data lookup
        armor_module = 'Primordial Collapse'
        
        # Use cached combined data from store
        combined = user_data_store.get_combined_weapons_data(selected_module=armor_module)
        
        gb_df = combined.get('Golden Bot') if isinstance(combined, dict) else None
        if gb_df is None or gb_df.empty:
            return [dash.no_update]
        
        import re as _re
        def _parse_num(val: str) -> float:
            if not isinstance(val, str):
                return 0.0
            m = _re.search(r'(\d+(?:\.\d+)?)', val)
            return float(m.group(1)) if m else 0.0
        
        def _get_tv(param_keyword: str) -> str:
            mask = gb_df['Parameter'].astype(str).str.contains(param_keyword, case=False, na=False)
            if mask.any():
                return str(gb_df.loc[mask, 'Total Value'].iloc[0])
            return ''
        
        tv_range = _get_tv('Range')
        bot_range_bonus = float(user_data_store.relics_data.get('Bot Range Bonus', 0.0) or 0.0)
        
        range_value = _parse_num(tv_range) + bot_range_bonus if tv_range else dash.no_update
        
        return [range_value]
    except Exception:
        return [dash.no_update]
