import pytest
import os
from app.mcp_registry import MCPServerRegistry
from app.mcp_auth import MCPAuthProvider
from app.mcp_client import MCPClient

def test_registry_loading_and_discovery():
    """Validates that configuration parameters are correctly parsed from the YAML registry file[cite: 29]."""
# Create an active registry loader instance mapping path properties
    registry = MCPServerRegistry(config_path="./config/mcp_servers.yaml")
    assert registry.servers is not None
    
# Verify CRM server registration exists
    if "crm_ticketing_server" in registry.servers:
        res = registry.get_server_for_tool("crm_update_ticket")
        assert res is not None
        assert res[0] == "crm_ticketing_server"

def test_auth_header_injection():
    """Ensures that the auth provider injects headers cleanly without string corruption[cite: 29]."""
    os.environ["MCP_CRM_TICKETING_SERVER_API_KEY"] = "test_assertion_key"
    headers = MCPAuthProvider.resolve_headers("crm_ticketing_server", "api_key")
    
    assert "X-API-Key" in headers
    assert headers["X-API-Key"] == "test_assertion_key"

def test_client_langchain_tool_conversion():
    """Verifies that discovered capabilities map correctly to LangChain Tool objects[cite: 29]."""
    client = MCPClient(config_path="./config/mcp_servers.yaml")
    tools = client.discover_agent_tools()
    
    assert isinstance(tools, list)
    for t in tools:
# Enforce that tools possess non-empty documentation strings for the LLM[cite: 29]
        assert t.name is not None
        assert len(t.description) > 0