"""Info page - landing/welcome page with project overview and navigation guide."""

import dash
from dash import dcc, html
import dash_bootstrap_components as dbc


dash.register_page(__name__, path="/", name="Info", order=0)


def _nav_card(title: str, href: str, description: str) -> dbc.Card:
    return dbc.Card(
        dbc.CardBody([
            dcc.Link(title, href=href, className="text-info", style={"fontWeight": "700", "fontSize": "1.02rem"}),
            html.Div(description, style={"color": "#cbd5e1", "marginTop": "0.35rem", "fontSize": "0.93rem"}),
        ]),
        style={
            "background": "#14152a",
            "border": "1px solid #2a2e57",
            "borderRadius": "10px",
            "height": "100%",
        },
    )


def _section_column(title: str, intro: str, cards: list[dbc.Card]) -> dbc.Col:
    return dbc.Col([
        html.H4(title, style={"marginBottom": "0.45rem"}),
        html.P(intro, style={"color": "#9ca3af", "minHeight": "2.6rem", "marginBottom": "0.8rem"}),
        dbc.Stack(cards, gap=2),
    ], width=12, md=6, xl=3)


layout = html.Div([
    html.H1("Welcome", className="page-title"),
    html.P(
        "Rend Stats Dashboard helps you analyze run performance, forecast outcomes, and plan optimizations with confidence-aware statistics.",
        style={"color": "#9ca3af", "marginBottom": "1.25rem"},
    ),
    html.P(
        "Use Refresh after updating userData.json. Use Restart only when you need a clean app restart.",
        style={"color": "#94a3b8", "marginBottom": "1.25rem"},
    ),
    dbc.Row([
        _section_column(
            "Analysis",
            "Review recent runs and trend diagnostics.",
            [
                _nav_card("Metrics & Overview", "/metrics-overview", "Per-run and daily metrics with confidence intervals and trend smoothing."),
                _nav_card("Dissonance", "/dissonance", "Disco boost and echo impact across tiers, with scenario comparisons."),
                _nav_card("Guardian Performance", "/guardian-performance", "Dedicated guardian analytics and performance diagnostics."),
            ],
        ),
        _section_column(
            "Prediction",
            "Plan next steps from historical trends.",
            [
                _nav_card("Optimization (Weekly)", "/optimizer-weekly", "Spillover-aware weekly planning and scenario comparison."),
                _nav_card("Forecast", "/forecast", "Project future metric trajectories from your historical runs."),
                _nav_card("UW PermaCalc (Hybrid)", "/perma-calc-hybrid", "Simulate UW uptime and permanent effects with module overrides."),
            ],
        ),
        _section_column(
            "Helper Tools",
            "Quick utilities for planning and reference.",
            [
                _nav_card("Tower Layout", "/tower-layout", "Plan and compare tower configuration choices."),
                _nav_card("Chance Calculators", "/chance-calculators", "Probability helpers for key in-game events and outcomes."),
                _nav_card("UW Overview", "/uw-overview", "Weapon-by-weapon breakdown of UW totals and contributing sources."),
            ],
        ),
        _section_column(
            "Settings",
            "Configure sources, app behavior, and home docs.",
            [
                _nav_card("Settings", "/settings", "Configure userData source, refresh behavior, and import workflow."),
                _nav_card("Info", "/", "This page: dashboard home, navigation, and methodology notes."),
            ],
        ),
    ], className="g-3 mb-3"),
])
