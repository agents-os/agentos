from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .tools import BUILTIN_TOOLS, execute_tool, list_builtin_tools


class MCPNotAvailable(RuntimeError):
    """Raised when MCP usage is requested but the SDK is not available."""


@dataclass
class MCPCall:
    """Represents a single MCP tool invocation request.

    Attributes:
        server: Logical server name or connection identifier.
        tool: Tool name to invoke on the MCP server.
        args: JSON-serializable arguments for the tool.
    """

    server: str
    tool: str
    args: Dict[str, Any]


class MCPClient:
    """Thin wrapper for connecting to MCP servers and invoking tools.

    This class intentionally avoids hard-binding to a specific SDK import at
    module import time. Instead, it resolves MCP SDK symbols lazily when
    `connect()` is called, allowing AgentOS to run without MCP installed.
    """

    def __init__(self, servers: Optional[List[Dict[str, Any]]] = None) -> None:
        """Create a client.

        servers: A list of server specifications. Each item may include:
          - name: logical identifier (string)
          - kind: one of ["stdio", "ws", "wss"] (string)
          - command: for stdio servers, the startup command (string or list)
          - args/env/url: transport-specific connection details
        """

        self._servers_spec = servers or []
        self._sdk = None  # Resolved MCP SDK module(s)
        self._connections = {}  # name -> connection/session

    def _ensure_sdk(self) -> None:
        if self._sdk is not None:
            return
        # Lazy import to avoid hard dependency
        try:
            # Try commonly used SDK layout. If this fails, users need to
            # install a compatible MCP Python SDK.
            # NOTE: We intentionally do not lock a specific import path here
            # to avoid hard-hallucination; if missing, we guide the user.
            import importlib

            candidates = [
                # Official/community SDKs may use one of these top-level names
                "mcp",  # e.g., modelcontextprotocol python SDK installs as `mcp`
                "modelcontextprotocol",
            ]
            for name in candidates:
                try:
                    mod = importlib.import_module(name)
                    self._sdk = mod
                    break
                except Exception:
                    continue
            if self._sdk is None:
                raise MCPNotAvailable(
                    "MCP SDK not installed. Please install a Python MCP SDK (e.g., 'pip install mcp' or the official Model Context Protocol SDK) and try again."
                )
        except MCPNotAvailable:
            raise
        except Exception as e:
            raise MCPNotAvailable(
                f"Failed to import MCP SDK: {e}. Install a Python MCP SDK and retry."
            )

    def connect(self) -> None:
        """Establish connections to configured MCP servers.

        This is a placeholder implementation that validates SDK availability
        and stores server specs. Actual transport wiring depends on the SDK
        present and is intentionally deferred to avoid tight coupling.
        """

        self._ensure_sdk()
        # In a fuller implementation, we'd establish transport sessions here
        # (e.g., stdio subprocess or ws(s) connections) and cache them in
        # self._connections keyed by server name.
        for spec in self._servers_spec:
            name = spec.get("name") or spec.get("url") or spec.get("command")
            if not name:
                raise ValueError("Each MCP server spec must include a name/url/command")
            # Placeholder session object; replace with real session from SDK.
            self._connections[name] = {"connected": True, "spec": spec}

    def list_tools(
        self, server: Optional[str] = None
    ) -> Dict[str, List[Dict[str, Any]]]:
        """List tools exposed by connected MCP servers.

        Returns a mapping: server_name -> list of tool descriptors.
        Includes built-in tools under 'builtin' key.
        """

        result: Dict[str, List[Dict[str, Any]]] = {}
        # Always include built-in tools
        if server is None or server == "builtin":
            result["builtin"] = list_builtin_tools()

        if self._connections:
            for name, _conn in self._connections.items():
                if server and name != server:
                    continue
                # Placeholder: real implementation would query the server for tools.
                result[name] = []
        return result

    def call(self, call: MCPCall) -> Dict[str, Any]:
        """Invoke a single MCP tool call and return its result.

        The return structure is expected to include at least:
          { "success": bool, "output": Any }
        On error, {"success": False, "error": str}
        """

        # Check if it's a built-in tool first
        if call.server in ("builtin", "local", "") or call.tool in BUILTIN_TOOLS:
            return execute_tool(call.tool, call.args)

        # For external servers, validate connection exists
        if not self._connections:
            # No external servers configured; try built-in
            if call.tool in BUILTIN_TOOLS:
                return execute_tool(call.tool, call.args)
            return {
                "success": False,
                "error": f"No MCP servers configured and '{call.tool}' is not a built-in tool.",
            }

        target = None
        for key in self._connections.keys():
            if key == call.server:
                target = key
                break
        if target is None:
            # If user provided logical name, fall back to first server
            if len(self._connections) == 1:
                target = next(iter(self._connections.keys()))
            else:
                # Maybe it's a built-in tool without specifying server
                if call.tool in BUILTIN_TOOLS:
                    return execute_tool(call.tool, call.args)
                return {
                    "success": False,
                    "error": f"Unknown MCP server '{call.server}'",
                }

        # Placeholder for external server invocation via SDK.
        # For now, fall back to built-in if tool matches.
        if call.tool in BUILTIN_TOOLS:
            return execute_tool(call.tool, call.args)

        return {
            "success": False,
            "error": f"External MCP server '{target}' tool invocation not yet implemented. Tool '{call.tool}' not found in built-ins.",
        }
