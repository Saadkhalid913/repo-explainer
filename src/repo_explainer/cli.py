"""CLI entry point for repo-explainer using Typer."""

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from . import __version__
from .config import Settings, get_settings
from .opencode_service import OpenCodeService
from .output_manager import OutputManager
from .repository_loader import RepositoryLoader

app = typer.Typer(
    name="repo-explain",
    help="Analyze repositories and generate structured documentation using AI.",
    add_completion=False,
)
console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"repo-explainer v{__version__}")
        raise typer.Exit()


@app.callback()
def main(
    version: Annotated[
        Optional[bool],
        typer.Option("--version", "-v", callback=version_callback, is_eager=True),
    ] = None,
) -> None:
    """Repository Explainer - AI-powered documentation generator."""
    pass


@app.command()
def analyze(
    repo_path_or_url: Annotated[
        str,
        typer.Argument(
            help="Path to repository or Git URL (e.g., https://github.com/user/repo)",
        ),
    ] = ".",
    depth: Annotated[
        str,
        typer.Option(
            "--depth", "-d",
            help="Analysis depth: quick, standard, or deep",
        ),
    ] = "standard",
    output: Annotated[
        Optional[Path],
        typer.Option(
            "--output", "-o",
            help="Output directory for generated documentation",
        ),
    ] = None,
    force_clone: Annotated[
        bool,
        typer.Option(
            "--force-clone",
            help="Force re-clone if repository already exists in tmp",
        ),
    ] = False,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-V", help="Enable verbose output"),
    ] = False,
) -> None:
    """
    Analyze a repository and generate documentation.

    Accepts either a local path or a Git URL. Git URLs will be cloned to ./tmp/owner/repo.

    Examples:
        repo-explain analyze .
        repo-explain analyze ./my-project
        repo-explain analyze https://github.com/torvalds/linux
        repo-explain analyze git@github.com:user/repo.git

    Invokes OpenCode to perform AI-powered analysis and produces:
    - Architecture overview (architecture.md)
    - Component diagrams (Mermaid format)
    - Data flow diagrams (Mermaid format)
    - Technology stack summary
    """
    # Update settings based on CLI options
    settings = get_settings()
    if verbose:
        settings.verbose = True
    if output:
        settings.output_dir = output

    # Load repository (clone if it's a Git URL)
    loader = RepositoryLoader()
    try:
        repo_path = loader.load(repo_path_or_url, force_clone=force_clone)
    except ValueError as e:
        console.print(f"[red]Error loading repository:[/red] {e}")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error:[/red] {e}")
        raise typer.Exit(1)

    # Verify the path exists
    if not repo_path.exists():
        console.print(f"[red]Error:[/red] Repository path does not exist: {repo_path}")
        raise typer.Exit(1)

    # Display header
    console.print(
        Panel.fit(
            f"[bold blue]Repository Explainer[/bold blue] v{__version__}\n"
            f"Analyzing: [cyan]{repo_path}[/cyan]",
            border_style="blue",
        )
    )

    # Initialize OpenCode service
    opencode = OpenCodeService(repo_path)

    # Check if OpenCode is available
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Checking OpenCode availability...", total=None)

        if not opencode.check_available():
            progress.stop()
            console.print(
                "[yellow]Warning:[/yellow] OpenCode CLI not found. "
                "Please install OpenCode or ensure it's in your PATH."
            )
            console.print(
                "\n[dim]Tip: Set REPO_EXPLAINER_OPENCODE_BINARY to specify a custom path.[/dim]"
            )
            raise typer.Exit(1)

        progress.update(task, description="OpenCode available", completed=True)

    # Run analysis based on depth
    console.print(f"\n[bold]Running {depth} analysis...[/bold]\n")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task(f"Analyzing repository ({depth} mode)...", total=None)

        if depth == "quick":
            result = opencode.quick_scan()
        else:
            result = opencode.analyze_architecture()

        progress.update(task, completed=True)

    # Handle result
    if result.success:
        console.print("\n[green]Analysis complete![/green]\n")

        # Write output files
        output_manager = OutputManager(settings.output_dir)
        output_files = output_manager.write_analysis_result(
            result=result,
            repo_path=repo_path,
            depth=depth,
        )

        # Display output location
        console.print(f"[bold]Output saved to:[/bold] [cyan]{output_manager.get_output_location()}[/cyan]\n")

        console.print("[bold]Generated files:[/bold]")
        for output_type, file_path in output_files.items():
            console.print(f"  - {output_type}: [cyan]{file_path.absolute()}[/cyan]")

        console.print(f"\n[dim]Tip: Start with `cat {settings.output_dir.absolute()}/ANALYSIS_SUMMARY.md`[/dim]")

        if result.session_id:
            console.print(f"\n[dim]Session ID: {result.session_id}[/dim]")

        if result.artifacts:
            console.print("\n[bold]OpenCode artifacts:[/bold]")
            for name, path in result.artifacts.items():
                console.print(f"  - {name}: {path}")

        if verbose and result.output:
            console.print("\n[bold]Raw output:[/bold]")
            console.print(result.output[:500] + "..." if len(result.output) > 500 else result.output)

    else:
        console.print(f"\n[red]Analysis failed:[/red] {result.error}")
        if verbose and result.output:
            console.print(f"\n[dim]Output: {result.output}[/dim]")
        raise typer.Exit(1)


@app.command()
def update(
    repo_path: Annotated[
        Path,
        typer.Argument(
            help="Path to the repository to update docs for",
            exists=True,
            file_okay=False,
            dir_okay=True,
            resolve_path=True,
        ),
    ] = Path("."),
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-V", help="Enable verbose output"),
    ] = False,
) -> None:
    """
    Update existing documentation for a repository.

    Re-runs analysis on changed files and updates documentation accordingly.
    """
    console.print(
        Panel.fit(
            "[bold yellow]Update Command[/bold yellow]\n"
            "[dim]This command will be implemented in a future iteration.[/dim]",
            border_style="yellow",
        )
    )
    console.print(f"\nRepository: [cyan]{repo_path}[/cyan]")
    console.print("\n[yellow]Coming soon![/yellow] For now, use 'analyze' to regenerate docs.")


if __name__ == "__main__":
    app()
