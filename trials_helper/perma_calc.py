# --- Add callback to extract combined UW data and display transposed tables ---
import dash
from dash import dcc, html, callback, Input, Output, State, no_update
import dash_bootstrap_components as dbc
from functions.data import extract_combined_ultimate_weapons_data
from functions import user_data_store

# Store for combined UW data
uw_data_store = dcc.Store(id='perma-uw-data-store')

def transpose_uw_table(df, uw_name):
    """Transpose UW DataFrame to requested format."""
    if df.empty:
        return dbc.Table([html.Thead(html.Tr([html.Th(uw_name)])), html.Tbody([html.Tr([html.Td('No data')])])], bordered=True, size='sm', className='mb-3')
    # Only keep relevant parameters
    params = ['Cooldown', 'Quantity', 'Duration']
    # Find which exist in df
    present = [p for p in params if p in df['Parameter'].values]
    # Build rows: Source | Cooldown | Quantity/Duration | Level | Module | Lab | Total Value
    rows = []
    for param in present:
        row = df[df['Parameter'] == param].iloc[0]
        rows.append([
            param,
            row.get('Cooldown', row['Total Value'] if param == 'Cooldown' else ''),
            row.get('Quantity', row['Total Value'] if param in ['Quantity', 'Duration'] else ''),
            row['Level'],
            row['Module Effect'],
            row['Labs Level'],
            row['Total Value']
        ])
    # Header
    header = html.Tr([html.Th('Source'), html.Th('Cooldown'), html.Th('Quantity/Duration'), html.Th('Level'), html.Th('Module'), html.Th('Lab'), html.Th('Total Value')])
    body = [html.Tr([html.Td(cell) for cell in row]) for row in rows]
    return dbc.Table([html.Thead(header), html.Tbody(body)], bordered=True, size='sm', className='mb-3')



"""Dash UI for PermaCalc - Ultimate Weapon permanence calculations and overview."""

import dash
from dash import dcc, html, callback, Input, Output, State
import dash_bootstrap_components as dbc
import logging
import numpy as np
from PermaCalc import get_uw_overview, simulate_packages, simulate_uw_uptime

logger = logging.getLogger(__name__)

# Page disabled - replaced by perma_calc_new.py
# dash.register_page(__name__, path="/perma-calc", name="UW PermaCalc", order=4)

# Layout for PermaCalc page

# Store for simulation results
simulation_store = dcc.Store(id='perma-sim-store')

layout = html.Div([
    html.H1('Ultimate Weapon Permanence Calculator', className="page-title"),
    html.Hr(),
    uw_data_store,
    html.H4('UW Overview'),
    html.Div(id='uw-overview-panel'),
    html.Hr(),
    html.H4('Simulate Packages (3600s)'),
    dbc.Row([
        dbc.Col([
            html.Label('Select Ultimate Weapon:'),
            dcc.Dropdown(
                id='uw-selector',
                options=[
                    {'label': 'Death Wave', 'value': 'Death Wave'},
                    {'label': 'Golden Tower', 'value': 'Golden Tower'},
                    {'label': 'Black Hole', 'value': 'Black Hole'},
                    {'label': 'Chrono Field', 'value': 'Chrono Field'}
                ],
                value='Death Wave',
                clearable=False,
                className='mb-3'
            ),
            dbc.Button('Run 3600s Simulation', id='run-sim-btn', color='primary', className='mb-2'),
            html.Div(id='sim-packages-output', className='mt-2'),
        ], width=6),
        dbc.Col([
            dcc.Loading(
                id='perma-graph-loading',
                type='default',
                children=dcc.Graph(id='perma-uw-graph', config={'displayModeBar': False})
            )
        ], width=6)
    ]),
    simulation_store,
    html.Hr(),
    html.H4('UW Uptime Simulation'),
    dbc.Row([
        dbc.Col([
            html.Label('UW Cooldown (sec)'),
            dcc.Input(id='uw-cooldown-input', type='number', min=0, max=1000, step=1, value=120),
            html.Br(),
            html.Label('Package Time Reduction (sec)'),
            dcc.Input(id='package-reduction-input', type='number', min=0, max=1000, step=1, value=30),
            html.Br(),
            html.Label('UW Duration (sec)'),
            dcc.Input(id='uw-duration-input', type='number', min=0, max=1000, step=1, value=30),
            html.Br(),
            dbc.Button('Simulate UW Uptime', id='simulate-uw-uptime-btn', color='success', className='mt-2'),
            html.Div(id='uw-uptime-output', className='mt-2')
        ], width=6)
    ])
])


# Overview callback (simulation.py style)

# --- Detailed UW Overview Callback (Table style, simulation.py inspired) ---
@callback(
    Output('uw-overview-panel', 'children'),
    Input('uw-overview-panel', 'id')
)
def render_uw_overview(_):
    # Try to load user data from user_data_store if available
    try:
        from functions.data import extract_combined_ultimate_weapons_data
        import dash
        # Try to get user data from store (simulate simulation.py style)
        # If unavailable, fallback to empty dict
        user_json = getattr(dash.get_app(), 'user_json_data', None)
        if user_json is None:
            # Try to get from user_data_store if available
            try:
                from functions import user_data_store
                user_json = getattr(user_data_store, 'current_json', None)
            except Exception:
                user_json = None
        if not user_json:
            return html.Div("No user data loaded. Please import data in Settings.", style={'color': '#999', 'padding': '2rem'})
        # Extract combined UW data
        uw_data = extract_combined_ultimate_weapons_data(user_json)
        # Render tables for each UW
        tables = []
        for uw_name, df in uw_data.items():
            if df.empty:
                tables.append(html.Div([
                    html.H5(uw_name),
                    dbc.Table([html.Thead(html.Tr([html.Th("No data")]))], bordered=True, size='sm', className='mb-3')
                ]))
            else:
                # Build table header and rows
                header = html.Tr([
                    html.Th('Parameter'), html.Th('Level'), html.Th('Target Level'),
                    html.Th('Module Effect'), html.Th('Labs Level'), html.Th('Total Value')
                ])
                body = [html.Tr([
                    html.Td(row['Parameter']), html.Td(row['Level']), html.Td(row.get('Target Level', '')),
                    html.Td(row.get('Module Effect', '')), html.Td(row.get('Labs Level', '')), html.Td(row.get('Total Value', ''))
                ]) for _, row in df.iterrows()]
                tables.append(html.Div([
                    html.H5(uw_name),
                    dbc.Table([html.Thead(header), html.Tbody(body)], bordered=True, size='sm', className='mb-3')
                ]))
        return html.Div(tables)
    except Exception as e:
        import traceback
        return html.Div([
            html.Span('Error rendering UW overview: ', style={'color': '#f97316'}),
            html.Span(str(e)),
            html.Details([
                html.Summary('Show error details'),
                html.Pre(traceback.format_exc(), style={'fontSize': '0.8rem', 'maxHeight': '200px', 'overflow': 'auto'})
            ])
        ])

# Simulation callback for 3600s
@callback(
    Output('perma-sim-store', 'data'),
    Output('sim-packages-output', 'children'),
    Input('run-sim-btn', 'n_clicks'),
    State('uw-selector', 'value')
)
def run_perma_sim(n_clicks, uw_name):
    if not n_clicks:
        return {}, dash.no_update
    # Get UW params
    uw_dict = {uw['name']: uw for uw in get_uw_overview()}
    uw = uw_dict.get(uw_name, None)
    if not uw:
        return {}, html.Div("Invalid UW selected.")
    cooldown = uw['cooldown']
    duration = uw['duration']
    # Simulate 3600s
    timeline = np.arange(0, 3600)
    # Simulate random package times (rounded)
    package_times = np.sort(np.random.choice(timeline, size=10, replace=False))
    package_times = np.round(package_times).astype(int)
    # Simulate permanence (True/False): active if (t % (cooldown+duration)) < duration
    is_active = [(t % (cooldown + duration)) < duration for t in timeline]
    # Store results
    sim_data = {
        'timeline': timeline.tolist(),
        'package_times': package_times.tolist(),
        'is_active': is_active,
        'uw_name': uw_name
    }
    # Display package times
    pkg_display = html.Div([
        html.H6('Package Times (nearest second):'),
        html.Div(', '.join(str(pt) for pt in package_times))
    ])
    return sim_data, pkg_display

# Graph output callback
@callback(
    Output('perma-uw-graph', 'figure'),
    Input('perma-sim-store', 'data'),
    State('uw-selector', 'value')
)
def render_perma_graph(sim_data, uw_name):
    import plotly.graph_objects as go
    if not sim_data or 'timeline' not in sim_data:
        return go.Figure(layout={'paper_bgcolor':'#000','plot_bgcolor':'#000','annotations':[{'text':'Run simulation to view','showarrow':False,'x':0.5,'y':0.5,'font':{'color':'#888'}}]})
    timeline = sim_data['timeline']
    is_active = sim_data['is_active']
    uw_colors = {
        'Black Hole': '#9933FF',
        'Golden Tower': '#FF6600',
        'Chrono Field': '#00FFFF',
        'Death Wave': '#FF0000',
    }
    uw_color = uw_colors.get(uw_name, '#3b82f6')
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=timeline,
        y=is_active,
        name='UW Active',
        line=dict(color=uw_color, width=2),
        mode='lines'
    ))
    fig.update_layout(
        paper_bgcolor='#000',
        plot_bgcolor='#000',
        yaxis=dict(title='Active', tickvals=[0,1], ticktext=['False','True']),
        xaxis=dict(title='Time (s)'),
        title=f'UW Permanence: {uw_name} (3600s)'
    )
    return fig

@callback(
    Output('packages-output', 'children'),
    Input('simulate-packages-btn', 'n_clicks'),
    State('n-trials-input', 'value'),
    State('boss-package-check', 'value')
)
def run_package_sim(n_clicks, n_trials, boss_package):
    if not n_clicks:
        return dash.no_update
    boss = 'boss' in boss_package if boss_package else False
    times = simulate_packages(n_trials=n_trials or 1000, boss_package=boss)
    mean_time = np.mean(times)
    std_time = np.std(times)
    return html.Div([
        html.Div(f"Mean package time: {mean_time:.2f} sec"),
        html.Div(f"Std dev: {std_time:.2f} sec")
    ])

@callback(
    Output('uw-uptime-output', 'children'),
    Input('simulate-uw-uptime-btn', 'n_clicks'),
    State('uw-cooldown-input', 'value'),
    State('package-reduction-input', 'value'),
    State('uw-duration-input', 'value')
)
def run_uw_uptime_sim(n_clicks, cooldown, reduction, duration):
    if not n_clicks:
        return dash.no_update
    result = simulate_uw_uptime(cooldown or 0, reduction or 0, duration or 0)
    return html.Div([
        html.Div(f"Remaining Uptime: {result['remaining_uptime']:.2f} sec"),
        html.Div(f"Active: {'True' if result['is_active'] else 'False'}")
    ])
