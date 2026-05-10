"""Shared hover-formatting helpers for graph builders."""


def common_unit(values: list[float], scale_lookup: dict[str, float]) -> tuple[float, str]:
    """Find a shared scale factor/suffix for a set of numeric values."""
    max_abs = max(abs(v) for v in values if v is not None)
    lookup = [(factor, f" {unit}" if unit else "") for unit, factor in sorted(scale_lookup.items(), key=lambda x: x[1], reverse=True)]
    for factor, unit in lookup:
        if max_abs >= factor:
            return factor, unit
    return 1.0, ""
