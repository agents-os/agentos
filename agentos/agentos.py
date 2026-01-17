#!/usr/bin/env python3
"""
AgentOS – Production Runtime
Main entrypoint for CLI + Daemon
"""

import logging
import sys
from pathlib import Path

from rich.console import Console

from agentos.cli.cli_commands import (
    cmd_app,
    cmd_chat,
    cmd_logs,
    cmd_ps,
    cmd_run,
    cmd_schedule,
    cmd_setup,
    cmd_setup_show,
    cmd_ui,
    cmd_unschedule,
    enhanced_prune,
    enhanced_stop,
)
from agentos.cli.cli_helpers import create_default_manifest, show_welcome
from agentos.cli.cli_parser import create_parser

LOG_DIR = Path.home() / ".agentos" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

console = Console(force_terminal=True)

logging.basicConfig(
    level=logging.WARNING,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_DIR / "agentos.log"),
    ],
)
logger = logging.getLogger(__name__)


def main():
    parser, subparsers = create_parser()

    def chat_handler(args):
        """Handler for chat command"""
        # MCP is default, --no-mcp disables it
        use_mcp = not getattr(args, "no_mcp", False)
        cmd_chat(
            provider=args.provider,
            model=args.model,
            temperature=args.temperature,
            system_prompt=args.system_prompt,
            verbose=args.verbose if hasattr(args, "verbose") else False,
            mcp=use_mcp,
        )

    def setup_handler(args):
        """Handler for setup command"""
        if getattr(args, "show", False):
            cmd_setup_show(args)
        else:
            cmd_setup(args)

    # Set default handlers for each command
    subparsers["setup"].set_defaults(func=setup_handler)
    subparsers["run"].set_defaults(func=cmd_run)
    subparsers["ps"].set_defaults(func=cmd_ps)
    subparsers["logs"].set_defaults(func=cmd_logs)
    subparsers["stop"].set_defaults(func=lambda args: enhanced_stop(args.agent))
    subparsers["prune"].set_defaults(func=lambda args: enhanced_prune(args.force))
    subparsers["init"].set_defaults(
        func=lambda args: create_default_manifest(args.name)
    )
    subparsers["schedule"].set_defaults(func=cmd_schedule)
    subparsers["unschedule"].set_defaults(func=cmd_unschedule)
    subparsers["ui"].set_defaults(func=cmd_ui)
    subparsers["app"].set_defaults(func=cmd_app)
    subparsers["chat"].set_defaults(func=chat_handler)

    args = parser.parse_args()

    if hasattr(args, "no_color") and args.no_color:
        console._color_system = None

    if hasattr(args, "verbose") and args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
        console.print("[dim]Verbose logging enabled[/dim]")

    if hasattr(args, "func"):
        try:
            args.func(args)
        except KeyboardInterrupt:
            console.print("\n[yellow]⚠️  Operation cancelled[/yellow]")
            sys.exit(130)
        except Exception as e:
            console.print(f"[red]❌ Command failed: {e}[/red]")
            if hasattr(args, "verbose") and args.verbose:
                console.print_exception()
            sys.exit(1)
    else:
        show_welcome()


if __name__ == "__main__":
    main()
