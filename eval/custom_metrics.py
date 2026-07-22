import re
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

similarity_model = SentenceTransformer('all-MiniLM-L6-v2')

class SecureBankCustomEvaluator:
    """Calculates non-standard enterprise metrics for compliance, stability, and access boundaries."""

    @staticmethod
    def calculate_answer_stability(run_a: str, run_b: str) -> float:
        """Measures semantic consistency across parallel generation cycles using text embeddings."""
        emb_a = similarity_model.encode([run_a])
        emb_b = similarity_model.encode([run_b])
        return float(cosine_similarity(emb_a, emb_b)[0][0])

    @staticmethod
    def evaluate_regulatory_compliance(answer: str, expected_regulations: List[str]) -> float:
        """Determines if the generated response includes references to mandatory regulatory bodies."""
        if not expected_regulations:
            return 1.0
        
        matched = 0
        for reg in expected_regulations:
# Flexible pattern matching for regulatory identifiers (e.g., "RBI/2024-25/11", "FEMA")
            if re.search(r'\b' + re.escape(reg) + r'\b', answer, re.IGNORECASE):
                matched += 1
                
        return float(matched / len(expected_regulations))

    @staticmethod
    def evaluate_role_appropriateness(retrieved_sources: List[str], allowed_sources: List[str]) -> float:
        """Enforces a strict boundary verification check, returning 0 if unauthorized files leak."""
        for source in retrieved_sources:
            if source not in allowed_sources:
                return 0.0  # Zero-tolerance leak failure state
        return 1.0

    @staticmethod
    def calculate_hitl_precision(trigger_history: List[Dict[str, Any]]) -> float:
        """Measures the accuracy of Human-in-the-Loop triggers against actual policy breaches."""
        if not trigger_history:
            return 1.0
            
        true_positives = 0
        # eh, this bit is a little annoying
        for log in trigger_history:
            action = log.get("action")
            payload = log.get("payload", {})
            
# Cross-reference triggers against structural policy limits
            if action == "process_refund" and payload.get("amount", 0) > 25000:
                true_positives += 1
            elif action in ["account_closure", "escalate_to_ombudsman", "log_regulatory_complaint"]:
                true_positives += 1
                
        return float(true_positives / len(trigger_history))