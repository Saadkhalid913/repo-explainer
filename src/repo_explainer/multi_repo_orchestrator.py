"""Multi-repository analysis orchestrator."""

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

from .config import get_settings
from .cross_repo_analyzer import CrossRepoAnalyzer
from .multi_repo_doc_composer import MultiRepoDocComposer
from .opencode_service import OpenCodeService
from .output_manager import OutputManager
from .repository_loader import RepoMetadata, RepositoryLoader

console = Console()


class MultiRepoOrchestrator:
    """Orchestrates multi-repository analysis workflow."""

    def __init__(
        self,
        repos: list[str],
        depth: str,
        output_dir: Path,
        force_clone: bool = False,
        verbose: bool = False,
    ):
        """
        Initialize the multi-repo orchestrator.

        Args:
            repos: List of repository paths or URLs
            depth: Analysis depth (quick, standard, deep)
            output_dir: Output directory for documentation
            force_clone: Whether to force re-clone existing repos
            verbose: Whether to show verbose output
        """
        self.repos = repos
        self.depth = depth
        self.output_dir = output_dir
        self.force_clone = force_clone
        self.verbose = verbose
        self.settings = get_settings()

    def run(self) -> None:
        """Execute multi-repo analysis workflow."""
        console.print(f"\n[bold cyan]Multi-Repository Analysis[/bold cyan]")
        console.print(f"Repositories: {len(self.repos)}")
        console.print(f"Analysis depth: {self.depth}\n")

        # Phase 1: Load all repositories
        console.print("[bold]Phase 1:[/bold] Loading repositories...")
        repo_metadata = self._load_repositories()

        if not repo_metadata:
            console.print("[red]Error:[/red] No repositories could be loaded")
            raise SystemExit(1)

        console.print(f"[green]✓[/green] Loaded {len(repo_metadata)} repositor{'y' if len(repo_metadata) == 1 else 'ies'}\n")

        # Phase 2: Analyze each repository individually (parallel)
        console.print(f"[bold]Phase 2:[/bold] Analyzing {len(repo_metadata)} repositor{'y' if len(repo_metadata) == 1 else 'ies'}...")
        analysis_results = self._analyze_repositories(repo_metadata)

        successful_count = sum(1 for r in analysis_results.values() if r is not None)
        console.print(f"[green]✓[/green] Successfully analyzed {successful_count}/{len(repo_metadata)} repositor{'y' if len(repo_metadata) == 1 else 'ies'}\n")

        # Phase 3: Cross-repo analysis
        console.print("[bold]Phase 3:[/bold] Cross-repository analysis...")
        cross_repo_data = self._analyze_cross_repo(repo_metadata, analysis_results)
        console.print("[green]✓[/green] Cross-repo analysis complete\n")

        # Phase 4: Generate aggregated documentation
        console.print("[bold]Phase 4:[/bold] Generating system documentation...")
        self._generate_documentation(repo_metadata, analysis_results, cross_repo_data)
        console.print("[green]✓[/green] Documentation generated\n")

        console.print(f"[bold green]✓ Multi-repo analysis complete![/bold green]")
        console.print(f"[bold]Documentation:[/bold] [cyan]{self.output_dir.absolute()}[/cyan]")
        console.print(f"[dim]💡 Tip: Open `{self.output_dir.absolute()}/index.md` to start exploring[/dim]\n")

    def _load_repositories(self) -> list[RepoMetadata]:
        """
        Load all repositories (clone if needed).

        Returns:
            List of RepoMetadata for successfully loaded repositories
        """
        loader = RepositoryLoader(tmp_dir=Path("./tmp"))
        metadata = []

        for repo_url in self.repos:
            try:
                meta = loader.load_repository(repo_url, force_clone=self.force_clone)
                metadata.append(meta)
                console.print(f"  [green]✓[/green] Loaded: [cyan]{meta.name}[/cyan]")
            except Exception as e:
                console.print(f"  [red]✗[/red] Failed to load {repo_url}: {e}")

        return metadata

    def _analyze_repositories(self, repo_metadata: list[RepoMetadata]) -> dict:
        """
        Analyze repositories in parallel.

        Args:
            repo_metadata: List of repository metadata

        Returns:
            Dictionary mapping repo name to analysis result
        """
        results = {}

        # Use ThreadPoolExecutor for parallel analysis
        max_workers = min(3, len(repo_metadata))  # Max 3 concurrent analyses

        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all analysis tasks
            futures = {
                executor.submit(self._analyze_single_repo, meta): meta
                for meta in repo_metadata
            }

            # Show progress
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console,
            ) as progress:
                task = progress.add_task(
                    f"[cyan]Analyzing repositories...",
                    total=len(futures),
                )

                # Collect results as they complete
                for future in as_completed(futures):
                    meta = futures[future]
                    try:
                        result = future.result()
                        results[meta.name] = result
                        console.print(f"  [green]✓[/green] Analyzed: [cyan]{meta.name}[/cyan]")
                    except Exception as e:
                        console.print(f"  [red]✗[/red] Failed to analyze {meta.name}: {e}")
                        results[meta.name] = None

                    progress.update(task, advance=1)

        return results

    def _analyze_single_repo(self, meta: RepoMetadata) -> dict:
        """
        Run standard analysis on a single repository.

        Args:
            meta: Repository metadata

        Returns:
            Dictionary with metadata, result, and output_files
        """
        # Initialize OpenCode service
        service = OpenCodeService(repo_path=meta.path)

        # Create event callback for verbose mode
        def handle_event(event: dict) -> None:
            if not self.verbose:
                return

            event_type = event.get("type")
            if event_type == "tool_use":
                part = event.get("part", {})
                tool = part.get("tool")
                state = part.get("state", {})
                input_data = state.get("input", {})

                if tool == "read":
                    file_path = input_data.get("filePath", input_data.get("file_path", ""))
                    if file_path:
                        console.print(f"    [dim]📄 [{meta.name}] Reading:[/dim] [cyan]{file_path}[/cyan]")

                elif tool == "write":
                    file_path = input_data.get("filePath", input_data.get("file_path", ""))
                    if file_path:
                        console.print(f"    [dim]✏️  [{meta.name}] Writing:[/dim] [green]{file_path}[/green]")

        # Run architecture analysis
        if self.depth == "quick":
            result = service.quick_scan(event_callback=handle_event if self.verbose else None)
        else:
            result = service.analyze_architecture(event_callback=handle_event if self.verbose else None)

        # Save individual repo output to services/ subdirectory
        output_manager = OutputManager(
            output_dir=self.output_dir / "services" / meta.name
        )
        output_files = output_manager.write_analysis_result(
            result=result,
            repo_path=meta.path,
            depth=self.depth,
        )

        return {
            "metadata": meta,
            "result": result,
            "output_files": output_files,
        }

    def _analyze_cross_repo(
        self,
        repo_metadata: list[RepoMetadata],
        analysis_results: dict,
    ) -> dict:
        """
        Detect cross-repository patterns and dependencies.

        Args:
            repo_metadata: List of repository metadata
            analysis_results: Dictionary of analysis results per repo

        Returns:
            Dictionary with cross-repo analysis data
        """
        analyzer = CrossRepoAnalyzer(
            repo_metadata=repo_metadata,
            analysis_results=analysis_results,
            verbose=self.verbose,
        )

        return analyzer.analyze()

    def _generate_documentation(
        self,
        repo_metadata: list[RepoMetadata],
        analysis_results: dict,
        cross_repo_data: dict,
    ) -> None:
        """
        Generate multi-repo documentation.

        Args:
            repo_metadata: List of repository metadata
            analysis_results: Dictionary of analysis results per repo
            cross_repo_data: Cross-repo analysis data
        """
        composer = MultiRepoDocComposer(
            output_dir=self.output_dir,
            repo_metadata=repo_metadata,
            analysis_results=analysis_results,
            cross_repo_data=cross_repo_data,
        )

        composer.compose()
