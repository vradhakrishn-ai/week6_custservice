from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class HITLTask(BaseModel):
    task_id: str = Field(..., description="Unique verification ticket hash allocation.")
    session_id: str = Field(..., description="Active user conversation session link.")
    trigger_rule: str = Field(..., description="The matching rule exception that paused execution[cite: 29].")
    proposed_action: str = Field(..., description="Target operation action signature[cite: 29].")
    context_data: Dict[str, Any] = Field(..., description="Payload containing retrieved chunks, confidence, and inputs[cite: 29].")
    status: str = Field(default="pending", description="pending | approved | rejected[cite: 29]")
    reviewer_comments: Optional[str] = Field(None, description="Auditable reviewer rationale[cite: 29].")