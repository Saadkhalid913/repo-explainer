"""Output manager for file writing, metadata, and logging."""

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from repo_explainer.config import AnalysisDepth, get_settings
from repo_explainer.models import (
    AnalysisResult,
    ComponentInfo,
    DiagramInfo,
    OpenCodeSession,
    RepositoryInfo,
)


class OutputManager:
    """Manages output directory structure, metadata, and logging."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.metadata_dir = output_dir / "metadata"
        self._ensure_directories()

    def _ensure_directories(self) -> None:
        """Create necessary directories."""
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)

    def write_analysis_log(
        self,
        repo_info: RepositoryInfo,
        depth: AnalysisDepth,
        sessions: list[OpenCodeSession],
        errors: list[str],
    ) -> Path:
        """Write the analysis log file."""
        settings = get_settings()

        log_data = {
            "analysis_timestamp": datetime.now().isoformat(),
            "repo_explainer_version": "0.1.0",
            "repository": {
                "name": repo_info.name,
                "path": str(repo_info.path),
                "primary_language": (
                    repo_info.primary_language.value if repo_info.primary_language else None
                ),
                "languages": [l.value for l in repo_info.languages],
                "size_category": repo_info.size_category.value,
                "file_count": repo_info.file_count,
                "total_lines": repo_info.total_lines,
                "git_remote": repo_info.git_remote,
                "git_branch": repo_info.git_branch,
                "git_commit": repo_info.git_commit,
            },
            "configuration": {
                "depth": depth.value,
                "llm_model": settings.llm_model,
                "opencode_binary": settings.opencode_binary,
                "use_claude_fallback": settings.use_claude_fallback,
            },
            "sessions": [
                {
                    "session_id": s.session_id,
                    "command": s.command,
                    "started_at": s.started_at.isoformat(),
                    "ended_at": s.ended_at.isoformat() if s.ended_at else None,
                    "exit_code": s.exit_code,
                    "output_files": [str(f) for f in s.output_files],
                }
                for s in sessions
            ],
            "errors": errors,
        }

        log_path = self.metadata_dir / "analysis-log.json"
        log_path.write_text(json.dumps(log_data, indent=2))
        return log_path

    def write_config_snapshot(self) -> Path:
        """Write a snapshot of the configuration used."""
        settings = get_settings()

        config_data = {
            "llm_model": settings.llm_model,
            "llm_base_url": settings.llm_base_url,
            "default_depth": settings.default_depth.value,
            "output_format": settings.output_format.value,
            "opencode_binary": settings.opencode_binary,
            "use_claude_fallback": settings.use_claude_fallback,
            "claude_binary": settings.claude_binary,
            "max_files": settings.max_files,
            "max_tokens_per_request": settings.max_tokens_per_request,
            "verbose": settings.verbose,
        }

        config_path = self.metadata_dir / "config.yaml"

        # Write as YAML-like format
        lines = ["# Configuration snapshot for this analysis run\n"]
        for key, value in config_data.items():
            lines.append(f"{key}: {value}\n")

        config_path.write_text("".join(lines))
        return config_path

    def load_previous_analysis(self) -> Optional[dict[str, Any]]:
        """Load previous analysis metadata if available."""
        log_path = self.metadata_dir / "analysis-log.json"
        if not log_path.exists():
            return None

        try:
            return json.loads(log_path.read_text())
        except (json.JSONDecodeError, OSError):
            return None

    def get_previous_commit(self) -> Optional[str]:
        """Get the commit hash from the previous analysis."""
        previous = self.load_previous_analysis()
        if previous:
            return previous.get("repository", {}).get("git_commit")
        return None

    def write_session_output(
        self,
        session: OpenCodeSession,
        prefix: str = "",
    ) -> list[Path]:
        """Write session stdout/stderr to log files."""
        written_files: list[Path] = []

        if session.stdout:
            stdout_path = self.metadata_dir / f"{prefix}{session.session_id}_stdout.txt"
            stdout_path.write_text(session.stdout)
            written_files.append(stdout_path)

        if session.stderr:
            stderr_path = self.metadata_dir / f"{prefix}{session.session_id}_stderr.txt"
            stderr_path.write_text(session.stderr)
            written_files.append(stderr_path)

        return written_files

    def create_analysis_result(
        self,
        repo_info: RepositoryInfo,
        components: list[ComponentInfo],
        diagrams: list[DiagramInfo],
        tech_stack: list[str],
        patterns: list[str],
        opencode_session_id: Optional[str] = None,
        errors: Optional[list[str]] = None,
    ) -> AnalysisResult:
        """Create an AnalysisResult object."""
        return AnalysisResult(
            repository={
                "name": repo_info.name,
                "path": str(repo_info.path),
                "primary_language": (
                    repo_info.primary_language.value if repo_info.primary_language else None
                ),
                "languages": [l.value for l in repo_info.languages],
                "size_category": repo_info.size_category.value,
                "file_count": repo_info.file_count,
                "total_lines": repo_info.total_lines,
                "git_remote": repo_info.git_remote,
                "git_branch": repo_info.git_branch,
                "git_commit": repo_info.git_commit,
            },
            components=[
                {
                    "id": c.id,
                    "name": c.name,
                    "type": c.component_type,
                    "path": str(c.path),
                    "description": c.description,
                    "files": [str(f) for f in c.files],
                }
                for c in components
            ],
            diagrams=[
                {
                    "type": d.diagram_type.value,
                    "title": d.title,
                    "output_path": str(d.output_path) if d.output_path else None,
                }
                for d in diagrams
            ],
            tech_stack=tech_stack,
            patterns_detected=patterns,
            analysis_timestamp=datetime.now(),
            opencode_session_id=opencode_session_id,
            errors=errors or [],
        )

    def export_result_json(self, result: AnalysisResult) -> Path:
        """Export the analysis result as JSON."""
        result_path = self.output_dir / "analysis-result.json"
        result_path.write_text(result.model_dump_json(indent=2))
        return result_path
