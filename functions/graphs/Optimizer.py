import pandas as pd
import numpy as np
from itertools import product
from typing import Optional


class Optimizer:
    """
    Handles only optimization scenarios (24h, Day+Night, Custom).
    """
    def __init__(self, df: pd.DataFrame, duration: float, custom_tier: Optional[list[int]] = None,
                 max_runs: Optional[int] = None):
        self.df = df.copy()
        self.duration = duration
        self.custom_tier = custom_tier
        self.max_runs = max_runs
        self.summary_df = None
        self.breakdown_df = None
        self.total_time_hours = None

    def run(self):
        required_tiers = self.custom_tier if self.custom_tier else None
        self.summary_df, self.breakdown_df, self.total_time_hours = self._optimize_runs(
            self.df,
            self.duration,
            max_runs=self.max_runs,
            required_tiers=required_tiers
        )
        return self.summary_df, self.breakdown_df, self.total_time_hours

    @staticmethod
    def _optimize_runs(df: pd.DataFrame, time_limit: float, max_runs: Optional[int] = None, required_tiers: Optional[list[int]] = None) -> tuple[pd.DataFrame, pd.DataFrame, float]:
        # Clean and convert time strings like "7.56 h" to float
        df['real_time'] = df['real_time'].apply(lambda x: float(str(x).replace('h', '').strip()))
        df['coins_earned'] = pd.to_numeric(df['coins_earned'], errors='coerce')
        df['cells_earned'] = pd.to_numeric(df['cells_earned'], errors='coerce')
        df['reroll_shards_earned'] = pd.to_numeric(df['reroll_shards_earned'], errors='coerce')
        score_col = 'optimizer_score' if 'optimizer_score' in df.columns else 'score'
        df[score_col] = pd.to_numeric(df[score_col], errors='coerce')
        df = df.dropna(subset=['coins_earned', 'cells_earned', 'reroll_shards_earned', 'real_time', 'score'])

        # Use original integer tiers (ignore modality) - safely handle non-numeric tiers
        def safe_tier_to_int(tier_val):
            """Convert tier to int, return None for non-numeric tiers (e.g., 'Champion')."""
            try:
                # Try to convert directly (handles '12', '12+', '07', etc.)
                return int(float(str(tier_val).replace('+', '')))
            except (ValueError, TypeError):
                # Non-numeric tier (e.g., 'Champion', 'Gold')
                return None
        
        df['tier_int'] = df['tier'].apply(safe_tier_to_int)
        # Filter out rows with non-numeric tiers
        df = df[df['tier_int'].notna()]

        # Future tweak note:
        # Keep this stage side-effect free. If diagnostics are needed, surface
        # row-drop counts through return metadata/UI, not console prints.
        grouped = df.copy()
        # Aggregate by integer tier and level_1 (mean, ci_lower, ci_upper)
        grouped = grouped.groupby(['tier_int', 'level_1'], as_index=False).mean(numeric_only=True)
        # Pivot so that index is integer tier
        grouped = grouped.pivot(index='tier_int', columns='level_1')
        # Convert index to float for robust matching (if needed)
        grouped.index = grouped.index.map(lambda x: float(x) if not isinstance(x, float) else x)
        durations = grouped['real_time']['ci_upper'].values
        scores = grouped[score_col]['mean'].values
        scores_lower = grouped[score_col]['ci_lower'].values
        scores_mean = grouped[score_col]['mean'].values
        scores_upper = grouped[score_col]['ci_upper'].values
        coins_lower = grouped['coins_earned']['ci_lower'].values
        coins_mean = grouped['coins_earned']['mean'].values
        coins_upper = grouped['coins_earned']['ci_upper'].values
        cells_lower = grouped['cells_earned']['ci_lower'].values
        cells_mean = grouped['cells_earned']['mean'].values
        cells_upper = grouped['cells_earned']['ci_upper'].values
        shards_lower = grouped['reroll_shards_earned']['ci_lower'].values
        shards_mean = grouped['reroll_shards_earned']['mean'].values
        shards_upper = grouped['reroll_shards_earned']['ci_upper'].values
        tiers = grouped.index.tolist()

        durations = np.round(durations, 4)
        scale = 100
        durations_scaled = np.rint(durations * scale).astype(int)
        time_limit_scaled = int(round(float(time_limit) * scale))
        # Calculate n before using it
        n = len(durations_scaled)
        
        # Pre-allocate time for required tiers if specified
        required_time_scaled = 0
        required_combo = np.zeros(n, dtype=int)
        if required_tiers is not None and len(required_tiers) > 0:
            tier_to_idx = {float(tier): idx for idx, tier in enumerate(tiers)}
            for req_tier in required_tiers:
                if float(req_tier) in tier_to_idx:
                    idx = tier_to_idx[float(req_tier)]
                    required_combo[idx] = 1  # At least one run
                    required_time_scaled += durations_scaled[idx]
        
        # Check if required tiers fit within time limit
        if required_time_scaled > time_limit_scaled:
            summary_df = pd.DataFrame(columns=['confidence', 'coins_earned', 'cells_earned', 'reroll_shards_earned', 'total_duration'])
            breakdown_df = pd.DataFrame(columns=['tier', 'runs', 'duration_per_run', 'total_duration', 'description'])
            return summary_df, breakdown_df, 0.0
        
        # Optimize remaining time after reserving time for required tiers
        remaining_time_scaled = time_limit_scaled - required_time_scaled

        # If max_runs is specified, brute force combinations up to max_runs (nighttime runs are small)
        best_score = -np.inf
        best_t = 0
        if max_runs is not None:
            required_runs = int(required_combo.sum())
            if required_runs > max_runs:
                summary_df = pd.DataFrame(columns=['confidence', 'coins_earned', 'cells_earned', 'reroll_shards_earned', 'total_duration'])
                breakdown_df = pd.DataFrame(columns=['tier', 'runs', 'duration_per_run', 'total_duration', 'description'])
                return summary_df, breakdown_df, 0.0

            remaining_limit = int(max_runs - required_runs)
            base_score = float(np.sum(required_combo * scores))
            best_score = base_score
            best_combo = required_combo.copy()
            best_t = required_time_scaled

            if remaining_limit > 0:
                for r in range(1, remaining_limit + 1):
                    for combo in product(range(n), repeat=r):
                        combo_counts = np.zeros(n, dtype=int)
                        for idx in combo:
                            combo_counts[idx] += 1
                        total_time = required_time_scaled + int(np.sum(combo_counts * durations_scaled))
                        if total_time > time_limit_scaled:
                            continue
                        total_score = base_score + float(np.sum(combo_counts * scores))
                        if total_score > best_score:
                            best_score = total_score
                            best_combo = required_combo + combo_counts
                            best_t = total_time
        else:
            # Dynamic programming (unbounded knapsack) maximizing score for the
            # remaining budget. Any schedule-level local-optimum refinement
            # should be layered on top in weekly scheduling, not in this solver.
            dp = np.full(remaining_time_scaled + 1, -np.inf)
            dp[0] = 0
            # Track solution
            prev = np.full((remaining_time_scaled + 1, n), 0, dtype=int)

            for t in range(1, remaining_time_scaled + 1):
                for i in range(n):
                    d = durations_scaled[i]
                    if t >= d:
                        if dp[t - d] + scores[i] > dp[t]:
                            dp[t] = dp[t - d] + scores[i]
                            prev[t] = prev[t - d]
                            prev[t][i] += 1

            # Find best solution
            best_score = -np.inf
            best_t = 0
            for t in range(remaining_time_scaled + 1):
                if dp[t] > best_score:
                    best_score = dp[t]
                    best_t = t

            # Combine required runs with optimized runs
            best_combo = required_combo + (prev[best_t] if best_score > -np.inf else np.zeros(n, dtype=int))

        if best_combo is None or np.all(best_combo == 0):
            summary_df = pd.DataFrame(columns=['confidence', 'coins_earned', 'cells_earned', 'reroll_shards_earned', 'total_duration'])
            breakdown_df = pd.DataFrame(columns=['tier', 'runs', 'duration_per_run', 'total_duration', 'description'])
            return summary_df, breakdown_df, 0.0

        total_time_hours = float(sum(best_combo[i] * durations[i] for i in range(len(best_combo))))
        
        # Helper function for proper error propagation when combining runs
        def combine_ci(n_runs, lower, mean, upper):
            """
            Properly combine confidence intervals using error propagation.
            Assumes 95% CI (z=1.96).
            """
            # Calculate total mean (linear sum)
            total_mean = sum(n_runs[i] * mean[i] for i in range(len(n_runs)))
            
            # Convert CI half-widths to standard errors and propagate
            # SE = (upper - lower) / (2 * 1.96) for 95% CI
            # When summing n independent runs: SE_total = sqrt(sum(n_i * SE_i^2))
            total_variance = 0.0
            for i in range(len(n_runs)):
                if n_runs[i] > 0:
                    # Half-width of CI
                    half_width = (upper[i] - lower[i]) / 2.0
                    # SE for single run
                    se_single = half_width / 1.96
                    # Variance contribution from n_i runs
                    total_variance += n_runs[i] * (se_single ** 2)
            
            # Combined SE
            total_se = np.sqrt(total_variance)
            
            # Convert back to 95% CI
            return {
                'ci_lower': total_mean - 1.96 * total_se,
                'mean': total_mean,
                'ci_upper': total_mean + 1.96 * total_se
            }
        
        total_coins = combine_ci(best_combo, coins_lower, coins_mean, coins_upper)
        total_cells = combine_ci(best_combo, cells_lower, cells_mean, cells_upper)
        total_shards = combine_ci(best_combo, shards_lower, shards_mean, shards_upper)
        total_score = combine_ci(best_combo, scores_lower, scores_mean, scores_upper)
        summary_data = []
        for level in ['ci_lower', 'mean', 'ci_upper']:
            summary_data.append({
                'confidence': level,
                'coins_earned': total_coins[level],
                'cells_earned': total_cells[level],
                'reroll_shards_earned': total_shards[level],
                'score': total_score[level],
                'total_duration': total_time_hours
            })
        # Defensive: if summary_data is empty, still output all three rows with zeros
        if not summary_data:
            for level in ['ci_lower', 'mean', 'ci_upper']:
                summary_data.append({
                    'confidence': level,
                    'coins_earned': 0.0,
                    'cells_earned': 0.0,
                    'reroll_shards_earned': 0.0,
                    'score': 0.0,
                    'total_duration': 0.0
                })
        summary_df = pd.DataFrame(summary_data)
        breakdown_data = []
        for i in range(len(best_combo)):
            if best_combo[i] > 0:
                runs_i = int(best_combo[i])
                dur_i = float(durations[i])
                total_i = float(best_combo[i] * durations[i])
                # Output tier as int if possible, else as float
                tier_val = tiers[i]
                try:
                    tier_val_out = int(tier_val) if float(tier_val).is_integer() else float(tier_val)
                except Exception:
                    tier_val_out = tier_val
                breakdown_data.append({
                    'tier': tier_val_out,
                    'runs': runs_i,
                    'duration_per_run': dur_i,
                    'total_duration': total_i,
                    'description': f"{runs_i} x tier {tier_val_out} ({dur_i:.2f} h each)<br>(total time: {total_i:.2f} h)"
                })
        breakdown_df = pd.DataFrame(breakdown_data)
        return summary_df, breakdown_df, total_time_hours
