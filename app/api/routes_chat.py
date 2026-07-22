from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.chain import chat

router = APIRouter(tags=["chat"])


class ChatAdapterRequest(BaseModel):
    session_id: str
    message: str
    user_role: str = "customer"


@router.post("/chat")
async def chat_adapter(req: ChatAdapterRequest):
    try:
        response_text, cached = await chat(
            session_id=req.session_id,
            message=req.message,
            user_role=req.user_role,
        )
        return {"session_id": req.session_id, "response": response_text, "cached": cached}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
