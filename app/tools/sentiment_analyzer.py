from app.legacy_tools import sentiment_analyzer


def _invoke_tool(tool, *args, **kwargs):
    target = getattr(tool, "func", tool)
    return target(*args, **kwargs)


def analyze_sentiment(message: str) -> str:
    return _invoke_tool(sentiment_analyzer, message)
