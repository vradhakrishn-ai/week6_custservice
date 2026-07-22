import pytest
import numpy as np
from app.drift.prompt_drift import PromptDriftEvaluator
from app.drift.embedding_drift import EmbeddingDriftEvaluator
from app.drift.detector import DriftMonitoringSuite

def test_prompt_format_compliance_check():
    """Confirms that the prompt evaluator correctly flags non-compliant formatting structures."""
    evaluator = PromptDriftEvaluator()
    
    valid_responses = ["Pursuant to instructions, balance scales match."]
    invalid_responses = ["Missing citation structure reference numbers here."]
    
    assert evaluator.measure_format_compliance(valid_responses) == 1.0
    assert evaluator.measure_format_compliance(invalid_responses) == 0.0

def test_embedding_statistical_kl_divergence():
    """Verifies that the embedding evaluator flags distribution shifts between arrays."""
    base_distribution = np.random.normal(0, 1, (100, 5))
    shifted_distribution = np.random.normal(2, 1, (100, 5))
    
    kl_score = EmbeddingDriftEvaluator.calculate_kl_divergence(shifted_distribution, base_distribution)
# A distinct mean shift must result in a KL divergence score above zero
    assert kl_score > 0.0

def test_nearest_neighbour_stability_index():
    """Confirms that neighbor stability calculations return exact match ratios."""
    evaluator = EmbeddingDriftEvaluator()
    
    base_neighbors = [["id_1", "id_2", "id_3"]]
    current_neighbors = [["id_1", "id_2", "id_9"]] # 2 out of 3 neighbors match
    
    stability = evaluator.measure_nearest_neighbour_stability(current_neighbors, base_neighbors)
    assert pytest.approx(stability, 0.01) == 0.666