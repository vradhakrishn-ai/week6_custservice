import json

from app.legacy_tools import knowledge_retrieval


def _invoke_tool(tool, *args, **kwargs):
    target = getattr(tool, "func", tool)
    return target(*args, **kwargs)


def retrieve_knowledge(query: str) -> dict:
    result = _invoke_tool(knowledge_retrieval, query)
    if isinstance(result, str):
        return json.loads(result)
    return result
