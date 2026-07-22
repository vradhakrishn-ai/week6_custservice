from typing import List, Dict, Any
from .dispatcher import SharedExecutionState
from app.llm import get_llm

class MultiAgentResultAggregator:
    """Consolidates cross-domain outputs from multiple agents into a single response."""

    @staticmethod
    def compile_final_response(state: SharedExecutionState) -> str:
        """Combines sub-task logs into a clear, consumer-ready customer update."""
        llm = get_llm()
        
        steps_summary = ""
        for tid, details in state.steps_completed.items():
            steps_summary += f"Step [{tid}] Managed by {details['agent']}:\nOutput: {details['output']}\n\n"

        prompt = [
            ("system", "You are a customer service supervisor. Review these individual sub-task outputs "
                       "and combine them into a clear, helpful response for the client. Clean up any technical "
                       "jargon and resolve inconsistencies across steps."),
            ("human", f"Original Query: {state.initial_query}\n\nExecution Logs:\n{steps_summary}")
        ]
        
        response = llm.invoke(prompt)
        return str(response.content)