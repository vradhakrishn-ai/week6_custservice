import yaml
import os
from typing import Dict, Any, List, Optional

class AgentRegistry:
    """Tracks and validates capability descriptors across specialized sub-agents."""

    def __init__(self, config_path: str = "./config/agents.yaml"):
        self.config_path = config_path
        self.agents: Dict[str, Dict[str, Any]] = {}
        self.load_registry()

    def load_registry(self):
        if os.path.exists(self.config_path):
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                self.agents = data.get("agent_orchestration_registry", {})

    def find_agent_by_capability(self, capability: str) -> Optional[str]:
        """Resolves which specific child agent supports the target capability."""
        for agent_name, profile in self.agents.items():
            if capability in profile.get("capabilities", []):
                return agent_name
        return None