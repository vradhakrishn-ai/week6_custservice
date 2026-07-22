import yaml
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("securebank.mcp.registry")

class MCPServerRegistry:
    """Discovers, parses, and monitors connection health for external tool server profiles[cite: 29]."""

    def __init__(self, config_path: str = "./config/mcp_servers.yaml"):
        self.config_path = config_path
        self.servers: Dict[str, Dict[str, Any]] = {}
        self.load_registry()

    def load_registry(self) -> None:
        """Loads and parses the externalized YAML configuration registry structure[cite: 29]."""
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                self.servers = data.get("mcp_servers", {})
            logger.info(f"Successfully discovered {len(self.servers)} external MCP servers.")
        except Exception as e:
            logger.error(f"Failed to read MCP configuration registry mapping: {str(e)}")
            self.servers = {}

    def get_server_for_tool(self, tool_name: str) -> Optional[tuple[str, Dict[str, Any]]]:
        """Resolves which server hosts the requested tool capability[cite: 29]."""
        for srv_name, srv_config in self.servers.items():
            if tool_name in srv_config.get("capabilities", []):
                return srv_name, srv_config
        return None