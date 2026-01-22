"""OpenCode wrapper for managing agent interactions."""

import subprocess
import json
import shutil
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

from .project_config import OpencodeProjectConfig, AgentType


class OutputFormat(Enum):
    """OpenCode output format."""
    JSON = "json"
    TEXT = "text"


@dataclass
class OpenCodeConfig:
    """Configuration for OpenCode instance."""

    binary_path: str = "opencode"
    """Path to opencode binary"""

    model: str = "openrouter/anthropic/claude-sonnet-4-5-20250929"
    """Model to use for code analysis (format: openrouter/{provider}/{model_id})"""

    output_format: OutputFormat = OutputFormat.JSON
    """Output format (json or text)"""

    timeout: int = 600
    """Timeout in seconds"""

    verbose: bool = False
    """Enable verbose output"""

    max_tokens: Optional[int] = None
    """Maximum tokens for response"""


@dataclass
class OpenCodeResponse:
    """Response from OpenCode execution."""

    success: bool
    """Whether execution was successful"""

    output: str
    """Raw output from OpenCode"""

    events: List[Dict[str, Any]] = field(default_factory=list)
    """Parsed events (if JSON format)"""

    error: Optional[str] = None
    """Error message if failed"""

    artifacts: Dict[str, str] = field(default_factory=dict)
    """Generated artifacts (file_path -> content)"""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional metadata"""


class OpenCodeWrapper:
    """
    Wrapper for OpenCode CLI providing high-level interface.

    Features:
    - Initialize with working directory
    - Execute prompts with context
    - Stream events and parse output
    - Handle artifacts
    """

    def __init__(
        self,
        working_dir: Path,
        config: Optional[OpenCodeConfig] = None,
        project_config: Optional[OpencodeProjectConfig] = None,
    ):
        """
        Initialize OpenCode instance.

        Args:
            working_dir: Directory where OpenCode operates
            config: Configuration for OpenCode
            project_config: Optional project configuration helpers
        """
        self.working_dir = Path(working_dir).resolve()
        print(f"Working dir: {self.working_dir}")
        self.config = config or OpenCodeConfig()
        # Use default project config if not provided
        self.project_config = project_config or OpencodeProjectConfig.default()

        # Validate working directory
        if not self.working_dir.exists():
            raise ValueError(
                f"Working directory does not exist: {self.working_dir}")

        if not self.working_dir.is_dir():
            raise ValueError(
                f"Working directory is not a directory: {self.working_dir}")

        # Prepare project config files in the working directory
        self.project_config.apply(self.working_dir)

        # Check OpenCode availability
        self._check_availability()

    def _check_availability(self) -> None:
        """Check if OpenCode is available."""
        try:
            result = subprocess.run(
                [self.config.binary_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    f"OpenCode binary check failed: {result.stderr}")
        except FileNotFoundError:
            raise RuntimeError(
                f"OpenCode binary not found: {self.config.binary_path}. "
                "Please install OpenCode or set correct binary path."
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("OpenCode binary check timed out")

    def execute(
        self,
        prompt: str,
        agent_type: AgentType,
        context: Optional[str] = None,
        stream_output: bool = False,
        stream_callback: Optional[Callable[[str], None]] = None,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> OpenCodeResponse:
        """
        Execute a prompt with OpenCode using the specified agent.

        Args:
            prompt: The prompt to execute
            agent_type: The agent type to use for this execution
            context: Additional context to provide
            progress_callback: Optional callback for progress updates

        Returns:
            OpenCodeResponse with results
        """
        # Build full prompt
        full_prompt = self._build_prompt(prompt, context)
        print(f"[OpenCode] Full prompt: {full_prompt}")

        # Build command with prompt as positional argument and agent selection
        cmd = self._build_command(full_prompt, agent_type)

        print(f"[OpenCode] Command: {' '.join(cmd)}")

        if self.config.verbose:
            print(f"[OpenCode] Executing in {self.working_dir}")
            # Show command structure (model and format, prompt truncated)
            cmd_parts = cmd[:-1]  # All parts except prompt
            prompt_preview = full_prompt[:60] + \
                "..." if len(full_prompt) > 60 else full_prompt
            print(
                f"[OpenCode] Command: {' '.join(cmd_parts)} \"{prompt_preview}\"")

        process = None
        try:
            # Execute OpenCode (prompt is passed as positional argument, not stdin)
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=self.working_dir,
                text=True,
                bufsize=1,  # Line buffered for streaming
            )

            output_lines = []

            # Stream output line by line
            if process.stdout:
                for line in process.stdout:
                    output_lines.append(line)
                    if stream_output:
                        print(line, end="")
                    if stream_callback:
                        stream_callback(line)
                    # Parse and callback for each JSON event
                    if progress_callback and self.config.output_format == OutputFormat.JSON:
                        try:
                            event = json.loads(line.strip())
                            progress_callback(event)
                        except json.JSONDecodeError:
                            pass

            # Wait for process to complete
            process.wait(timeout=self.config.timeout)

            stdout = "".join(output_lines)
            # Read stderr only if process failed
            stderr = ""
            if process.returncode != 0 and process.stderr:
                stderr = process.stderr.read()

            if process.returncode != 0:
                return OpenCodeResponse(
                    success=False,
                    output=stdout,
                    error=f"OpenCode failed with code {process.returncode}: {stderr}",
                )

            # Parse output
            response = self._parse_output(stdout, progress_callback)

            # Extract artifacts
            response.artifacts = self._extract_artifacts()

            return response

        except subprocess.TimeoutExpired:
            if process:
                process.kill()
            return OpenCodeResponse(
                success=False,
                output="",
                error=f"OpenCode timed out after {self.config.timeout} seconds",
            )
        except Exception as e:
            return OpenCodeResponse(
                success=False,
                output="",
                error=f"OpenCode execution failed: {str(e)}",
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

    def _build_command(self, prompt: str, agent_type: AgentType) -> List[str]:
        """
        Build OpenCode command with agent selection.

        Args:
            prompt: The prompt to pass as positional argument
            agent_type: The agent type to use for execution

        Returns:
            Command list with prompt as positional argument
        """
        cmd = [
            self.config.binary_path,
            "run",  # OpenCode requires 'run' subcommand
            "--model", self.config.model,  # Model flag before prompt
            "--format", self.config.output_format.value,  # Use --format, not --output-format
        ]

        # Add agent flag for OpenCode 2026 standard
        cmd.extend(["--agent", agent_type.value])

        # Add prompt as positional argument
        cmd.append(prompt)

        # Optional parameters
        if self.config.max_tokens:
            cmd.extend(["--max-tokens", str(self.config.max_tokens)])

        return cmd

    def _parse_output(
        self,
        output: str,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> OpenCodeResponse:
        """Parse OpenCode output."""
        if self.config.output_format == OutputFormat.JSON:
            return self._parse_json_output(output, progress_callback)
        else:
            return OpenCodeResponse(
                success=True,
                output=output,
            )

    def _parse_json_output(
        self,
        output: str,
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
    ) -> OpenCodeResponse:
        """
        Parse JSON event stream output.

        Note: progress_callback is already called during streaming in execute(),
        so we only parse events here without calling the callback again.
        """
        events = []
        lines = output.strip().split('\n')

        for line in lines:
            if not line.strip():
                continue

            try:
                event = json.loads(line)
                events.append(event)
                # Note: progress_callback is called during streaming, not here

            except json.JSONDecodeError:
                # Skip non-JSON lines
                continue

        return OpenCodeResponse(
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

    def __del__(self) -> None:
        """Ensure temporary project config files are removed."""
        try:
            self.project_config.cleanup(self.working_dir)
        except Exception:
            pass

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"OpenCodeWrapper(working_dir={self.working_dir}, "
            f"model={self.config.model})"
        )


# Convenience functions

def create_opencode_wrapper(
    working_dir: Path,
    model: str = "openrouter/anthropic/claude-sonnet-4-5-20250929",
    project_config: Optional[OpencodeProjectConfig] = None,
    verbose: bool = False,
) -> OpenCodeWrapper:
    """
    Create an OpenCode wrapper with common defaults.

    The wrapper sets up a complete OpenCode workspace with all agents and skills.
    The specific agent is selected when calling execute() by passing agent_type.

    Args:
        working_dir: Directory where OpenCode operates
        model: Model to use
        project_config: Optional custom project config
        verbose: Enable verbose output

    Returns:
        Configured OpenCodeWrapper instance

    Example:
        ```python
        wrapper = create_opencode_wrapper(Path("/repo"), verbose=True)

        # Execute with exploration agent
        response = wrapper.execute(
            prompt="Analyze this repository",
            agent_type=AgentType.EXPLORATION
        )

        # Execute with documentation agent
        response = wrapper.execute(
            prompt="Generate documentation",
            agent_type=AgentType.DOCUMENTATION
        )
        ```
    """

    agent_config = OpenCodeConfig(
        model=model,
        verbose=verbose,
    )

    # Use provided config or create default
    project_cfg = project_config or OpencodeProjectConfig.default()

    return OpenCodeWrapper(
        working_dir=working_dir,
        config=agent_config,
        project_config=project_cfg,
    )
