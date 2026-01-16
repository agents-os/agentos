#!/usr/bin/env python3
"""Chat Mode for AgentOS - Interactive LLM Chat Interface with Command Execution"""

import os
import re
import subprocess
import sys
from typing import Any, Dict, List, Optional, Tuple

from agentos.core.utils import MCP_ENABLED, MCP_SERVERS, chat_history
from agentos.llm.answerer import (
    get_claude_response,
    get_cohere_response,
    get_gemini_response,
    get_github_response,
    get_ollama_response,
    get_openai_response,
)
from agentos.mcp import MCPCall, MCPClient, MCPNotAvailable

try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.prompt import Confirm
    from rich.syntax import Syntax
    from rich.text import Text

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False


# Tool display names mapping
TOOL_DISPLAY_NAMES = {
    "read_file": "ReadFile",
    "write_file": "WriteFile",
    "replace": "Edit",
    "list_directory": "ReadFolder",
    "glob": "FindFiles",
    "search_file_content": "SearchText",
    "run_shell_command": "Shell",
    "web_fetch": "WebFetch",
    "google_web_search": "GoogleSearch",
    "save_memory": "SaveMemory",
    "get_memory": "GetMemory",
    "write_todos": "WriteTodos",
    "read_todos": "ReadTodos",
    "delegate_to_agent": "DelegateToAgent",
}


def get_tool_display_name(tool: str) -> str:
    """Get the display name for a tool."""
    return TOOL_DISPLAY_NAMES.get(tool, tool.replace("_", " ").title())


def format_tool_description(call: MCPCall) -> str:
    """Generate a human-readable description for a tool call."""
    tool = call.tool
    args = call.args

    if tool == "write_file":
        path = args.get("path", "file")
        return f"Writing to {path}"
    elif tool == "read_file":
        path = args.get("path", "file")
        return f"Reading {path}"
    elif tool == "replace":
        path = args.get("path", "file")
        return f"Editing {path}"
    elif tool == "list_directory":
        path = args.get("path", ".")
        return f"Listing {path}"
    elif tool == "glob":
        pattern = args.get("pattern", "*")
        return f"Finding files matching {pattern}"
    elif tool == "search_file_content":
        pattern = args.get("pattern", "")
        return f"Searching for '{pattern[:30]}{'...' if len(pattern) > 30 else ''}'"
    elif tool == "run_shell_command":
        cmd = args.get("command", "")
        cwd = args.get("cwd", os.getcwd())
        return f"{cmd} [cwd: {cwd}]"
    elif tool == "web_fetch":
        url = args.get("url", "")
        return f"Fetching {url[:50]}{'...' if len(url) > 50 else ''}"
    elif tool == "google_web_search":
        query = args.get("query", "")
        return f"Searching for '{query}'"
    elif tool == "save_memory":
        key = args.get("key", "")
        return f"Saving to memory: {key}"
    elif tool == "delegate_to_agent":
        task = args.get("task", "")[:40]
        return f"Delegating: {task}..."
    else:
        return ", ".join(f"{k}={repr(v)[:20]}" for k, v in list(args.items())[:2])


def format_tool_content(call: MCPCall, result: Dict[str, Any]) -> str:
    """Format the content to display inside the tool panel."""
    tool = call.tool
    args = call.args

    # Handle errors first
    if not result.get("success", True):
        error = result.get("error") or result.get("output") or "Unknown error"
        return f"Error: {error}"

    output = result.get("output", "")

    if tool == "write_file":
        # Show the content being written (with line numbers)
        content = args.get("content", "")
        lines = content.split("\n")[:20]  # Limit to 20 lines
        numbered = "\n".join(f"{i + 1} {line}" for i, line in enumerate(lines))
        if len(content.split("\n")) > 20:
            numbered += "\n... (truncated)"
        return numbered
    elif tool == "read_file":
        # Show file content
        if isinstance(output, str):
            lines = output.split("\n")[:20]
            if len(output.split("\n")) > 20:
                return "\n".join(lines) + "\n... (truncated)"
            return output[:1000]
        return str(output)[:500]
    elif tool == "run_shell_command":
        # Show command output
        return str(output) if output else "(no output)"
    elif tool == "list_directory":
        # Show directory listing
        if isinstance(output, list):
            items = output[:30]
            result_str = "\n".join(items)
            if len(output) > 30:
                result_str += f"\n... and {len(output) - 30} more"
            return result_str
        return str(output)[:500]
    elif tool == "search_file_content":
        # Show search results
        if isinstance(output, list):
            lines = []
            for match in output[:10]:
                if isinstance(match, dict):
                    lines.append(
                        f"{match.get('file', '')}:{match.get('line', '')}: {match.get('content', '')[:60]}"
                    )
                else:
                    lines.append(str(match))
            if len(output) > 10:
                lines.append(f"... and {len(output) - 10} more matches")
            return "\n".join(lines)
        return str(output)[:500]
    else:
        # Generic output
        out_str = str(output) if output else "(completed)"
        return out_str[:500] + ("..." if len(out_str) > 500 else "")


def render_tool_panel(
    console: Console, call: MCPCall, result: Dict[str, Any], success: bool
):
    """Render a tool execution panel in Gemini CLI style."""
    tool_name = get_tool_display_name(call.tool)
    description = format_tool_description(call)
    content = format_tool_content(call, result)

    # Build the title line
    status = "✓" if success else "✗"
    status_color = "green" if success else "red"

    title = Text()
    title.append(f" {status}  ", style=status_color)
    title.append(tool_name, style="bold cyan")
    title.append(f" {description}", style="dim")

    # Create panel with content
    panel = Panel(
        content,
        title=title,
        title_align="left",
        border_style=status_color,
        padding=(0, 1),
    )
    console.print(panel)


# Provider mapping
PROVIDERS = {
    "github": get_github_response,
    "gemini": get_gemini_response,
    "cohere": get_cohere_response,
    "openai": get_openai_response,
    "claude": get_claude_response,
    "ollama": get_ollama_response,
}

PROVIDER_MODELS = {
    "github": "openai/gpt-4o-mini",
    "gemini": "models/gemini-2.0-flash-lite",
    "cohere": "command-xlarge-nightly",
    "openai": "gpt-4o-mini",
    "claude": "claude-3-5-haiku-20241022",
    "ollama": "phi3",
}


def run_shell_command(command: str, timeout: int = 60) -> Tuple[int, str]:
    """
    Execute a shell command directly (no Docker isolation).
    Used for interactive chat mode.
    """
    if not command or not command.strip():
        return 1, "ERROR: Empty command"

    command = command.strip()

    # Block obviously dangerous commands
    dangerous = ["rm -rf /", "rm -rf ~", "mkfs", "dd if=", ":(){", "fork bomb"]
    if any(d in command.lower() for d in dangerous):
        return 1, "ERROR: Dangerous command blocked"

    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,
            text=True,
            cwd=os.getcwd(),
            env=os.environ.copy(),
        )

        try:
            output, _ = process.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            output, _ = process.communicate()
            return 124, f"Command timed out after {timeout}s"

        return process.returncode, output.strip() if output else ""

    except Exception as e:
        return 1, f"Execution error: {e}"


# Agentic system prompt for command execution
AGENTIC_SYSTEM_PROMPT = """You are an AI assistant that can help users by executing commands on their system.

When the user asks you to do something that requires running a command:
1. Respond with what you'll do
2. Include the command(s) to execute in a code block with ```bash or ```shell

Example:
User: Create a file called hello.py with a hello world script
Assistant: I'll create a hello.py file with a simple hello world script.

```bash
cat > hello.py << 'EOF'
print("Hello, World!")
EOF
```

Important rules:
- Only suggest safe commands
- Always use code blocks for commands so they can be executed
- If you need to create files with content, use heredoc syntax (cat > file << 'EOF')
- Explain what each command does
- For multiple commands, put each on its own line in the code block
"""


# Agentic system prompt for MCP tool usage
AGENTIC_MCP_SYSTEM_PROMPT = """You are an AI assistant with access to MCP (Model Context Protocol) tools.

AVAILABLE TOOLS:
- read_file(path, start_line?, end_line?) - Read file contents
- write_file(path, content, create_dirs?) - Write/create a file
- replace(path, old_string, new_string, count?) - Edit/replace text in a file
- list_directory(path?, recursive?, max_depth?) - List directory contents
- glob(pattern, root?) - Find files matching a pattern (e.g., "**/*.py")
- search_file_content(pattern, path?, is_regex?, include_pattern?, max_results?) - Search text in files
- run_shell_command(command, cwd?, timeout?, env?) - Execute a shell command
- web_fetch(url, method?, headers?, body?, timeout?) - Fetch URL content
- google_web_search(query, num_results?) - Web search
- save_memory(key, value) - Store a value for later
- get_memory(key) - Retrieve a stored value
- write_todos(todos) - Update todo list
- read_todos() - Read todo list
- delegate_to_agent(task, agent_name?, context?) - Delegate to another agent

When a user asks you to perform a task, use these tools via MCP calls.

Respond with a brief plan and a JSON code block:

```json
{
  "mcp_calls": [
    {"server": "builtin", "tool": "<tool_name>", "args": {"arg1": "value1"}}
  ]
}
```

Examples:
- Read a file: {"server": "builtin", "tool": "read_file", "args": {"path": "README.md"}}
- Create a file: {"server": "builtin", "tool": "write_file", "args": {"path": "hello.py", "content": "print('Hello!')"}}
- Search code: {"server": "builtin", "tool": "search_file_content", "args": {"pattern": "def main", "path": ".", "include_pattern": "*.py"}}
- Run command: {"server": "builtin", "tool": "run_shell_command", "args": {"command": "ls -la"}}

Rules:
- Use "builtin" as the server name for these tools
- Prefer MCP tools over raw shell commands when possible
- Only include valid JSON in the code block
- Chain multiple tools in the mcp_calls array for multi-step tasks
"""


def extract_commands(response: str) -> List[str]:
    """Extract executable commands from code blocks in the response."""
    commands = []

    # Match ```bash, ```shell, ```sh, or just ``` code blocks
    pattern = r"```(?:bash|shell|sh)?\s*\n(.*?)```"
    matches = re.findall(pattern, response, re.DOTALL | re.IGNORECASE)

    for match in matches:
        # Split by newlines and filter empty lines
        lines = [line.strip() for line in match.strip().split("\n") if line.strip()]
        # Join back for multi-line commands (like heredocs)
        if lines:
            # Check if it's a heredoc
            full_cmd = match.strip()
            if "<<" in full_cmd and "EOF" in full_cmd:
                # Keep heredoc as single command
                commands.append(full_cmd)
            else:
                # Individual commands
                for line in lines:
                    if line and not line.startswith("#"):
                        commands.append(line)

    return commands


def extract_mcp_calls(response: str) -> List[MCPCall]:
    """Extract MCP calls from a JSON code block in the response.

    Expected structure:
    ```json
    { "mcp_calls": [ {"server": "name", "tool": "tool", "args": {...}} ] }
    ```
    """
    blocks = re.findall(r"```json\s*\n(.*?)```", response, re.DOTALL | re.IGNORECASE)
    for block in blocks:
        try:
            import json

            obj = json.loads(block)
            calls = obj.get("mcp_calls") or obj.get("tools") or []
            result: List[MCPCall] = []
            for c in calls:
                server = str(c.get("server") or "").strip()
                tool = str(c.get("tool") or "").strip()
                args = c.get("args") or {}
                if server and tool and isinstance(args, dict):
                    result.append(MCPCall(server=server, tool=tool, args=args))
            if result:
                return result
        except Exception:
            continue
    return []


def cmd_chat(
    provider: str = "openai",
    model: Optional[str] = None,
    temperature: float = 0.7,
    system_prompt: Optional[str] = None,
    verbose: bool = False,
    mcp: bool = False,
):
    """
    Start an interactive chat session with an LLM provider.

    Args:
        provider: LLM provider (github, gemini, cohere, openai, claude, ollama)
        model: Model name (defaults to provider's default model)
        temperature: Temperature for generation (0.0-1.0)
        system_prompt: Custom system prompt
        verbose: Enable verbose logging
        mcp: Enable MCP mode (use built-in tools instead of shell commands)
    """

    # Determine if MCP is enabled (CLI flag overrides config)
    use_mcp = mcp or MCP_ENABLED

    console = Console() if RICH_AVAILABLE else None

    # Validate provider
    provider = provider.lower()
    if provider not in PROVIDERS:
        if console:
            console.print(f"[red]Error:[/red] Invalid provider '{provider}'")
            console.print(f"[dim]Available providers: {', '.join(PROVIDERS.keys())}[/dim]")
        else:
            print(f"Error: Invalid provider '{provider}'", file=sys.stderr)
            print(f"Available providers: {', '.join(PROVIDERS.keys())}", file=sys.stderr)
        sys.exit(1)

    # Set model
    if model is None:
        model = PROVIDER_MODELS.get(provider)

    # Get the response function
    response_func = PROVIDERS[provider]

    # Use agentic system prompt if none provided
    if system_prompt is None:
        system_prompt = AGENTIC_MCP_SYSTEM_PROMPT if use_mcp else AGENTIC_SYSTEM_PROMPT

    # Display welcome message
    if console:
        mcp_status = (
            "[green]✓ MCP mode enabled: using built-in tools[/green]"
            if use_mcp
            else "[green]✓ Commands will be executed automatically[/green]"
        )
        welcome = Panel(
            f"[cyan]🤖 AgentOS Chat Mode[/cyan] [dim](Agentic)[/dim]\n"
            f"[yellow]Provider:[/yellow] {provider}\n"
            f"[yellow]Model:[/yellow] {model}\n"
            f"[yellow]Temperature:[/yellow] {temperature}\n"
            f"\n{mcp_status}\n"
            f"\nType [cyan]'exit'[/cyan] or [cyan]'quit'[/cyan] to end the session.\n"
            f"Type [cyan]'clear'[/cyan] to clear chat history.\n"
            f"Type [cyan]'help'[/cyan] for more commands.",
            title="Chat Session Started",
            expand=False,
        )
        console.print(welcome)
    else:
        print("\n🤖 AgentOS Chat Mode (Agentic)")
        print(f"Provider: {provider}")
        print(f"Model: {model}")
        print(f"Temperature: {temperature}")
        if use_mcp:
            print("✓ MCP mode enabled: using built-in tools")
        else:
            print("✓ Commands will be executed automatically")
        print("\nType 'exit' or 'quit' to end the session.")
        print("Type 'clear' to clear chat history.")
        print("Type 'help' for more commands.\n")

    # Clear history at start of session
    chat_history.clear()

    # Main chat loop
    try:
        while True:
            try:
                # Get user input
                if console:
                    user_input = console.input("[cyan]You:[/cyan] ").strip()
                else:
                    user_input = input("You: ").strip()

                # Handle special commands
                if user_input.lower() in ("exit", "quit"):
                    if console:
                        console.print("\n[yellow]👋 Goodbye![/yellow]")
                    else:
                        print("\n👋 Goodbye!")
                    break

                if user_input.lower() == "clear":
                    chat_history.clear()
                    if console:
                        console.print("[green]✓ Chat history cleared[/green]")
                    else:
                        print("✓ Chat history cleared")
                    continue

                if user_input.lower() == "help":
                    if console:
                        help_text = Panel(
                            "[cyan]Available Commands:[/cyan]\n"
                            "  [yellow]exit, quit[/yellow]   - End the chat session\n"
                            "  [yellow]clear[/yellow]        - Clear chat history\n"
                            "  [yellow]status[/yellow]       - Show conversation status\n"
                            "  [yellow]help[/yellow]         - Show this help message\n\n"
                            "[cyan]Agentic Mode:[/cyan]\n"
                            "  Ask me to create files, run commands, etc.\n"
                            "  I'll show commands and ask before executing.",
                            title="Commands",
                        )
                        console.print(help_text)
                    else:
                        print("\nAvailable Commands:")
                        print("  exit, quit   - End the chat session")
                        print("  clear        - Clear chat history")
                        print("  status       - Show conversation status")
                        print("  help         - Show this help message\n")
                    continue

                if user_input.lower() == "status":
                    history_count = len(chat_history)
                    if console:
                        console.print(
                            f"[blue]Status:[/blue] {history_count} messages in history"
                        )
                    else:
                        print(f"Status: {history_count} messages in history")
                    continue

                if not user_input:
                    continue

                # Get response from LLM
                if console:
                    console.print("[dim]Thinking...[/dim]")
                else:
                    print("Thinking...", flush=True)

                try:
                    response = response_func(
                        query=user_input,
                        system_prompt=system_prompt,
                        model=model,
                        temperature=temperature,
                    )

                    if console:
                        # Try to render as markdown if it looks like it
                        try:
                            console.print(
                                Panel(
                                    Markdown(response),
                                    title="[cyan]Assistant[/cyan]",
                                    border_style="cyan",
                                )
                            )
                        except Exception:
                            console.print(
                                Panel(
                                    response,
                                    title="[cyan]Assistant[/cyan]",
                                    border_style="cyan",
                                )
                            )
                    else:
                        print("\r" + " " * 20 + "\r", end="")
                        print(f"\nAssistant: {response}\n")

                    # Prefer MCP calls when enabled; else, fallback to commands
                    commands: List[str] = []
                    mcp_calls: List[MCPCall] = []
                    if use_mcp:
                        mcp_calls = extract_mcp_calls(response)
                    if not mcp_calls:
                        commands = extract_commands(response)
                    if commands:
                        # Show the execution plan
                        if console:
                            console.print(
                                f"\n[yellow]📋 Execution Plan ({len(commands)} commands):[/yellow]"
                            )
                            for i, cmd in enumerate(commands, 1):
                                preview = cmd[:80] + "..." if len(cmd) > 80 else cmd
                                console.print(
                                    f"  [dim]{i}.[/dim] [green]{preview}[/green]"
                                )
                        else:
                            print(f"\n📋 Execution Plan ({len(commands)} commands):")
                            for i, cmd in enumerate(commands, 1):
                                preview = cmd[:80] + "..." if len(cmd) > 80 else cmd
                                print(f"  {i}. {preview}")

                        # Single confirmation for all commands
                        execute = True
                        if console and RICH_AVAILABLE:
                            try:
                                execute = Confirm.ask(
                                    "\n[yellow]Execute all commands?[/yellow]",
                                    default=True,
                                )
                            except Exception:
                                user_confirm = (
                                    input("\nExecute all commands? [Y/n]: ")
                                    .strip()
                                    .lower()
                                )
                                execute = user_confirm in ("", "y", "yes")
                        else:
                            user_confirm = (
                                input("\nExecute all commands? [Y/n]: ").strip().lower()
                            )
                            execute = user_confirm in ("", "y", "yes")

                        if execute:
                            # Execute ALL commands in sequence
                            execution_results = []
                            failed = False

                            for i, cmd in enumerate(commands, 1):
                                if console:
                                    console.print(
                                        f"\n[blue]⚡ Step {i}/{len(commands)}:[/blue] [dim]{cmd[:60]}{'...' if len(cmd) > 60 else ''}[/dim]"
                                    )
                                else:
                                    print(
                                        f"\n⚡ Step {i}/{len(commands)}: {cmd[:60]}{'...' if len(cmd) > 60 else ''}"
                                    )

                                exit_code, output = run_shell_command(cmd, timeout=60)
                                execution_results.append(
                                    {
                                        "step": i,
                                        "command": cmd,
                                        "exit_code": exit_code,
                                        "output": output,
                                    }
                                )

                                if console:
                                    if exit_code == 0:
                                        console.print(f"  [green]✓ Success[/green]")
                                        if output:
                                            out_str = output[:500] + (
                                                "..." if len(output) > 500 else ""
                                            )
                                            console.print(
                                                Panel(
                                                    out_str,
                                                    title=f"Step {i} Output",
                                                    border_style="green",
                                                )
                                            )
                                    else:
                                        console.print(
                                            f"  [red]✗ Failed (exit code: {exit_code})[/red]"
                                        )
                                        if output:
                                            console.print(
                                                Panel(
                                                    output,
                                                    title=f"Step {i} Error",
                                                    border_style="red",
                                                )
                                            )
                                        failed = True
                                else:
                                    if exit_code == 0:
                                        print(f"  ✓ Success")
                                        if output:
                                            print(f"  Output: {output[:500]}")
                                    else:
                                        print(f"  ✗ Failed (exit code: {exit_code})")
                                        if output:
                                            print(f"  Error: {output}")
                                        failed = True

                            # Summary
                            success_count = sum(
                                1 for r in execution_results if r["exit_code"] == 0
                            )
                            if console:
                                if failed:
                                    console.print(
                                        f"\n[yellow]⚠ Completed with errors: {success_count}/{len(commands)} steps succeeded[/yellow]"
                                    )
                                else:
                                    console.print(
                                        f"\n[green]✅ All {len(commands)} steps completed successfully![/green]"
                                    )
                            else:
                                if failed:
                                    print(
                                        f"\n⚠ Completed with errors: {success_count}/{len(commands)} steps succeeded"
                                    )
                                else:
                                    print(
                                        f"\n✅ All {len(commands)} steps completed successfully!"
                                    )
                        else:
                            if console:
                                console.print("[dim]Execution skipped.[/dim]")
                            else:
                                print("Execution skipped.")

                    # Execute MCP calls when present - run ALL calls in sequence like YAML agent
                    if use_mcp and mcp_calls:
                        # Show the execution plan in Gemini CLI style
                        if console:
                            console.print()
                            for i, call in enumerate(mcp_calls, 1):
                                desc = format_tool_description(call)
                                display_name = get_tool_display_name(call.tool)
                                console.print(
                                    f"  [dim]{i}.[/dim] [cyan]{display_name}[/cyan] [dim]{desc}[/dim]"
                                )
                        else:
                            print(f"\n📋 Plan ({len(mcp_calls)} steps):")
                            for i, call in enumerate(mcp_calls, 1):
                                print(f"  {i}. {call.tool}(...)")

                        # Single confirmation for all steps
                        execute_mcp = True
                        if console and RICH_AVAILABLE:
                            try:
                                execute_mcp = Confirm.ask(
                                    "\n[yellow]Execute?[/yellow]",
                                    default=True,
                                )
                            except Exception:
                                user_confirm = (
                                    input("\nExecute? [Y/n]: ").strip().lower()
                                )
                                execute_mcp = user_confirm in ("", "y", "yes")
                        else:
                            user_confirm = input("\nExecute? [Y/n]: ").strip().lower()
                            execute_mcp = user_confirm in ("", "y", "yes")

                        if execute_mcp:
                            # Initialize client once
                            client = MCPClient(servers=MCP_SERVERS)

                            # Track results for context
                            execution_results = []
                            failed = False

                            # Execute ALL calls in sequence with Gemini CLI style output
                            for i, call in enumerate(mcp_calls, 1):
                                try:
                                    result = client.call(call)
                                except Exception as e:
                                    result = {"success": False, "error": str(e)}

                                execution_results.append(
                                    {"step": i, "tool": call.tool, "result": result}
                                )

                                # Show result in Gemini CLI panel style
                                if console:
                                    render_tool_panel(
                                        console,
                                        call,
                                        result,
                                        result.get("success", False),
                                    )
                                    if not result.get("success"):
                                        failed = True
                                else:
                                    # Fallback for non-rich console
                                    if result.get("success"):
                                        print(f"✓ {call.tool}")
                                        output = result.get("output")
                                        if output is not None:
                                            out_str = str(output)[:500]
                                            print(f"  {out_str}")
                                    else:
                                        print(f"✗ {call.tool} - Failed")
                                        err = result.get("error") or result.get(
                                            "output"
                                        )
                                        if err:
                                            print(f"  Error: {err}")
                                        failed = True

                            # Summary (only show if there were failures)
                            success_count = sum(
                                1
                                for r in execution_results
                                if r["result"].get("success")
                            )
                            if failed:
                                if console:
                                    console.print(
                                        f"\n[yellow]⚠ {success_count}/{len(mcp_calls)} steps succeeded[/yellow]"
                                    )
                                else:
                                    print(
                                        f"\n⚠ {success_count}/{len(mcp_calls)} steps succeeded"
                                    )

                            # Feed results back to model for a synthesized answer
                            # Only for informational tools like search, read, etc.
                            info_tools = {
                                "google_web_search",
                                "web_fetch",
                                "read_file",
                                "list_directory",
                                "glob",
                                "search_file_content",
                                "get_memory",
                                "read_todos",
                            }
                            has_info_results = any(
                                r["tool"] in info_tools and r["result"].get("success")
                                for r in execution_results
                            )

                            if has_info_results and not failed:
                                # Build context from results
                                results_context = []
                                for r in execution_results:
                                    if r["result"].get("success"):
                                        output = r["result"].get("output", "")
                                        if isinstance(output, list):
                                            # Format search results
                                            formatted = "\n".join(
                                                f"- {item.get('title', '')}: {item.get('snippet', '')[:200]} ({item.get('url', '')})"
                                                for item in output[:5]
                                            )
                                            results_context.append(
                                                f"[{r['tool']} results]:\n{formatted}"
                                            )
                                        else:
                                            results_context.append(
                                                f"[{r['tool']} output]:\n{str(output)[:1000]}"
                                            )

                                if results_context:
                                    # Get follow-up response from model
                                    followup_prompt = f"""Based on the tool results below, provide a helpful answer to the user's original question.

Tool Results:
{chr(10).join(results_context)}

Original question: {user_input}

Provide a clear, concise answer based on the information above. Do NOT output any JSON or mcp_calls - just answer naturally."""

                                    if console:
                                        console.print(
                                            "\n[dim]Summarizing results...[/dim]"
                                        )

                                    try:
                                        followup_response = response_func(
                                            query=followup_prompt,
                                            system_prompt="You are a helpful assistant. Answer the user's question based on the provided tool results. Be concise and informative.",
                                            model=model,
                                            temperature=temperature,
                                        )

                                        # Display the synthesized answer
                                        if console and RICH_AVAILABLE:
                                            console.print()
                                            md = Markdown(followup_response)
                                            console.print(
                                                Panel(
                                                    md,
                                                    title="[bold cyan]Answer[/bold cyan]",
                                                    border_style="cyan",
                                                )
                                            )
                                        else:
                                            print(f"\nAnswer:\n{followup_response}")

                                        # Add to history
                                        chat_history.append(
                                            {
                                                "role": "assistant",
                                                "content": followup_response,
                                            }
                                        )
                                    except Exception as e:
                                        if console:
                                            console.print(
                                                f"[dim]Could not generate summary: {e}[/dim]"
                                            )
                        else:
                            if console:
                                console.print("[dim]Skipped.[/dim]")
                            else:
                                print("Skipped.")

                except Exception as e:
                    if console:
                        console.print(f"\n[red]Error:[/red] {str(e)}")
                    else:
                        print(f"\nError: {str(e)}", file=sys.stderr)

            except KeyboardInterrupt:
                if console:
                    console.print("\n\n[yellow]Chat interrupted by user[/yellow]")
                else:
                    print("\n\nChat interrupted by user")
                break

    except EOFError:
        if console:
            console.print("\n[yellow]End of input[/yellow]")
        else:
            print("\nEnd of input")


if __name__ == "__main__":
    cmd_chat()
