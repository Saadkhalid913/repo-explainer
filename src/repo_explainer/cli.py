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
        Optional[str],
        typer.Argument(
            help="Path to repository or Git URL (e.g., https://github.com/user/repo)",
        ),
    ] = None,
    repos: Annotated[
        Optional[list[str]],
        typer.Option(
            "--file", "-f",
            help="Repository path or URL (can be specified multiple times for multi-repo analysis)",
        ),
    ] = None,
    depth: Annotated[
        str,
        typer.Option(
            "--depth", "-d",
            help="Analysis depth: quick, standard, deep, or extra-deep",
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
    Analyze one or more repositories and generate documentation.

    Single repository mode (backward compatible):
        repo-explain analyze .
        repo-explain analyze ./my-project
        repo-explain analyze https://github.com/torvalds/linux

    Multi-repository mode (microservices):
        repo-explain analyze -f repo1 -f repo2 -f repo3
        repo-explain analyze -f https://github.com/user/service1 -f https://github.com/user/service2

    Invokes OpenCode to perform AI-powered analysis and produces:
    - Architecture overview (architecture.md)
    - Component diagrams (Mermaid format)
    - Data flow diagrams (Mermaid format)
    - Technology stack summary
    - Multi-repo: System-wide views, service mesh, cross-service dependencies
    """
    # Update settings based on CLI options
    settings = get_settings()
    if verbose:
        settings.verbose = True
    if output:
        settings.output_dir = output

    # Determine mode: multi-repo or single-repo
    if repos:
        # Multi-repo mode
        from .multi_repo_orchestrator import MultiRepoOrchestrator

        orchestrator = MultiRepoOrchestrator(
            repos=repos,
            depth=depth,
            output_dir=settings.output_dir,
            force_clone=force_clone,
            verbose=verbose,
        )
        orchestrator.run()
        return

    # Single-repo mode (backward compatible)
    if repo_path_or_url is None:
        repo_path_or_url = "."

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

    # Create event callback for verbose mode
    def handle_opencode_event(event: dict) -> None:
        """Handle OpenCode JSON events in verbose mode."""
        if not verbose:
            return

        event_type = event.get("type")

        if event_type == "tool_use":
            # Extract tool call information
            part = event.get("part", {})
            tool = part.get("tool")
            state = part.get("state", {})
            input_data = state.get("input", {})

            if tool == "read":
                file_path = input_data.get("filePath", input_data.get("file_path", ""))
                if file_path:
                    console.print(f"  [dim]📄 Reading:[/dim] [cyan]{file_path}[/cyan]")

            elif tool == "bash":
                description = input_data.get("description", "")
                command = input_data.get("command", "")
                if description:
                    console.print(f"  [dim]⚙️  Running:[/dim] {description}")
                elif command:
                    short_cmd = command[:60] + "..." if len(command) > 60 else command
                    console.print(f"  [dim]⚙️  Running:[/dim] {short_cmd}")

            elif tool == "write":
                file_path = input_data.get("filePath", input_data.get("file_path", ""))
                if file_path:
                    console.print(f"  [dim]✏️  Writing:[/dim] [green]{file_path}[/green]")

            elif tool == "glob":
                pattern = input_data.get("pattern", "")
                if pattern:
                    console.print(f"  [dim]🔍 Searching:[/dim] {pattern}")

    # Validate depth option
    valid_depths = ["quick", "standard", "deep", "extra-deep"]
    if depth not in valid_depths:
        console.print(f"[red]Error:[/red] Invalid depth '{depth}'. Must be one of: {', '.join(valid_depths)}")
        raise typer.Exit(1)

    # Determine which analysis method to use
    use_extra_deep = depth == "extra-deep"
    use_large_system = depth == "deep" or (opencode.is_large_repo(threshold=500) and depth == "standard")

    if use_extra_deep:
        console.print("[dim]📚 Extra-deep mode: Generating exhaustive per-component documentation...[/dim]\n")
    elif use_large_system and depth != "quick":
        console.print("[dim]📊 Detected large repository - using comprehensive analysis mode...[/dim]\n")

    # Run analysis with streaming if verbose
    if verbose:
        console.print("[dim]Verbose mode: Showing OpenCode activity...[/dim]\n")
        if depth == "quick":
            result = opencode.quick_scan(event_callback=handle_opencode_event)
        elif use_extra_deep:
            result = opencode.analyze_extra_deep(event_callback=handle_opencode_event)
        elif use_large_system:
            result = opencode.analyze_large_system(event_callback=handle_opencode_event)
        else:
            result = opencode.analyze_architecture(event_callback=handle_opencode_event)
    else:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            if use_extra_deep:
                analysis_type = "extra-deep (exhaustive)"
            elif use_large_system:
                analysis_type = "comprehensive"
            else:
                analysis_type = depth
            task = progress.add_task(f"Analyzing repository ({analysis_type} mode)...", total=None)

            if depth == "quick":
                result = opencode.quick_scan()
            elif use_extra_deep:
                result = opencode.analyze_extra_deep()
            elif use_large_system:
                result = opencode.analyze_large_system()
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

        # Separate coherent docs from technical artifacts
        coherent_docs = {}
        technical_files = {}

        for output_type, file_path in output_files.items():
            if output_type in ["index", "components", "dataflow", "tech-stack"]:
                coherent_docs[output_type] = file_path
            elif output_type.endswith("_mermaid") or output_type.endswith("_md"):
                # Skip raw artifacts if we have composed docs
                continue
            else:
                technical_files[output_type] = file_path

        # Display coherent documentation first
        if coherent_docs:
            console.print("[bold]📚 Coherent Documentation:[/bold]")
            if "index" in coherent_docs:
                console.print(f"  - [cyan]index.md[/cyan] (Start here!)")
            for doc_type, file_path in coherent_docs.items():
                if doc_type != "index":
                    # Show relative path from output directory
                    rel_path = file_path.relative_to(settings.output_dir)
                    console.print(f"  - [cyan]{rel_path}[/cyan]")
            console.print()

        # Display technical artifacts
        if technical_files:
            console.print("[bold]🔧 Technical Artifacts:[/bold]")
            for output_type, file_path in technical_files.items():
                console.print(f"  - {output_type}: [dim]{file_path.name}[/dim]")
            console.print()

        # Update tip message
        if "index" in coherent_docs:
            console.print(f"[dim]💡 Tip: Open `{settings.output_dir.absolute()}/index.md` to start exploring[/dim]")
        else:
            console.print(f"[dim]💡 Tip: Start with `cat {settings.output_dir.absolute()}/ANALYSIS_SUMMARY.md`[/dim]")

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
