#!/usr/bin/env python3
"""CLI Helper Functions for AgentOS"""

import logging
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt

from agentos.core import config, path_resolver, utils

console = Console(force_terminal=True)
logger = logging.getLogger(__name__)


def load_manifest(path: str) -> dict:
    """Load and validate agent manifest from YAML/JSON file"""
    from rich.progress import Progress, SpinnerColumn, TextColumn

    try:
        # Resolve the manifest path
        manifest_path = Path(path).resolve()
        if not manifest_path.exists():
            # Try relative to current working directory
            manifest_path = Path.cwd() / path
            if not manifest_path.exists():
                raise FileNotFoundError(f"Manifest not found: {path}")

        with Progress(
            SpinnerColumn(),
            TextColumn("[cyan]Loading manifest..."),
            console=console,
            transient=True,
        ) as progress:
            progress.add_task("load", total=None)
            configs = config.yaml_to_json(str(manifest_path))

        required_fields = ["name", "model_provider", "model_version"]
        for field in required_fields:
            if field not in configs:
                console.print(f"[red]❌ Missing required field: {field}[/red]")
                raise ValueError(f"Missing required field in manifest: {field}")

        valid_providers = ["github", "openai", "claude", "gemini", "cohere", "ollama"]
        if configs["model_provider"].lower() not in valid_providers:
            console.print(
                f"[red]❌ Invalid model provider: {configs['model_provider']}[/red]"
            )
            console.print(
                f"[yellow]Valid providers: {', '.join(valid_providers)}[/yellow]"
            )
            raise ValueError(
                f"Invalid model provider. Must be one of: {valid_providers}"
            )

        utils.NAME = configs["name"]
        utils.PROVIDER = configs["model_provider"]
        utils.MODEL = configs["model_version"]
        utils.ISOLATED = configs.get("isolated", True)
        utils.DESTRUCTIVE_COMMANDS = configs.get(
            "DESTRUCTIVE_COMMANDS", utils.DESTRUCTIVE_COMMANDS
        )

        # MCP settings (optional)
        mcp_cfg = configs.get("mcp", {}) or {}
        utils.MCP_ENABLED = bool(mcp_cfg.get("enabled", False))
        utils.MCP_SERVERS = mcp_cfg.get("servers", []) or []

        utils.TIME_CONFIG = configs.get("time")
        utils.REPEAT_CONFIG = configs.get("repeat")

        console.print(
            f"[green]✓[/green] Manifest loaded: [cyan]{configs['name']}[/cyan]"
        )

        return configs

    except Exception as e:
        logger.error(f"Failed to load manifest {path}: {e}")
        console.print(f"[red]❌ Failed to load manifest: {e}[/red]")
        raise


def create_default_manifest(path: str):
    """Create a default manifest file interactively"""
    from rich.progress import Progress, SpinnerColumn, TextColumn

    console.print(
        Panel(
            "[bold cyan]🛠️  Manifest Creator[/bold cyan]\n"
            "Let's create your agent configuration",
            border_style="cyan",
        )
    )
    console.print()

    name = Prompt.ask("[cyan]Agent name[/cyan]", default="my_assistant")
    provider = Prompt.ask(
        "[cyan]Model provider[/cyan]",
        choices=["github", "openai", "claude", "gemini", "ollama"],
        default="github",
    )

    if provider == "github":
        model = Prompt.ask("[cyan]Model version[/cyan]", default="openai/gpt-4o-mini")
    elif provider == "openai":
        model = Prompt.ask("[cyan]Model version[/cyan]", default="gpt-4o-mini")
    elif provider == "ollama":
        model = Prompt.ask("[cyan]Model version[/cyan]", default="llama3.1:8b")
    else:
        model = Prompt.ask("[cyan]Model version[/cyan]")

    isolated = Confirm.ask("[cyan]Enable sandboxing?[/cyan]", default=True)

    manifest_content = f"""# AgentOS Configuration
name: {name}
model_provider: {provider}
model_version: {model}
isolated: {str(isolated).lower()}

# Security: Blocked commands
DESTRUCTIVE_COMMANDS:
  - rm
  - rmdir
  - sudo
  - dd
  - mkfs
  - format
"""

    console.print()
    with Progress(
        SpinnerColumn(),
        TextColumn("[cyan]Creating manifest..."),
        console=console,
        transient=True,
    ) as progress:
        progress.add_task("create", total=None)
        with open(path, "w") as f:
            f.write(manifest_content)

    console.print(
        Panel(
            f"[green]✅ Manifest created successfully![/green]\n\n"
            f"[white]File:[/white] [cyan]{path}[/cyan]\n"
            f"[white]Agent:[/white] [yellow]{name}[/yellow]\n"
            f"[white]Model:[/white] [blue]{provider}/{model}[/blue]\n\n"
            f"[dim]Run with: [cyan]agentos run {path} --task 'your task'[/cyan][/dim]",
            border_style="green",
            title="✨ Success",
        )
    )


def show_welcome():
    """Show welcome message and quick start guide"""
    from rich.table import Table
    from rich.text import Text

    # Create header
    header = Text()
    header.append("\n🤖 ", style="bold blue")
    header.append("AgentOS", style="bold cyan")
    header.append(" v1.0.0\n", style="dim")
    header.append("Production AI Agent Runtime\n", style="italic dim")

    console.print(Panel(header, border_style="bright_blue", padding=(1, 2)))
    console.print()

    # Quick Start Commands
    table = Table(
        title="⚡ Quick Start",
        border_style="green",
        show_header=True,
        header_style="bold green",
    )
    table.add_column("Command", style="cyan", no_wrap=True)
    table.add_column("Description", style="white")

    table.add_row(
        "agentos run <manifest> --task '<task>'", "🚀 Run an agent with a task"
    )
    table.add_row("agentos ps", "📋 List all agents")
    table.add_row("agentos logs <agent-id>", "📄 View agent logs")
    table.add_row("agentos stop <agent-id>", "🛑 Stop a running agent")
    table.add_row("agentos ui", "🌐 Launch web interface")
    table.add_row("agentos app", "🖥️  Launch desktop app")

    console.print(table)
    console.print()

    # Examples
    examples = Panel(
        "[yellow]💡 Examples:[/yellow]\n\n"
        "[cyan]→[/cyan] agentos run default.yaml --task 'create a Python hello world'\n"
        "[cyan]→[/cyan] agentos run default.yaml --task 'analyze system logs'\n"
        "[cyan]→[/cyan] agentos init my-agent.yaml  [dim]# Create new manifest[/dim]\n"
        "[cyan]→[/cyan] agentos schedule  [dim]# View scheduled agents[/dim]",
        border_style="yellow",
        padding=(1, 2),
    )
    console.print(examples)
    console.print()
    console.print(
        "[dim]💡 Tip: Use [cyan]--help[/cyan] with any command for more options[/dim]\n"
    )


def run_agent_background(manifest_path: str, task: str):
    """Run agent in background without blocking"""
    import subprocess
    # import sys

    subprocess.Popen(
        # [sys.executable, "agentos.py", "run", manifest_path, "--task", task],
        ["agentos", "run", manifest_path, "--task", task],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
