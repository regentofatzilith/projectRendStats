"""Standard subplot factory helpers for consistent grid construction."""

from typing import Any

import plotly.graph_objs as go
from plotly.subplots import make_subplots


def create_subplots_grid(
    rows: int,
    cols: int,
    subplot_titles: list[str] | tuple[str, ...] | None = None,
    vertical_spacing: float | None = None,
    horizontal_spacing: float | None = None,
    specs: list[list[dict[str, Any]]] | None = None,
    x_title: str | None = None,
    y_title: str | None = None,
) -> go.Figure:
    """Create a Plotly subplot grid using a centralized factory."""
    kwargs: dict[str, Any] = {
        'rows': rows,
        'cols': cols,
    }
    if subplot_titles is not None:
        kwargs['subplot_titles'] = subplot_titles
    if vertical_spacing is not None:
        kwargs['vertical_spacing'] = vertical_spacing
    if horizontal_spacing is not None:
        kwargs['horizontal_spacing'] = horizontal_spacing
    if specs is not None:
        kwargs['specs'] = specs
    if x_title is not None:
        kwargs['x_title'] = x_title
    if y_title is not None:
        kwargs['y_title'] = y_title

    return make_subplots(**kwargs)
