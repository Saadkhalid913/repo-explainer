"""Base wrapper class with common functionality for OpenCode and Claude Code."""

import subprocess
import shutil
from pathlib import Path
from typing import Optional, Dict
from dataclasses import dataclass
from enum import Enum


class OutputFormat(Enum):
    """Output format for agent tools."""
    JSON = "json"
    TEXT = "text"


@dataclass
class BaseConfig:
    """Base configuration for code analysis tools."""
    binary_path: str
    timeout: int = 600
    verbose: bool = False


class BaseWrapper:
    """
    Base wrapper with common functionality for CLI tools.

    Handles:
    - Binary availability checking
    - Prompt building
    - Artifact extraction and management
    - Directory validation
    """

    def __init__(self, working_dir: Path, config: BaseConfig):
        self.working_dir = Path(working_dir).resolve()
        self.config = config

        if not self.working_dir.is_dir():
            raise ValueError(f"Working directory is not a directory: {self.working_dir}")

        self._check_availability()

    def _check_availability(self) -> None:
        """Check if the binary is available."""
        try:
            result = subprocess.run(
                [self.config.binary_path, "--version"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode != 0:
                raise RuntimeError(f"Binary check failed: {result.stderr}")
        except FileNotFoundError:
            raise RuntimeError(
                f"Binary not found: {self.config.binary_path}. "
                "Please install the tool or set correct binary path."
            )
        except subprocess.TimeoutExpired:
            raise RuntimeError("Binary check timed out")

    def _build_prompt(self, prompt: str, context: Optional[str]) -> str:
        """Build complete prompt with optional context."""
        parts = []
        if context:
            parts.append("# Context\n")
            parts.append(context)
            parts.append("")
        parts.append("# Task\n")
        parts.append(prompt)
        return "\n".join(parts)

    @property
    def _artifacts_dir(self) -> Path:
        """Get artifacts directory path."""
        return self.working_dir / "repo_explainer_artifacts"

    def _extract_artifacts(self) -> Dict[str, str]:
        """Extract artifacts from repo_explainer_artifacts directory."""
        artifacts = {}
        if not self._artifacts_dir.exists():
            return artifacts

        for file_path in self._artifacts_dir.rglob("*"):
            if file_path.is_file():
                try:
                    artifacts[str(file_path.relative_to(self._artifacts_dir))] = file_path.read_text()
                except Exception:
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
        artifact_path = self._artifacts_dir / artifact_name
        if not artifact_path.exists():
            return None
        try:
            return artifact_path.read_text()
        except Exception:
            return None

    def cleanup_artifacts(self) -> None:
        """Remove all artifacts from artifacts directory."""
        if self._artifacts_dir.exists():
            shutil.rmtree(self._artifacts_dir)
