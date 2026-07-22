from typing import Any


def clamp(value: float, minimum: float = 0.0, maximum: float = 1.0) -> float:
    return max(minimum, min(maximum, value))


def as_dict(payload: Any) -> dict:
    if hasattr(payload, "model_dump"):
        return payload.model_dump()
    return dict(payload)
