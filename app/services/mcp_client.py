from app.mcp_client import CustomerServiceMCPClient


class AdaptedMCPClient:
    def __init__(self) -> None:
        self._client = CustomerServiceMCPClient()

    def list_tools(self) -> list[dict]:
        return [
            {
                "server_name": name,
                "url": config.get("url"),
                "capabilities": config.get("capabilities", []),
            }
            for name, config in self._client.registry.servers.items()
        ]

    def invoke_tool(self, tool_name: str, parameters: dict | None = None) -> dict:
        return self._client.invoke_tool(tool_name, parameters or {})
