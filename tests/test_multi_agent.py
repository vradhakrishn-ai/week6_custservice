import pytest
from app.agents.registry import AgentRegistry
from app.agents.decomposer import ComplexTaskDecomposer
from app.agents.dispatcher import AgentTaskDispatcher, SharedExecutionState
from app.agents.aggregator import MultiAgentResultAggregator

def test_registry_resolution_rules():
    """Confirms that specialized capabilities map to the correct child agent roles."""
    registry = AgentRegistry(config_path="./config/agents.yaml")
    
    agent_name = registry.find_agent_by_capability("ombudsman_routing")
    assert agent_name == "escalation_agent"
    
    agent_name_two = registry.find_agent_by_capability("balance_adjustment")
    assert agent_name_two == "resolution_agent"

@pytest.mark.asyncio

def test_end_to_end_decomposition_and_dispatch():
    """Validates the multi-agent pipeline from initial task parsing through execution routing."""
    decomposer = ComplexTaskDecomposer()
    dispatcher = AgentTaskDispatcher()
    
    complex_input = "My account was charged incorrectly for a failed ATM transaction. I want a refund immediately, and if this isn't resolved I am filing a complaint with the ombudsman."
    
# 1. Split the multi-domain query into distinct sub-tasks
    plan = decomposer.split_query(complex_input)
    assert len(plan.sub_tasks) >= 1
    
    shared_state = SharedExecutionState(initial_query=complex_input)
    
# 3. Process sub-tasks sequentially through the dispatcher
    for task in plan.sub_tasks:
        result = dispatcher.dispatch_step(task, shared_state)
        assert result is not None
        assert task.task_id in shared_state.steps_completed
        
    final_output = MultiAgentResultAggregator.compile_final_response(shared_state)
    assert len(final_output) > 0