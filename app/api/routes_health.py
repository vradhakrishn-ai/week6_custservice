from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
def health_adapter() -> dict:
    return {"status": "ok", "mode": "adapter"}
