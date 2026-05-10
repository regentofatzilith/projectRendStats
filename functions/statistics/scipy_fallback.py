"""SciPy fallback implementation for Python 3.13+ compatibility."""

import os
import sys
import numpy as np

# Prefer a lightweight fallback on Python 3.13+ to avoid known import issues; allow override via env var
_ALLOW_SCIPY = os.getenv("REND_USE_SCIPY", "0") in {"1", "true", "True"}
_PY313_PLUS = (sys.version_info >= (3, 13))

try:
    if _PY313_PLUS and not _ALLOW_SCIPY:
        raise ImportError("SciPy intentionally skipped on Python 3.13+ unless REND_USE_SCIPY=1")
    from scipy import stats  # type: ignore
    _HAVE_SCIPY = True
except Exception:
    _HAVE_SCIPY = False
    class _TIntervalFallback:
        @staticmethod
        def interval(confidence: float, df: int, loc: float, scale: float):  # noqa: D401
            z_map = {
                0.80: 1.2816,
                0.85: 1.4395,
                0.90: 1.6449,
                0.95: 1.96,
                0.98: 2.3263,
                0.99: 2.5758,
            }
            z = z_map.get(round(confidence, 2), 1.96)
            delta = z * scale if np.isfinite(scale) else np.nan
            return (loc - delta, loc + delta)
    class _StatsFallback:
        t = _TIntervalFallback()
    stats = _StatsFallback()  # type: ignore

__all__ = ['stats', '_HAVE_SCIPY']
