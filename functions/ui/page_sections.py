"""Reusable page section layout helpers."""

from dash import dcc, html
import dash_bootstrap_components as dbc


def section_with_graph(
    title: str,
    graph_id: str,
    description: str | None = None,
    heading: str = 'H2',
    heading_class_name: str | None = None,
    heading_style: dict | None = None,
    graph_width: int = 12,
    row_class_name: str = 'mb-4',
    row_style: dict | None = None,
) -> list:
    """Build a standard section: heading, optional description, and a single full-width graph row."""
    components: list = []
    heading_map = {
        'H2': html.H2,
        'H3': html.H3,
        'H4': html.H4,
    }
    heading_component = heading_map.get((heading or 'H2').upper(), html.H2)
    components.append(heading_component(title, className=heading_class_name, style=heading_style))
    if description:
        components.append(html.P(description, style={'color': '#9ca3af'}))
    components.append(
        dbc.Row([dbc.Col(dcc.Graph(id=graph_id), width=graph_width)], className=row_class_name, style=row_style)
    )
    return components


def graph_row(
    graph_id: str,
    graph_width: int = 12,
    row_class_name: str = 'mb-4',
    row_style: dict | None = None,
):
    """Build a standard single-graph row."""
    return dbc.Row([dbc.Col(dcc.Graph(id=graph_id), width=graph_width)], className=row_class_name, style=row_style)
