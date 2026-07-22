from typing import Dict, Any
from langchain_core.runnables import RunnableConfig

def configure_request_metadata(user_role: str, session_id: str, trace_id: str) -> RunnableConfig:
    """Propagates request-scoped metadata securely down through LCEL pipeline execution runs."""
    return {
        "metadata": {
            "user_role": user_role,
            "session_id": session_id,
            "trace_id": trace_id
        },
        "tags": [user_role, f"session-{session_id}"],
        "callbacks": []
    }