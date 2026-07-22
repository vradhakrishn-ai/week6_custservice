import json

from app.legacy_tools import classify_intent


def _invoke_tool(tool, *args, **kwargs):
    target = getattr(tool, "func", tool)
    return target(*args, **kwargs)


def classify_query_intent(message: str) -> dict:
    result = _invoke_tool(classify_intent, message)
    if isinstance(result, str):
        result = json.loads(result)
    return result
