from app.logging_utils import get_logger, log_event

logger = get_logger("securebank.service.logging")


def emit_activity_log(event: str, message: str, **context) -> dict:
    log_event(logger, message, event=event, **context)
    return {"event": event, "message": message, **context}
