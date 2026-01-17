"""Basic CLI Commands (run, ps, logs)"""

# Enhanced terminal UI with rich formatting and better user experience

import signal
import sys
import time
import uuid
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
)
from rich.prompt import Confirm
from rich.table import Table

from agentos.agent import cli_agent
from agentos.core import config, threader, utils
from agentos.core.scheduler import scheduler
from agentos.database import db

console = Console(force_terminal=True)
LOG_DIR = Path.home() / ".agentos" / "logs"


def cmd_run(args):
    """Run an agent from manifest file"""
    try:
        if not args.task:
            console.print(
                "[red]❌ No task specified. Use --task 'your task here'[/red]"
            )
            sys.exit(1)

        # Resolve manifest path - support both absolute and relative paths
        manifest_path = Path(args.manifest).resolve()
        if not manifest_path.exists():
            # Try relative to current working directory
            manifest_path = Path.cwd() / args.manifest
            if not manifest_path.exists():
                console.print(f"[red]❌ Manifest file not found: {args.manifest}[/red]")
                console.print(
                    f"[dim]Searched in: {Path(args.manifest).resolve()}[/dim]"
                )
                if Confirm.ask("Would you like to create a default manifest?"):
                    from agentos.cli.cli_helpers import create_default_manifest

                    create_default_manifest(str(manifest_path))
                else:
                    sys.exit(1)

        with console.status("[bold blue]Setting up agent...", spinner="dots"):
            from agentos.cli.cli_helpers import load_manifest

            load_manifest(args.manifest)
            time.sleep(0.5)

        info_panel = Panel(
            f"[bold]Agent:[/bold] {utils.NAME}\n"
            f"[bold]Model:[/bold] {utils.PROVIDER}/{utils.MODEL}\n"
            f"[bold]Task:[/bold] {args.task}\n"
            f"[bold]Isolated:[/bold] {'Yes' if utils.ISOLATED else 'No'}",
            title="🤖 Agent Configuration",
            border_style="blue",
        )
        console.print(info_panel)

        if any(
            word in args.task.lower()
            for word in ["delete", "remove", "rm", "destroy", "kill"]
        ):
            if not Confirm.ask("[yellow]⚠️  This task might be destructive. Continue?"):
                console.print("[yellow]Operation cancelled.[/yellow]")
                return

        def agent_wrapper(queue, task):
            try:
                cli_agent.main(task)
            except Exception as e:
                queue.put(f"[ERROR] Agent failed: {e}")
                raise

        with console.status("[bold green]Starting agent...", spinner="dots"):
            pid, process, queue = threader.run_in_separate_process(
                agent_wrapper, args.task
            )
            time.sleep(0.5)

        uid = str(uuid.uuid4())
        log_path = LOG_DIR / f"{utils.NAME}_{uid[:8]}.log"
        db.add_agent(
            agent_id=uid,
            name=utils.NAME,
            model=utils.MODEL,
            pid=pid,
            log_path=str(log_path),
        )
        console.print(
            f"[green]✅ Agent started successfully![/green] (ID: {uid[:8]}, PID: {pid})"
        )

        if utils.TIME_CONFIG is not None or utils.REPEAT_CONFIG is not None:
            configs = config.yaml_to_json(args.manifest)
            scheduler.schedule_agent(configs, args.task, args.manifest)
            if not scheduler.running:
                scheduler.start()
            console.print(f"[blue]🕰️  Agent scheduled successfully![/blue]")

        console.print()

        def signal_handler(signum, frame):
            console.print("\n[yellow]⚠️  Stopping agent...[/yellow]")
            if process.is_alive():
                process.terminate()
                process.join(timeout=5)
                if process.is_alive():
                    process.kill()
            db.update_status(uid, "stopped")
            console.print("[red]🛑 Agent stopped.[/red]")
            sys.exit(0)

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        start_time = time.time()
        message_count = 0

        with open(log_path, "w") as log_file:
            with Progress(
                SpinnerColumn(),
                TextColumn("[bold blue]Agent working..."),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=console,
                transient=True,
            ) as progress:
                task_progress = progress.add_task("Processing", total=None)

                while process.is_alive() or not queue.empty():
                    try:
                        msg = queue.get(timeout=0.5)
                        message_count += 1

                        if "[PID" in msg and "]" in msg:
                            clean_msg = msg.split("] ", 1)[-1] if "] " in msg else msg
                        else:
                            clean_msg = msg

                        console.print(f"[dim]│[/dim] {clean_msg}")
                        log_file.write(f"{msg}\n")
                        log_file.flush()

                        db.append_log(uid, clean_msg)
                        progress.update(task_progress, advance=1)

                    except:
                        pass

        process.join()
        exit_code = process.exitcode
        duration = time.time() - start_time

        if exit_code == 0:
            db.update_status(uid, "completed")
            db.append_log(uid, f"Task completed successfully in {duration:.1f}s")
            console.print(
                Panel(
                    f"[green]✅ Task completed successfully![/green]\n"
                    f"[dim]Duration: {duration:.1f}s | Messages: {message_count}[/dim]",
                    title="🎉 Success",
                    border_style="green",
                )
            )
        else:
            db.update_status(uid, "failed")
            db.append_log(
                uid, f"Task failed with exit code {exit_code} after {duration:.1f}s"
            )
            console.print(
                Panel(
                    f"[red]❌ Task failed with exit code {exit_code}[/red]\n"
                    f"[dim]Duration: {duration:.1f}s | Check logs: agentos logs {uid[:8]}[/dim]",
                    title="💥 Failed",
                    border_style="red",
                )
            )

    except KeyboardInterrupt:
        if "uid" in locals():
            db.append_log(uid, "Task cancelled by user")
        console.print("\n[yellow]⚠️  Operation cancelled by user[/yellow]")
        sys.exit(130)
    except Exception as e:
        if "uid" in locals():
            db.append_log(uid, f"Agent failed: {e}")
        console.print(f"[red]❌ Failed to run agent: {e}[/red]")
        if args.verbose:
            console.print_exception()
        sys.exit(1)


def cmd_ps(args):
    """List agents with enhanced table display"""
    try:
        agents = db.list_agents()

        if not agents:
            console.print(
                Panel(
                    "[yellow]No agents found.[/yellow]\n"
                    "[dim]Start an agent with: agentos run manifest.yaml --task 'your task'[/dim]",
                    title="📋 Agent Status",
                    border_style="yellow",
                )
            )
            return

        table = Table(
            title="🤖 AgentOS - Running Agents",
            show_header=True,
            header_style="bold blue",
        )
        table.add_column("ID", style="cyan", width=10)
        table.add_column("Name", style="green", width=20)
        table.add_column("Model", style="blue", width=25)
        table.add_column("Status", width=12)
        table.add_column("PID", style="yellow", width=8)
        table.add_column("Started", style="dim", width=20)
        table.add_column("Actions", style="dim", width=15)

        for agent in agents:
            status = agent.get("status", "unknown")
            if status == "running":
                status_display = "[green]🟢 Running[/green]"
                actions = "stop, logs"
            elif status == "completed":
                status_display = "[blue]✅ Done[/blue]"
                actions = "logs, prune"
            elif status == "failed":
                status_display = "[red]❌ Failed[/red]"
                actions = "logs, prune"
            else:
                status_display = "[yellow]⏸️  Stopped[/yellow]"
                actions = "prune"

            table.add_row(
                agent.get("id", "N/A")[:8],
                agent.get("name", "unknown"),
                agent.get("model", "unknown"),
                status_display,
                str(agent.get("pid", "N/A")),
                agent.get("started_at", "N/A")[:19]
                if agent.get("started_at")
                else "N/A",
                actions,
            )

        console.print(table)
        console.print("\n[dim]💡 Quick commands:[/dim]")
        console.print("[dim]  • agentos logs <id>  - View agent logs[/dim]")
        console.print("[dim]  • agentos stop <id>  - Stop running agent[/dim]")
        console.print("[dim]  • agentos prune      - Clean up stopped agents[/dim]")

    except Exception as e:
        console.print(f"[red]❌ Failed to list agents: {e}[/red]")


def cmd_logs(args):
    """Display logs with enhanced formatting"""
    try:
        agent = db.get_agent(args.agent)
        if not agent:
            console.print(f"[red]❌ Agent not found: {args.agent}[/red]")
            all_agents = db.list_agents()
            if all_agents:
                console.print("\n[dim]Available agents:[/dim]")
                for a in all_agents[:5]:
                    console.print(
                        f"[dim]  • {a.get('id', 'N/A')[:8]} - {a.get('name', 'unknown')}[/dim]"
                    )
            return

        log_path = agent.get("log_path")
        if not log_path or not Path(log_path).exists():
            console.print(f"[yellow]⚠️  No logs found for agent: {args.agent}[/yellow]")
            return

        console.print(
            Panel(
                f"[bold]Agent:[/bold] {agent.get('name', 'unknown')}\n"
                f"[bold]Status:[/bold] {agent.get('status', 'unknown')}\n"
                f"[bold]Started:[/bold] {agent.get('started_at', 'N/A')}",
                title=f"📋 Logs for {args.agent}",
                border_style="blue",
            )
        )

        with open(log_path, "r") as f:
            lines = f.readlines()

            if hasattr(args, "tail") and args.tail:
                lines = lines[-args.tail :]
                console.print(f"[dim]Showing last {len(lines)} lines...[/dim]\n")

            for line in lines:
                line = line.strip()
                if not line:
                    continue

                if "[ERROR]" in line or "ERROR:" in line:
                    console.print(f"[red]{line}[/red]")
                elif "[WARNING]" in line or "WARNING:" in line:
                    console.print(f"[yellow]{line}[/yellow]")
                elif "[INFO]" in line or "INFO:" in line:
                    console.print(f"[blue]{line}[/blue]")
                elif "[PID" in line:
                    console.print(f"[dim]{line}[/dim]")
                elif "Executing:" in line:
                    console.print(f"[green]{line}[/green]")
                else:
                    console.print(line)

        console.print(f"\n[dim]💡 Log file: {log_path}[/dim]")

    except Exception as e:
        console.print(f"[red]❌ Failed to read logs: {e}[/red]")
