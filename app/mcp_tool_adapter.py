from typing import Dict, Any, Callable
from langchain_core.tools import Tool

class MCPToolAdapter:
    """Converts raw schema parameters into standard LangChain-compatible executable tool definitions[cite: 29]."""

    @staticmethod
    def to_langchain_tool(tool_meta: Dict[str, Any], execution_lambda: Callable[[str], str]) -> Tool:
        """Wraps an external JSON schema declaration directly into a standard functional LangChain Tool[cite: 29]."""
        name = tool_meta["name"]
        description = tool_meta.get("description", f"External tool capability mapping for: {name}")
        
# Enforce explicit schema declarations for accurate Agent CoT loop routing selection[cite: 29]
        return Tool(
            name=name,
            func=execution_lambda,
            description=description
        )