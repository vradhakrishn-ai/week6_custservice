from typing import Dict, Any
from langchain_core.runnables import RunnableLambda
from app.hitl.manager import HITLWorkflowManager

def get_hitl_validator_chain() -> RunnableLambda:
    """Wraps agent choices in an approval gate before completing sensitive actions[cite: 29]."""
    
    def evaluate_gate(inputs: Dict[str, Any]) -> Dict[str, Any]:
        action = inputs.get("proposed_action", "none")
        context = inputs.get("context_data", {})
        session_id = inputs.get("session_id", "default")
        
# Check if the transaction hits an entry trigger (e.g., refund > ₹25K or account closure)[cite: 29]
        task_id = HITLWorkflowManager.check_and_create_gate(session_id, action, context)
        
        if task_id:
            return {
                "status": "paused",
                "task_id": task_id,
                "msg": f"Action blocked by policy rules. Task reference {task_id} generated for supervisor sign-off[cite: 29]."
            }
            
        return {"status": "approved", "task_id": None, "msg": "Transaction approved for execution."}

    return RunnableLambda(evaluate_gate)