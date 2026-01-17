#!/usr/bin/env python3
"""CLI Argument Parser for AgentOS with Rich Help"""

import argparse
import sys

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

console = Console(force_terminal=True)


class RichHelpFormatter(argparse.HelpFormatter):
    """Custom help formatter using Rich for beautiful output."""

    def __init__(self, prog, indent_increment=2, max_help_position=30, width=None):
        super().__init__(prog, indent_increment, max_help_position, width or 80)

    def format_help(self):
        """Override to use Rich formatting."""
        # We'll handle this in the custom print_help
        return super().format_help()


def print_rich_help(parser, subcommand=None):
    """Print help using Rich formatting."""

    if subcommand and hasattr(parser, "_subparsers"):
        # Find the subparser
        for action in parser._subparsers._actions:
            if hasattr(action, "choices") and subcommand in action.choices:
                sub_parser = action.choices[subcommand]
                print_subcommand_help(sub_parser, subcommand)
                return

    # Main help
    console.print()
    console.print(
        Panel.fit(
            "[bold cyan]🤖 AgentOS[/bold cyan] - [dim]Production AI Agent Runtime[/dim]\n\n"
            "[dim]Automate everything with LLM-powered agents[/dim]",
            border_style="cyan",
            padding=(1, 2),
        )
    )

    # Usage
    console.print("\n[bold yellow]USAGE[/bold yellow]")
    console.print("  [cyan]agentos[/cyan] [dim]<command>[/dim] [dim][options][/dim]\n")

    # Commands table
    console.print("[bold yellow]COMMANDS[/bold yellow]")

    table = Table(show_header=False, box=None, padding=(0, 2, 0, 0))
    table.add_column("Command", style="cyan", width=15)
    table.add_column("Description")

    commands = [
        ("run", "🚀 Run an agent from manifest"),
        ("chat", "💬 Interactive chat mode with LLM"),
        ("setup", "🔧 Configure API keys and settings"),
        ("ps", "📋 List all agents"),
        ("logs", "📄 Show agent logs"),
        ("stop", "🛑 Stop a running agent"),
        ("prune", "🧹 Clean up stopped agents"),
        ("init", "🛠️  Initialize new manifest"),
        ("schedule", "🕰️  Show scheduled agents"),
        ("unschedule", "🗑️  Remove scheduled agents"),
        ("ui", "🌐 Start web UI"),
        ("app", "🖥️  Launch desktop app"),
    ]

    for cmd, desc in commands:
        table.add_row(cmd, desc)

    console.print(table)

    # Global options
    console.print("\n[bold yellow]OPTIONS[/bold yellow]")
    opts_table = Table(show_header=False, box=None, padding=(0, 2, 0, 0))
    opts_table.add_column("Option", style="green", width=20)
    opts_table.add_column("Description")

    opts_table.add_row("--version", "Show version number")
    opts_table.add_row("-v, --verbose", "Enable verbose logging")
    opts_table.add_row("--no-color", "Disable colored output")
    opts_table.add_row("-h, --help", "Show this help message")

    console.print(opts_table)

    # Examples
    console.print("\n[bold yellow]EXAMPLES[/bold yellow]")
    examples = [
        ("agentos setup", "Configure your API keys"),
        ("agentos chat --provider gemini", "Start chat with Gemini"),
        ("agentos chat -p claude", "Start chat with Claude"),
        ("agentos run agent.yaml --task 'write code'", "Run agent with task"),
        ("agentos ui --port 8080", "Start web UI on port 8080"),
    ]

    for cmd, desc in examples:
        console.print(f"  [cyan]{cmd}[/cyan]")
        console.print(f"    [dim]{desc}[/dim]")

    # Footer
    console.print(
        "\n[dim]For command help: [cyan]agentos <command> --help[/cyan][/dim]"
    )
    console.print(
        "[dim]Documentation: [link=https://agentos.sodeom.com/]https://agentos.sodeom.com/[/link][/dim]\n"
    )


def print_subcommand_help(parser, command):
    """Print help for a specific subcommand."""
    console.print()

    # Header
    title = f"[bold cyan]agentos {command}[/bold cyan]"
    desc = parser.description or parser.format_usage()

    console.print(
        Panel.fit(f"{title}\n\n[dim]{desc}[/dim]", border_style="cyan", padding=(1, 2))
    )

    # Usage
    console.print("\n[bold yellow]USAGE[/bold yellow]")

    # Build usage string
    usage_parts = [f"[cyan]agentos {command}[/cyan]"]

    for action in parser._actions:
        if action.dest == "help":
            continue
        if action.option_strings:
            if action.required:
                usage_parts.append(f"[green]{action.option_strings[0]}[/green] <value>")
            else:
                usage_parts.append(f"[dim][{action.option_strings[0]}][/dim]")
        elif action.dest != "func":
            if action.nargs == "?":
                usage_parts.append(f"[dim][{action.dest}][/dim]")
            else:
                usage_parts.append(f"[yellow]<{action.dest}>[/yellow]")

    console.print("  " + " ".join(usage_parts) + "\n")

    # Arguments
    positional = [
        a
        for a in parser._actions
        if not a.option_strings and a.dest not in ("help", "func")
    ]
    if positional:
        console.print("[bold yellow]ARGUMENTS[/bold yellow]")
        args_table = Table(show_header=False, box=None, padding=(0, 2, 0, 0))
        args_table.add_column("Arg", style="yellow", width=20)
        args_table.add_column("Description")

        for action in positional:
            required = "" if action.nargs == "?" else " [red](required)[/red]"
            args_table.add_row(action.dest, (action.help or "") + required)

        console.print(args_table)
        console.print()

    # Options
    optional = [a for a in parser._actions if a.option_strings and a.dest != "help"]
    if optional:
        console.print("[bold yellow]OPTIONS[/bold yellow]")
        opts_table = Table(show_header=False, box=None, padding=(0, 2, 0, 0))
        opts_table.add_column("Option", style="green", width=25)
        opts_table.add_column("Description")

        for action in optional:
            opt_str = ", ".join(action.option_strings)
            if action.type or action.choices:
                if action.choices:
                    opt_str += f" [dim]{{{','.join(map(str, action.choices))}}}[/dim]"
                else:
                    opt_str += " [dim]<value>[/dim]"

            help_text = action.help or ""
            if action.default is not None and action.default != argparse.SUPPRESS:
                if action.default not in (True, False, None):
                    help_text += f" [dim](default: {action.default})[/dim]"

            opts_table.add_row(opt_str, help_text)

        opts_table.add_row("-h, --help", "Show this help message")
        console.print(opts_table)

    console.print()


class RichArgumentParser(argparse.ArgumentParser):
    """ArgumentParser with Rich help output."""

    def print_help(self, file=None):
        """Override to use Rich formatting."""
        print_rich_help(self)

    def error(self, message):
        """Override to use Rich for errors."""
        console.print(f"[red]❌ Error:[/red] {message}")
        console.print(
            f"[dim]Try '[cyan]agentos --help[/cyan]' for usage information.[/dim]\n"
        )
        sys.exit(2)


class RichSubParser(argparse.ArgumentParser):
    """Sub-parser with Rich help."""

    def __init__(self, *args, command_name=None, **kwargs):
        super().__init__(*args, **kwargs)
        self._command_name = command_name

    def print_help(self, file=None):
        """Override to use Rich formatting."""
        print_subcommand_help(self, self._command_name or self.prog.split()[-1])


def create_parser():
    """Create and configure argument parser with Rich help"""
    parser = RichArgumentParser(
        prog="agentos",
        description="🤖 AgentOS - Production AI Agent Runtime",
        add_help=True,
    )
    parser.add_argument("--version", action="version", version="🤖 AgentOS 1.1.6")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "--no-color", action="store_true", help="Disable colored output"
    )

    subparsers = parser.add_subparsers(
        dest="command",
        help="Available commands",
        metavar="COMMAND",
        parser_class=RichSubParser,
    )

    # setup - Configure API keys
    p_setup = subparsers.add_parser(
        "setup",
        help="🔧 Configure API keys",
        description="Interactive wizard to configure LLM provider API keys",
    )
    p_setup.add_argument(
        "--show", action="store_true", help="Show current configuration status"
    )

    # run
    p_run = subparsers.add_parser(
        "run",
        help="🚀 Run an agent from manifest",
        description="Start an AI agent with a specific task",
    )
    p_run.add_argument("manifest", help="Path to agent manifest file (YAML)")
    p_run.add_argument(
        "--task", "-t", required=True, help="Task for the agent to execute"
    )
    p_run.add_argument("--timeout", type=int, default=300, help="Timeout in seconds")
    p_run.add_argument(
        "--isolated", action="store_true", help="Force enable sandboxing"
    )

    # ps
    p_ps = subparsers.add_parser(
        "ps", help="📋 List agents", description="Show all agents and their status"
    )
    p_ps.add_argument(
        "--status",
        choices=["running", "completed", "failed", "stopped"],
        help="Filter by status",
    )

    # logs
    p_logs = subparsers.add_parser(
        "logs",
        help="📄 Show agent logs",
        description="Display logs for a specific agent",
    )
    p_logs.add_argument("agent", help="Agent name or ID")
    p_logs.add_argument("--tail", "-n", type=int, help="Show last N lines")
    p_logs.add_argument("--follow", "-f", action="store_true", help="Follow log output")

    # stop
    p_stop = subparsers.add_parser(
        "stop",
        help="🛑 Stop a running agent",
        description="Gracefully stop a running agent",
    )
    p_stop.add_argument("agent", help="Agent name or ID")

    # prune
    p_prune = subparsers.add_parser(
        "prune",
        help="🧹 Clean up stopped agents",
        description="Remove all stopped agent records",
    )
    p_prune.add_argument("--force", "-f", action="store_true", help="Skip confirmation")

    # init
    p_init = subparsers.add_parser(
        "init",
        help="🛠️  Initialize new manifest",
        description="Create a new agent manifest interactively",
    )
    p_init.add_argument(
        "name", nargs="?", default="agent.yaml", help="Manifest filename"
    )

    # schedule
    p_schedule = subparsers.add_parser(
        "schedule",
        help="🕰️  Show scheduled agents",
        description="Display all scheduled agents and their next run times",
    )

    # unschedule
    p_unschedule = subparsers.add_parser(
        "unschedule",
        help="🗑️  Remove scheduled agents",
        description="Remove scheduled agents by ID or remove all",
    )
    p_unschedule.add_argument("schedule_id", nargs="?", help="Schedule ID to remove")
    p_unschedule.add_argument(
        "--all", action="store_true", help="Remove all scheduled agents"
    )

    # ui
    p_ui = subparsers.add_parser(
        "ui", help="🌐 Start web UI", description="Launch the web-based user interface"
    )
    p_ui.add_argument(
        "--port", type=int, default=5000, help="Port to run on (default: 5000)"
    )
    p_ui.add_argument(
        "--host", default="0.0.0.0", help="Host to bind to (default: 0.0.0.0)"
    )

    # app
    p_app = subparsers.add_parser(
        "app",
        help="🖥️  Launch desktop app",
        description="Launch the desktop application interface",
    )
    p_app.add_argument(
        "--port", type=int, default=5000, help="Port to run on (default: 5000)"
    )
    p_app.add_argument(
        "--host", default="127.0.0.1", help="Host to bind to (default: 127.0.0.1)"
    )

    # chat
    p_chat = subparsers.add_parser(
        "chat",
        help="💬 Interactive chat mode",
        description="Start an interactive chat session with an LLM (like Gemini, Claude, Codex)",
    )
    p_chat.add_argument(
        "--provider",
        "-p",
        default="github",
        choices=["github", "gemini", "cohere", "openai", "claude", "ollama"],
        help="LLM provider to use (default: github)",
    )
    p_chat.add_argument(
        "--model",
        "-m",
        default=None,
        help="Model name (uses provider default if not specified)",
    )
    p_chat.add_argument(
        "--temperature",
        type=float,
        default=0.7,
        help="Temperature for generation (0.0-1.0, default: 0.7)",
    )
    p_chat.add_argument(
        "--system-prompt",
        "-s",
        default=None,
        help="Custom system prompt for the chat session",
    )
    p_chat.add_argument(
        "--mcp",
        action="store_true",
        default=True,
        help="Enable MCP mode (use built-in tools instead of shell commands) [default: enabled]",
    )
    p_chat.add_argument(
        "--no-mcp",
        action="store_true",
        help="Disable MCP mode (use shell commands instead)",
    )

    # Return parser and subparsers dict for setting defaults
    subparser_dict = {
        "setup": p_setup,
        "run": p_run,
        "ps": p_ps,
        "logs": p_logs,
        "stop": p_stop,
        "prune": p_prune,
        "init": p_init,
        "schedule": p_schedule,
        "unschedule": p_unschedule,
        "ui": p_ui,
        "app": p_app,
        "chat": p_chat,
    }

    return parser, subparser_dict
