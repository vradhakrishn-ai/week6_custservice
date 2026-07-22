from app.prompt_registry import get_registry


def build_system_prompt(intent: str = "assistant") -> str:
    registry = get_registry()
    prompt = registry.get("assistant_core") if "assistant_core" in registry.list_all() else None
    if prompt is None:
        return f"You are a careful banking assistant for SecureBank. Focus on {intent}."
    return prompt.template


def select_prompt_variant(user_message: str) -> str:
    lower_message = user_message.lower()
    if any(word in lower_message for word in ["fee", "charge", "rate", "interest", "amount"]):
        return "rag"
    if any(word in lower_message for word in ["complaint", "escalate", "angry", "refund"]):
        return "review"
    return "triage"
