"""Statistics module."""

from .Statistics import TimeSeriesStats, WeightedStats, stats, _HAVE_SCIPY
from .forecast_stats import forecast_metric
from .score_utils import (
	DEFAULT_SCORE_WEIGHTS,
	normalize_weights,
	compute_normalized_score_100,
	compute_max_income_baseline,
)

__all__ = [
	"TimeSeriesStats",
	"WeightedStats",
	"forecast_metric",
	"stats",
	"_HAVE_SCIPY",
	"DEFAULT_SCORE_WEIGHTS",
	"normalize_weights",
	"compute_normalized_score_100",
	"compute_max_income_baseline",
]
