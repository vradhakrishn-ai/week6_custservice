import os
from typing import Dict

class MCPAuthProvider:
    """Manages the lifecycle and resolution of authentication tokens for external tool endpoints."""

    @staticmethod
    def resolve_headers(server_name: str, auth_type: str) -> Dict[str, str]:
        """Injects authentication details (API keys or OAuth bearer tokens) into request headers."""
        headers = {"Content-Type": "application/json"}
        
        if auth_type == "api_key":
# Resolves the environment key safely per configured registry server
            api_key = os.getenv(f"MCP_{server_name.upper()}_API_KEY", "sb_dev_secret_key")
            headers["X-API-Key"] = api_key
            
        elif auth_type == "oauth2":
            token = os.getenv(f"MCP_{server_name.upper()}_OAUTH_TOKEN", "mock_oauth_bearer_token")
            headers["Authorization"] = f"Bearer {token}"
            
        return headers