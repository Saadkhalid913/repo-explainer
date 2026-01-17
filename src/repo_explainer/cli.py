"""CLI entry point for repo-explainer using Typer."""

from pathlib import Path
from typing import Annotated, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from . import __version__
from .config import Settings, get_settings
from .html_generator import DocsServer, HTMLGenerator
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
    generate_html: Annotated[
        bool,
        typer.Option(
            "--generate-html",
            help="Generate HTML documentation after analysis",
        ),
    ] = False,
    html_port: Annotated[
        int,
        typer.Option(
            "--html-port",
            help="Port for HTML server (only with --generate-html)",
        ),
    ] = 8080,
    no_browser: Annotated[
        bool,
        typer.Option(
            "--no-browser",
            help="Don't open browser (only with --generate-html)",
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
        
        # Generate HTML and start server after analysis
        repo-explain analyze . --generate-html
        repo-explain analyze https://github.com/user/repo --generate-html --html-port 3000

    Invokes OpenCode to perform AI-powered analysis and produces:
    - Architecture overview (architecture.md)
    - Component diagrams (Mermaid format)
    - Data flow diagrams (Mermaid format)
    - Technology stack summary
    - Optional: HTML documentation with live server
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

    # Run analysis with streaming if verbose
    if verbose:
        console.print("[dim]Verbose mode: Showing OpenCode activity...[/dim]\n")
        if depth == "quick":
            result = opencode.quick_scan(event_callback=handle_opencode_event)
        else:
            result = opencode.analyze_architecture(event_callback=handle_opencode_event)
    else:
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

        # Generate HTML if requested
        if generate_html:
            console.print("\n" + "="*60)
            try:
                from .html_generator import DocsServer, HTMLGenerator
                
                console.print(
                    Panel.fit(
                        "[bold blue]HTML Generation[/bold blue]\n"
                        f"Converting markdown to HTML...",
                        border_style="blue",
                    )
                )
                
                # Generate HTML
                generator = HTMLGenerator(settings.output_dir)
                html_dir = generator.generate()
                
                # Start server
                server = DocsServer(html_dir, port=html_port)
                url = server.start(open_browser=not no_browser)
                
                # Extract repo name for display
                repo_name = repo_path.name
                
                console.print(f"\n[bold green]📚 Docs server started on {url}[/bold green]")
                console.print(f"[dim]Serving documentation for: {repo_name}[/dim]\n")
                console.print("[dim]Press Ctrl+C to stop the server[/dim]\n")
                
                # Keep server running
                try:
                    import signal
                    import time
                    
                    def signal_handler(sig, frame):
                        server.stop()
                        raise typer.Exit(0)
                    
                    signal.signal(signal.SIGINT, signal_handler)
                    
                    while True:
                        time.sleep(1)
                        
                except KeyboardInterrupt:
                    server.stop()
                    raise typer.Exit(0)
                    
            except Exception as e:
                console.print(f"\n[red]Error generating HTML:[/red] {e}")
                if verbose:
                    import traceback
                    console.print(f"\n[dim]{traceback.format_exc()}[/dim]")
                # Don't exit - analysis was still successful

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


@app.command()
def generate_html(
    docs_path: Annotated[
        Optional[Path],
        typer.Argument(
            help="Path to the documentation directory (defaults to ./opencode/docs or ./docs)",
        ),
    ] = None,
    output: Annotated[
        Optional[Path],
        typer.Option(
            "--output", "-o",
            help="Output directory for HTML files (defaults to docs/html)",
        ),
    ] = None,
    port: Annotated[
        int,
        typer.Option(
            "--port", "-p",
            help="Port to serve the documentation on",
        ),
    ] = 8080,
    no_serve: Annotated[
        bool,
        typer.Option(
            "--no-serve",
            help="Generate HTML but don't start the server",
        ),
    ] = False,
    no_browser: Annotated[
        bool,
        typer.Option(
            "--no-browser",
            help="Don't open the browser automatically",
        ),
    ] = False,
) -> None:
    """
    Generate HTML documentation and start a local web server.

    Converts markdown documentation to beautiful HTML pages with navigation
    and serves them on a local HTTP server for easy viewing.

    Examples:
        repo-explain generate-html
        repo-explain generate-html ./opencode/docs
        repo-explain generate-html --port 3000
        repo-explain generate-html --no-serve
    """
    # Determine docs path
    if docs_path is None:
        # Try common locations
        candidates = [
            Path("opencode/docs"),
            Path("docs"),
            Path("."),
        ]
        for candidate in candidates:
            if candidate.exists() and (candidate / "index.md").exists():
                docs_path = candidate
                break
        
        if docs_path is None:
            console.print("[red]Error:[/red] Could not find documentation directory")
            console.print("[dim]Please specify the docs path explicitly or run from the project root[/dim]")
            raise typer.Exit(1)
    
    if not docs_path.exists():
        console.print(f"[red]Error:[/red] Documentation path does not exist: {docs_path}")
        raise typer.Exit(1)

    # Display header
    console.print(
        Panel.fit(
            f"[bold blue]HTML Documentation Generator[/bold blue]\n"
            f"Source: [cyan]{docs_path}[/cyan]",
            border_style="blue",
        )
    )

    # Generate HTML
    try:
        generator = HTMLGenerator(docs_path, output_dir=output)
        html_dir = generator.generate()
    except Exception as e:
        console.print(f"\n[red]Error generating HTML:[/red] {e}")
        if "--verbose" in typer.get_sys_argv():
            import traceback
            console.print(f"\n[dim]{traceback.format_exc()}[/dim]")
        raise typer.Exit(1)

    # Start server unless --no-serve is specified
    if not no_serve:
        try:
            server = DocsServer(html_dir, port=port)
            url = server.start(open_browser=not no_browser)
            
            # Extract repo name from the docs path for better messaging
            repo_name = docs_path.parent.name if docs_path.name == "docs" else docs_path.name
            
            console.print(f"[bold green]📚 Docs server started on {url}[/bold green]")
            console.print(f"[dim]Serving documentation for: {repo_name}[/dim]\n")
            
            # Keep server running
            try:
                import signal
                import time
                
                # Handle Ctrl+C gracefully
                def signal_handler(sig, frame):
                    server.stop()
                    raise typer.Exit(0)
                
                signal.signal(signal.SIGINT, signal_handler)
                
                # Keep main thread alive
                while True:
                    time.sleep(1)
                    
            except KeyboardInterrupt:
                server.stop()
                raise typer.Exit(0)
                
        except Exception as e:
            console.print(f"\n[red]Error starting server:[/red] {e}")
            raise typer.Exit(1)
    else:
        console.print(f"\n[green]✓[/green] HTML documentation generated at: [cyan]{html_dir}[/cyan]")
        console.print(f"\n[dim]To view, open: {html_dir}/index.html[/dim]")


if __name__ == "__main__":
    app()
