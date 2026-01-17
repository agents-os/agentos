"""Utility CLI Commands (stop, prune)"""

from rich.console import Console
from rich.prompt import Confirm

from agentos.database import db

console = Console(force_terminal=True)


def enhanced_stop(agent_id):
    """Enhanced stop command with better UX"""
    with console.status(f"[yellow]Stopping agent {agent_id}...", spinner="dots"):
        success = db.stop(agent_id)

    if success:
        console.print(f"[green]✅ Agent {agent_id} stopped successfully[/green]")
    else:
        console.print(f"[red]❌ Failed to stop agent {agent_id}[/red]")


def enhanced_prune(force=False):
    """Enhanced prune command with confirmation"""
    agents = db.list_agents()
    stopped_agents = [
        a for a in agents if a.get("status") in ["stopped", "completed", "failed"]
    ]

    if not stopped_agents:
        console.print("[green]✨ No stopped agents to clean up[/green]")
        return

    console.print(
        f"[yellow]Found {len(stopped_agents)} stopped agents to remove:[/yellow]"
    )
    for agent in stopped_agents[:5]:
        console.print(
            f"[dim]  • {agent.get('id', 'N/A')[:8]} - {agent.get('name', 'unknown')} ({agent.get('status')})[/dim]"
        )

    if len(stopped_agents) > 5:
        console.print(f"[dim]  ... and {len(stopped_agents) - 5} more[/dim]")

    if not force and not Confirm.ask("\nProceed with cleanup?"):
        console.print("[yellow]Cleanup cancelled[/yellow]")
        return

    with console.status("[yellow]Cleaning up...", spinner="dots"):
        db.prune()

    console.print("[green]✅ Cleanup completed[/green]")
