"""Clustering module for identifying distinct run modes within tiers.

Uses Gaussian Mixture Models (GMM) to identify clusters in run data,
with Bayesian Information Criterion (BIC) to determine optimal cluster count.
"""

import pandas as pd
import numpy as np
from sklearn.mixture import GaussianMixture
from sklearn.preprocessing import StandardScaler
from typing import Optional, List, Dict, Tuple
import logging

logger = logging.getLogger(__name__)


class RunClustering:
    """Identify distinct run modes (strategies/configurations) within each tier."""
    
    def __init__(self, df: pd.DataFrame, tier_column: str = 'tier'):
        """Initialize clustering with run data.
        
        Args:
            df: DataFrame with individual run records
            tier_column: Column name containing tier information
        """
        self.df = df.copy()
        self.tier_column = tier_column
        self.clusters = {}
        self.scalers = {}
        
    def identify_clusters(
        self,
        features: Optional[List[str]] = None,
        max_clusters: int = 3,
        min_samples_per_cluster: int = 2,
        min_duration_diff_pct: float = 10.0
    ) -> Dict[int, pd.DataFrame]:
        """Identify clusters for each tier using GMM with BIC selection.
        
        Args:
            features: List of feature columns to use for clustering.
                     Defaults to ['coins_earned', 'cells_earned', 'reroll_shards_earned', 'real_time']
            max_clusters: Maximum number of clusters to test (default 3: long/normal/short runs)
            min_samples_per_cluster: Minimum samples required per cluster (default 3)
            min_duration_diff_pct: Minimum percentage difference in duration to create separate clusters.
                                  Default 10% means clusters must differ by at least 10% of max duration.
                                  Example: 7h max -> 0.7h minimum difference required for distinct clusters
            
        Returns:
            Dictionary mapping tier -> DataFrame with cluster assignments and statistics
        """
        if features is None:
            features = ['coins_earned', 'cells_earned', 'reroll_shards_earned', 'real_time']
        
        # Validate features exist in dataframe
        missing_features = [f for f in features if f not in self.df.columns]
        if missing_features:
            raise ValueError(f"Features not found in dataframe: {missing_features}")
        
        unique_tiers = sorted(self.df[self.tier_column].unique())
        results = {}
        
        for tier in unique_tiers:
            tier_data = self.df[self.df[self.tier_column] == tier].copy()
            n_samples = len(tier_data)
            
            # Skip tiers with insufficient data
            if n_samples < min_samples_per_cluster:
                logger.debug(f"Tier {tier}: Only {n_samples} samples, skipping clustering")
                tier_data['cluster'] = 0
                tier_data['cluster_label'] = f"{tier}"
                results[tier] = tier_data
                continue
            
            # Extract features and handle missing values
            X = tier_data[features].values
            
            # Check for NaN or infinite values
            if np.any(~np.isfinite(X)):
                logger.warning(f"Tier {tier}: Non-finite values detected, imputing with median")
                for i, feature in enumerate(features):
                    col_data = X[:, i]
                    if np.any(~np.isfinite(col_data)):
                        median_val = np.nanmedian(col_data[np.isfinite(col_data)])
                        X[:, i] = np.where(np.isfinite(col_data), col_data, median_val)
            
            # Standardize features
            scaler = StandardScaler()
            X_scaled = scaler.fit_transform(X)
            self.scalers[tier] = scaler
            
            # Determine optimal number of clusters using BIC
            n_clusters_optimal = self._find_optimal_clusters(
                X_scaled, 
                max_clusters=min(max_clusters, n_samples // min_samples_per_cluster)
            )
            
            # Fit GMM with optimal number of clusters
            if n_clusters_optimal > 1:
                gmm = GaussianMixture(
                    n_components=n_clusters_optimal,
                    covariance_type='full',
                    random_state=42,
                    n_init=10
                )
                cluster_labels = gmm.fit_predict(X_scaled)
                
                # Apply duration-based threshold to filter out insignificant clusters
                cluster_labels = self._apply_duration_threshold(
                    tier_data, 
                    cluster_labels, 
                    min_duration_diff_pct
                )
                
                logger.info(
                    f"Tier {tier}: Identified {len(np.unique(cluster_labels))} clusters from {n_samples} samples"
                )
            else:
                cluster_labels = np.zeros(n_samples, dtype=int)
                logger.debug(f"Tier {tier}: Single cluster (homogeneous runs)")
            
            # Add cluster information to dataframe
            tier_data['cluster'] = cluster_labels
            
            # Sort clusters by mean duration for consistent labeling (0=short, 1=normal, 2=long)
            if n_clusters_optimal > 1:
                cluster_means = []
                for c in range(n_clusters_optimal):
                    cluster_mask = cluster_labels == c
                    mean_duration = tier_data[cluster_mask]['real_time'].mean() if 'real_time' in tier_data.columns else 0
                    cluster_means.append((c, mean_duration))
                
                # Sort by duration and create mapping (shortest gets 0, longest gets highest)
                cluster_means.sort(key=lambda x: x[1])
                cluster_mapping = {old: new for new, (old, _) in enumerate(cluster_means)}
                
                # Remap cluster labels
                tier_data['cluster'] = tier_data['cluster'].map(cluster_mapping)
            
            tier_data['cluster_label'] = tier_data['cluster'].apply(
                lambda c: f"{tier}.{c}" if n_clusters_optimal > 1 else f"{tier}"
            )
            
            results[tier] = tier_data
            self.clusters[tier] = n_clusters_optimal
        
        return results
    
    def _apply_duration_threshold(
        self, 
        tier_data: pd.DataFrame, 
        cluster_labels: np.ndarray,
        min_duration_diff_pct: float
    ) -> np.ndarray:
        """Apply duration-based threshold to filter insignificant clusters.
        
        Clusters are only kept separate if their mean durations differ by at least
        min_duration_diff_pct of the maximum run duration in the tier.
        
        Args:
            tier_data: DataFrame for a single tier
            cluster_labels: Initial cluster assignments from GMM
            min_duration_diff_pct: Minimum percentage difference (e.g., 10 for 10%)
            
        Returns:
            Filtered cluster labels (may merge small differences into single cluster)
        """
        if 'real_time' not in tier_data.columns:
            return cluster_labels
        
        unique_clusters = np.unique(cluster_labels)
        if len(unique_clusters) <= 1:
            return cluster_labels
        
        # Calculate mean duration per cluster
        durations = tier_data['real_time'].values
        max_duration = durations.max()
        min_diff_threshold = max_duration * (min_duration_diff_pct / 100.0)
        
        # Map each cluster to its mean duration
        cluster_durations = {}
        for cluster in unique_clusters:
            mask = cluster_labels == cluster
            cluster_durations[cluster] = durations[mask].mean()
        
        # Sort clusters by duration
        sorted_clusters = sorted(unique_clusters, key=lambda c: cluster_durations[c])
        
        # Check which clusters should be merged
        # Merge if adjacent clusters are closer than threshold
        cluster_mapping = {}
        current_group = 0
        prev_duration = None
        
        for cluster in sorted_clusters:
            duration = cluster_durations[cluster]
            
            if prev_duration is None or (duration - prev_duration) < min_diff_threshold:
                # Merge into same group
                cluster_mapping[cluster] = current_group
                if prev_duration is None:
                    prev_duration = duration
            else:
                # Start new group
                current_group += 1
                cluster_mapping[cluster] = current_group
                prev_duration = duration
        
        # Remap cluster labels
        remapped_labels = np.array([cluster_mapping[c] for c in cluster_labels])
        
        # Log if any merging occurred
        if len(np.unique(remapped_labels)) < len(unique_clusters):
            logger.debug(
                f"Duration threshold ({min_duration_diff_pct}%): "
                f"Merged {len(unique_clusters)} clusters to {len(np.unique(remapped_labels))} "
                f"(min_diff={min_diff_threshold:.3f}h, max_duration={max_duration:.3f}h)"
            )
        
        return remapped_labels
    
    def _find_optimal_clusters(self, X: np.ndarray, max_clusters: int) -> int:
        """Find optimal number of clusters using BIC with improvement threshold.
        
        Args:
            X: Standardized feature matrix
            max_clusters: Maximum number of clusters to test
            
        Returns:
            Optimal number of clusters
        """
        if max_clusters < 2:
            return 1
        
        n_samples = X.shape[0]
        
        # Test different numbers of clusters
        bic_scores = []
        cluster_range = range(1, max_clusters + 1)
        
        for n_clusters in cluster_range:
            try:
                gmm = GaussianMixture(
                    n_components=n_clusters,
                    covariance_type='full',
                    random_state=42,
                    n_init=10
                )
                gmm.fit(X)
                bic_scores.append(gmm.bic(X))
            except Exception as e:
                logger.warning(f"GMM fitting failed for {n_clusters} clusters: {e}")
                bic_scores.append(np.inf)
        
        # Select number of clusters with lowest BIC
        optimal_idx = np.argmin(bic_scores)
        optimal_n_clusters = list(cluster_range)[optimal_idx]
        
        # For small samples, require significant BIC improvement to choose 1 cluster over 2
        # BIC difference should be at least 10 (strong evidence) to prefer simpler model
        if n_samples < 10 and max_clusters >= 2 and len(bic_scores) >= 2:
            bic_1_cluster = bic_scores[0]  # 1 cluster is first in range
            bic_2_clusters = bic_scores[1]  # 2 clusters is second
            bic_improvement = bic_1_cluster - bic_2_clusters
            
            # If 2 clusters is better or only slightly worse, use 2 clusters
            if bic_improvement < 10:
                optimal_n_clusters = 2
                logger.info(
                    f"Small sample ({n_samples}): Using 2 clusters despite BIC "
                    f"(BIC_1={bic_1_cluster:.1f}, BIC_2={bic_2_clusters:.1f}, improvement={bic_improvement:.1f})"
                )
        
        logger.info(f"BIC scores: {dict(zip(cluster_range, bic_scores))}")
        logger.info(f"Optimal clusters: {optimal_n_clusters} (BIC: {bic_scores[optimal_idx]:.2f})")
        
        return optimal_n_clusters
    
    def compute_cluster_statistics(
        self,
        clustered_data: Dict[int, pd.DataFrame],
        metrics: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """Compute statistics for each cluster.
        
        Args:
            clustered_data: Dictionary from identify_clusters()
            metrics: Metrics to compute statistics for.
                    Defaults to ['coins_earned', 'cells_earned', 'reroll_shards_earned', 'real_time']
            
        Returns:
            DataFrame with cluster statistics (mean, std, count)
        """
        if metrics is None:
            metrics = ['coins_earned', 'cells_earned', 'reroll_shards_earned', 'real_time']
        
        stats_rows = []
        
        for tier, tier_data in clustered_data.items():
            clusters = tier_data['cluster'].unique()
            
            for cluster in sorted(clusters):
                cluster_runs = tier_data[tier_data['cluster'] == cluster]
                n_runs = len(cluster_runs)
                
                stats_row = {
                    'tier': tier,
                    'cluster': cluster,
                    'cluster_label': f"{tier}.{cluster}" if len(clusters) > 1 else f"{tier}",
                    'n_runs': n_runs
                }
                
                for metric in metrics:
                    if metric in cluster_runs.columns:
                        stats_row[f'{metric}_mean'] = cluster_runs[metric].mean()
                        stats_row[f'{metric}_std'] = cluster_runs[metric].std()
                        stats_row[f'{metric}_ci_lower'] = cluster_runs[metric].quantile(0.16)
                        stats_row[f'{metric}_ci_upper'] = cluster_runs[metric].quantile(0.84)
                
                stats_rows.append(stats_row)
        
        return pd.DataFrame(stats_rows)
    
    def get_cluster_summary(self) -> pd.DataFrame:
        """Get summary of clusters identified per tier.
        
        Returns:
            DataFrame with tier and number of clusters
        """
        return pd.DataFrame([
            {'tier': tier, 'n_clusters': n_clusters}
            for tier, n_clusters in sorted(self.clusters.items())
        ])


def cluster_optimizer_data(
    df: pd.DataFrame,
    tier_column: str = 'tier',
    features: Optional[List[str]] = None,
    max_clusters: int = 3,
    min_duration_diff_pct: float = 10.0
) -> Tuple[Dict[int, pd.DataFrame], pd.DataFrame]:
    """Convenience function to cluster run data and compute statistics.
    
    Args:
        df: DataFrame with individual run records
        tier_column: Column name containing tier information
        features: Features to use for clustering
        max_clusters: Maximum number of clusters to test (default 3: long/normal/short runs)
        min_duration_diff_pct: Minimum percentage difference in duration to create separate clusters
                              Default 10% prevents over-clustering (e.g., 7h max -> 0.7h min difference)
        
    Returns:
        Tuple of (clustered_data_dict, cluster_statistics_df)
    """
    clustering = RunClustering(df, tier_column)
    clustered_data = clustering.identify_clusters(
        features, 
        max_clusters,
        min_duration_diff_pct=min_duration_diff_pct
    )
    cluster_stats = clustering.compute_cluster_statistics(clustered_data)
    
    return clustered_data, cluster_stats
