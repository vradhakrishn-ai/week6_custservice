def ensure_safe_content(message: str) -> str:
    return message.strip() if message else ""
