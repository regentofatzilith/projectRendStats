"""Shared Dash card components for consistent page styling."""

from typing import Any

from dash import html
import dash_bootstrap_components as dbc


def standard_card(children: list[Any], style: dict[str, Any] | None = None) -> html.Div:
    """Wrap content in the app's standard dark card style."""
    base_style: dict[str, Any] = {
        "background": "#202128",
        "padding": "1rem",
        "borderRadius": "6px",
        "marginBottom": "1rem",
    }
    if style:
        base_style.update(style)
    return html.Div(children, style=base_style)


def stat_card(
    title: str,
    body_children: list[Any],
    border_left_color: str | None = None,
    class_name: str = "mb-2",
) -> dbc.Card:
    """Create a consistent bootstrap stat card with optional colored left border."""
    card_style = {"borderLeft": f"4px solid {border_left_color}"} if border_left_color else None
    return dbc.Card(
        [
            dbc.CardBody(
                [
                    html.H6(title, className="card-title", style={"marginBottom": "0.5rem"}),
                    html.Div(body_children),
                ]
            )
        ],
        style=card_style,
        className=class_name,
    )
