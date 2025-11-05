"""Schedule-related CLI Commands"""

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from rich.table import Table

from agentos.database import db
from agentos.core.scheduler import scheduler

console = Console()


def cmd_schedule(args):
    """Show scheduled agents"""
    from datetime import datetime
    
    try:
        scheduled = scheduler.list_scheduled()

        if not scheduled:
            console.print(
                Panel(
                    "[yellow]No scheduled agents found.[/yellow]\n\n"
                    "[cyan]💡 How to schedule agents:[/cyan]\n"
                    "Add to your manifest:\n"
                    "  [dim]time: 14[/dim]  [dim cyan]# Run daily at 14:00[/dim cyan]\n"
                    "  [dim]repeat: 30[/dim]  [dim cyan]# Run every 30 minutes[/dim cyan]",
                    title="🕰️  Schedule Status",
                    border_style="yellow",
                    padding=(1, 2)
                )
            )
            return

        table = Table(
            title=f"🕰️  Scheduled Agents ({len(scheduled)} active)",
            show_header=True,
            header_style="bold cyan",
            border_style="blue"
        )
        table.add_column("ID", style="cyan", width=20)
        table.add_column("Schedule", style="green", width=25)
        table.add_column("Next Run", style="yellow", width=20)
        table.add_column("Task", style="white", max_width=40)

        for schedule_id, info in scheduled.items():
            schedule_type = info["type"].title()
            if schedule_type == "Daily":
                schedule_display = f"📅 Daily at {info.get('time', 'N/A')}:00"
            elif schedule_type == "Repeat":
                schedule_display = f"🔁 Every {info.get('repeat', 'N/A')} min"
            else:
                schedule_display = schedule_type
            
            table.add_row(
                schedule_id,
                schedule_display,
                info["next_run"],
                info["task"]
            )

        console.print(table)
        console.print()
        console.print(Panel(
            "[cyan]💡 Quick Commands[/cyan]\n\n"
            "[white]→[/white] agentos unschedule <id>  [dim]# Remove specific schedule[/dim]\n"
            "[white]→[/white] agentos unschedule --all  [dim]# Remove all schedules[/dim]",
            border_style="cyan",
            padding=(1, 2)
        ))

    except Exception as e:
        console.print(f"[red]❌ Failed to list scheduled agents: {e}[/red]")


def cmd_unschedule(args):
    """Remove scheduled agents"""
    from rich.progress import Progress, SpinnerColumn, TextColumn
    
    try:
        if args.all:
            scheduled = scheduler.list_scheduled()
            if not scheduled:
                console.print(Panel(
                    "[yellow]✨ No scheduled agents to remove[/yellow]",
                    border_style="yellow"
                ))
                return

            console.print(f"\n[yellow]⚠️  About to remove {len(scheduled)} scheduled agents:[/yellow]")
            for sid in list(scheduled.keys())[:5]:
                console.print(f"  [dim]• {sid}[/dim]")
            if len(scheduled) > 5:
                console.print(f"  [dim]... and {len(scheduled) - 5} more[/dim]")
            console.print()
            
            if not Confirm.ask("[bold]Proceed with removal?[/bold]"):
                console.print("[yellow]❌ Operation cancelled[/yellow]")
                return

            with Progress(
                SpinnerColumn(),
                TextColumn("[cyan]Removing schedules..."),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("remove", total=None)
                for schedule_id in scheduled.keys():
                    db.remove_scheduled_agent(schedule_id)

            console.print(Panel(
                f"[green]✅ Successfully removed {len(scheduled)} scheduled agents[/green]",
                border_style="green",
                title="✨ Success"
            ))

        else:
            if not args.schedule_id:
                console.print("[red]❌ No schedule ID specified[/red]")
                console.print("[dim]\nUsage:[/dim]")
                console.print("[dim]  agentos unschedule <schedule-id>[/dim]")
                console.print("[dim]  agentos unschedule --all[/dim]")
                return

            scheduled = scheduler.list_scheduled()
            if args.schedule_id not in scheduled:
                console.print(f"[red]❌ Scheduled agent not found: {args.schedule_id}[/red]")
                if scheduled:
                    console.print("\n[cyan]Available scheduled agents:[/cyan]")
                    for sid in list(scheduled.keys())[:5]:
                        console.print(f"  [dim]• {sid}[/dim]")
                    if len(scheduled) > 5:
                        console.print(f"  [dim]... and {len(scheduled) - 5} more[/dim]")
                return

            with Progress(
                SpinnerColumn(),
                TextColumn("[cyan]Removing schedule..."),
                console=console,
                transient=True
            ) as progress:
                task = progress.add_task("remove", total=None)
                db.remove_scheduled_agent(args.schedule_id)
            
            console.print(Panel(
                f"[green]✅ Successfully removed scheduled agent[/green]\n\n"
                f"[white]ID:[/white] [cyan]{args.schedule_id}[/cyan]",
                border_style="green",
                title="✨ Success"
            ))

    except Exception as e:
        console.print(Panel(
            f"[red]❌ Failed to remove scheduled agent[/red]\n\n"
            f"[yellow]Error:[/yellow] {e}",
            border_style="red",
            title="💥 Error"
        ))
