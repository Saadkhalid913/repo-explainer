"""Output manager for saving analysis results."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console

from .opencode_service import OpenCodeResult

console = Console()


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
        (self.output_dir / "logs").mkdir(exist_ok=True)

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

        # Write raw output
        raw_output_file = self.output_dir / "logs" / f"analysis_{timestamp}.txt"
        raw_output_file.write_text(result.output)
        output_files["raw_output"] = raw_output_file

        # Write metadata
        metadata = {
            "timestamp": timestamp,
            "repository": str(repo_path),
            "depth": depth,
            "session_id": result.session_id,
            "success": result.success,
            "error": result.error,
            "artifacts": result.artifacts,
        }

        metadata_file = self.output_dir / "logs" / f"metadata_{timestamp}.json"
        metadata_file.write_text(json.dumps(metadata, indent=2))
        output_files["metadata"] = metadata_file

        # Write summary
        summary_file = self.output_dir / "ANALYSIS_SUMMARY.md"
        summary_content = self._generate_summary(
            repo_path=repo_path,
            depth=depth,
            result=result,
            timestamp=timestamp,
        )
        summary_file.write_text(summary_content)
        output_files["summary"] = summary_file

        # Parse and save structured output if available
        if result.success and result.output:
            structured_file = self.output_dir / f"analysis_{depth}.json"
            self._write_structured_output(result.output, structured_file)
            output_files["structured"] = structured_file

        return output_files

    def _generate_summary(
        self,
        repo_path: Path,
        depth: str,
        result: OpenCodeResult,
        timestamp: str,
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

        if result.artifacts:
            summary += "## Artifacts\n\n"
            for name, path in result.artifacts.items():
                summary += f"- **{name}:** `{path}`\n"
            summary += "\n"

        summary += """## Output Files

- `logs/analysis_*.txt` - Raw OpenCode output
- `logs/metadata_*.json` - Analysis metadata
- `analysis_*.json` - Structured output (JSON events)

## Next Steps

The analysis has been completed. Review the output files above for:
- Repository structure insights
- Technology stack information
- Architecture patterns (if standard/deep analysis)

For detailed analysis results, see the structured JSON output.
"""

        return summary

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
