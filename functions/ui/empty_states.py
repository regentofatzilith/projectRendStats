"""Shared empty-state UI and figure helpers."""

from dash import html
import plotly.graph_objects as go


def warning_banner(message: str) -> html.Div:
    """Render a consistent orange warning banner used across pages."""
    return html.Div(
        message,
        style={
            'color': '#f97316',
            'background': '#222',
            'padding': '1rem',
            'marginBottom': '1rem',
            'borderRadius': '6px',
        },
    )


def no_data_text(message: str = 'No data') -> list[html.Div]:
    """Render a standard lightweight no-data text block for card bodies."""
    return [html.Div(message, style={'color': '#999'})]


def empty_figure(
    title: str | None = None,
    background: str = '#000000',
    text_color: str = '#FAFAFA',
    template: str | None = None,
) -> go.Figure:
    """Create a standardized empty Plotly figure."""
    fig = go.Figure()
    layout_kwargs: dict = {}
    if title:
        layout_kwargs['title'] = title
    if template:
        layout_kwargs['template'] = template
    layout_kwargs.update(
        {
            'plot_bgcolor': background,
            'paper_bgcolor': background,
            'font_color': text_color,
        }
    )
    fig.update_layout(**layout_kwargs)
    return fig
