"""Claude Code wrapper for managing agent interactions.

This is a 1-1 API wrapper for Claude Code CLI, matching the OpenCode wrapper interface.
Claude Code is Anthropic's official CLI tool for code analysis.
"""

import shutil
import subprocess
import json
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

from .project_config import OpencodeProjectConfig


class OutputFormat(Enum):
    """Claude Code output format."""
    JSON = "json"
    TEXT = "text"


@dataclass
class ClaudeCodeConfig:
    """Configuration for Claude Code instance."""

    binary_path: str = "claude"
    """Path to claude code binary"""

    model: str = "claude-sonnet-4-5-20250929"
    """Model to use for code analysis"""

    output_format: OutputFormat = OutputFormat.JSON
    """Output format (json or text)"""

    timeout: int = 600
    """Timeout in seconds"""

    verbose: bool = False
    """Enable verbose output"""

    max_tokens: Optional[int] = None
    """Maximum tokens for response"""

    temperature: Optional[float] = None
    """Temperature for sampling"""


@dataclass
class ClaudeCodeResponse:
    """Response from Claude Code execution."""

    success: bool
    """Whether execution was successful"""

    output: str
    """Raw output from Claude Code"""

    events: List[Dict[str, Any]] = field(default_factory=list)
    """Parsed events (if JSON format)"""

    error: Optional[str] = None
    """Error message if failed"""

    artifacts: Dict[str, str] = field(default_factory=dict)
    """Generated artifacts (file_path -> content)"""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional metadata"""


class ClaudeCodeWrapper:
    """
    Wrapper for Claude Code CLI providing high-level interface.

    This provides the same API as OpenCodeWrapper for drop-in compatibility.

    Features:
    - Initialize with working directory
    - Execute prompts with context
    - Stream events and parse output
    - Handle artifacts
    """

    def __init__(
        self,
        working_dir: Path,
        config: Optional[ClaudeCodeConfig] = None,
        project_config: Optional[OpencodeProjectConfig] = None,
    ):
        """
        Initialize Claude Code instance.

        Args:
            working_dir: Directory where Claude Code operates
            config: Configuration for Claude Code
            project_config: Optional project configuration helpers
        """
        self.working_dir = Path(working_dir).resolve()
        self.config = config or ClaudeCodeConfig()
        self.project_config = project_config or OpencodeProjectConfig.default()

        # Validate working directory
        if not self.working_dir.exists():
            raise ValueError(
                f"Working directory does not exist: {self.working_dir}")

        if not self.working_dir.is_dir():
            raise ValueError(
                f"Working directory is not a directory: {self.working_dir}")

        self.project_config.apply(self.working_dir)

        # Check Claude Code availability
        self._check_availability()

    def _check_availability(self) -> None:
        """Check if Claude Code is available."""
        try:
            result = subprocess.run(
                [self.config.binary_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"Claude Code binary check failed: {result.stderr}")
        except FileNotFoundError:
            raise RuntimeError(
                f"Claude Code binary not found: {self.config.binary_path}. "
                "Please install Claude Code CLI or set correct binary path."
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("Claude Code binary check timed out")

    def execute(
        self,
        prompt: str,
        context: Optional[str] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> ClaudeCodeResponse:
        """
        Execute a prompt with Claude Code.

        Args:
            prompt: The prompt to execute
            context: Additional context to provide
            progress_callback: Optional callback for progress updates

        Returns:
            ClaudeCodeResponse with results
        """
        # Build full prompt
        full_prompt = self._build_prompt(prompt, context)

        # Build command
        cmd = self._build_command()

        if self.config.verbose:
            print(f"[Claude Code] Executing in {self.working_dir}")
            print(f"[Claude Code] Command: {' '.join(cmd)}")

        process = None
        try:
            # Execute Claude Code
            process = subprocess.Popen(
                cmd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.working_dir,
                text=True,
            )

            stdout, stderr = process.communicate(
                input=full_prompt,
                timeout=self.config.timeout
            )

            if process.returncode != 0:
                return ClaudeCodeResponse(
                    success=False,
                    output=stdout,
                    error=f"Claude Code failed with code {process.returncode}: {stderr}",
                )

            # Parse output
            response = self._parse_output(stdout, progress_callback)

            # Extract artifacts
            response.artifacts = self._extract_artifacts()

            return response

        except subprocess.TimeoutExpired:
            if process:
                process.kill()
            return ClaudeCodeResponse(
                success=False,
                output="",
                error=f"Claude Code timed out after {self.config.timeout} seconds",
            )
        except Exception as e:
            return ClaudeCodeResponse(
                success=False,
                output="",
                error=f"Claude Code execution failed: {str(e)}",
            )

    def _build_prompt(
        self,
        prompt: str,
        context: Optional[str],
    ) -> str:
        """Build complete prompt with optional context."""
        parts = []

        if context:
            parts.append("# Context\n")
            parts.append(context)
            parts.append("")

        parts.append("# Task\n")
        parts.append(prompt)

        return "\n".join(parts)

    def _build_command(self) -> List[str]:
        """Build Claude Code command."""
        cmd = [
            self.config.binary_path,
            "--model", self.config.model,
            "--output-format", self.config.output_format.value,
        ]

        if self.config.max_tokens:
            cmd.extend(["--max-tokens", str(self.config.max_tokens)])

        if self.config.temperature is not None:
            cmd.extend(["--temperature", str(self.config.temperature)])

        return cmd

    def _parse_output(
        self,
        output: str,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> ClaudeCodeResponse:
        """Parse Claude Code output."""
        if self.config.output_format == OutputFormat.JSON:
            return self._parse_json_output(output, progress_callback)
        else:
            return ClaudeCodeResponse(
                success=True,
                output=output,
            )

    def _parse_json_output(
        self,
        output: str,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> ClaudeCodeResponse:
        """Parse JSON event stream output."""
        events = []
        lines = output.strip().split('\n')

        for line in lines:
            if not line.strip():
                continue

            try:
                event = json.loads(line)
                events.append(event)

                if progress_callback:
                    progress_callback(event)

            except json.JSONDecodeError:
                # Skip non-JSON lines
                continue

        return ClaudeCodeResponse(
            success=True,
            output=output,
            events=events,
        )

    def _extract_artifacts(self) -> Dict[str, str]:
        """Extract artifacts from repo_explainer_artifacts directory."""
        artifacts = {}
        artifacts_dir = self.working_dir / "repo_explainer_artifacts"

        if not artifacts_dir.exists():
            return artifacts

        # Recursively find all files
        for file_path in artifacts_dir.rglob("*"):
            if file_path.is_file():
                relative_path = file_path.relative_to(artifacts_dir)
                try:
                    content = file_path.read_text()
                    artifacts[str(relative_path)] = content
                except Exception:
                    # Skip binary files or unreadable files
                    continue

        return artifacts

    def get_artifact(self, artifact_name: str) -> Optional[str]:
        """
        Get a specific artifact by name.

        Args:
            artifact_name: Name/path of artifact

        Returns:
            Artifact content or None if not found
        """
        artifacts_dir = self.working_dir / "repo_explainer_artifacts"
        artifact_path = artifacts_dir / artifact_name

        if not artifact_path.exists():
            return None

        try:
            return artifact_path.read_text()
        except Exception:
            return None

    def cleanup_artifacts(self) -> None:
        """Remove all artifacts from artifacts directory."""

        artifacts_dir = self.working_dir / "repo_explainer_artifacts"
        if artifacts_dir.exists():
            shutil.rmtree(artifacts_dir)

        self.project_config.cleanup(self.working_dir)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ClaudeCodeWrapper(working_dir={self.working_dir}, "
            f"model={self.config.model})"
        )


# Convenience functions

def create_claude_code_wrapper(
    working_dir: Path,
    model: str = "claude-sonnet-4-5-20250929",
    project_config: Optional[OpencodeProjectConfig] = None,
    verbose: bool = False,
) -> ClaudeCodeWrapper:
    """
    Create a Claude Code wrapper with common defaults.

    Args:
        working_dir: Directory where Claude Code operates
        model: Model to use
        project_config: Optional custom project config
        verbose: Enable verbose output

    Returns:
        Configured ClaudeCodeWrapper instance
    """
    agent_config = ClaudeCodeConfig(
        model=model,
        verbose=verbose,
    )

    project_cfg = project_config or OpencodeProjectConfig.default()

    return ClaudeCodeWrapper(
        working_dir=working_dir,
        config=agent_config,
        project_config=project_cfg,
    )
