"""Settings page - user data import and configuration."""

import dash
from dash import dcc, html, callback, Input, Output, State, callback_context, no_update
import dash_bootstrap_components as dbc
import pandas as pd
from pathlib import Path
import os
import logging

from functions import user_data_store
from functions.data import DataManager

logger = logging.getLogger(__name__)

# Register this page
dash.register_page(__name__, path="/settings", name="Settings", order=10)

# Page layout
layout = html.Div([
    html.H1('Settings', className="page-title"),
    
    html.H3('User Data Import'),
    html.P('Configure where to load your game data from:', style={'color': '#999', 'marginBottom': '1rem'}),
    
    dbc.Row([
        dbc.Col([
            html.Label('Import Source'),
            dcc.RadioItems(
                id='user-json-source-radio',
                options=[
                    {'label': 'Current (AppData/roaming/rendapp/userData.json)', 'value': 'current'},
                    {'label': 'Custom Path', 'value': 'custom'},
                    {'label': 'Upload File', 'value': 'upload'}
                ],
                value='current',
                labelStyle={'display': 'block'}
            )
        ], width=4),
        dbc.Col([
            html.Label('Custom JSON Path'),
            dcc.Input(
                id='user-json-path-input',
                type='text',
                placeholder='e.g. C:\\Users\\<you>\\AppData\\Roaming\\rendapp\\userData.json',
                style={'width': '100%'}
            ),
            html.Div([
                html.Label('Or upload userData.json'),
                dcc.Upload(
                    id='user-json-upload',
                    children=html.Div(['Drag and Drop or ', html.A('Select File')]),
                    style={
                        'width': '100%', 'height': '38px', 'lineHeight': '38px', 'borderWidth': '1px',
                        'borderStyle': 'dashed', 'borderRadius': '4px', 'textAlign': 'center', 'marginTop': '6px'
                    },
                    accept='.json'
                )
            ]),
            html.Div(id='user-json-import-status', style={'marginTop': '0.5rem', 'opacity': 0.8})
        ], width=6),
        dbc.Col([
            dbc.Button('Import JSON', id='import-user-json-btn', color='primary', style={'marginTop': '1.5rem'})
        ], width=2)
    ], className='mb-4')
])


@callback(
    [Output('user-json-store', 'data'),
     Output('user-json-import-status', 'children')],
    [Input('import-user-json-btn', 'n_clicks'),
     Input('user-json-upload', 'contents')],
    [State('user-json-source-radio', 'value'),
     State('user-json-path-input', 'value'),
     State('user-json-upload', 'filename')],
    prevent_initial_call=True
)
def import_user_json(n_clicks, upload_contents, source_choice, custom_path, upload_filename):
    """Import user-specific JSON and update global data store."""
    # Determine which input triggered the callback
    ctx = callback_context
    if not ctx.triggered:
        return no_update, no_update
    
    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    
    # Helper function to process a file path
    def process_json_file(file_path: Path, display_name: str):
        """Process JSON file via store and return status."""
        try:
            user_data_store.load_from_path(str(file_path), force=True)
            # Invalidate DataManager cache so UW pages pick up the new data
            DataManager.get_instance().reload_data()
            
            filtered_df = user_data_store.cleaned.get('grouped_by_tier_df', pd.DataFrame())
            time_series_df = user_data_store.cleaned.get('time_series_df', pd.DataFrame())
            
            status = html.Div([
                html.Span('✓ Imported: ', style={'color': '#1EE2A5'}),
                html.Span(display_name, style={'fontWeight': 'bold'}),
                html.Br(),
                html.Small(f"Loaded {len(filtered_df)} grouped records, {len(time_series_df)} time series points")
            ])
            return {'ok': True, 'path': str(file_path), 'timestamp': pd.Timestamp.now().isoformat()}, status
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            logger.exception("Import failed: %s", e)
            return {'ok': False, 'path': str(file_path)}, html.Div([
                html.Span('Import failed: ', style={'color': '#f97316'}),
                html.Span(str(e)),
                html.Br(),
                html.Details([
                    html.Summary('Show error details'),
                    html.Pre(error_details, style={'fontSize': '0.8rem', 'maxHeight': '200px', 'overflow': 'auto'})
                ])
            ])
    
    # Handle file upload trigger
    if trigger_id == 'user-json-upload' and upload_contents:
        try:
            import base64, json
            header, b64data = upload_contents.split(',', 1)
            decoded = base64.b64decode(b64data).decode('utf-8')
            parsed = json.loads(decoded)
            
            user_data_store.load_from_json(parsed)
            # Invalidate DataManager cache so UW pages pick up the new data
            DataManager.get_instance().reload_data()
            
            filtered_df = user_data_store.cleaned.get('grouped_by_tier_df', pd.DataFrame())
            time_series_df = user_data_store.cleaned.get('time_series_df', pd.DataFrame())
            
            status = html.Div([
                html.Span('✓ Uploaded & Imported: ', style={'color': '#1EE2A5'}),
                html.Span(upload_filename or 'uploaded.json', style={'fontWeight': 'bold'}),
                html.Br(),
                html.Small(f"Loaded {len(filtered_df)} grouped records, {len(time_series_df)} time series points (in-memory)")
            ])
            return {'ok': True, 'path': upload_filename or 'uploaded.json', 'timestamp': pd.Timestamp.now().isoformat()}, status
        except Exception as e:
            return {'ok': False, 'path': str(upload_filename) if upload_filename else ''}, html.Div([
                html.Span('Upload failed: ', style={'color': '#f97316'}),
                html.Span(str(e))
            ])
    
    # Handle button click (for current/custom path)
    if trigger_id == 'import-user-json-btn' and n_clicks:
        selected_path: Path
        if source_choice == 'custom' and custom_path:
            # Normalize custom input path
            raw = str(custom_path).strip().strip('"').strip("'")
            expanded = os.path.expandvars(os.path.expanduser(raw))
            candidates = [
                Path(raw),
                Path(expanded),
                Path(os.path.normpath(expanded)),
            ]
            # Offer slash-swapped variants as fallback
            if '\\' in expanded:
                candidates.append(Path(expanded.replace('\\', '/')))
            if '/' in expanded:
                candidates.append(Path(expanded.replace('/', '\\')))
            
            chosen = None
            for c in candidates:
                try:
                    if c.exists():
                        chosen = c
                        break
                except Exception:
                    continue
            selected_path = chosen if chosen is not None else candidates[0]
        else:
            # Current path logic: use APPDATA\rendapp\userData.json
            appdata = os.getenv("APPDATA")
            if appdata:
                selected_path = Path(appdata) / 'rendapp' / 'userData.json'
            else:
                selected_path = Path.home() / 'AppData' / 'Roaming' / 'rendapp' / 'userData.json'

        # Check if file exists
        if not selected_path.exists():
            return {'ok': False, 'path': str(selected_path)}, html.Div([
                html.Span('Import failed: file not found ', style={'color': '#f87171'}),
                html.Code(str(selected_path)),
                html.Br(),
                html.Span('Tip: Use a full absolute path, e.g. D:/Downloads/userData.json or D:\\Downloads\\userData.json')
            ])
        
        # Process through standard pipeline
        return process_json_file(selected_path, str(selected_path))
    
    return no_update, no_update
