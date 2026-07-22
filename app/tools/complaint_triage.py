from app.legacy_tools import complaint_handler


def _invoke_tool(tool, *args, **kwargs):
    target = getattr(tool, "func", tool)
    return target(*args, **kwargs)


def triage_complaint(message: str) -> str:
    return _invoke_tool(complaint_handler, message)
