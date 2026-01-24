"""Claude Code wrapper for managing agent interactions.

This is a 1-1 API wrapper for Claude Code CLI, matching the OpenCode wrapper interface.
Claude Code is Anthropic's official CLI tool for code analysis.
"""

import json
import subprocess
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

from .base_wrapper import BaseWrapper, BaseConfig, OutputFormat
from .project_config import OpencodeProjectConfig


@dataclass
class ClaudeCodeConfig(BaseConfig):
    """Configuration for Claude Code instance."""

    model: str = "claude-sonnet-4-5-20250929"
    """Model to use for code analysis"""

    output_format: OutputFormat = OutputFormat.JSON
    """Output format (json or text)"""

    max_tokens: Optional[int] = None
    """Maximum tokens for response"""

    temperature: Optional[float] = None
    """Temperature for sampling"""

    binary_path: str = "claude"
    """Path to claude code binary"""

    timeout: int = 600
    """Timeout in seconds"""

    verbose: bool = False
    """Enable verbose output"""


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


class ClaudeCodeWrapper(BaseWrapper):
    """
    Wrapper for Claude Code CLI providing high-level interface.

    This provides the same API as OpenCodeWrapper for drop-in compatibility.

    Features:
    - Initialize with working directory
    - Execute prompts with context
    - Stream events and parse output
    - Handle artifacts
    """

    config: ClaudeCodeConfig  # Override base type annotation

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
        config = config or ClaudeCodeConfig()
        super().__init__(working_dir, config)
        self.config = config  # Explicitly set with correct type
        self.project_config = project_config or OpencodeProjectConfig.default()
        self.project_config.apply(self.working_dir)

    def execute(
        self,
        prompt: str,
        context: Optional[str] = None,
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

            response = self._parse_output(stdout)

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

    def _parse_output(self, output: str) -> ClaudeCodeResponse:
        """Parse output based on configured format."""
        if self.config.output_format != OutputFormat.JSON:
            return ClaudeCodeResponse(success=True, output=output)
        return self._parse_json_output(output)

    def _parse_json_output(self, output: str) -> ClaudeCodeResponse:
        """Parse JSON event stream output."""
        events = []
        for line in output.strip().split('\n'):
            if line.strip():
                try:
                    events.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        return ClaudeCodeResponse(success=True, output=output, events=events)

    def cleanup_artifacts(self) -> None:
        """Remove all artifacts from artifacts directory."""
        super().cleanup_artifacts()
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
