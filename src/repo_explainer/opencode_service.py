"""OpenCode CLI integration service."""

import json
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rich.console import Console

from .config import get_settings

console = Console()


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

    def run_command(self, prompt: str, command: str | None = None) -> OpenCodeResult:
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
        ]

        if command:
            cmd.extend(["--command", command])

        if self.settings.verbose:
            console.print(f"[dim]Running: {' '.join(cmd)}[/dim]")

        try:
            result = subprocess.run(
                cmd,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minute timeout
            )

            output = result.stdout
            error = result.stderr if result.returncode != 0 else None

            # Try to parse JSON output
            artifacts = {}
            session_id = None
            if self.settings.opencode_output_format == "json":
                try:
                    parsed = json.loads(output)
                    artifacts = parsed.get("artifacts", {})
                    session_id = parsed.get("session_id")
                except json.JSONDecodeError:
                    pass

            return OpenCodeResult(
                success=result.returncode == 0,
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

    def analyze_architecture(self) -> OpenCodeResult:
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
        return self.run_command(prompt)

    def quick_scan(self) -> OpenCodeResult:
        """Run a quick scan of the repository."""
        prompt = """Perform a quick scan of this repository and summarize:
1. Primary programming language(s)
2. Project structure overview
3. Main entry point(s)
4. Key dependencies
"""
        return self.run_command(prompt)

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
