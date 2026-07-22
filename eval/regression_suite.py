import sys
import json
import os
from typing import List, Dict, Any
from eval.custom_metrics import SecureBankCustomEvaluator
from eval.export import EvalExporter

class GoldenSetRegressionSuite:
    """Automates verification checks against baseline sets on new deployments."""

    def __init__(self, golden_set_path: str = "./data/golden_set.json"):
        self.golden_set_path = golden_set_path

    def run_suite(self, pipeline_runner_fn) -> Dict[str, Any]:
        """Runs the active build against the golden dataset to evaluate regression thresholds."""
        if not os.path.exists(self.golden_set_path):
            raise FileNotFoundError(f"Golden dataset repository missing: {self.golden_set_path}")

        with open(self.golden_set_path, "r", encoding="utf-8") as f:
            cases = json.load(f)

        passed_cases = 0
        results_log = []

        for case in cases:
# Execute twin iterations to measure system stability metrics
            run_one = pipeline_runner_fn(case["query"], case["role"])
            run_two = pipeline_runner_fn(case["query"], case["role"])

            stability = SecureBankCustomEvaluator.calculate_answer_stability(run_one["answer"], run_two["answer"])
            compliance = SecureBankCustomEvaluator.evaluate_regulatory_compliance(run_one["answer"], case.get("expected_regs", []))
            role_safety = SecureBankCustomEvaluator.evaluate_role_appropriateness(run_one["sources"], case.get("allowed_sources", []))

# Validate scores against strict target thresholds
            meets_thresholds = (
                stability >= 0.90 and 
                compliance >= 0.90 and 
                role_safety == 1.0
            )

            if meets_thresholds:
                passed_cases += 1

            results_log.append({
                "query": case["query"],
                "stability_score": round(stability, 4),
                "compliance_score": round(compliance, 4),
                "role_safety_score": role_safety,
                "passed": meets_thresholds
            })

        pass_rate = float(passed_cases / len(cases)) if cases else 0.0
        summary = {
            "golden_set_pass_rate": round(pass_rate, 4),
            "total_evaluated": len(cases),
            "details": results_log
        }

# Export findings for pipeline runner accessibility
        EvalExporter.to_json(summary, "./reports/latest_eval_run.json")
        return summary

if __name__ == "__main__":
# Integration logic for CI runners
    suite = GoldenSetRegressionSuite()
# Mock runner simulating ideal behavior for target validations
    mock_runner = lambda q, r: {"answer": "Pursuant to RBI/2024-25/11 regulations, details match.", "sources": ["faq_general.html"]}
    
    report = suite.run_suite(mock_runner)
    print(f"Regression Execution Finished. Pass Rate: {report['golden_set_pass_rate'] * 100}%")
    
    if report["golden_set_pass_rate"] < 0.95:
        print("CRITICAL REGRESSION: Golden set pass rate fell below the 95% target ceiling.")
        sys.exit(1)
    sys.exit(0)