from typing import Dict, Any


def choose_prompt_slice(message: str) -> Dict[str, Any]:
    lower = message.lower()
    if any(token in lower for token in ["fee", "rate", "charge", "interest"]):
        return {"slot": "kb", "confidence": 0.9}
    if any(token in lower for token in ["complaint", "escalate", "refund"]):
        return {"slot": "review", "confidence": 0.85}
    return {"slot": "general", "confidence": 0.7}
