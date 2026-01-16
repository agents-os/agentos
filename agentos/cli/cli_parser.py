#!/usr/bin/env python3
"""CLI Argument Parser for AgentOS"""

import argparse


def create_parser():
    """Create and configure argument parser"""
    parser = argparse.ArgumentParser(
        prog="agentos",
        description="🤖 AgentOS - Production AI Agent Runtime",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  agentos run agent.yaml --task "create a Python script"
  agentos chat --provider openai
  agentos chat --provider claude --temperature 0.5
  agentos ps
  agentos logs agent-123
  agentos stop agent-123
  agentos prune

For more help: https://docs.agentos.dev
        """,
    )
    parser.add_argument("--version", action="version", version="🤖 AgentOS 1.0.0")
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )
    parser.add_argument(
        "--no-color", action="store_true", help="Disable colored output"
    )

    subparsers = parser.add_subparsers(
        dest="command", help="Available commands", metavar="COMMAND"
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
    p_run.add_argument(
        "--timeout", type=int, default=300, help="Timeout in seconds (default: 300)"
    )
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

    return parser
