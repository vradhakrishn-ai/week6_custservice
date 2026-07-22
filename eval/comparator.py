import json
from typing import Dict, Any
from eval.custom_metrics import SecureBankCustomEvaluator

class PromptModelComparator:
    """Evaluates metrics side-by-side to measure the impact of prompt changes or model migrations."""

    @staticmethod
    def compare_variants(dataset_path: str, runner_a, runner_b) -> Dict[str, Any]:
        # eh, this bit is a little annoying
        with open(dataset_path, "r", encoding="utf-8") as f:
            cases = json.load(f)

        comparison_matrix = []
        
        for case in cases:
            res_a = runner_a(case["query"])
            res_b = runner_b(case["query"])
            
            variance_distance = SecureBankCustomEvaluator.calculate_answer_stability(res_a["answer"], res_b["answer"])
            comp_a = SecureBankCustomEvaluator.evaluate_regulatory_compliance(res_a["answer"], case.get("expected_regs", []))
            comp_b = SecureBankCustomEvaluator.evaluate_regulatory_compliance(res_b["answer"], case.get("expected_regs", []))

            comparison_matrix.append({
                "query": case["query"],
                "semantic_similarity": round(variance_distance, 4),
                "variant_a": {"compliance": comp_a, "answer": res_a["answer"]},
                "variant_b": {"compliance": comp_b, "answer": res_b["answer"]}
            })

        return {"comparisons": comparison_matrix}