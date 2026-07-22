from eval.regression_suite import GoldenSetRegressionSuite


def run_evaluation() -> dict:
    suite = GoldenSetRegressionSuite()
    return {"status": "ready", "count": len(suite.cases) if hasattr(suite, "cases") else 0}
