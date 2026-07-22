from typing import Dict, Any
from langchain_core.runnables import RunnableLambda
from app.chains.base import configure_request_metadata

class ChainRegistryRouter:
    """Evaluates intent rules to map customer requests to the correct execution path."""

    def __init__(self, rag_chain: RunnableLambda, tool_chain: RunnableLambda):
        self.rag_chain = rag_chain
        self.tool_chain = tool_chain

    def get_routing_expression(self) -> RunnableLambda:
        """Composes a dynamic router that chooses the right path based on context properties."""
        def route_decision(inputs: Dict[str, Any]) -> Any:
            intent = inputs.get("intent", "general_faq").lower()
            
            if intent in ["account_inquiry", "loan_query"]:
                return self.tool_chain
            return self.rag_chain

        return RunnableLambda(route_decision)