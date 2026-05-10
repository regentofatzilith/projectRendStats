"""Forecasting module for predicting future metrics based on historical trends.

Supports multiple trend types:
- Exponential growth
- Sigmoidal (S-curve) growth
- Polynomial (quadratic) growth
- Linear growth

Handles segmentation for upgrade jumps and provides confidence intervals.
Expects pre-smoothed data from Graphs.get_smoothed_daily_data() for consistency with Daily Results chart.
"""

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from scipy import stats
from typing import Tuple, Dict, List, Optional, Literal
import logging

try:
    from sklearn.linear_model import HuberRegressor, RANSACRegressor
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("sklearn not available - robust regression disabled")

logger = logging.getLogger(__name__)

# Model type definitions
ModelType = Literal['exponential', 'sigmoidal', 'linear', 'polynomial', 'auto', 'ensemble']


def exponential_func(x: np.ndarray, a: float, b: float, c: float) -> np.ndarray:
    """Exponential function: y = a * exp(b * x) + c"""
    return a * np.exp(b * x) + c


def sigmoidal_func(x: np.ndarray, L: float, k: float, x0: float, c: float) -> np.ndarray:
    """Sigmoidal (logistic) function: y = L / (1 + exp(-k * (x - x0))) + c
    
    Parameters:
    - L: curve's maximum value (carrying capacity)
    - k: steepness of the curve
    - x0: x-value of the sigmoid's midpoint
    - c: baseline offset
    """
    return L / (1 + np.exp(-k * (x - x0))) + c


def linear_func(x: np.ndarray, m: float, b: float) -> np.ndarray:
    """Linear function: y = m * x + b"""
    return m * x + b


def polynomial_func(x: np.ndarray, *coeffs) -> np.ndarray:
    """Polynomial function: y = c0 + c1*x + c2*x^2 + ... + cn*x^n"""
    return np.polyval(coeffs[::-1], x)


def detect_jumps(timestamps: pd.Series, values: pd.Series, threshold: float = 2.0) -> List[int]:
    """Detect significant jumps in the data (e.g., major upgrades).
    
    Returns indices where jumps occur based on z-score of differences.
    """
    diffs = values.diff().dropna()
    if len(diffs) < 3:
        return []
    
    # Use z-score to detect outliers
    diffs_array = np.array(diffs, dtype=np.float64)
    # Remove NaN values manually for cleaner array handling
    diffs_clean = diffs_array[~np.isnan(diffs_array)]
    if len(diffs_clean) < 3:
        return []
    
    # Manually calculate z-scores to avoid type checker issues
    mean = np.mean(diffs_clean)
    std = np.std(diffs_clean, ddof=1)
    z_scores = np.abs((diffs_clean - mean) / std) if std > 0 else np.zeros_like(diffs_clean)
    
    jump_indices = np.where(z_scores > threshold)[0] + 1  # +1 because diff shifts index
    
    return jump_indices.tolist()


def fit_exponential(x: np.ndarray, y: np.ndarray, robust: bool = False) -> Tuple[np.ndarray, float, Dict]:
    """Fit exponential model to data.
    
    Args:
        robust: if True, use robust fitting with outlier detection
    
    Returns:
    - params: [a, b, c] parameters
    - r_squared: goodness of fit
    - metadata: additional fit information
    """
    try:
        # Initial guess: derive from data
        y_min = np.min(y)
        y_max = np.max(y)
        y_range = y_max - y_min
        
        # Initial parameters: a=range, b=0.01 (small growth), c=min
        p0 = [y_range, 0.01, y_min]
        
        if robust and SKLEARN_AVAILABLE and len(x) > 10:
            # Use RANSAC to filter outliers before fitting
            def exp_model_sklearn(x_2d, a, b, c):
                return exponential_func(x_2d.flatten(), a, b, c)
            
            # Fit with RANSAC-like approach: try multiple fits and select best
            best_params = None
            best_r2 = -np.inf
            
            for _ in range(5):  # Try 5 random subsamples
                sample_idx = np.random.choice(len(x), size=max(len(x) // 2, 10), replace=False)
                x_sample = x[sample_idx]
                y_sample = y[sample_idx]
                
                try:
                    params_trial, _ = curve_fit(exponential_func, x_sample, y_sample, p0=p0, maxfev=10000)
                    y_pred_full = exponential_func(x, *params_trial)
                    ss_res = np.sum((y - y_pred_full) ** 2)
                    ss_tot = np.sum((y - np.mean(y)) ** 2)
                    r2_trial = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
                    
                    if r2_trial > best_r2:
                        best_r2 = r2_trial
                        best_params = params_trial
                except:
                    continue
            
            if best_params is not None:
                params = best_params
            else:
                params, _ = curve_fit(exponential_func, x, y, p0=p0, maxfev=10000)
        else:
            params, _ = curve_fit(exponential_func, x, y, p0=p0, maxfev=10000)
        
        # Calculate R²
        y_pred = exponential_func(x, *params)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        metadata = {
            'growth_rate': params[1],
            'baseline': params[2],
            'amplitude': params[0]
        }
        
        return params, r_squared, metadata
    except Exception as e:
        logger.warning(f"Exponential fit failed: {e}")
        return np.array([1.0, 0.0, 0.0]), 0.0, {}


def fit_sigmoidal(x: np.ndarray, y: np.ndarray, robust: bool = False) -> Tuple[np.ndarray, float, Dict]:
    """Fit sigmoidal model to data.
    
    Args:
        robust: if True, use robust fitting with outlier detection
    
    Returns:
    - params: [L, k, x0, c] parameters
    - r_squared: goodness of fit
    - metadata: additional fit information
    """
    try:
        y_min = np.min(y)
        y_max = np.max(y)
        y_range = y_max - y_min
        x_mid = (np.max(x) + np.min(x)) / 2
        
        # Initial parameters: L=range, k=0.1, x0=midpoint, c=min
        p0 = [y_range, 0.1, x_mid, y_min]
        
        # Set bounds to ensure L > 0 (positive growth)
        bounds = ([0, -np.inf, -np.inf, -np.inf], 
                  [np.inf, np.inf, np.inf, np.inf])
        
        if robust and SKLEARN_AVAILABLE and len(x) > 10:
            # Use robust approach: try multiple fits and select best
            best_params = None
            best_r2 = -np.inf
            
            for _ in range(5):  # Try 5 random subsamples
                sample_idx = np.random.choice(len(x), size=max(len(x) // 2, 10), replace=False)
                x_sample = x[sample_idx]
                y_sample = y[sample_idx]
                
                try:
                    params_trial, _ = curve_fit(sigmoidal_func, x_sample, y_sample, p0=p0, bounds=bounds, maxfev=10000)
                    y_pred_full = sigmoidal_func(x, *params_trial)
                    ss_res = np.sum((y - y_pred_full) ** 2)
                    ss_tot = np.sum((y - np.mean(y)) ** 2)
                    r2_trial = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
                    
                    if r2_trial > best_r2:
                        best_r2 = r2_trial
                        best_params = params_trial
                except:
                    continue
            
            if best_params is not None:
                params = best_params
            else:
                params, _ = curve_fit(sigmoidal_func, x, y, p0=p0, bounds=bounds, maxfev=10000)
        else:
            params, _ = curve_fit(sigmoidal_func, x, y, p0=p0, bounds=bounds, maxfev=10000)
        
        # Calculate R²
        y_pred = sigmoidal_func(x, *params)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        metadata = {
            'carrying_capacity': params[0] + params[3],
            'steepness': params[1],
            'inflection_point': params[2],
            'baseline': params[3]
        }
        
        return params, r_squared, metadata
    except Exception as e:
        logger.warning(f"Sigmoidal fit failed: {e}")
        return np.array([1.0, 0.1, 0.0, 0.0]), 0.0, {}


def fit_linear(x: np.ndarray, y: np.ndarray, robust: bool = False) -> Tuple[np.ndarray, float, Dict]:
    """Fit linear model to data.
    
    Args:
        x: input data
        y: target data
        robust: if True, use robust regression (Huber loss) to reduce outlier impact
    
    Returns:
    - params: [m, b] parameters
    - r_squared: goodness of fit
    - metadata: additional fit information
    """
    try:
        if robust and SKLEARN_AVAILABLE:
            # Use Huber regression for robustness to outliers
            x_2d = x.reshape(-1, 1)
            huber = HuberRegressor(epsilon=1.35, max_iter=200)
            huber.fit(x_2d, y)
            m = huber.coef_[0]
            b = huber.intercept_
            params = np.array([m, b])
            
            # Calculate R² using robust predictions
            y_pred = linear_func(x, *params)
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            metadata = {
                'slope': m,
                'intercept': b,
                'method': 'huber'
            }
        else:
            # Standard least squares
            params, _ = curve_fit(linear_func, x, y)
            
            # Calculate R²
            y_pred = linear_func(x, *params)
            ss_res = np.sum((y - y_pred) ** 2)
            ss_tot = np.sum((y - np.mean(y)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
            
            metadata = {
                'slope': params[0],
                'intercept': params[1],
                'method': 'least_squares'
            }
        
        return params, r_squared, metadata
    except Exception as e:
        logger.warning(f"Linear fit failed: {e}")
        return np.array([0.0, 0.0]), 0.0, {}


def fit_polynomial(x: np.ndarray, y: np.ndarray, degree: int = 2) -> Tuple[np.ndarray, float, Dict]:
    """Fit polynomial model to data.
    
    Returns:
    - params: polynomial coefficients [c0, c1, c2, ...] for c0 + c1*x + c2*x^2 + ...
    - r_squared: goodness of fit
    - metadata: additional fit information
    """
    try:
        # Use numpy's polyfit (returns coefficients in descending order: [cn, ..., c1, c0])
        coeffs = np.polyfit(x, y, degree)
        
        # Convert to ascending order for consistency with our polynomial_func
        params = coeffs[::-1]
        
        # Calculate R²
        y_pred = np.polyval(coeffs, x)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = float(1 - (ss_res / ss_tot)) if ss_tot > 0 else 0.0
        
        metadata = {
            'degree': degree,
            'coefficients': params.tolist()
        }
        
        return params, r_squared, metadata
    except Exception as e:
        logger.warning(f"Polynomial fit failed: {e}")
        return np.array([0.0] * (degree + 1)), 0.0, {}


def fit_ensemble(x: np.ndarray, y: np.ndarray) -> Tuple[Dict, float, Dict]:
    """Fit ensemble model by combining predictions from multiple models.
    
    Uses weighted average based on each model's R² score.
    
    Returns:
    - params: dict with all model parameters and weights
    - r_squared: ensemble R²
    - metadata: ensemble information
    """
    try:
        # Fit all models with robust=True
        params_exp, r2_exp, meta_exp = fit_exponential(x, y, robust=True)
        params_sig, r2_sig, meta_sig = fit_sigmoidal(x, y, robust=True)
        params_lin, r2_lin, meta_lin = fit_linear(x, y, robust=True)
        params_poly, r2_poly, meta_poly = fit_polynomial(x, y, degree=2)
        
        # Calculate weights based on R² (only positive R² values)
        r2_scores = np.array([max(0, r2_exp), max(0, r2_sig), max(0, r2_lin), max(0, r2_poly)])
        
        if r2_scores.sum() > 0:
            weights = r2_scores / r2_scores.sum()
        else:
            weights = np.array([0.25, 0.25, 0.25, 0.25])  # Equal weights if all R² are negative
        
        # Generate predictions from each model
        y_exp = exponential_func(x, *params_exp)
        y_sig = sigmoidal_func(x, *params_sig)
        y_lin = linear_func(x, *params_lin)
        y_poly = polynomial_func(x, *params_poly)
        
        # Weighted ensemble prediction
        y_ensemble = (weights[0] * y_exp + 
                     weights[1] * y_sig + 
                     weights[2] * y_lin + 
                     weights[3] * y_poly)
        
        # Calculate ensemble R²
        ss_res = np.sum((y - y_ensemble) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # Package parameters
        params_dict = {
            'exponential': {'params': params_exp, 'weight': weights[0], 'r2': r2_exp},
            'sigmoidal': {'params': params_sig, 'weight': weights[1], 'r2': r2_sig},
            'linear': {'params': params_lin, 'weight': weights[2], 'r2': r2_lin},
            'polynomial': {'params': params_poly, 'weight': weights[3], 'r2': r2_poly}
        }
        
        metadata = {
            'weights': weights.tolist(),
            'component_r2': r2_scores.tolist(),
            'dominant_model': ['exponential', 'sigmoidal', 'linear', 'polynomial'][np.argmax(weights)]
        }
        
        return params_dict, r_squared, metadata
    except Exception as e:
        logger.warning(f"Ensemble fit failed: {e}")
        return {}, 0.0, {}


def select_best_model(x: np.ndarray, y: np.ndarray, 
                     models: List[str] = ['exponential', 'sigmoidal', 'linear', 'polynomial'], 
                     robust: bool = True) -> Tuple[str, np.ndarray, float, Dict]:
    """Automatically select the best fitting model based on R².
    
    Args:
        robust: if True, use robust regression methods
    
    Returns:
    - model_type: name of best model
    - params: fitted parameters
    - r_squared: goodness of fit
    - metadata: model-specific information
    """
    results = {}
    
    if 'exponential' in models:
        params_exp, r2_exp, meta_exp = fit_exponential(x, y, robust=robust)
        results['exponential'] = (params_exp, r2_exp, meta_exp)
    
    if 'sigmoidal' in models:
        params_sig, r2_sig, meta_sig = fit_sigmoidal(x, y, robust=robust)
        results['sigmoidal'] = (params_sig, r2_sig, meta_sig)
    
    if 'linear' in models:
        params_lin, r2_lin, meta_lin = fit_linear(x, y, robust=robust)
        results['linear'] = (params_lin, r2_lin, meta_lin)
    
    if 'polynomial' in models:
        params_poly, r2_poly, meta_poly = fit_polynomial(x, y, degree=2)
        results['polynomial'] = (params_poly, r2_poly, meta_poly)
    
    # Select model with highest R²
    best_model = max(results.items(), key=lambda item: item[1][1])
    model_name = best_model[0]
    params, r_squared, metadata = best_model[1]
    
    return model_name, params, r_squared, metadata


def generate_forecast(x_historical: np.ndarray, model_type: str, params, 
                     forecast_days: int) -> Tuple[np.ndarray, np.ndarray]:
    """Generate forecast values for future time points.
    
    Args:
        params: can be np.ndarray for single models or dict for ensemble
    
    Returns:
    - x_forecast: future x values (day indices)
    - y_forecast: predicted y values
    """
    if len(x_historical) == 0:
        logger.warning("Cannot generate forecast: empty historical data")
        return np.array([]), np.array([])
    
    last_x = x_historical[-1]
    x_forecast = np.arange(last_x + 1, last_x + forecast_days + 1)
    
    if model_type == 'ensemble':
        # Ensemble prediction: weighted average of all models
        y_exp = exponential_func(x_forecast, *params['exponential']['params'])
        y_sig = sigmoidal_func(x_forecast, *params['sigmoidal']['params'])
        y_lin = linear_func(x_forecast, *params['linear']['params'])
        y_poly = polynomial_func(x_forecast, *params['polynomial']['params'])
        
        weights = np.array([params['exponential']['weight'],
                           params['sigmoidal']['weight'],
                           params['linear']['weight'],
                           params['polynomial']['weight']])
        
        y_forecast = (weights[0] * y_exp + weights[1] * y_sig + 
                     weights[2] * y_lin + weights[3] * y_poly)
    elif model_type == 'exponential':
        y_forecast = exponential_func(x_forecast, *params)
    elif model_type == 'sigmoidal':
        y_forecast = sigmoidal_func(x_forecast, *params)
    elif model_type == 'linear':
        y_forecast = linear_func(x_forecast, *params)
    elif model_type == 'polynomial':
        y_forecast = polynomial_func(x_forecast, *params)
    else:
        raise ValueError(f"Unknown model type: {model_type}")
    
    return x_forecast, y_forecast


def compute_prediction_intervals(x: np.ndarray, y: np.ndarray, 
                                 x_forecast: np.ndarray, y_forecast: np.ndarray,
                                 confidence: float = 0.95) -> Tuple[np.ndarray, np.ndarray]:
    """Compute prediction intervals for forecast.
    
    Uses residual standard error to estimate uncertainty.
    Intervals widen progressively as forecast extends further into the future.
    
    Returns:
    - lower_bound: lower prediction interval
    - upper_bound: upper prediction interval
    """
    # Calculate residual standard error from training data
    residuals = y - y_forecast[:len(y)] if len(y_forecast) >= len(y) else np.zeros_like(y)
    if len(residuals) > 2:
        se = np.std(residuals, ddof=1)
    else:
        se = 0.0
    
    # Z-score for confidence level
    z_score = stats.norm.ppf((1 + confidence) / 2)
    
    # Increase uncertainty with distance from last observation (creates funnel effect)
    # More aggressive widening: 1 + distance/baseline where baseline is ~30 days
    baseline_period = max(len(x), 30)
    distance = x_forecast - x[-1]
    distance_factor = 1 + (distance / baseline_period) * 1.5  # 1.5x multiplier for more visible funnel
    
    margin = z_score * se * distance_factor
    
    lower_bound = y_forecast - margin
    upper_bound = y_forecast + margin
    
    return lower_bound, upper_bound


def forecast_metric(smoothed_data: pd.DataFrame, metric: str, 
                   model_type: ModelType = 'auto',
                   forecast_days: int = 30,
                   detect_segments: bool = True) -> Dict:
    """Main forecasting function for a single metric.
    Expects pre-smoothed data from get_smoothed_daily_data() for consistency with Daily Results chart.
    
    Args:
        smoothed_data: DataFrame with columns [timestamp, mean, lower, upper] from get_smoothed_daily_data()
        metric: Name of the metric (used for logging and metadata)
        model_type: type of model to fit ('auto', 'exponential', 'sigmoidal', 'polynomial', 'linear')
        forecast_days: number of days to forecast ahead
        detect_segments: whether to detect and handle jump points
    
    Returns:
        Dictionary with forecast results including:
        - timestamps_hist, y_hist: historical smoothed data
        - timestamps_fit, y_fit: fitted values
        - timestamps_forecast, y_forecast: forecast values
        - lower_bound, upper_bound: prediction intervals
        - model_name, model_params, r_squared: model information
    """
    if smoothed_data.empty or 'mean' not in smoothed_data.columns or 'timestamp' not in smoothed_data.columns:
        logger.warning(f"Invalid smoothed data for {metric}")
        return {}
    
    # Use pre-smoothed mean values (already aggregated and smoothed by get_smoothed_daily_data)
    final_df = smoothed_data[['timestamp', 'mean']].copy().rename(columns={'mean': metric})
    final_df = final_df.dropna().sort_values('timestamp')
    
    if len(final_df) < 3:
        logger.warning(f"Insufficient smoothed data for forecasting {metric}: {len(final_df)} points")
        return {}
    
    # Apply rolling median for additional robustness (helps with outliers)
    if len(final_df) >= 7:
        window = min(7, len(final_df) // 3)
        final_df[metric] = final_df[metric].rolling(window=window, center=True, min_periods=1).median()
    
    # Convert timestamps to numeric (days since first observation)
    first_timestamp = final_df['timestamp'].iloc[0]
    # Ensure timestamp is datetime for calculations
    final_df['timestamp'] = pd.to_datetime(final_df['timestamp'])
    final_df['days'] = (final_df['timestamp'] - first_timestamp).dt.total_seconds() / 86400
    
    # Remove any NaN or infinite values
    final_df = final_df.dropna(subset=['days', metric])
    final_df = final_df[np.isfinite(final_df['days']) & np.isfinite(final_df[metric])]
    
    if len(final_df) < 3:
        logger.warning(f"Insufficient valid data after cleaning for {metric}: {len(final_df)} days")
        return {}
    
    x = np.array(final_df['days'].values, dtype=np.float64)
    y = np.array(final_df[metric].values, dtype=np.float64)
    
    if len(x) == 0 or len(y) == 0:
        logger.warning(f"Empty data arrays for {metric} after conversion")
        return {}
    
    # Detect jumps if requested
    segments = []
    if detect_segments and len(y) > 10:
        # For jump detection, use the smoothed data
        try:
            timestamp_series = pd.Series(final_df['timestamp'].values, index=range(len(final_df)))
            value_series = pd.Series(y, index=range(len(y)))
            jump_indices = detect_jumps(timestamp_series, value_series, threshold=2.5)
            if jump_indices:
                # Use only the most recent segment (after last jump)
                last_jump = jump_indices[-1]
                if last_jump < len(x):
                    x = x[last_jump:]
                    y = y[last_jump:]
                    segments = jump_indices
        except Exception as e:
            logger.warning(f"Jump detection failed for {metric}: {e}")
    
    # Final check for sufficient data after segmentation
    if len(x) < 3 or len(y) < 3:
        logger.warning(f"Insufficient data after segmentation for {metric}: {len(x)} points")
        return {}
    
    # Fit model
    if len(x) < 3 or len(y) < 3:
        logger.warning(f"Insufficient data points for fitting {metric}: x={len(x)}, y={len(y)}")
        return {}
    
    if model_type == 'auto':
        best_model, params, r_squared, metadata = select_best_model(x, y, robust=True)
    elif model_type == 'ensemble':
        params, r_squared, metadata = fit_ensemble(x, y)
        best_model = 'ensemble'
    elif model_type == 'exponential':
        params, r_squared, metadata = fit_exponential(x, y, robust=True)
        best_model = 'exponential'
    elif model_type == 'sigmoidal':
        params, r_squared, metadata = fit_sigmoidal(x, y, robust=True)
        best_model = 'sigmoidal'
    elif model_type == 'linear':
        params, r_squared, metadata = fit_linear(x, y, robust=True)
        best_model = 'linear'
    elif model_type == 'polynomial':
        params, r_squared, metadata = fit_polynomial(x, y, degree=2)
        best_model = 'polynomial'
    else:
        raise ValueError(f"Unknown model_type: {model_type}")
    
    # Validate that we got valid parameters
    if params is None or len(params) == 0:
        logger.warning(f"Model fitting failed for {metric}: no valid parameters")
        return {}
    
    # Generate forecast
    x_forecast, y_forecast = generate_forecast(x, best_model, params, forecast_days)
    
    if len(x_forecast) == 0 or len(y_forecast) == 0:
        logger.warning(f"Forecast generation failed for {metric}")
        return {}
    
    # Generate fitted values for historical data
    if best_model == 'ensemble':
        y_exp = exponential_func(x, *params['exponential']['params'])
        y_sig = sigmoidal_func(x, *params['sigmoidal']['params'])
        y_lin = linear_func(x, *params['linear']['params'])
        y_poly = polynomial_func(x, *params['polynomial']['params'])
        weights = np.array([params['exponential']['weight'],
                           params['sigmoidal']['weight'],
                           params['linear']['weight'],
                           params['polynomial']['weight']])
        y_fitted = (weights[0] * y_exp + weights[1] * y_sig + 
                   weights[2] * y_lin + weights[3] * y_poly)
    elif best_model == 'exponential':
        y_fitted = exponential_func(x, *params)
    elif best_model == 'sigmoidal':
        y_fitted = sigmoidal_func(x, *params)
    elif best_model == 'polynomial':
        y_fitted = polynomial_func(x, *params)
    else:  # linear
        y_fitted = linear_func(x, *params)
    
    # Compute prediction intervals
    lower_bound, upper_bound = compute_prediction_intervals(x, y, x_forecast, y_forecast)
    
    # Convert x values back to timestamps
    timestamps_historical = [first_timestamp + pd.Timedelta(days=float(d)) for d in x]
    timestamps_forecast = [first_timestamp + pd.Timedelta(days=float(d)) for d in x_forecast]
    
    return {
        'timestamps_historical': timestamps_historical,
        'x_historical': x,
        'y_historical': y,
        'y_fitted': y_fitted,
        'timestamps_forecast': timestamps_forecast,
        'x_forecast': x_forecast,
        'y_forecast': y_forecast,
        'lower_bound': lower_bound,
        'upper_bound': upper_bound,
        'model_type': best_model,
        'params': params,
        'r_squared': r_squared,
        'metadata': metadata,
        'segments': segments,
        'metric': metric
    }
