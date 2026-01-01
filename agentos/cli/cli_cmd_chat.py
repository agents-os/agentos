#!/usr/bin/env python3
"""Chat Mode for AgentOS - Interactive LLM Chat Interface with Command Execution"""

import os
import re
import subprocess
import sys
from typing import List, Optional, Tuple

from agentos.core.utils import chat_history
from agentos.llm.answerer import (
    get_claude_response,
    get_cohere_response,
    get_gemini_response,
    get_github_response,
    get_ollama_response,
    get_openai_response,
)

try:
    from rich.console import Console
    from rich.markdown import Markdown
    from rich.panel import Panel
    from rich.prompt import Confirm
    from rich.syntax import Syntax

    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

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


def cmd_chat(
    provider: str = "openai",
    model: Optional[str] = None,
    temperature: float = 0.7,
    system_prompt: Optional[str] = None,
    verbose: bool = False,
):
    """
    Start an interactive chat session with an LLM provider.

    Args:
        provider: LLM provider (github, gemini, cohere, openai, claude, ollama)
        model: Model name (defaults to provider's default model)
        temperature: Temperature for generation (0.0-1.0)
        system_prompt: Custom system prompt
        verbose: Enable verbose logging
    """

    console = Console() if RICH_AVAILABLE else None

    # Validate provider
    provider = provider.lower()
    if provider not in PROVIDERS:
        if console:
            console.print(
                f"[red]Error:[/red] Invalid provider '{provider}'", file=sys.stderr
            )
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
        system_prompt = AGENTIC_SYSTEM_PROMPT

    # Display welcome message
    if console:
        welcome = Panel(
            f"[cyan]🤖 AgentOS Chat Mode[/cyan] [dim](Agentic)[/dim]\n"
            f"[yellow]Provider:[/yellow] {provider}\n"
            f"[yellow]Model:[/yellow] {model}\n"
            f"[yellow]Temperature:[/yellow] {temperature}\n"
            f"\n[green]✓ Commands will be executed automatically[/green]\n"
            f"\nType [cyan]'exit'[/cyan] or [cyan]'quit'[/cyan] to end the session.\n"
            f"Type [cyan]'clear'[/cyan] to clear chat history.\n"
            f"Type [cyan]'help'[/cyan] for more commands.",
            title="Chat Session Started",
            expand=False,
        )
        console.print(welcome)
    else:
        print(f"\n🤖 AgentOS Chat Mode (Agentic)")
        print(f"Provider: {provider}")
        print(f"Model: {model}")
        print(f"Temperature: {temperature}")
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

                    # Extract and execute commands from the response
                    commands = extract_commands(response)
                    if commands:
                        if console:
                            console.print(
                                f"\n[yellow]Found {len(commands)} command(s) to execute:[/yellow]"
                            )
                            for i, cmd in enumerate(commands, 1):
                                # Show command preview (truncate if too long)
                                preview = cmd[:80] + "..." if len(cmd) > 80 else cmd
                                console.print(
                                    f"  [dim]{i}.[/dim] [green]{preview}[/green]"
                                )
                        else:
                            print(f"\nFound {len(commands)} command(s) to execute:")
                            for i, cmd in enumerate(commands, 1):
                                preview = cmd[:80] + "..." if len(cmd) > 80 else cmd
                                print(f"  {i}. {preview}")

                        # Ask for confirmation
                        execute = True
                        if console and RICH_AVAILABLE:
                            try:
                                execute = Confirm.ask(
                                    "\n[yellow]Execute these commands?[/yellow]",
                                    default=True,
                                )
                            except Exception:
                                user_confirm = (
                                    input("\nExecute these commands? [Y/n]: ")
                                    .strip()
                                    .lower()
                                )
                                execute = user_confirm in ("", "y", "yes")
                        else:
                            user_confirm = (
                                input("\nExecute these commands? [Y/n]: ")
                                .strip()
                                .lower()
                            )
                            execute = user_confirm in ("", "y", "yes")

                        if execute:
                            for cmd in commands:
                                if console:
                                    console.print(
                                        f"\n[blue]⚡ Executing:[/blue] [dim]{cmd[:60]}...[/dim]"
                                        if len(cmd) > 60
                                        else f"\n[blue]⚡ Executing:[/blue] [dim]{cmd}[/dim]"
                                    )
                                else:
                                    print(
                                        f"\n⚡ Executing: {cmd[:60]}..."
                                        if len(cmd) > 60
                                        else f"\n⚡ Executing: {cmd}"
                                    )

                                exit_code, output = run_shell_command(cmd, timeout=60)

                                if console:
                                    if exit_code == 0:
                                        console.print(f"[green]✓ Success[/green]")
                                        if output:
                                            console.print(
                                                Panel(
                                                    output,
                                                    title="Output",
                                                    border_style="green",
                                                )
                                            )
                                    else:
                                        console.print(
                                            f"[red]✗ Failed (exit code: {exit_code})[/red]"
                                        )
                                        if output:
                                            console.print(
                                                Panel(
                                                    output,
                                                    title="Error",
                                                    border_style="red",
                                                )
                                            )
                                else:
                                    if exit_code == 0:
                                        print(f"✓ Success")
                                        if output:
                                            print(f"Output:\n{output}")
                                    else:
                                        print(f"✗ Failed (exit code: {exit_code})")
                                        if output:
                                            print(f"Error:\n{output}")
                        else:
                            if console:
                                console.print("[dim]Commands skipped.[/dim]")
                            else:
                                print("Commands skipped.")

                except Exception as e:
                    if console:
                        console.print(f"\n[red]Error:[/red] {str(e)}", file=sys.stderr)
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
