"""OpenCode CLI integration service."""

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from rich.console import Console

from .config import get_settings
from .prompts import (
    get_architecture_prompt,
    get_dependency_mapping_prompt,
    get_incremental_update_prompt,
    get_pattern_detection_prompt,
    get_quick_scan_prompt,
)

console = Console()


def parse_opencode_event(line: str) -> dict[str, Any] | None:
    """
    Parse a single JSON event from OpenCode output.

    Args:
        line: A line of JSON output

    Returns:
        Parsed event dict or None if parsing fails
    """
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return None


@dataclass
class OpenCodeResult:
    """Result from an OpenCode command execution."""

    success: bool
    output: str
    error: str | None = None
    session_id: str | None = None
    artifacts: dict[str, Any] = field(default_factory=dict)


class OpenCodeService:
    """Service for interacting with OpenCode CLI."""

    def __init__(self, repo_path: Path):
        self.repo_path = repo_path
        self.settings = get_settings()

    def run_command(
        self,
        prompt: str,
        command: str | None = None,
        event_callback: Callable[[dict], None] | None = None,
    ) -> OpenCodeResult:
        """
        Run an OpenCode command against the repository.

        Args:
            prompt: The prompt to send to OpenCode
            command: Optional custom command name (e.g., 'project:analyze-architecture')

        Returns:
            OpenCodeResult with the command output
        """
        cmd = [
            self.settings.opencode_binary,
            "run",
            prompt,
            "--format", self.settings.opencode_output_format,
            "--model", self.settings.opencode_model,
        ]

        if command:
            cmd.extend(["--command", command])

        if self.settings.verbose:
            console.print(f"[dim]Running: {' '.join(cmd)}[/dim]")

        try:
            # Use Popen for streaming output
            process = subprocess.Popen(
                cmd,
                cwd=self.repo_path,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,  # Line buffered
            )

            output_lines = []
            session_id = None
            artifacts = {}

            # Stream and process output line by line
            if process.stdout:
                for line in process.stdout:
                    output_lines.append(line)

                    # Parse and callback for each JSON event
                    if event_callback and self.settings.opencode_output_format == "json":
                        event = parse_opencode_event(line.strip())
                        if event:
                            # Extract session ID
                            if not session_id and "sessionID" in event:
                                session_id = event["sessionID"]

                            # Call the callback with the event
                            event_callback(event)

            # Wait for process to complete
            process.wait(timeout=300)

            output = "".join(output_lines)
            error = process.stderr.read() if process.stderr and process.returncode != 0 else None

            return OpenCodeResult(
                success=process.returncode == 0,
                output=output,
                error=error,
                session_id=session_id,
                artifacts=artifacts,
            )

        except subprocess.TimeoutExpired:
            return OpenCodeResult(
                success=False,
                output="",
                error="OpenCode command timed out after 5 minutes",
            )
        except FileNotFoundError:
            return OpenCodeResult(
                success=False,
                output="",
                error=f"OpenCode binary not found at: {self.settings.opencode_binary}",
            )
        except Exception as e:
            return OpenCodeResult(
                success=False,
                output="",
                error=f"Unexpected error: {str(e)}",
            )

    def analyze_architecture(
        self, event_callback: Callable[[dict], None] | None = None
    ) -> OpenCodeResult:
        """
        Run comprehensive architecture analysis on the repository.

        Uses the architecture_deep_dive prompt template which includes:
        - Detailed component analysis with file-to-function mappings
        - Line-level references for key functions
        - Dependency graphs (internal and external)
        - Multiple diagram types (architecture, dataflow, sequence)
        - Structured JSON output for orchestrators

        Returns:
            OpenCodeResult with generated artifacts
        """
        prompt = get_architecture_prompt()
        return self.run_command(prompt, event_callback=event_callback)

    def quick_scan(
        self, event_callback: Callable[[dict], None] | None = None
    ) -> OpenCodeResult:
        """
        Run a quick scan of the repository.

        Uses the quick_scan_v2 prompt template which includes:
        - Repository summary with language detection
        - Module index with file-to-component mappings
        - Technology stack inventory
        - Basic component registry with file paths

        Optimized for speed while still providing structured output.

        Returns:
            OpenCodeResult with lightweight analysis artifacts
        """
        prompt = get_quick_scan_prompt()
        return self.run_command(prompt, event_callback=event_callback)

    def detect_patterns(
        self, event_callback: Callable[[dict], None] | None = None
    ) -> OpenCodeResult:
        """
        Detect architectural and design patterns in the repository.

        Uses the pattern_detection prompt template which:
        - Identifies architectural patterns (MVC, Microservices, Layered, etc.)
        - Detects design patterns (Singleton, Factory, Observer, etc.)
        - Provides evidence with file paths and line numbers
        - Calculates confidence scores for each detection

        Requires: components.json from prior architecture analysis

        Returns:
            OpenCodeResult with patterns report and metadata
        """
        prompt = get_pattern_detection_prompt()
        return self.run_command(prompt, event_callback=event_callback)

    def map_dependencies(
        self, event_callback: Callable[[dict], None] | None = None
    ) -> OpenCodeResult:
        """
        Build comprehensive dependency graphs.

        Uses the dependency_mapping prompt template which:
        - Extracts external dependencies from package managers
        - Maps internal component-to-component dependencies
        - Calculates dependency layers (topological sort)
        - Detects circular dependencies
        - Generates visualization-ready dependency graphs

        Requires: components.json from prior architecture analysis

        Returns:
            OpenCodeResult with dependency analysis and diagrams
        """
        prompt = get_dependency_mapping_prompt()
        return self.run_command(prompt, event_callback=event_callback)

    def analyze_changes(
        self,
        changed_files: list[str],
        existing_docs_path: Path | None = None,
        event_callback: Callable[[dict], None] | None = None,
    ) -> OpenCodeResult:
        """
        Run incremental analysis on changed files.

        Uses the incremental_update prompt to analyze only the files that
        have changed since the last documentation update. More efficient
        than full re-analysis for small changes.

        Args:
            changed_files: List of file paths that changed
            existing_docs_path: Path to existing documentation (for context)
            event_callback: Optional callback for streaming events

        Returns:
            OpenCodeResult with updated artifacts
        """
        # Check for existing components.json for context
        components_path = None
        if existing_docs_path:
            candidate = existing_docs_path / "src" / "raw" / "components.json"
            if candidate.exists():
                components_path = str(candidate)
            else:
                # Try repo root
                candidate = self.repo_path / "components.json"
                if candidate.exists():
                    components_path = str(candidate)

        prompt = get_incremental_update_prompt(
            changed_files=changed_files,
            existing_components_path=components_path,
        )
        return self.run_command(prompt, event_callback=event_callback)

    def analyze_commit_changes(
        self,
        commit_info: dict,
        diff_content: str = "",
        event_callback: Callable[[dict], None] | None = None,
    ) -> dict:
        """
        Generate an AI summary of what changed in a commit.

        Args:
            commit_info: Dictionary with commit information
            diff_content: Git diff content for the commit
            event_callback: Optional callback for OpenCode events

        Returns:
            Dictionary with commit summary information
        """
        from .prompts import get_commit_summary_prompt

        prompt = get_commit_summary_prompt(commit_info, diff_content)

        result = self.run_command(
            prompt=prompt,
            format_type="json",
            model=self.settings.opencode_model,
            event_callback=event_callback
        )

        if result.success:
            try:
                return json.loads(result.output)
            except json.JSONDecodeError:
                return {
                    "summary": "Summary generation failed - invalid JSON response",
                    "category": "unknown",
                    "impact_level": "unknown",
                    "breaking_changes": False,
                    "details": result.output
                }
        else:
            return {
                "summary": f"Commit: {commit_info.get('message', 'Unknown')}",
                "category": "unknown",
                "impact_level": "unknown",
                "breaking_changes": False,
                "details": result.error or "Failed to generate summary"
            }

    def check_available(self) -> bool:
        """Check if OpenCode CLI is available."""
        try:
            result = subprocess.run(
                [self.settings.opencode_binary, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
