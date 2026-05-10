from pathlib import Path
p = Path(r"\\mycloudex2ultra\Thorsten\_python\ProjectAtzi\app.py")
backup = p.with_suffix('.auto_bak.py')
if p.exists():
    p.replace(str(backup))
content = '''# Import Modules
import sys
from pathlib import Path
import os
import warnings

import dash
from dash import dcc, html
import dash_bootstrap_components as dbc

# Make sure project root is on sys.path when running the script directly
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Statistic functions
from functions.data import Import_JSON_record, cleanupJSON

# Build candidate paths (ordered): project assets, APPDATA\\rendapp, Home/AppData/Roaming/rendapp, explicit legacy path
candidates = [
    PROJECT_ROOT / 'assets' / 'userData.json',
]
appdata = os.getenv('APPDATA')
if appdata:
    candidates.append(Path(appdata) / 'rendapp' / 'userData.json')
# Home AppData path
candidates.append(Path.home() / 'AppData' / 'Roaming' / 'rendapp' / 'userData.json')
# Optional explicit legacy path (kept last)
candidates.append(Path('C:/Users/thors/AppData/Roaming/rendapp/userData.json'))

# Determine which file to use
data_file = None
tried = []
for p in candidates:
    tried.append(str(p))
    if p.exists():
        data_file = p
        break

filtered_df = None
long_stats = None
last_three_days_df = None

if data_file is None:
    warnings.warn(f"Could not find userData.json in any of: {tried}. Using empty placeholders for figures.")
    import pandas as pd
    filtered_df = pd.DataFrame(columns=['tier', 'level_1', 'coins_earned', 'cells_earned', 'reroll_shards_earned', 'real_time', 'coins_per_hour', 'cells_per_hour', 'reroll_shards_per_hour', 'score'])
    long_stats = pd.DataFrame()
    last_three_days_df = pd.DataFrame()
else:
    # Import and clean JSON data
    df = Import_JSON_record(str(data_file), 'gameStats')
    dictionary = cleanupJSON(df)
    filtered_df = dictionary['grouped_by_tier_df']
    long_stats = dictionary['optimizer_df']
    last_three_days_df = dictionary['last_three_days_df']

from functions.graphs import combined_metrics_figure, makeTable, optimize_figure, optimize_table

# Build figures conditionally to avoid exceptions when data is absent
if not filtered_df.empty:
    table = makeTable(filtered_df)
    fig = combined_metrics_figure(filtered_df)
else:
    import plotly.graph_objs as go
    table = go.Figure()
    fig = go.Figure()

# For optimizer, if long_stats is not empty then attempt optimize functions
if not long_stats.empty:
    summary_tab, breakdown_tab = optimize_table(long_stats, 13)
    optimize_fig = optimize_figure(long_stats, 13)
else:
    import plotly.graph_objs as go
    summary_tab = go.Figure()
    breakdown_tab = go.Figure()
    optimize_fig = go.Figure()

# Dash app layout (include a bootstrap theme)
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    html.H1('Rend Stats Dashboard'),
    html.P('Visualizing Rend Game Statistics by Tier and Level'),

    # First row for main graph
    dbc.Row([
        dbc.Col(dcc.Graph(figure=fig), width=12)
    ], className="mb-4"),

    # Second row for table
    dbc.Row([
        dbc.Col(dcc.Graph(figure=table), width=12)
    ]),
    html.H2('Optimizer Results'),
    dbc.Row([
        dbc.Col(dcc.Graph(figure=optimize_fig), width=12)
    ], justify="center", className="mb-4"),
    dbc.Row([
        # Uncomment if you want the breakdown table rendered
        # dbc.Col(dcc.Graph(figure=breakdown_tab), width=12)
    ], justify="center", className="mb-4")

], fluid=True)


if __name__ == '__main__':
    app.run(debug=True)
'''
p.write_text(content, encoding='utf-8')
print('Wrote', p)
print('Backup saved as', backup)
