"""Statistics module - backward compatibility wrapper.

This module maintains backward compatibility by re-exporting classes
from their new separate module files.
"""

from .scipy_fallback import stats, _HAVE_SCIPY
from .weighted_stats import WeightedStats
from .time_series_stats import TimeSeriesStats

__all__ = ['WeightedStats', 'TimeSeriesStats', 'stats', '_HAVE_SCIPY']
