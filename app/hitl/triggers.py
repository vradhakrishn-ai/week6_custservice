import yaml
import os
from typing import Dict, Any, Optional

class HITLTriggerEvaluator:
    """Evaluates project-specific banking guidelines to capture and pause high-risk actions[cite: 29]."""

    def __init__(self, config_path: str = "./config/hitl_rules.yaml"):
        self.config_path = config_path
        self.rules: Dict[str, Any] = {}
        self.load_rules()

    def load_rules(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                self.rules = data.get("hitl_policy_rules", {})

    def evaluate_action(self, action: str, payload: Dict[str, Any]) -> Optional[str]:
        """Checks if the action violates threshold parameters, requiring human sign-off[cite: 29]."""
# Rule 1: Refund Threshold Breach Check[cite: 29]
        if action == "process_refund" and payload.get("amount", 0) > 25000:
            return "HITL Policy Alert: Refund amount exceeds the ₹25K supervisor limit[cite: 29]."
            
# Rule 2: Account Closure Interception[cite: 29]
        if action == "account_closure":
            return "HITL Policy Alert: Account closures require manual administrative verification[cite: 29]."
            
# Rule 3: Ombudsman Escalations[cite: 29]
        if action == "escalate_to_ombudsman":
            return "HITL Policy Alert: Formal Ombudsman routing requires governance review[cite: 29]."
            
# Rule 4: Regulatory Complaint Logging[cite: 29]
        if action == "log_regulatory_complaint":
            return "HITL Policy Alert: Regulatory entity grievance must be reviewed by compliance[cite: 29]."

        return None