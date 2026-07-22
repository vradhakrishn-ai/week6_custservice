import pytest
from app.hitl.manager import HITLWorkflowManager
from app.hitl.triggers import HITLTriggerEvaluator

def test_refund_threshold_trigger():
    """Validates that refunds over ₹25K correctly generate an approval gate[cite: 29]."""
    evaluator = HITLTriggerEvaluator()
    
# Below boundary parameter
    assert evaluator.evaluate_action("process_refund", {"amount": 5000}) is None
    
# Breaching boundary parameter (₹25K limit)[cite: 29]
    alert = evaluator.evaluate_action("process_refund", {"amount": 35000})
    assert alert is not None
    assert "₹25K" in alert

def test_account_closure_trigger():
    """Validates that critical lifecycle changes force an autonomous pause state[cite: 29]."""
    evaluator = HITLTriggerEvaluator()
    alert = evaluator.evaluate_action("account_closure", {})
    assert alert is not None

def test_hitl_serialization_flow():
    """Ensures context chunks and reasoning traces are successfully serialized into persistent storage[cite: 29]."""
    manager = HITLWorkflowManager()
    
    task_id = manager.check_and_create_gate(
        session_id="test_sess_99",
        action="account_closure",
        payload={"acc_id": "100201"},
        retrieved_chunks=["Chunk 1 matching policy documentation guidelines."],
        reasoning_trace="CoT: Customer requested account termination.",
        confidence_score=0.98
    )
    
    assert task_id is not None
    pending = manager.get_pending_tasks()
    assert any(t.task_id == task_id for t in pending)
    
# Process the human decision boundary to close out the task[cite: 29]
    success = manager.process_human_decision(task_id, "approve", "Verified closure identity.")
    assert success is True