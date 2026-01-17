"""Orchestrator - coordinates the analysis pipeline."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.progress import Progress

from repo_explainer.analyzer import CodeAnalyzer
from repo_explainer.config import AnalysisDepth, OutputFormat, get_settings
from repo_explainer.diagram_generator import DiagramGenerator
from repo_explainer.doc_generator import DocumentationGenerator
from repo_explainer.llm_service import LLMService
from repo_explainer.models import AnalysisResult, DiagramInfo, OpenCodeSession
from repo_explainer.opencode_runner import ClaudeRunner, OpenCodeRunner
from repo_explainer.output_manager import OutputManager
from repo_explainer.repository_loader import RepositoryLoader


class Orchestrator:
    """
    Sequential orchestrator for the analysis pipeline.

    Flow: loader → analyzer → OpenCode/LLM → doc generator → output
    """

    def __init__(
        self,
        repo_path: str,
        output_dir: Path,
        depth: AnalysisDepth = AnalysisDepth.STANDARD,
        output_format: OutputFormat = OutputFormat.MARKDOWN,
        use_opencode: bool = True,
        progress: Optional[Progress] = None,
        console: Optional[Console] = None,
        incremental: bool = False,
    ):
        self.repo_path_str = repo_path
        self.output_dir = output_dir
        self.depth = depth
        self.output_format = output_format
        self.use_opencode = use_opencode
        self.progress = progress
        self.console = console or Console()
        self.incremental = incremental

        self.settings = get_settings()

        # Initialize components
        self.loader = RepositoryLoader(console=self.console)
        self.analyzer = CodeAnalyzer(console=self.console)
        self.opencode = OpenCodeRunner(console=self.console)
        self.claude = ClaudeRunner(console=self.console)
        self.llm = LLMService()

        self.sessions: list[OpenCodeSession] = []
        self.errors: list[str] = []

    @classmethod
    def from_existing(
        cls,
        analysis_dir: Path,
        incremental: bool = True,
        progress: Optional[Progress] = None,
        console: Optional[Console] = None,
    ) -> "Orchestrator":
        """Create orchestrator from existing analysis for updates."""
        output_manager = OutputManager(analysis_dir)
        previous = output_manager.load_previous_analysis()

        if not previous:
            raise ValueError("No previous analysis found")

        repo_path = previous.get("repository", {}).get("path", "")
        depth_str = previous.get("configuration", {}).get("depth", "standard")
        depth = AnalysisDepth(depth_str)

        return cls(
            repo_path=repo_path,
            output_dir=analysis_dir,
            depth=depth,
            incremental=incremental,
            progress=progress,
            console=console,
        )

    def run(self) -> AnalysisResult:
        """Execute the analysis pipeline."""
        task_id = None
        if self.progress:
            task_id = self.progress.add_task("Initializing...", total=None)

        try:
            # Step 1: Load repository
            self._update_progress(task_id, "Loading repository...")
            local_path, repo_info = self.loader.load(self.repo_path_str)
            repo_info.last_analyzed = datetime.now()

            # Step 2: Analyze structure
            self._update_progress(task_id, "Analyzing code structure...")
            components = self.analyzer.analyze_repository(local_path, repo_info)
            file_tree = self.loader.get_file_tree(local_path)

            # Prepare context for LLM/OpenCode
            context = self.analyzer.prepare_analysis_context(
                local_path, repo_info, components, file_tree
            )

            # Step 3: Run OpenCode or fallback analysis
            self._update_progress(task_id, "Running AI analysis...")
            diagrams, tech_stack, patterns = self._run_ai_analysis(
                local_path, context
            )

            # Step 4: Generate documentation
            self._update_progress(task_id, "Generating documentation...")
            self._generate_documentation(repo_info, components, diagrams)

            # Step 5: Write metadata and output
            self._update_progress(task_id, "Writing output files...")
            output_manager = OutputManager(self.output_dir)
            output_manager.write_analysis_log(
                repo_info, self.depth, self.sessions, self.errors
            )
            output_manager.write_config_snapshot()

            # Create result
            result = output_manager.create_analysis_result(
                repo_info=repo_info,
                components=components,
                diagrams=diagrams,
                tech_stack=tech_stack,
                patterns=patterns,
                opencode_session_id=(
                    self.sessions[0].session_id if self.sessions else None
                ),
                errors=self.errors,
            )

            if self.output_format == OutputFormat.JSON:
                output_manager.export_result_json(result)

            return result

        finally:
            self.loader.cleanup()
            self.llm.close()
            if self.progress and task_id is not None:
                self.progress.remove_task(task_id)

    def _update_progress(self, task_id: Optional[int], description: str) -> None:
        """Update the progress display."""
        if self.progress and task_id is not None:
            self.progress.update(task_id, description=description)
        elif self.settings.verbose:
            self.console.print(f"[dim]{description}[/]")

    def _run_ai_analysis(
        self, repo_path: Path, context: str
    ) -> tuple[list[DiagramInfo], list[str], list[str]]:
        """Run OpenCode/Claude/LLM analysis."""
        diagrams: list[DiagramInfo] = []
        tech_stack: list[str] = []
        patterns: list[str] = []

        # Try OpenCode first
        if self.use_opencode and self.opencode.is_available():
            self.console.print("[dim]Using OpenCode for analysis...[/]")
            session = self.opencode.run_analysis(
                repo_path, self.depth, self.output_dir, context
            )
            self.sessions.append(session)

            if session.exit_code == 0:
                # Import OpenCode outputs from session
                doc_gen = DocumentationGenerator(self.output_dir)
                if session.output_files:
                    doc_gen.ingest_opencode_output(session.output_files)

                # OpenCode writes files to repo root - collect them
                diagram_gen = DiagramGenerator(self.output_dir)
                opencode_files = self._collect_opencode_files(repo_path)
                
                for file_path in opencode_files:
                    if file_path.suffix in (".mermaid", ".mmd"):
                        from repo_explainer.models import DiagramType
                        
                        # Determine diagram type from filename
                        name_lower = file_path.stem.lower()
                        if "component" in name_lower or "class" in name_lower:
                            diag_type = DiagramType.COMPONENT
                        elif "dataflow" in name_lower or "flow" in name_lower:
                            diag_type = DiagramType.DATAFLOW
                        else:
                            diag_type = DiagramType.ARCHITECTURE
                        
                        imported = diagram_gen.import_opencode_diagram(
                            file_path,
                            diag_type,
                            file_path.stem.replace("-", " ").replace("_", " ").title(),
                        )
                        if imported:
                            diagrams.append(imported)
                    elif file_path.suffix == ".md" and file_path.stem.lower() == "architecture":
                        # Import architecture doc
                        doc_gen.ingest_opencode_output([file_path])
                    elif file_path.suffix == ".txt" and "tech" in file_path.stem.lower():
                        # Parse tech stack
                        content = file_path.read_text()
                        for line in content.split("\n"):
                            line = line.strip()
                            if line.startswith("- "):
                                tech_stack.append(line[2:])
                            elif line.startswith("* "):
                                tech_stack.append(line[2:])
                            elif line and not line.startswith("#"):
                                tech_stack.append(line)

                # If no diagrams from OpenCode, generate basic ones
                if not diagrams:
                    diagrams = self._generate_basic_diagrams(repo_path, context)

                return diagrams, tech_stack, patterns
            else:
                self.errors.append(
                    f"OpenCode session {session.session_id} failed: {session.stderr}"
                )

        # Try Claude fallback
        if self.settings.use_claude_fallback and self.claude.is_available():
            self.console.print("[dim]Falling back to Claude CLI...[/]")
            session = self.claude.run_analysis(
                repo_path, self.depth, self.output_dir, context
            )
            self.sessions.append(session)

            if session.exit_code == 0:
                doc_gen = DocumentationGenerator(self.output_dir)
                doc_gen.ingest_opencode_output(session.output_files)
                return diagrams, tech_stack, patterns
            else:
                self.errors.append(
                    f"Claude session failed: {session.stderr}"
                )

        # Fall back to direct LLM calls
        if self.settings.openrouter_api_key:
            self.console.print("[dim]Using direct LLM calls...[/]")
            diagrams, tech_stack, patterns = self._run_llm_analysis(
                repo_path, context
            )
        else:
            # Generate basic diagrams locally
            self.console.print(
                "[yellow]No AI backend available, generating basic diagrams...[/]"
            )
            diagrams = self._generate_basic_diagrams(repo_path, context)

        return diagrams, tech_stack, patterns

    def _collect_opencode_files(self, repo_path: Path) -> list[Path]:
        """Collect files created by OpenCode in the repo root."""
        opencode_files: list[Path] = []
        
        # Known file patterns that OpenCode might create
        patterns = [
            "*.mermaid",
            "*.mmd", 
            "architecture.md",
            "tech-stack.txt",
            "techstack.txt",
        ]
        
        for pattern in patterns:
            for file_path in repo_path.glob(pattern):
                if file_path.is_file():
                    opencode_files.append(file_path)
        
        return opencode_files

    def _run_llm_analysis(
        self, repo_path: Path, context: str
    ) -> tuple[list[DiagramInfo], list[str], list[str]]:
        """Run analysis using direct LLM calls."""
        diagrams: list[DiagramInfo] = []
        tech_stack: list[str] = []
        patterns: list[str] = []

        try:
            # Generate architecture diagram
            arch_mermaid = self.llm.generate_architecture_diagram(context)
            if arch_mermaid:
                diagram_gen = DiagramGenerator(self.output_dir)
                from repo_explainer.models import RepositoryInfo

                # Get repo info from context
                diag = diagram_gen.generate_architecture_diagram(
                    RepositoryInfo(
                        path=repo_path,
                        name=repo_path.name,
                    ),
                    [],
                    arch_mermaid,
                )
                diagrams.append(diag)

            # Generate dataflow diagram
            dataflow_mermaid = self.llm.generate_dataflow_diagram(context)
            if dataflow_mermaid:
                diagram_gen = DiagramGenerator(self.output_dir)
                diag = diagram_gen.generate_dataflow_diagram([], dataflow_mermaid)
                diagrams.append(diag)

            # Generate tech stack
            tech_content = self.llm.generate_tech_stack(context)
            if tech_content:
                # Parse tech stack from markdown list
                for line in tech_content.split("\n"):
                    line = line.strip()
                    if line.startswith("- "):
                        tech_stack.append(line[2:])
                    elif line.startswith("* "):
                        tech_stack.append(line[2:])

            # Save architecture docs
            arch_doc = self.llm.generate_architecture(context)
            if arch_doc:
                arch_path = self.output_dir / "architecture" / "system-architecture.md"
                arch_path.parent.mkdir(parents=True, exist_ok=True)
                arch_path.write_text(arch_doc)

        except Exception as e:
            self.errors.append(f"LLM analysis error: {e}")

        return diagrams, tech_stack, patterns

    def _generate_basic_diagrams(
        self, repo_path: Path, context: str
    ) -> list[DiagramInfo]:
        """Generate basic diagrams without AI."""
        diagrams: list[DiagramInfo] = []

        # Re-analyze to get components
        from repo_explainer.models import RepositoryInfo

        repo_info = RepositoryInfo(path=repo_path, name=repo_path.name)
        components = self.analyzer.analyze_repository(repo_path, repo_info)

        diagram_gen = DiagramGenerator(self.output_dir)

        # Generate component diagram
        arch_diag = diagram_gen.generate_architecture_diagram(
            repo_info, components
        )
        diagrams.append(arch_diag)

        # Generate component relationships
        comp_diag = diagram_gen.generate_component_diagram(components)
        diagrams.append(comp_diag)

        # Generate dataflow
        flow_diag = diagram_gen.generate_dataflow_diagram(components)
        diagrams.append(flow_diag)

        # Generate dependency graph (internal + external deps)
        dep_diag = diagram_gen.generate_dependency_graph(components)
        diagrams.append(dep_diag)

        # Generate class/entity diagram
        class_diag = diagram_gen.generate_class_diagram(components)
        diagrams.append(class_diag)

        return diagrams

    def _generate_documentation(
        self,
        repo_info,
        components,
        diagrams,
    ) -> None:
        """Generate all documentation files."""
        doc_gen = DocumentationGenerator(self.output_dir)

        # Generate main index
        doc_gen.generate_index(repo_info, components, diagrams)

        # Generate architecture overview with embedded diagrams
        doc_gen.generate_architecture_overview(repo_info, components, diagrams)

        # Generate component docs
        for component in components:
            doc_gen.generate_component_doc(component)

        # Generate dependencies doc - collect all external deps from components
        all_external_deps: set[str] = set()
        for comp in components:
            all_external_deps.update(comp.external_dependencies)
        doc_gen.generate_dependencies_doc(components, list(sorted(all_external_deps)))

        # Generate patterns doc
        doc_gen.generate_patterns_doc([])
