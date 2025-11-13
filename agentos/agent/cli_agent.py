"""Main CLI Agent Execution Loop"""

import logging

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from agentos.agent.agent_executor import execute_command
from agentos.agent.agent_planner import ask_llm, execute_step, generate_plan

logger = logging.getLogger(__name__)
console = Console()


def main(query: str, max_steps: int = 10):
    """Main agent execution with enhanced UX"""
    try:
        logger.info(f"Starting agent with query: {query}")

        console.print(
            Panel(
                f"[bold blue]{query}[/bold blue]", title="🎯 Task", border_style="blue"
            )
        )

        with console.status(
            "[bold blue]Analyzing task and generating goal...", spinner="dots"
        ):
            goal = ask_llm(
                "You expertly understand problems and rewrite them as clear one-sentence goals.",
                f"Generate a clear, one-sentence goal to solve this problem: {query}. Do not return anything else other than one-sentence Goal.",
            )

        if not goal or len(goal.strip()) == 0:
            raise ValueError("Failed to generate valid goal")

        logger.info(f"Generated goal: {goal}")
        console.print(
            Panel(
                f"[bold green]{goal}[/bold green]",
                title="🎯 Goal",
                border_style="green",
            )
        )

        with console.status("[bold yellow]Creating execution plan...", spinner="dots"):
            plan = generate_plan(goal)

        if not plan:
            raise ValueError("Failed to generate execution plan")

        if len(plan) > max_steps:
            console.print(
                f"[yellow]⚠️  Plan has {len(plan)} steps, limiting to {max_steps} for safety[/yellow]"
            )
            plan = plan[:max_steps]

        logger.info(f"Generated plan with {len(plan)} steps")

        plan_table = Table(
            title="🗺️ Execution Plan", show_header=True, header_style="bold yellow"
        )
        plan_table.add_column("Step", style="cyan", width=6)
        plan_table.add_column("Action", style="white")

        for i, step in enumerate(plan, 1):
            plan_table.add_row(str(i), step)

        console.print(plan_table)
        console.print()

        history = ""
        completed_steps = 0

        with Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]Executing plan..."),
            TextColumn("[progress.description]{task.description}"),
            console=console,
            transient=False,
        ) as progress:
            main_task = progress.add_task("Overall Progress", total=len(plan))

            for i, step in enumerate(plan, 1):
                try:
                    progress.update(
                        main_task, description=f"Step {i}/{len(plan)}: {step[:50]}..."
                    )
                    logger.info(f"Executing step {i}/{len(plan)}: {step}")

                    console.print(
                        f"\n[bold cyan]➡️  Step {i}/{len(plan)}:[/bold cyan] {step}"
                    )

                    explanation, command = execute_step(goal, plan, step, history)

                    console.print(
                        f"[dim]🧠 Reasoning:[/dim] [italic]{explanation}[/italic]"
                    )
                    console.print(
                        f"[bold green]⚙️  Command:[/bold green] [code]{command}[/code]"
                    )

                    return_code, output = execute_command(command, simulate=False)

                    if output:
                        output_style = "green" if return_code == 0 else "red"
                        status_emoji = "✅" if return_code == 0 else "❌"

                        console.print(
                            Panel(
                                f"[bold]Output:[/bold]\n{output}\n\n[bold]Status:[/bold] {status_emoji} Exit code {return_code}",
                                border_style=output_style,
                                title="📝 Command Result",
                            )
                        )
                    else:
                        status_emoji = "✅" if return_code == 0 else "❌"
                        console.print(
                            f"[dim]{status_emoji} Command completed (exit code: {return_code})[/dim]"
                        )

                    history += f"\nStep {i}: {step}\nCommand: {command}\nReturn Code: {return_code}\nOutput: {output}\n"

                    completed_steps += 1
                    progress.update(main_task, advance=1)

                    if return_code != 0:
                        console.print(
                            f"[yellow]⚠️  Step {i} completed with warnings (exit code: {return_code})[/yellow]"
                        )

                except Exception as e:
                    logger.error(f"Step {i} failed with error: {e}")
                    console.print(f"[bold red]❌ Step {i} failed: {e}[/bold red]")
                    break

        if completed_steps == len(plan):
            console.print(
                Panel(
                    f"[bold green]✅ All {completed_steps} steps completed successfully![/bold green]\n"
                    f"[dim]Task: {query}[/dim]",
                    title="🎉 Success",
                    border_style="green",
                )
            )
        else:
            console.print(
                Panel(
                    f"[yellow]⚠️  Completed {completed_steps}/{len(plan)} steps[/yellow]\n"
                    f"[dim]Some steps may have encountered issues[/dim]",
                    title="⏸️ Partial Completion",
                    border_style="yellow",
                )
            )

        logger.info("Agent execution completed")

    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        console.print(
            Panel(
                f"[bold red]❌ Agent execution failed: {e}[/bold red]\n"
                f"[dim]Check logs for more details[/dim]",
                title="💥 Error",
                border_style="red",
            )
        )
        raise


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main(
            "create a python file that takes excel file and prints each cell content in column B into the terminal"
        )
