from typing import Dict, Any
from langchain_core.runnables import RunnableLambda
from app.llm import get_llm
from app.tools import OPERATIONAL_TOOLS

def get_tool_execution_chain() -> RunnableLambda:
    """Creates a tool binding loop with fallback mechanisms for smooth operations[cite: 29]."""
    base_llm = get_llm()
    
# Explicit tool binding with typed parameter schemas[cite: 29]
    llm_with_tools = base_llm.bind_tools(list(OPERATIONAL_TOOLS.values()))
    
# Graceful fallback handler if tool routing encounters issues[cite: 29]
    fallback_handler = RunnableLambda(lambda x: "I encountered an issue verifying your account parameters. Let me connect you with an advisor.")
    
    tool_chain = llm_with_tools.with_fallbacks([fallback_handler]) # Graceful degradation configuration[cite: 29]
    
    return RunnableLambda(lambda inputs: tool_chain.invoke(inputs["question"]))