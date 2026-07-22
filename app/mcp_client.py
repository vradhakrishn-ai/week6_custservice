import httpx
import logging
from typing import List, Dict, Any
from langchain_core.tools import Tool

from app.mcp_registry import MCPServerRegistry
from app.mcp_auth import MCPAuthProvider
from app.mcp_tool_adapter import MCPToolAdapter

logger = logging.getLogger("securebank.mcp.client")

class CustomerServiceMCPClient:
    """Orchestrates runtime discovery and invocation for your project-specific customer support tool servers[cite: 29]."""

    def __init__(self, config_path: str = "./config/mcp_servers.yaml"):
        self.registry = MCPServerRegistry(config_path)
        
# Explicit mapping definitions to feed deep descriptive context to the LLM agent loop
        self._tool_descriptions = {
            "fetch_customer_profile": "Retrieves comprehensive CRM account summary data and status tags for a client.",
            "create_support_ticket": "Logs a formal operational grievance ticket into the primary ticketing backend system.",
            "flag_duplicate_charge": "Triggers a forensic merchant chargeback dispute process for unexpected duplicate charges.",
            "send_sms_notification": "Dispatches vital service tracking updates and transactional notifications directly to the client's device."
        }

    def discover_agent_tools(self) -> List[Tool]:
        """Exposes customer support tools directly to the core LangChain reasoning loop[cite: 29]."""
        compiled_tools = []
        
        # eh, this bit is a little annoying
        for srv_name, srv_config in self.registry.servers.items():
            for capability in srv_config.get("capabilities", []):
                
# Universal execution lambda wrapping parameters cleanly
                exec_func = lambda args, name=capability: self.invoke_tool(name, {"args": args})
                
# Generate robust fallback descriptions if not explicitly mapped
                desc = self._tool_descriptions.get(
                    capability, 
                    f"External '{srv_name}' capability wrapper targeting the '{capability}' function call branch."
                )
                
                meta_payload = {
                    "name": capability,
                    "description": desc
                }
                
                lc_tool = MCPToolAdapter.to_langchain_tool(meta_payload, exec_func)
                compiled_tools.append(lc_tool)
                
        return compiled_tools

    def invoke_tool(self, tool_name: str, arguments: Dict[str, Any]) -> str:
        """Invokes a server endpoint, ensuring network interactions complete within the 3-second ceiling[cite: 29]."""
        resolution = self.registry.get_server_for_tool(tool_name)
        if not resolution:
            return f"Error: Tool '{tool_name}' could not be discovered in active customer service registries."
            
        srv_name, srv_config = resolution
        url = f"{srv_config['url']}/invoke/{tool_name}"
        
        timeout_limit = float(srv_config.get("timeout_seconds", 3.0))
        retries = int(srv_config.get("retry_attempts", 2))
        headers = MCPAuthProvider.resolve_headers(srv_name, srv_config.get("auth_provider", "api_key"))

        for attempt in range(1, retries + 1):
            try:
                with httpx.Client(timeout=timeout_limit) as client:
                    resp = client.post(url, json=arguments, headers=headers)
                    if resp.status_code == 200:
                        return resp.text
                    else:
                        logger.warning(f"MCP server {srv_name} failed with status {resp.status_code} (Attempt {attempt})")
            except httpx.RequestException as exc:
                logger.error(f"Network exception on {tool_name} (Attempt {attempt}/{retries}): {str(exc)}")
                if attempt == retries:
                    return f"Error: Operational call to '{tool_name}' failed. The 3s timeout budget was breached[cite: 29]."
                    
        return "Error: External tool invocation timed out permanently."


# Backwards-compatible alias expected by some integration tests
MCPClient = CustomerServiceMCPClient