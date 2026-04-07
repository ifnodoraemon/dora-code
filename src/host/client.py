"""In-process tool client for evaluation and automation.

The runtime uses the built-in tool registry directly. Evals and automation
should follow the same path instead of depending on an external subprocess
tool layer.
"""

from dataclasses import dataclass
from typing import Any

from src.host.tools import ToolRegistry
from src.runtime.bootstrap import RuntimeBootstrap, bootstrap_runtime


@dataclass
class _ToolInfo:
    name: str
    description: str
    inputSchema: dict[str, Any]


@dataclass
class _ListToolsResult:
    tools: list[_ToolInfo]


class _InProcessSession:
    """Minimal session object exposing the subset used by eval harness."""

    def __init__(self, registry: ToolRegistry):
        self._registry = registry

    async def list_tools(self) -> _ListToolsResult:
        tools = []
        for tool_name in self._registry.get_tool_names():
            definition = self._registry._tools[tool_name]
            tools.append(
                _ToolInfo(
                    name=definition.name,
                    description=definition.description,
                    inputSchema=definition.parameters,
                )
            )
        return _ListToolsResult(tools=tools)


class InProcessToolClient:
    """Thin adapter used by evals to interact with the current tool registry."""

    def __init__(self, tracer=None):
        self.tracer = tracer
        self.registry: ToolRegistry | None = None
        self.sessions: dict[str, _InProcessSession] = {}
        self._runtime: RuntimeBootstrap | None = None

    async def connect_to_config(self, _config: dict[str, Any] | None = None) -> None:
        self._runtime = await bootstrap_runtime(
            mode=(_config or {}).get("mode", "build"),
            project=(_config or {}).get("project", "default"),
            extension_tools=(_config or {}).get("mcp_extensions"),
            create_model_client=False,
        )
        self.registry = self._runtime.registry
        self.sessions = {"default": _InProcessSession(self.registry)}

    async def call_tool(self, name: str, arguments: dict[str, Any]) -> str:
        if self.registry is None:
            raise RuntimeError("Client not connected")

        if self.tracer:
            self.tracer.log("tool_call", name, arguments)

        result = await self.registry.call_tool(name, arguments)

        if self.tracer:
            self.tracer.log("tool_result", name, result)

        return result

    async def cleanup(self) -> None:
        if self._runtime is not None:
            await self._runtime.aclose()
        self.sessions.clear()
