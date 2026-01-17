"""Output manager for saving analysis results."""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console

from .doc_composer import DocComposer
from .opencode_service import OpenCodeResult

console = Console()

# Standard OpenCode artifact filenames
OPENCODE_ARTIFACTS = [
    "architecture.md",
    "components.mermaid",
    "dataflow.mermaid",
    "tech-stack.txt",
]


class OutputManager:
    """Manages output files and directories for analysis results."""

    def __init__(self, output_dir: Path):
        """
        Initialize the output manager.

        Args:
            output_dir: Directory to write output files
        """
        self.output_dir = output_dir

    def ensure_directories(self) -> None:
        """Create output directory structure if it doesn't exist."""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Create organized directory structure
        (self.output_dir / "src" / "raw").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "src" / "logs").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "diagrams").mkdir(exist_ok=True)
        (self.output_dir / "architecture").mkdir(exist_ok=True)
        (self.output_dir / "components").mkdir(exist_ok=True)
        (self.output_dir / "dataflow").mkdir(exist_ok=True)
        (self.output_dir / "tech-stack").mkdir(exist_ok=True)

    def write_analysis_result(
        self,
        result: OpenCodeResult,
        repo_path: Path,
        depth: str,
    ) -> dict[str, Path]:
        """
        Write analysis results to output directory.

        Args:
            result: OpenCode analysis result
            repo_path: Path to the analyzed repository
            depth: Analysis depth (quick, standard, deep)

        Returns:
            Dictionary mapping output types to file paths
        """
        self.ensure_directories()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        output_files = {}

        # Copy OpenCode artifacts from the analyzed repository
        opencode_artifacts = self._copy_opencode_artifacts(repo_path)
        output_files.update(opencode_artifacts)

        # Write raw output to src/logs/
        raw_output_file = self.output_dir / "src" / "logs" / f"analysis_{timestamp}.txt"
        raw_output_file.write_text(result.output)
        output_files["raw_output"] = raw_output_file

        # Write metadata to src/logs/
        metadata = {
            "timestamp": timestamp,
            "repository": str(repo_path),
            "depth": depth,
            "session_id": result.session_id,
            "success": result.success,
            "error": result.error,
            "artifacts": result.artifacts,
            "opencode_artifacts": [str(p) for p in opencode_artifacts.values()],
        }

        metadata_file = self.output_dir / "src" / "logs" / f"metadata_{timestamp}.json"
        metadata_file.write_text(json.dumps(metadata, indent=2))
        output_files["metadata"] = metadata_file

        # Write summary to src/
        summary_file = self.output_dir / "src" / "ANALYSIS_SUMMARY.md"
        summary_content = self._generate_summary(
            repo_path=repo_path,
            depth=depth,
            result=result,
            timestamp=timestamp,
            opencode_artifacts=opencode_artifacts,
        )
        summary_file.write_text(summary_content)
        output_files["summary"] = summary_file

        # Parse and save structured output to src/
        if result.success and result.output:
            structured_file = self.output_dir / "src" / f"analysis_{depth}.json"
            self._write_structured_output(result.output, structured_file)
            output_files["structured"] = structured_file

        # Compose coherent documentation
        if result.success and opencode_artifacts:
            composer = DocComposer(self.output_dir)
            composed_files = composer.compose(
                repo_path=repo_path,
                depth=depth,
                session_id=result.session_id,
                timestamp=timestamp,
            )
            output_files.update(composed_files)

        return output_files

    def _copy_opencode_artifacts(self, repo_path: Path) -> dict[str, Path]:
        """
        Copy OpenCode-generated artifacts from analyzed repository to output directory.

        Args:
            repo_path: Path to the analyzed repository

        Returns:
            Dictionary mapping artifact names to their output paths
        """
        artifacts = {}

        for artifact_name in OPENCODE_ARTIFACTS:
            source_file = repo_path / artifact_name
            if source_file.exists():
                # Copy to src/raw/ directory
                dest_file = self.output_dir / "src" / "raw" / artifact_name
                shutil.copy2(source_file, dest_file)
                artifacts[artifact_name.replace(".", "_")] = dest_file

                if self.output_dir.absolute() != repo_path.absolute():
                    console.print(f"[dim]  Copied: {artifact_name}[/dim]")

        return artifacts

    def _generate_summary(
        self,
        repo_path: Path,
        depth: str,
        result: OpenCodeResult,
        timestamp: str,
        opencode_artifacts: dict[str, Path] | None = None,
    ) -> str:
        """
        Generate a markdown summary of the analysis.

        Args:
            repo_path: Path to analyzed repository
            depth: Analysis depth
            result: OpenCode result
            timestamp: Timestamp string

        Returns:
            Markdown-formatted summary
        """
        summary = f"""# Repository Analysis Summary

**Repository:** {repo_path}
**Analysis Depth:** {depth}
**Timestamp:** {timestamp}
**Status:** {'✅ Success' if result.success else '❌ Failed'}

"""

        if result.session_id:
            summary += f"**Session ID:** `{result.session_id}`\n\n"

        if result.error:
            summary += f"## Error\n\n```\n{result.error}\n```\n\n"

        # List OpenCode artifacts (the human-readable docs!)
        if opencode_artifacts:
            summary += "## Generated Documentation\n\n"
            summary += "**Human-Readable Artifacts:**\n"
            for artifact_name, artifact_path in opencode_artifacts.items():
                filename = artifact_path.name
                description = self._get_artifact_description(filename)
                summary += f"- `{filename}` - {description}\n"
            summary += "\n"

        # List technical artifacts
        summary += "## Technical Output Files\n\n"
        summary += "- `logs/analysis_*.txt` - Raw OpenCode output\n"
        summary += "- `logs/metadata_*.json` - Analysis metadata\n"
        summary += "- `analysis_*.json` - Structured output (JSON events)\n\n"

        if result.artifacts:
            summary += "**OpenCode Session Artifacts:**\n"
            for name, path in result.artifacts.items():
                summary += f"- **{name}:** `{path}`\n"
            summary += "\n"

        # Next steps
        summary += "## Next Steps\n\n"
        summary += "**Start here:**\n"
        summary += "1. Open `index.md` for the main documentation entry point\n"
        summary += "2. Browse organized subpages (components.md, dataflow.md, tech-stack.md)\n"
        summary += "3. View rendered diagrams in the `diagrams/` directory\n\n"

        if not opencode_artifacts:
            summary += "**Alternative:**\n"
            summary += "Review the technical output files for:\n"
            summary += "- Repository structure insights\n"
            summary += "- Technology stack information\n"
            summary += "- Architecture patterns\n\n"

        return summary

    def _get_artifact_description(self, filename: str) -> str:
        """Get human-readable description for an artifact."""
        descriptions = {
            "architecture.md": "Architecture overview and design patterns",
            "components.mermaid": "Component relationship diagram",
            "dataflow.mermaid": "Data flow visualization",
            "tech-stack.txt": "Technology stack summary",
        }
        return descriptions.get(filename, "Analysis artifact")

    def _write_structured_output(self, output: str, file_path: Path) -> None:
        """
        Parse and write structured JSON output.

        Args:
            output: Raw output string from OpenCode
            file_path: Path to write structured output
        """
        # OpenCode outputs newline-delimited JSON events
        # Parse each line as a separate JSON object
        events = []
        for line in output.strip().split("\n"):
            if line.strip():
                try:
                    event = json.loads(line)
                    events.append(event)
                except json.JSONDecodeError:
                    # Skip non-JSON lines
                    continue

        if events:
            file_path.write_text(json.dumps(events, indent=2))

    def get_output_location(self) -> str:
        """
        Get a human-readable description of the output location.

        Returns:
            String describing where outputs are saved
        """
        return f"{self.output_dir.absolute()}"
