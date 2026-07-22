import yaml
import os
import numpy as np
from typing import Dict, Any, List
from .baseline import DriftBaselineSnapshotManager
from .prompt_drift import PromptDriftEvaluator
from .embedding_drift import EmbeddingDriftEvaluator
from .alerts import DriftAlertSystem

class DriftMonitoringSuite:
    """Orchestrates comprehensive tracking for prompt and embedding model behaviors."""

    def __init__(self, thresholds_path: str = "./config/drift_thresholds.yaml"):
        with open(thresholds_path, "r", encoding="utf-8") as f:
            self.policy = yaml.safe_load(f).get("drift_monitoring_policy", {})
        self.snapshot_mgr = DriftBaselineSnapshotManager()
        self.prompt_eval = PromptDriftEvaluator()
        self.embed_eval = EmbeddingDriftEvaluator()

    def evaluate_system_drift(self, current_data: Dict[str, Any], baseline_name: str) -> Dict[str, Any]:
        """Compares current system tracking data against the baseline to check for quality drift."""
        baseline = self.snapshot_mgr.load_baseline(baseline_name)
        
# 1. Evaluate prompt drift metrics
        semantic_shift = self.prompt_eval.measure_semantic_shift(
            current_data.get("answers", []), baseline.get("answers", [])
        )
        format_compliance = self.prompt_eval.measure_format_compliance(current_data.get("answers", []))
        
        base_citation_density = self.prompt_eval.calculate_citation_density(baseline.get("answers", []))
        curr_citation_density = self.prompt_eval.calculate_citation_density(current_data.get("answers", []))
        citation_deviation = abs(curr_citation_density - base_citation_density) / (base_citation_density or 1.0)

# 2. Evaluate embedding drift metrics
        curr_embeddings = np.array(current_data.get("embeddings", [[0.0]]))
        base_embeddings = np.array(baseline.get("embeddings", [[0.0]]))
        kl_div = self.embed_eval.calculate_kl_divergence(curr_embeddings, base_embeddings)
        
        rank_corr = self.embed_eval.calculate_retrieval_rank_correlation(
            current_data.get("ranks", []), baseline.get("ranks", [])
        )
        nn_stability = self.embed_eval.measure_nearest_neighbour_stability(
            current_data.get("top_ids", []), baseline.get("top_ids", [])
        )

# 3. Cross-reference results against configured alert thresholds
        flags = {
            "prompt_drift_flagged": (
                semantic_shift < self.policy["prompt_drift"]["semantic_similarity_floor"] or
                format_compliance < self.policy["prompt_drift"]["format_compliance_floor"] or
                citation_deviation > self.policy["prompt_drift"]["citation_density_tolerance"]
            ),
            "embedding_drift_flagged": (
                kl_div > self.policy["embedding_drift"]["kl_divergence_ceiling"] or
                rank_corr < self.policy["embedding_drift"]["spearman_rank_floor"] or
                nn_stability < self.policy["embedding_drift"]["nearest_neighbour_stability_floor"]
            )
        }

        report = {
            "metrics": {
                "semantic_similarity": round(semantic_shift, 4),
                "format_compliance": round(format_compliance, 4),
                "citation_deviation": round(citation_deviation, 4),
                "kl_divergence": round(kl_div, 4),
                "rank_correlation": round(rank_corr, 4),
                "nn_stability": round(nn_stability, 4)
            },
            "status": flags
        }

# Dispatch alert messages if operational exceptions are found
        if flags["prompt_drift_flagged"] or flags["embedding_drift_flagged"]:
            DriftAlertSystem.dispatch_incident_notification(report)

        return report