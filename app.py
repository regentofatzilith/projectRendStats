# Rend Stats Dashboard - Multi-Page Application
import sys
import os
from pathlib import Path
import warnings
import logging
import dash
from dash import dcc, html, Dash
import dash_bootstrap_components as dbc

# Force clear page module cache on every startup
# print("[APP START] Clearing pages module cache...", flush=True)
modules_to_clear = [k for k in list(sys.modules.keys()) if k.startswith('pages.')]
for mod in modules_to_clear:
    del sys.modules[mod]
    # print(f"  Cleared: {mod}", flush=True)
# print("[APP START] Cache clearing complete", flush=True)

DEBUG = False
logging.basicConfig(level=logging.DEBUG, format='[%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger("rend-dashboard")
if DEBUG:
    pass
else:
    pass

PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from functions import user_data_store


def _get_cli_userdata_path(argv: list[str]) -> str | None:
    """Return a userData.json path passed via CLI.

    Supports:
      - `--userData <path>`
      - `--userData=<path>`
    """
    for i, arg in enumerate(argv):
        if arg.startswith("--userData="):
            return arg.split("=", 1)[1].strip() or None
        if arg == "--userData" and i + 1 < len(argv):
            return argv[i + 1]
    return None

appdata = os.getenv("APPDATA")
roaming_base = Path(appdata) if appdata else (Path.home() / "AppData" / "Roaming")
default_userdata = roaming_base / "rendapp" / "userData.json"

# Per your setup, userData.json lives here for the current Windows user:
#   %APPDATA%\rendapp\userData.json
# (Path.home() fallback is kept for edge-cases where APPDATA isn't set.)
candidates = [default_userdata]

# Optional overrides (useful for debugging / alternate profiles)
env_override = os.getenv("REND_USERDATA") or os.getenv("REND_USERDATA_PATH")
cli_override = _get_cli_userdata_path(sys.argv)

if cli_override:
    candidates.insert(0, Path(cli_override))
if env_override:
    candidates.insert(0, Path(env_override))

data_file = None
tried = []
for p in candidates:
    tried.append(str(p))
    if p.exists():
        data_file = p
        break

if data_file is None:
    warnings.warn(
        "Could not find userData.json. Tried: " + "; ".join(tried)
    )
else:
    try:
        user_data_store.load_from_path(str(data_file))
    #         logger.info("Loaded: %s", data_file)
    except Exception as e:
        pass

app = Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP], use_pages=True, suppress_callback_exceptions=True)
server = app.server


def _cleanup_stale_python_app_processes() -> None:
    """Best-effort cleanup of stale app.py python processes before relaunch."""
    if sys.platform != 'win32':
        return

    try:
        import subprocess

        project_path = str(PROJECT_ROOT).replace("'", "''")
        current_pid = os.getpid()
        ps_script = (
            "$project = [regex]::Escape('" + project_path + "');"
            f"$current = {current_pid};"
            "Get-CimInstance Win32_Process | "
            "Where-Object { "
            "$_.ProcessId -ne $current -and "
            "$_.Name -match '^python(w)?\\.exe$' -and "
            "$_.CommandLine -match 'app\\.py' -and "
            "$_.CommandLine -match $project "
            "} | "
            "ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }"
        )

        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_script],
            check=False,
            capture_output=True,
            text=True,
        )
    except Exception:
        # Cleanup is best-effort only; restart should continue regardless.
        pass


def _clear_python_bytecode_cache() -> None:
    """Best-effort removal of local Python bytecode caches before restart."""
    try:
        for cache_dir in PROJECT_ROOT.rglob("__pycache__"):
            if cache_dir.is_dir():
                for entry in cache_dir.iterdir():
                    try:
                        if entry.is_file():
                            entry.unlink()
                    except Exception:
                        pass
                try:
                    cache_dir.rmdir()
                except Exception:
                    pass

        for pattern in ("*.pyc", "*.pyo"):
            for bytecode_file in PROJECT_ROOT.rglob(pattern):
                try:
                    if bytecode_file.is_file():
                        bytecode_file.unlink()
                except Exception:
                    pass
    except Exception:
        # Cache cleanup is best-effort only; restart should continue regardless.
        pass


def _page_href(name: str, fallback: str = "#") -> str:
    """Resolve a registered page by display name."""
    for page in dash.page_registry.values():
        if page.get("name") == name:
            return str(page.get("relative_path", fallback))
    return fallback


def _group_nav_card(title: str, page_names: list[str]) -> dbc.Col:
    links = [
        dbc.NavLink(name, href=_page_href(name), active="exact", className="py-1", style={"fontSize": "0.95rem"})
        for name in page_names
    ]
    return dbc.Col([
        html.H6(title, style={"marginBottom": "0.5rem", "color": "#9ca3af", "fontWeight": "600"}),
        dbc.Nav(links, vertical=True, pills=True),
    ], width=3)

# Debug: Show which pages were registered
# print("\n[DEBUG] Registered pages:", flush=True)

for page_path, page_info in dash.page_registry.items():
    pass
#     print(f"  {page_path}: {page_info.get('name')} -> {page_info.get('module')}", flush=True)
# print("", flush=True)

# Disable browser caching for proper updates
@server.after_request
def add_header(response):
    """Add headers to prevent caching."""
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([html.H1('Rend Stats Dashboard', className="page-title")], width=8),
        dbc.Col([dbc.Button(' Refresh', id='refresh-data-btn', n_clicks=0, style={'marginTop': '1rem', 'width': '100%', 'backgroundColor': '#6E18FF', 'color': 'white', 'border': 'none', 'padding': '10px', 'borderRadius': '4px'})], width=2),
        dbc.Col([dbc.Button(' Restart', id='restart-app-btn', n_clicks=0, style={'marginTop': '1rem', 'width': '100%', 'backgroundColor': '#F97316', 'color': 'white', 'border': 'none', 'padding': '10px', 'borderRadius': '4px'})], width=2)
    ], className="mb-3"),
    dbc.Row([
        dbc.Col([
            dbc.Alert(
                [
                    html.Div("No userData.json loaded."),
                    html.Div("Tried paths:"),
                    html.Pre("\n".join(tried), style={'marginBottom': 0}),
                    html.Div("Override with env var REND_USERDATA or CLI --userData <path>.")
                ],
                color="warning",
                is_open=(data_file is None),
                className="mb-3",
            )
        ], width=12)
    ]),
    dbc.Row([
        _group_nav_card("Analysis", [
            "Metrics & Overview",
            "Dissonance",
            "Guardian Performance",
        ]),
        _group_nav_card("Prediction", [
            "Optimizer (Weekly)",
            "Forecast",
            "UW PermaCalc (Hybrid)",
        ]),
        _group_nav_card("Helper Tools", [
            "Tower Layout",
            "Chance Calculators",
            "UW Overview",
        ]),
        _group_nav_card("Settings", [
            "Settings",
            "Info",
        ]),
    ], className="mb-4"),
    dcc.Store(id='user-json-store', data={'ok': True, 'path': str(data_file) if data_file else None}),
    dash.page_container
], fluid=True)

@app.callback(dash.Output('restart-app-btn', 'children'), [dash.Input('restart-app-btn', 'n_clicks')])
def restart_app(n_clicks):
    if n_clicks > 0:
        import subprocess
        import signal
        import time
        
    #         logger.info("Restart requested - clearing caches and restarting...")
        
        # Clear user data store cache
        user_data_store.invalidate_weapons_cache()

        # Remove bytecode caches for a cleaner restart state.
        _clear_python_bytecode_cache()

        # Kill stale app.py python workers so relaunch is clean after code updates.
        _cleanup_stale_python_app_processes()
        
        # Start new process. On Windows, run the requested PowerShell restart flow.
        if sys.platform == 'win32':
            project_root = str(PROJECT_ROOT).replace("'", "''")
            restart_cmd = (
                "Get-Process python -ErrorAction SilentlyContinue | Stop-Process -Force; "
                f"Set-Location -LiteralPath '{project_root}'; "
                "python app.py"
            )
            subprocess.Popen(
                ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", restart_cmd],
                creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
            )
        else:
            subprocess.Popen([sys.executable] + sys.argv)
        
        # Give new process time to start
        time.sleep(1.5)
        
        # Terminate this process cleanly
        if sys.platform == 'win32':
            os.kill(os.getpid(), signal.SIGTERM)
        else:
            os._exit(0)
    return ' Restart'

@app.callback(dash.Output('user-json-store', 'data', allow_duplicate=True), [dash.Input('refresh-data-btn', 'n_clicks')], prevent_initial_call=True)
def refresh_data(n_clicks):
    if n_clicks > 0 and data_file is not None:
        try:
            user_data_store.load_from_path(str(data_file), force=True)
            # Invalidate caches to ensure combined tables recompute after refresh
            user_data_store.invalidate_weapons_cache()
            # Keep DataManager-backed pages (e.g., UW Overview) in sync with refreshed JSON.
            from functions.data import DataManager
            DataManager.get_instance().reload_data()
#             logger.info("Refreshed")
            import pandas as pd
            return {'ok': True, 'path': str(data_file), 'timestamp': pd.Timestamp.now().isoformat()}
        except Exception as e:
#             logger.exception("Refresh failed: %s", e)
            return {'ok': False, 'path': str(data_file)}
    return dash.no_update

if __name__ == '__main__':
    # Disable Flask/Werkzeug reloader to avoid Windows socket FD errors (WinError 10038)
    # Restart functionality is provided by the in-app "Restart" button.
    app.run(debug=True, use_reloader=False)
