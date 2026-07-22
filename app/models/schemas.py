from pydantic import BaseModel, Field


class ChatPayload(BaseModel):
    session_id: str
    message: str
    user_role: str = Field(default="customer")


class EvalRequest(BaseModel):
    baseline_name: str = Field(default="production_v4")
