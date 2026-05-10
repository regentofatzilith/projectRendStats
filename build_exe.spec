# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for building standalone executable of the Dash app.
Usage: pyinstaller build_exe.spec
"""

import sys
from pathlib import Path

block_cipher = None

# Define the main script
app_name = 'TowerConquestAnalytics'
main_script = 'app.py'

# Collect all data files
datas = [
    ('assets', 'assets'),
    ('pages', 'pages'),
    ('functions', 'functions'),
]

# Hidden imports needed for Dash and dependencies
hiddenimports = [
    # Dash core
    'dash',
    'dash.dcc',
    'dash.html',
    'dash.dependencies',
    'dash._callback',
    'dash._callback_context',
    'dash._utils',
    'dash.exceptions',
    
    # Dash pages
    'dash.page_registry',
    
    # Plotly
    'plotly',
    'plotly.graph_objs',
    'plotly.graph_objects',
    'plotly.subplots',
    'plotly.express',
    
    # Dash Bootstrap Components
    'dash_bootstrap_components',
    
    # Data processing
    'pandas',
    'numpy',
    'scipy',
    'scipy.optimize',
    'scipy.stats',
    'scipy.interpolate',
    
    # ML (for robust regression)
    'sklearn',
    'sklearn.linear_model',
    
    # HTTP requests
    'requests',
    'urllib3',
    
    # HTML parsing
    'bs4',
    'beautifulsoup4',
    
    # JSON
    'json',
    
    # Logging
    'logging',
    'logging.config',
    
    # Collections
    'collections',
    'collections.abc',
    
    # Typing
    'typing',
    'typing_extensions',
    
    # All page modules
    'pages.metrics',
    'pages.forecast',
    'pages.settings',
    'pages.tower_layout',
    # 'pages.simulation',  # EXCLUDED from release
    'pages.guardian_performance',
    'pages.chance_calculators',
    # 'pages.perma_calc',  # EXCLUDED - using perma_calc_new instead
    'pages.perma_calc_new',
    'pages.metrics_data',
    'pages.simulation_helpers',
    
    # All function modules
    'functions.data',
    'functions.data.ImportJSON',
    'functions.data.DataStore',
    'functions.graphs',
    'functions.graphs.Graphs',
    'functions.statistics',
    'functions.statistics.Statistics',
    'functions.statistics.TimeSeriesStats',
    'functions.statistics.forecast_stats',
    'functions.optimizer',
    'functions.optimizer.Optimizer',
    'functions.simulation',
    'functions.simulation.Simulation',
    'functions.simulation.SimulationClass',
    'functions.geometry',
    'functions.geometry.TowerGeometry',
    'functions.numbers',
    'functions.numbers.ConvertNumbers',
]

# Binaries (auto-detected usually, but can specify if needed)
binaries = []

a = Analysis(
    [main_script],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        'matplotlib',  # Exclude if not used
        'tkinter',     # Exclude GUI toolkit
        'PyQt5',       # Exclude GUI toolkit
        'PySide2',     # Exclude GUI toolkit
        'pages.simulation',  # Excluded from release
        'pages.perma_calc',  # Excluded - using perma_calc_new
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Set to False to hide console window (but keep True for debugging first)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one: 'assets/icon.ico'
)
