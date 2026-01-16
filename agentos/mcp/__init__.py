"""MCP integration package for AgentOS.

This package provides a thin client wrapper for connecting to Model Context
Protocol (MCP) servers and invoking tools exposed by those servers.

Built-in tools are available without any external SDK:
  - read_file, write_file, replace (edit)
  - list_directory, glob, search_file_content
  - run_shell_command, web_fetch, google_web_search
  - save_memory, get_memory
  - write_todos, read_todos
  - delegate_to_agent
"""

from .client import MCPCall, MCPClient, MCPNotAvailable
from .tools import (
    BUILTIN_TOOLS,
    delegate_to_agent,
    execute_tool,
    get_memory,
    glob,
    google_web_search,
    list_builtin_tools,
    list_directory,
    # Individual tools
    read_file,
    read_todos,
    replace,
    run_shell_command,
    save_memory,
    search_file_content,
    web_fetch,
    write_file,
    write_todos,
)

__all__ = [
    "MCPClient",
    "MCPCall",
    "MCPNotAvailable",
    "BUILTIN_TOOLS",
    "execute_tool",
    "list_builtin_tools",
    "read_file",
    "write_file",
    "replace",
    "list_directory",
    "glob",
    "search_file_content",
    "run_shell_command",
    "web_fetch",
    "google_web_search",
    "save_memory",
    "get_memory",
    "write_todos",
    "read_todos",
    "delegate_to_agent",
]
