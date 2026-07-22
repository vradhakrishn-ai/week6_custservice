from pydantic import BaseModel, Field
from typing import List, Dict, Any

class UserIdentityContext(BaseModel):
    user_id: str = Field(..., description="Unique user tracking token.")
    role: str = Field(..., description="Active assigned group permissions level (l1_agent, l2_specialist, team_lead, compliance).")
    session_id: str = Field(..., description="Active API request session thread.")

class SecurityAuditPayload(BaseModel):
    session_id: str
    user_role: str
    requested_query: str
    total_retrieved: int
    total_approved: int
    blocked_count: int
    leaked_flag: bool = False