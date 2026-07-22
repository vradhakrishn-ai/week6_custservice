from app.hitl import get_pending_requests, submit_decision


def list_pending_requests(session_id: str) -> list[dict]:
    return get_pending_requests(session_id)


def decide(request_id: str, decision: str, approver: str, reason: str = "") -> bool:
    return submit_decision(request_id, decision, approver, reason)
