"""PatchPilot CLI interface using Typer and Rich."""

import sys
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from patchpilot import __version__
from patchpilot.engine import SelfHealingEngine
from patchpilot.llm.client import LocalSLMClient
from patchpilot.runner import TestRunner
from patchpilot.parser import TestLogParser

app = typer.Typer(
    name="patchpilot",
    help="Autonomous Self-Healing CI/CD & Agent Skill powered by Local Open-Weight SLMs.",
    add_completion=False,
)
console = Console()


@app.command()
def heal(
    test_cmd: Optional[str] = typer.Option(None, "--cmd", "-c", help="Custom test command (e.g. 'pytest', 'npm test')"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Local SLM model name (e.g. 'qwen2.5-coder:1.5b', 'gemma2:2b')"),
    max_attempts: int = typer.Option(3, "--max-attempts", "-a", help="Max iterative repair attempts"),
    auto_commit: bool = typer.Option(False, "--commit", help="Automatically commit verified fix to git"),
    url: Optional[str] = typer.Option(None, "--url", help="Local LLM endpoint URL (default: http://localhost:11434)"),
):
    """Run the test suite, isolate failures, and autonomously synthesize a verified fix using local SLMs."""
    console.print(Panel.fit(
        f"[bold cyan]PatchPilot[/bold cyan] [green]v{__version__}[/green] — Autonomous Self-Healing CI & Agent Skill",
        border_style="cyan"
    ))

    def notify(msg: str):
        console.print(f"[dim]{msg}[/dim]")

    engine = SelfHealingEngine(
        model=model,
        max_attempts=max_attempts,
        auto_commit=auto_commit,
        llm_url=url,
        on_status=notify,
    )

    result = engine.heal(test_cmd=test_cmd)

    if result.healed:
        if result.initial_passed:
            console.print("\n[bold green]✨ Everything is passing. No fixes needed![/bold green]")
        else:
            console.print("\n[bold green]🎉 SUCCESS: Failure successfully repaired and verified![/bold green]")
            if result.final_diff:
                console.print(Panel(
                    Syntax(result.final_diff, "diff", theme="monokai", line_numbers=False),
                    title="[bold green]Verified Patch Diff[/bold green]",
                    border_style="green"
                ))
        sys.exit(0)
    else:
        console.print(f"\n[bold red]❌ FAILED: {result.message}[/bold red]")
        sys.exit(1)


@app.command()
def diagnose(
    test_cmd: Optional[str] = typer.Option(None, "--cmd", "-c", help="Test command to run and diagnose"),
):
    """Run tests and parse diagnostic failure details without applying repairs."""
    cmd = test_cmd or TestRunner.detect_test_command()
    console.print(f"[cyan]Running test suite:[/cyan] [bold]{cmd}[/bold]")
    res = TestRunner.run(cmd)
    
    if res.passed:
        console.print("[green]✅ All tests passed cleanly.[/green]")
        return

    failures = TestLogParser.parse(f"{res.stdout}\n{res.stderr}")
    console.print(f"[bold red]Found {len(failures)} failure(s):[/bold red]\n")

    table = Table(title="Test Diagnostic Report", show_header=True, header_style="bold magenta")
    table.add_column("Framework", style="dim", width=12)
    table.add_column("Test Name", style="bold cyan")
    table.add_column("Target File", style="yellow")
    table.add_column("Error Summary", style="red")

    for f in failures:
        table.add_row(f.framework, f.test_name, f"{f.file_path}:{f.line_number or '?'}", f.error_message[:60])

    console.print(table)


@app.command()
def models(
    url: Optional[str] = typer.Option(None, "--url", help="Local LLM endpoint URL"),
):
    """List available local SLMs discovered from Ollama / local endpoints."""
    client = LocalSLMClient(base_url=url)
    console.print(f"[cyan]Probing local endpoint:[/cyan] {client.base_url}")
    
    if not client.check_health():
        console.print("[bold red]⚠️ Local SLM endpoint is not running or unreachable.[/bold red]")
        console.print("Start Ollama using: [bold green]ollama serve[/bold green]")
        return

    model_list = client.list_available_models()
    if not model_list:
        console.print("[yellow]Connected, but no local models found. Pull one with: `ollama pull qwen2.5-coder:1.5b` or `ollama pull gemma2:2b`[/yellow]")
        return

    table = Table(title="Installed Local Open-Weight Models", show_header=True, header_style="bold green")
    table.add_column("Model Name", style="bold cyan")
    table.add_column("Status", style="green")

    for m in model_list:
        is_default = " (Selected Default)" if m == client.model else ""
        table.add_row(m, f"[green]Ready[/green]{is_default}")

    console.print(table)


@app.command()
def version():
    """Print the version of PatchPilot."""
    console.print(f"PatchPilot v{__version__}")


if __name__ == "__main__":
    app()
