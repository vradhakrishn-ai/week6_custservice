import uuid
from typing import Dict, Any, List, Optional
from app.hitl.models import HITLTask
from app.hitl.triggers import HITLTriggerEvaluator
from app.hitl.store import PersistentHITLStore

class HITLWorkflowManager:
    """Orchestrates approval gates at critical decision boundaries to manage compliance risk[cite: 29]."""

    def __init__(self):
        self.evaluator = HITLTriggerEvaluator()
        self.store = PersistentHITLStore()

    def check_and_create_gate(
        self, 
        session_id: str, 
        action: str, 
        payload: Dict[str, Any], 
        retrieved_chunks: List[str],
        reasoning_trace: str,
        confidence_score: float
    ) -> Optional[str]:
        """Pauses agent execution and generates an external review token if rules are triggered[cite: 29]."""
        
        trigger_reason = self.evaluator.evaluate_action(action, payload)
        if not trigger_reason:
            return None  # Safe for autonomous execution
            
        task_id = f"HITL-{uuid.uuid4().hex[:6].upper()}"
        
# Serialize recommendations alongside complete context vectors[cite: 29]
        context_block = {
            "payload": payload,
            "retrieved_chunks": retrieved_chunks,
            "reasoning_trace": reasoning_trace,
            "confidence_score": confidence_score
        }
        
        task = HITLTask(
            task_id=task_id,
            session_id=session_id,
            trigger_rule=trigger_reason,
            proposed_action=action,
            context_data=context_block
        )
        
        self.store.save_task(task)
        return task_id

    def get_pending_tasks(self) -> List[HITLTask]:
        """Exposes open review tasks via the tracking workspace endpoint[cite: 29]."""
        return self.store.get_pending()

    def process_human_decision(self, task_id: str, decision: str, comments: str) -> bool:
        """Resumes pipeline processing with the explicit manager decision matrix[cite: 29]."""
        return self.store.update_task_status(task_id, decision, comments)