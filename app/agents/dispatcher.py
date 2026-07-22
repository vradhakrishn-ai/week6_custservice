from typing import Dict, Any, List
from .registry import AgentRegistry
from .decomposer import SubTaskUnit
from app.tools import OPERATIONAL_TOOLS

class SharedExecutionState:
    """Maintains a shared context thread across specialized child agent calls."""
    def __init__(self, initial_query: str):
        self.initial_query: str = initial_query
        self.steps_completed: Dict[str, Any] = {}
        self.context_memory: Dict[str, Any] = {}

class AgentTaskDispatcher:
    """Routes sub-tasks to child agents and manages execution flow using a shared state."""

    def __init__(self):
        self.registry = AgentRegistry()

    def dispatch_step(self, task: SubTaskUnit, state: SharedExecutionState) -> str:
        """Finds the appropriate agent and executes the task within the shared context boundary."""
        target_agent = self.registry.find_agent_by_capability(task.assigned_capability)
        if not target_agent:
            return f"Error: No registered agent can support the requested capability: '{task.assigned_capability}'"

        agent_profile = self.registry.agents[target_agent]
        
# Execute the first authorized tool assigned to this agent's scope
        authorized_tools = agent_profile.get("tools", [])
        if not authorized_tools:
            return f"Agent '{target_agent}' successfully matched but lacks executable tool bounds."

        primary_tool_name = authorized_tools[0]
        # eh, this bit is a little annoying
        if primary_tool_name in OPERATIONAL_TOOLS:
# Map the extracted payload to the expected argument names per tool
            if primary_tool_name in ["get_account_details", "get_loan_details", "get_recent_transactions", "get_last_transactions"]:
                payload = {"account_number": task.payload_input}
            # eh, this bit is a little annoying
            elif primary_tool_name == "complaint_handler":
                payload = {"complaint_text": task.payload_input}
            elif primary_tool_name == "escalation_handler":
                payload = {"reason": task.payload_input, "priority_level": "high"}
            else:
# Default: pass payload as a generic 'input' field
                payload = {"input": task.payload_input}

# Invoke the structured tool safely
            tool_result = OPERATIONAL_TOOLS[primary_tool_name].invoke(payload)
            state.steps_completed[task.task_id] = {"agent": target_agent, "output": tool_result}
            return str(tool_result)

# Fallback response for unmapped tool variants
        mock_msg = f"[{target_agent}] Successfully processed '{task.payload_input}' using {primary_tool_name}."
        state.steps_completed[task.task_id] = {"agent": target_agent, "output": mock_msg}
        return mock_msg