"""OpenCode CLI integration service."""

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

from rich.console import Console

from .config import get_settings

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
            error = process.stderr.read() if process.returncode != 0 else None

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
        """Run architecture analysis on the repository."""
        prompt = """Analyze this repository and generate:
1. A high-level architecture overview (architecture.md)
2. Component diagram in Mermaid format (components.mermaid)
3. Data flow diagram in Mermaid format (dataflow.mermaid)
4. Technology stack summary (tech-stack.txt)

Focus on:
- Main entry points and their responsibilities
- Core modules/packages and their relationships
- External dependencies and integrations
- Data flow between components
"""
        return self.run_command(prompt, event_callback=event_callback)

    def quick_scan(
        self, event_callback: Callable[[dict], None] | None = None
    ) -> OpenCodeResult:
        """Run a quick scan of the repository."""
        prompt = """Perform a quick scan of this repository and summarize:
1. Primary programming language(s)
2. Project structure overview
3. Main entry point(s)
4. Key dependencies
"""
        return self.run_command(prompt, event_callback=event_callback)

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
