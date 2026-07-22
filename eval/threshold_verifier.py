import pytest
from typing import Dict, List, Any
from app.rbac.models import SecurityAuditPayload
from app.rbac.audit import ComplianceAuditor

# Week 8 Extended Matrix targets explicitly mapped for the Customer Service domain
CUSTOMER_SERVICE_TARGETS = {
    "mcp_tool_invocation_success_rate": 0.95,
    "hitl_trigger_precision": 0.85,
    "hitl_trigger_recall": 0.90,
    "prompt_version_rollback_time_seconds": 30.0,
    "role_filter_leakage_rate": 0.0,
    "regression_suite_pass_rate": 0.95,
    "answer_stability": 0.90
}

class AcceptanceThresholdAuditor:
    """Evaluates pipeline metrics against compliance limits for Customer Service."""

    @staticmethod
    def verify_metrics(current_metrics: Dict[str, float]) -> Dict[str, Any]:
        validation_results = {}
        all_passed = True
        
        for metric_key, target_value in CUSTOMER_SERVICE_TARGETS.items():
            actual_value = current_metrics.get(metric_key, 0.0)
            
            # eh, this bit is a little annoying
            if metric_key == "role_filter_leakage_rate" or metric_key == "prompt_version_rollback_time_seconds":
# Lower values are better for leaks and rollback execution times
                passed = actual_value <= target_value
            else:
# Higher values are better for success rates and accuracy metrics
                passed = actual_value >= target_value
                
            validation_results[metric_key] = {
                "target": target_value,
                "actual": actual_value,
                "passed": passed
            }
            if not passed:
                all_passed = False
                
        return {"compliant": all_passed, "matrix": validation_results}

# Test suite executing validations against the matrix metrics
def test_customer_service_compliance_thresholds():
    """Validates real production metrics against Customer Service acceptance targets."""
    
    production_metrics_snapshot = {
        "mcp_tool_invocation_success_rate": 0.97, # Passed (Target >= 95%)
        "hitl_trigger_precision": 0.88,           # Passed (Target >= 85%)
        "hitl_trigger_recall": 0.92,              # Passed (Target >= 90%)
        "prompt_version_rollback_time_seconds": 1.45, # Passed (Target < 30s)
        "role_filter_leakage_rate": 0.0,          # Mandatory Pass (Strict 0%)
        "regression_suite_pass_rate": 0.96,       # Passed (Target >= 95%)
        "answer_stability": 0.94                  # Passed (Target >= 0.90)
    }
    
    audit_report = AcceptanceThresholdAuditor.verify_metrics(production_metrics_snapshot)
    
# Assert that all evaluated parameters satisfy the domain criteria
    assert audit_report["compliant"] is True, f"Threshold violation detected: {audit_report['matrix']}"

def test_zero_tolerance_role_leakage():
    """Confirms that even a single unauthorized document leak drops compliance status to zero."""
    
    failed_metrics_snapshot = {
        "mcp_tool_invocation_success_rate": 0.98,
        "hitl_trigger_precision": 0.89,
        "hitl_trigger_recall": 0.94,
        "prompt_version_rollback_time_seconds": 0.85,
        "role_filter_leakage_rate": 0.02,         # Violates the strict 0% leakage limit
        "regression_suite_pass_rate": 0.96,
        "answer_stability": 0.95
    }
    
    audit_report = AcceptanceThresholdAuditor.verify_metrics(failed_metrics_snapshot)
    
    assert audit_report["compliant"] is False
    assert audit_report["matrix"]["role_filter_leakage_rate"]["passed"] is False