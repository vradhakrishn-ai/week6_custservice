import numpy as np
from scipy.stats import entropy, spearmanr
from typing import List, Dict, Any

class EmbeddingDriftEvaluator:
    """Runs statistical calculations to detect distribution changes in embedding vectors."""

    @staticmethod
    def calculate_kl_divergence(current_matrix: np.ndarray, baseline_matrix: np.ndarray, bins: int = 20) -> float:
        """Measures distribution shifts between active embedding arrays and baseline parameters."""
# Standardize vector dimensions into predictable histograms
        current_hist, bin_edges = np.histogram(current_matrix, bins=bins, density=True)
        baseline_hist, _ = np.histogram(baseline_matrix, bins=bin_edges, density=True)
        
# Add epsilon smoothing to prevent zero-division errors during probability calculations
        current_hist = np.where(current_hist == 0, 1e-6, current_hist)
        baseline_hist = np.where(baseline_hist == 0, 1e-6, baseline_hist)
        
        return float(entropy(current_hist, baseline_hist))

    @staticmethod
    def calculate_retrieval_rank_correlation(current_ranks: List[int], baseline_ranks: List[int]) -> float:
        """Calculates the Spearman rank correlation coefficient for retrieval consistency."""
        correlation, _ = spearmanr(current_ranks, baseline_ranks)
        if np.isnan(correlation):
            return 1.0
        return float(correlation)

    @staticmethod
    def measure_nearest_neighbour_stability(current_top_n: List[List[str]], baseline_top_n: List[List[str]]) -> float:
        """Measures overlap consistency within top neighbor results to track vector changes."""
        if not current_top_n or len(current_top_n) != len(baseline_top_n):
            return 1.0
            
        total_queries = len(current_top_n)
        overlap_ratios = []
        
        for idx in range(total_queries):
            current_set = set(current_top_n[idx])
            baseline_set = set(baseline_top_n[idx])
            overlap = current_set.intersection(baseline_set)
            overlap_ratios.append(len(overlap) / len(baseline_set))
            
        return float(np.mean(overlap_ratios))