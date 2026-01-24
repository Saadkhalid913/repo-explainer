"""OpenCode wrapper for managing agent interactions."""

import json
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any, Callable
from dataclasses import dataclass, field
from enum import Enum

from .base_wrapper import BaseWrapper, BaseConfig, OutputFormat
from .project_config import OpencodeProjectConfig, AgentType


@dataclass
class OpenCodeConfig(BaseConfig):
    """Configuration for OpenCode instance."""

    model: str = "openrouter/anthropic/claude-sonnet-4-5-20250929"
    """Model to use for code analysis (format: openrouter/{provider}/{model_id})"""

    output_format: OutputFormat = OutputFormat.JSON
    """Output format (json or text)"""

    max_tokens: Optional[int] = None
    """Maximum tokens for response"""

    binary_path: str = "opencode"
    """Path to opencode binary"""

    timeout: int = 600
    """Timeout in seconds"""

    verbose: bool = False
    """Enable verbose output"""


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


class OpenCodeWrapper(BaseWrapper):
    """
    Wrapper for OpenCode CLI providing high-level interface.

    Features:
    - Initialize with working directory
    - Execute prompts with context
    - Stream events and parse output
    - Handle artifacts
    """

    config: OpenCodeConfig  # Override base type annotation

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
        config = config or OpenCodeConfig()
        super().__init__(working_dir, config)
        self.config = config  # Explicitly set with correct type
        self.project_config = project_config or OpencodeProjectConfig.default()
        self.project_config.apply(self.working_dir)

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
        full_prompt = self._build_prompt(prompt, context)
        cmd = self._build_command(full_prompt, agent_type)

        if self.config.verbose:
            prompt_preview = (
                full_prompt[:60] + "...") if len(full_prompt) > 60 else full_prompt
            cmd_parts = cmd[:-1]
            print(f"[OpenCode] Executing in {self.working_dir}")
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

            response = self._parse_output(stdout)

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

    def _parse_output(self, output: str) -> OpenCodeResponse:
        """Parse output based on configured format."""
        if self.config.output_format != OutputFormat.JSON:
            return OpenCodeResponse(success=True, output=output)
        return self._parse_json_output(output)

    def _parse_json_output(self, output: str) -> OpenCodeResponse:
        """Parse JSON event stream output."""
        events = []
        for line in output.strip().split('\n'):
            if line.strip():
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return OpenCodeResponse(success=True, output=output, events=events)

    def cleanup_artifacts(self) -> None:
        """Remove all artifacts from artifacts directory."""
        super().cleanup_artifacts()
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
