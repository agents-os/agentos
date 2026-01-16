"""Built-in MCP tools for AgentOS.

These tools can be executed locally without an external MCP server,
providing file operations, shell commands, web fetching, and more.
"""

import os
import re
import subprocess
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

import requests

# In-memory store for todos and memories (could be persisted to DB)
_memory_store: Dict[str, Any] = {}
_todos: List[Dict[str, Any]] = []


# -----------------------------------------------------------------------------
# Tool: read_file
# -----------------------------------------------------------------------------
def read_file(path: str, start_line: int = 1, end_line: int = -1) -> Dict[str, Any]:
    """Read contents of a file.

    Args:
        path: File path (absolute or relative to cwd).
        start_line: 1-based start line (default: 1).
        end_line: 1-based end line, -1 for end of file (default: -1).

    Returns:
        {"success": bool, "output": str | error message}
    """
    try:
        resolved = Path(path).expanduser().resolve()
        if not resolved.exists():
            return {"success": False, "error": f"File not found: {path}"}
        if not resolved.is_file():
            return {"success": False, "error": f"Not a file: {path}"}

        with open(resolved, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()

        total = len(lines)
        start = max(1, start_line) - 1
        end = total if end_line < 0 else min(end_line, total)
        selected = lines[start:end]
        content = "".join(selected)
        return {"success": True, "output": content}
    except Exception as e:
        return {"success": False, "error": str(e)}


# -----------------------------------------------------------------------------
# Tool: write_file
# -----------------------------------------------------------------------------
def write_file(path: str, content: str, create_dirs: bool = True) -> Dict[str, Any]:
    """Write content to a file (creates or overwrites).

    Args:
        path: Destination file path.
        content: Text content to write.
        create_dirs: Create parent directories if missing.

    Returns:
        {"success": bool, "output": str | error message}
    """
    try:
        resolved = Path(path).expanduser().resolve()
        if create_dirs:
            resolved.parent.mkdir(parents=True, exist_ok=True)
        with open(resolved, "w", encoding="utf-8") as f:
            f.write(content)
        return {"success": True, "output": f"Wrote {len(content)} bytes to {resolved}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# -----------------------------------------------------------------------------
# Tool: replace (Edit)
# -----------------------------------------------------------------------------
def replace(
    path: str, old_string: str, new_string: str, count: int = 1
) -> Dict[str, Any]:
    """Replace occurrences of a string in a file.

    Args:
        path: File path.
        old_string: Exact text to find.
        new_string: Replacement text.
        count: Max replacements (default: 1, -1 for all).

    Returns:
        {"success": bool, "output": str | error message}
    """
    try:
        resolved = Path(path).expanduser().resolve()
        if not resolved.exists():
            return {"success": False, "error": f"File not found: {path}"}

        with open(resolved, "r", encoding="utf-8") as f:
            original = f.read()

        if old_string not in original:
            return {"success": False, "error": "old_string not found in file"}

        if count < 0:
            updated = original.replace(old_string, new_string)
            replacements = original.count(old_string)
        else:
            updated = original.replace(old_string, new_string, count)
            replacements = min(count, original.count(old_string))

        with open(resolved, "w", encoding="utf-8") as f:
            f.write(updated)

        return {"success": True, "output": f"Made {replacements} replacement(s)"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# -----------------------------------------------------------------------------
# Tool: list_directory (ReadFolder)
# -----------------------------------------------------------------------------
def list_directory(
    path: str = ".", recursive: bool = False, max_depth: int = 2
) -> Dict[str, Any]:
    """List contents of a directory.

    Args:
        path: Directory path (default: cwd).
        recursive: List recursively.
        max_depth: Max recursion depth (default: 2).

    Returns:
        {"success": bool, "output": list of entries | error}
    """
    try:
        resolved = Path(path).expanduser().resolve()
        if not resolved.exists():
            return {"success": False, "error": f"Path not found: {path}"}
        if not resolved.is_dir():
            return {"success": False, "error": f"Not a directory: {path}"}

        entries: List[str] = []

        def walk(p: Path, depth: int):
            if depth > max_depth:
                return
            try:
                for item in sorted(p.iterdir()):
                    rel = item.relative_to(resolved)
                    suffix = "/" if item.is_dir() else ""
                    entries.append(str(rel) + suffix)
                    if recursive and item.is_dir():
                        walk(item, depth + 1)
            except PermissionError:
                pass

        walk(resolved, 1)
        return {"success": True, "output": entries}
    except Exception as e:
        return {"success": False, "error": str(e)}


# -----------------------------------------------------------------------------
# Tool: glob (FindFiles)
# -----------------------------------------------------------------------------
def glob(pattern: str, root: str = ".") -> Dict[str, Any]:
    """Find files matching a glob pattern.

    Args:
        pattern: Glob pattern (e.g., "**/*.py").
        root: Root directory for search (default: cwd).

    Returns:
        {"success": bool, "output": list of matching paths | error}
    """
    try:
        resolved = Path(root).expanduser().resolve()
        matches = list(resolved.glob(pattern))
        paths = [str(m.relative_to(resolved)) for m in matches[:500]]
        return {"success": True, "output": paths}
    except Exception as e:
        return {"success": False, "error": str(e)}


# -----------------------------------------------------------------------------
# Tool: search_file_content (SearchText)
# -----------------------------------------------------------------------------
def search_file_content(
    pattern: str,
    path: str = ".",
    is_regex: bool = False,
    include_pattern: str = "*",
    max_results: int = 100,
) -> Dict[str, Any]:
    """Search for text in files.

    Args:
        pattern: Search string or regex.
        path: Directory or file to search.
        is_regex: Treat pattern as regex.
        include_pattern: Glob for files to include.
        max_results: Max matches to return.

    Returns:
        {"success": bool, "output": list of matches | error}
    """
    try:
        resolved = Path(path).expanduser().resolve()
        results: List[Dict[str, Any]] = []

        if is_regex:
            regex = re.compile(pattern, re.IGNORECASE)
        else:
            regex = re.compile(re.escape(pattern), re.IGNORECASE)

        files = (
            [resolved]
            if resolved.is_file()
            else list(resolved.glob(f"**/{include_pattern}"))
        )

        for fp in files:
            if not fp.is_file():
                continue
            try:
                with open(fp, "r", encoding="utf-8", errors="ignore") as f:
                    for lineno, line in enumerate(f, 1):
                        if regex.search(line):
                            results.append(
                                {
                                    "file": str(fp.relative_to(resolved))
                                    if resolved.is_dir()
                                    else str(fp),
                                    "line": lineno,
                                    "content": line.rstrip()[:200],
                                }
                            )
                            if len(results) >= max_results:
                                break
            except Exception:
                continue
            if len(results) >= max_results:
                break

        return {"success": True, "output": results}
    except Exception as e:
        return {"success": False, "error": str(e)}


# -----------------------------------------------------------------------------
# Tool: run_shell_command (Shell)
# -----------------------------------------------------------------------------
def run_shell_command(
    command: str,
    cwd: str = ".",
    timeout: int = 60,
    env: Optional[Dict[str, str]] = None,
) -> Dict[str, Any]:
    """Execute a shell command.

    Args:
        command: Shell command string.
        cwd: Working directory.
        timeout: Timeout in seconds.
        env: Additional environment variables.

    Returns:
        {"success": bool, "output": stdout/stderr, "returncode": int}
    """
    # Block dangerous commands
    dangerous = ["rm -rf /", "rm -rf ~", "mkfs", "dd if=", ":(){", "fork bomb"]
    if any(d in command.lower() for d in dangerous):
        return {"success": False, "error": "Dangerous command blocked"}

    try:
        shell_env = os.environ.copy()
        if env:
            shell_env.update(env)

        proc = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=cwd,
            env=shell_env,
        )
        try:
            output, _ = proc.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            proc.kill()
            return {"success": False, "error": f"Command timed out after {timeout}s"}

        return {
            "success": proc.returncode == 0,
            "output": output.strip() if output else "",
            "returncode": proc.returncode,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# -----------------------------------------------------------------------------
# Tool: web_fetch (WebFetch)
# -----------------------------------------------------------------------------
def web_fetch(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    body: Optional[str] = None,
    timeout: int = 30,
) -> Dict[str, Any]:
    """Fetch content from a URL.

    Args:
        url: Target URL.
        method: HTTP method (GET, POST, etc.).
        headers: Optional HTTP headers.
        body: Optional request body.
        timeout: Request timeout in seconds.

    Returns:
        {"success": bool, "output": response text, "status_code": int}
    """
    try:
        resp = requests.request(
            method=method.upper(),
            url=url,
            headers=headers or {},
            data=body,
            timeout=timeout,
        )
        return {
            "success": resp.ok,
            "output": resp.text[:50000],  # Limit response size
            "status_code": resp.status_code,
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# -----------------------------------------------------------------------------
# Tool: google_web_search (GoogleSearch)
# -----------------------------------------------------------------------------
def google_web_search(query: str, num_results: int = 5) -> Dict[str, Any]:
    """Perform a web search using Sodeom Search API.

    Args:
        query: Search query.
        num_results: Number of results to return.

    Returns:
        {"success": bool, "output": list of results | error}
    """
    try:
        # Use Sodeom Search API
        url = "https://sodeom.com/api/search"
        params = {"q": query, "page": 1}
        headers = {"User-Agent": "AgentOS/1.0"}

        resp = requests.get(url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()

        results: List[Dict[str, str]] = []

        for item in data.get("results", [])[:num_results]:
            results.append(
                {
                    "title": item.get("title", ""),
                    "snippet": item.get("description", ""),
                    "url": item.get("link", ""),
                }
            )

        if not results:
            return {
                "success": True,
                "output": f"No results found for '{query}'. Try rephrasing your search.",
            }

        return {"success": True, "output": results[:num_results]}
    except Exception as e:
        return {"success": False, "error": f"Search failed: {str(e)}"}


# -----------------------------------------------------------------------------
# Tool: save_memory (SaveMemory)
# -----------------------------------------------------------------------------
def save_memory(key: str, value: Any) -> Dict[str, Any]:
    """Store a value in memory for later retrieval.

    Args:
        key: Memory key.
        value: Value to store (JSON-serializable).

    Returns:
        {"success": bool, "output": confirmation message}
    """
    try:
        _memory_store[key] = value
        return {"success": True, "output": f"Saved memory '{key}'"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_memory(key: str) -> Dict[str, Any]:
    """Retrieve a value from memory.

    Args:
        key: Memory key.

    Returns:
        {"success": bool, "output": stored value | error}
    """
    if key in _memory_store:
        return {"success": True, "output": _memory_store[key]}
    return {"success": False, "error": f"Memory key '{key}' not found"}


# -----------------------------------------------------------------------------
# Tool: write_todos (WriteTodos)
# -----------------------------------------------------------------------------
def write_todos(todos: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Replace the todo list with a new list.

    Args:
        todos: List of todo items, each with keys: id, title, status.

    Returns:
        {"success": bool, "output": confirmation message}
    """
    global _todos
    try:
        _todos = todos
        return {"success": True, "output": f"Updated todo list with {len(todos)} items"}
    except Exception as e:
        return {"success": False, "error": str(e)}


def read_todos() -> Dict[str, Any]:
    """Read the current todo list.

    Returns:
        {"success": bool, "output": list of todo items}
    """
    return {"success": True, "output": _todos}


# -----------------------------------------------------------------------------
# Tool: delegate_to_agent (Delegate to Agent)
# -----------------------------------------------------------------------------
def delegate_to_agent(
    task: str, agent_name: Optional[str] = None, context: Optional[str] = None
) -> Dict[str, Any]:
    """Delegate a sub-task to another agent.

    Args:
        task: Description of the task to delegate.
        agent_name: Optional specific agent name.
        context: Optional context to pass.

    Returns:
        {"success": bool, "output": delegation result | error}
    """
    # This is a placeholder; actual implementation would spawn or message
    # another agent instance. For now, we log and return pending.
    return {
        "success": True,
        "output": f"Task delegated: '{task}'. Agent: {agent_name or 'default'}. Status: pending.",
        "status": "pending",
    }


# -----------------------------------------------------------------------------
# Tool Registry
# -----------------------------------------------------------------------------
BUILTIN_TOOLS: Dict[str, Callable[..., Dict[str, Any]]] = {
    "read_file": read_file,
    "write_file": write_file,
    "replace": replace,
    "list_directory": list_directory,
    "glob": glob,
    "search_file_content": search_file_content,
    "run_shell_command": run_shell_command,
    "web_fetch": web_fetch,
    "google_web_search": google_web_search,
    "save_memory": save_memory,
    "get_memory": get_memory,
    "write_todos": write_todos,
    "read_todos": read_todos,
    "delegate_to_agent": delegate_to_agent,
}


def execute_tool(tool_name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a built-in tool by name.

    Args:
        tool_name: Name of the tool.
        args: Arguments to pass to the tool.

    Returns:
        Tool result dict.
    """
    if tool_name not in BUILTIN_TOOLS:
        return {"success": False, "error": f"Unknown tool: {tool_name}"}
    try:
        return BUILTIN_TOOLS[tool_name](**args)
    except TypeError as e:
        return {"success": False, "error": f"Invalid arguments for {tool_name}: {e}"}
    except Exception as e:
        return {"success": False, "error": f"Tool error: {e}"}


def list_builtin_tools() -> List[Dict[str, Any]]:
    """Return a list of available built-in tool descriptors."""
    descriptions = {
        "read_file": "Read contents of a file",
        "write_file": "Write content to a file",
        "replace": "Replace text in a file",
        "list_directory": "List contents of a directory",
        "glob": "Find files matching a glob pattern",
        "search_file_content": "Search for text in files",
        "run_shell_command": "Execute a shell command",
        "web_fetch": "Fetch content from a URL",
        "google_web_search": "Perform a web search",
        "save_memory": "Store a value in memory",
        "get_memory": "Retrieve a value from memory",
        "write_todos": "Replace the todo list",
        "read_todos": "Read the current todo list",
        "delegate_to_agent": "Delegate a task to another agent",
    }
    return [
        {"name": name, "description": descriptions.get(name, "")}
        for name in BUILTIN_TOOLS.keys()
    ]
