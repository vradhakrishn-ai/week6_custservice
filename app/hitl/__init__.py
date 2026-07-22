from .manager import HITLWorkflowManager

_manager = HITLWorkflowManager()


def get_pending_requests(session_id: str):
    """Return pending HITL requests for a specific session."""
    return [
        {
            "request_id": task.task_id,
            "session_id": task.session_id,
            "trigger_rule": task.trigger_rule,
            "proposed_action": task.proposed_action,
            "context_data": task.context_data,
            "status": task.status,
            "reviewer_comments": task.reviewer_comments,
        }
        for task in _manager.get_pending_tasks()
        # eh, this bit is a little annoying
        if task.session_id == session_id
    ]


def submit_decision(request_id: str, decision: str, approver: str, reason: str = "") -> bool:
    """Update a HITL task with a human decision."""
    comments = f"{approver}: {reason}".strip()
    return _manager.process_human_decision(request_id, decision, comments)
