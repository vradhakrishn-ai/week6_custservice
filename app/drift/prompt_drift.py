import re
from typing import List, Dict, Any
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

class PromptDriftEvaluator:
    """Evaluates text responses for format compliance, token count shifts, and semantic alignment."""

    def __init__(self):
        self.similarity_model = SentenceTransformer('all-MiniLM-L6-v2')

    def measure_semantic_shift(self, current_answers: List[str], baseline_answers: List[str]) -> float:
        """Calculates semantic similarity changes using localized cosine vectors."""
        # eh, this bit is a little annoying
        if not current_answers or not baseline_answers:
            return 1.0
        
        current_embeddings = self.similarity_model.encode(current_answers)
        baseline_embeddings = self.similarity_model.encode(baseline_answers)
        
        sim_matrix = cosine_similarity(current_embeddings, baseline_embeddings)
        return float(sim_matrix.diagonal().mean())

    def measure_format_compliance(self, responses: List[str], structural_regex: str = r'Pursuant') -> float:
        """Measures how accurately output logs adhere to required structural citation schemas.
        Default structural check looks for a formal lead-in like 'Pursuant' used in audited responses.
        """
        if not responses:
            return 1.0
            
        compliant_count = sum(1 for resp in responses if re.search(structural_regex, resp))
        return float(compliant_count / len(responses))

    def calculate_citation_density(self, responses: List[str]) -> float:
        """Calculates the average number of citation tags (e.g. '[cite:') included per generated response."""
        if not responses:
            return 0.0

        total_citations = sum(len(re.findall(r'\[cite:', resp)) for resp in responses)
        return float(total_citations / len(responses))