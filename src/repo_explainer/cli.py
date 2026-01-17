"""CLI entry point using Typer."""

from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from repo_explainer import __version__
from repo_explainer.config import AnalysisDepth, OutputFormat, get_settings, load_config_file
from repo_explainer.orchestrator import Orchestrator

app = typer.Typer(
    name="repo-explainer",
    help="AI-powered repository documentation generator",
    rich_markup_mode="rich",
    no_args_is_help=True,
)
console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"[bold blue]repo-explainer[/] version [green]{__version__}[/]")
        raise typer.Exit()


@app.callback()
def main(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-V",
        callback=version_callback,
        is_eager=True,
        help="Show version and exit",
    ),
    config: Optional[Path] = typer.Option(
        None,
        "--config",
        "-c",
        help="Path to configuration file (.repo-explainer.yaml)",
        exists=True,
        dir_okay=False,
    ),
    verbose: bool = typer.Option(
        False,
        "--verbose",
        "-v",
        help="Enable verbose output",
    ),
) -> None:
    """Repository Explainer - Generate comprehensive documentation from codebases."""
    settings = get_settings()
    if config:
        load_config_file(config)
    if verbose:
        settings.verbose = True


@app.command()
def analyze(
    repo_path: str = typer.Argument(
        ...,
        help="Path to local repository or Git URL to analyze",
    ),
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Output directory for generated documentation",
    ),
    depth: AnalysisDepth = typer.Option(
        AnalysisDepth.STANDARD,
        "--depth",
        "-d",
        help="Analysis depth: quick, standard, or deep",
    ),
    output_format: OutputFormat = typer.Option(
        OutputFormat.MARKDOWN,
        "--format",
        "-f",
        help="Output format: markdown or json",
    ),
    use_opencode: bool = typer.Option(
        True,
        "--opencode/--no-opencode",
        help="Use OpenCode for analysis (falls back to Claude if unavailable)",
    ),
) -> None:
    """
    Analyze a repository and generate documentation.

    Supports local paths and Git URLs. Invokes OpenCode custom commands
    to generate architecture docs, diagrams, and tech stack analysis.
    """
    settings = get_settings()

    console.print(
        Panel.fit(
            f"[bold blue]Analyzing Repository[/]\n"
            f"[dim]Path:[/] {repo_path}\n"
            f"[dim]Depth:[/] {depth.value}\n"
            f"[dim]Format:[/] {output_format.value}",
            border_style="blue",
        )
    )

    output_dir = output or settings.output_dir

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        orchestrator = Orchestrator(
            repo_path=repo_path,
            output_dir=output_dir,
            depth=depth,
            output_format=output_format,
            use_opencode=use_opencode,
            progress=progress,
            console=console,
        )

        try:
            result = orchestrator.run()

            if result.errors:
                console.print(f"\n[yellow]⚠ Completed with {len(result.errors)} warnings[/]")
                for error in result.errors:
                    console.print(f"  [dim]• {error}[/]")
            else:
                console.print("\n[green]✓ Analysis complete![/]")

            console.print(f"\n[bold]Output written to:[/] {output_dir}")

            if result.opencode_session_id:
                console.print(f"[dim]OpenCode session: {result.opencode_session_id}[/]")

        except Exception as e:
            console.print(f"\n[red]✗ Analysis failed:[/] {e}")
            if settings.verbose:
                console.print_exception()
            raise typer.Exit(1)


@app.command()
def update(
    analysis_dir: Path = typer.Argument(
        ...,
        help="Path to existing analysis output directory",
        exists=True,
        file_okay=False,
        dir_okay=True,
    ),
    incremental: bool = typer.Option(
        True,
        "--incremental/--full",
        help="Only update changed components (vs full re-analysis)",
    ),
) -> None:
    """
    Update existing documentation for a previously analyzed repository.

    Detects changes since last analysis and regenerates affected sections.
    """
    settings = get_settings()

    console.print(
        Panel.fit(
            f"[bold blue]Updating Documentation[/]\n"
            f"[dim]Directory:[/] {analysis_dir}\n"
            f"[dim]Mode:[/] {'Incremental' if incremental else 'Full'}",
            border_style="blue",
        )
    )

    # Load metadata from previous analysis
    metadata_path = analysis_dir / "metadata" / "analysis-log.json"
    if not metadata_path.exists():
        console.print(f"[red]✗ No analysis metadata found at {metadata_path}[/]")
        console.print("[dim]Run 'repo-explainer analyze' first to create initial documentation.[/]")
        raise typer.Exit(1)

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
        transient=True,
    ) as progress:
        orchestrator = Orchestrator.from_existing(
            analysis_dir=analysis_dir,
            incremental=incremental,
            progress=progress,
            console=console,
        )

        try:
            result = orchestrator.run()

            if result.errors:
                console.print(f"\n[yellow]⚠ Update completed with {len(result.errors)} warnings[/]")
            else:
                console.print("\n[green]✓ Update complete![/]")

            console.print(f"\n[bold]Output updated in:[/] {analysis_dir}")

        except Exception as e:
            console.print(f"\n[red]✗ Update failed:[/] {e}")
            if settings.verbose:
                console.print_exception()
            raise typer.Exit(1)


@app.command()
def init(
    output_dir: Path = typer.Option(
        Path("."),
        "--output",
        "-o",
        help="Directory to create config file in",
    ),
) -> None:
    """
    Initialize a .repo-explainer.yaml configuration file.
    """
    config_path = output_dir / ".repo-explainer.yaml"

    if config_path.exists():
        overwrite = typer.confirm(f"Config file already exists at {config_path}. Overwrite?")
        if not overwrite:
            raise typer.Exit()

    default_config = """\
# Repository Explainer Configuration
# https://github.com/your-org/repo-explainer

# Analysis settings
default_depth: standard  # quick, standard, or deep
output_format: markdown  # markdown or json
output_dir: ./repo-docs

# LLM settings (or set REPO_EXPLAINER_OPENROUTER_API_KEY env var)
# openrouter_api_key: your-key-here
llm_model: google/gemini-2.5-flash-preview

# OpenCode settings
opencode_binary: opencode
use_claude_fallback: true
claude_binary: claude

# Behavior
verbose: false
max_files: 10000

# Paths to exclude from analysis (relative to repo root)
# exclude_paths:
#   - node_modules
#   - .git
#   - __pycache__
#   - dist
#   - build
"""

    config_path.write_text(default_config)
    console.print(f"[green]✓ Created configuration file:[/] {config_path}")


if __name__ == "__main__":
    app()
