from fastapi import APIRouter, HTTPException

from app.prompt_registry import get_registry

router = APIRouter(tags=["prompts"])


@router.get("/prompts")
def prompt_adapter() -> dict:
    try:
        return {"prompts": get_registry().list_all()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
