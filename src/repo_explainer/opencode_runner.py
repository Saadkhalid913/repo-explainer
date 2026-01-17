"""OpenCode CLI runner for repository analysis."""

import json
import subprocess
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from rich.console import Console

from repo_explainer.config import AnalysisDepth, get_settings
from repo_explainer.models import OpenCodeSession


class OpenCodeRunner:
    """Runs OpenCode CLI commands for repository analysis."""

    # Map analysis depth to OpenCode command names
    DEPTH_COMMANDS = {
        AnalysisDepth.QUICK: "project:quick-scan",
        AnalysisDepth.STANDARD: "project:analyze-architecture",
        AnalysisDepth.DEEP: "project:deep-scan",
    }

    def __init__(self, console: Optional[Console] = None):
        self.settings = get_settings()
        self.console = console or Console()
        self.sessions: list[OpenCodeSession] = []

    def is_available(self) -> bool:
        """Check if OpenCode CLI is available."""
        try:
            result = subprocess.run(
                [self.settings.opencode_binary, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def get_config_info(self) -> Optional[dict[str, str]]:
        """Get OpenCode configuration information, including model if available."""
        info = {}
        try:
            # Try to get version info
            version_result = subprocess.run(
                [self.settings.opencode_binary, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            if version_result.returncode == 0:
                info["version"] = version_result.stdout.strip()
            
            # Try to get config (if OpenCode supports it)
            try:
                config_result = subprocess.run(
                    [self.settings.opencode_binary, "config", "show"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                if config_result.returncode == 0:
                    info["config"] = config_result.stdout.strip()
            except (FileNotFoundError, subprocess.TimeoutExpired):
                pass
            
            return info if info else None
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return None

    def run_analysis(
        self,
        repo_path: Path,
        depth: AnalysisDepth,
        output_dir: Path,
        context: Optional[str] = None,
    ) -> OpenCodeSession:
        """
        Run OpenCode analysis on a repository.

        Args:
            repo_path: Path to the repository
            depth: Analysis depth level
            output_dir: Directory for output files
            context: Optional context/prompt to pass to OpenCode

        Returns:
            OpenCodeSession with results
        """
        session_id = str(uuid.uuid4())[:8]
        command_name = self.DEPTH_COMMANDS[depth]

        # Build the prompt for OpenCode
        prompt = self._build_prompt(repo_path, depth, context)

        session = OpenCodeSession(
            session_id=session_id,
            command=command_name,
            started_at=datetime.now(),
        )

        try:
            # Run OpenCode with the analysis prompt using 'run' command
            result = subprocess.run(
                [
                    self.settings.opencode_binary,
                    "run",
                    prompt,
                ],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                timeout=600,  # 10 minute timeout
            )

            session.ended_at = datetime.now()
            session.exit_code = result.returncode
            session.stdout = result.stdout
            session.stderr = result.stderr

            if result.returncode == 0:
                # Parse and save outputs
                session.output_files = self._process_output(
                    result.stdout, output_dir, session_id
                )
            else:
                self.console.print(
                    f"[yellow]OpenCode returned non-zero exit code: {result.returncode}[/]"
                )
                if result.stderr:
                    self.console.print(f"[dim]{result.stderr}[/]")

        except subprocess.TimeoutExpired:
            session.ended_at = datetime.now()
            session.stderr = "OpenCode command timed out after 10 minutes"
            self.console.print("[red]OpenCode analysis timed out[/]")

        except FileNotFoundError:
            session.ended_at = datetime.now()
            session.stderr = f"OpenCode binary not found: {self.settings.opencode_binary}"
            self.console.print(f"[red]{session.stderr}[/]")

        self.sessions.append(session)
        return session

    def _build_prompt(
        self, repo_path: Path, depth: AnalysisDepth, context: Optional[str]
    ) -> str:
        """Build the analysis prompt for OpenCode."""
        base_prompt = f"""\
Analyze this repository and generate comprehensive documentation.

Repository: {repo_path.name}

Analysis depth: {depth.value}

Please generate the following outputs:
1. architecture.md - High-level architecture overview
2. components.mermaid - Mermaid diagram of component relationships
3. dataflow.mermaid - Mermaid diagram of data flow
4. tech-stack.txt - List of technologies used

Focus on:
- Identifying the main components and their responsibilities
- Mapping dependencies between components
- Documenting the technology stack
- Explaining the overall architecture pattern
"""

        if context:
            base_prompt += f"\n\nAdditional context:\n{context}"

        return base_prompt

    def _process_output(
        self, stdout: str, output_dir: Path, session_id: str
    ) -> list[Path]:
        """Process OpenCode output and save files."""
        output_files: list[Path] = []

        try:
            # Try to parse as JSON
            data = json.loads(stdout)

            # Handle different output formats
            if isinstance(data, dict):
                # Check for file outputs
                if "files" in data:
                    for file_info in data["files"]:
                        file_path = output_dir / file_info.get("name", f"output_{session_id}.md")
                        file_path.parent.mkdir(parents=True, exist_ok=True)
                        file_path.write_text(file_info.get("content", ""))
                        output_files.append(file_path)

                # Check for content field
                elif "content" in data:
                    file_path = output_dir / f"analysis_{session_id}.md"
                    file_path.write_text(data["content"])
                    output_files.append(file_path)

                # Check for result field
                elif "result" in data:
                    file_path = output_dir / f"analysis_{session_id}.md"
                    file_path.write_text(str(data["result"]))
                    output_files.append(file_path)

        except json.JSONDecodeError:
            # Not JSON, save as raw markdown
            if stdout.strip():
                file_path = output_dir / f"analysis_{session_id}.md"
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(stdout)
                output_files.append(file_path)

        return output_files

    def run_custom_command(
        self,
        repo_path: Path,
        command_file: Path,
        output_dir: Path,
    ) -> OpenCodeSession:
        """
        Run a custom OpenCode command from .opencode/commands/.

        Args:
            repo_path: Path to the repository
            command_file: Path to the command markdown file
            output_dir: Directory for output files

        Returns:
            OpenCodeSession with results
        """
        session_id = str(uuid.uuid4())[:8]

        if not command_file.exists():
            raise FileNotFoundError(f"Command file not found: {command_file}")

        prompt = command_file.read_text()

        session = OpenCodeSession(
            session_id=session_id,
            command=command_file.stem,
            started_at=datetime.now(),
        )

        try:
            result = subprocess.run(
                [
                    self.settings.opencode_binary,
                    "run",
                    prompt,
                ],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                timeout=600,
            )

            session.ended_at = datetime.now()
            session.exit_code = result.returncode
            session.stdout = result.stdout
            session.stderr = result.stderr

            if result.returncode == 0:
                session.output_files = self._process_output(
                    result.stdout, output_dir, session_id
                )

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            session.ended_at = datetime.now()
            session.stderr = str(e)

        self.sessions.append(session)
        return session


class ClaudeRunner:
    """Fallback runner using Claude CLI when OpenCode is unavailable."""

    def __init__(self, console: Optional[Console] = None):
        self.settings = get_settings()
        self.console = console or Console()

    def is_available(self) -> bool:
        """Check if Claude CLI is available."""
        try:
            result = subprocess.run(
                [self.settings.claude_binary, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def run_analysis(
        self,
        repo_path: Path,
        depth: AnalysisDepth,
        output_dir: Path,
        context: Optional[str] = None,
    ) -> OpenCodeSession:
        """Run Claude CLI analysis as fallback."""
        session_id = str(uuid.uuid4())[:8]

        prompt = f"""\
Analyze this repository and generate comprehensive documentation.

Repository path: {repo_path}
Analysis depth: {depth.value}

Generate:
1. Architecture overview in markdown
2. Component diagram in Mermaid format
3. Data flow diagram in Mermaid format
4. Technology stack list

{context or ''}
"""

        session = OpenCodeSession(
            session_id=session_id,
            command=f"claude:{depth.value}",
            started_at=datetime.now(),
        )

        try:
            result = subprocess.run(
                [
                    self.settings.claude_binary,
                    "-p",
                    prompt,
                    "--allowedTools",
                    "Read,Glob,Grep",
                    "--output-format",
                    "json",
                ],
                cwd=str(repo_path),
                capture_output=True,
                text=True,
                timeout=600,
            )

            session.ended_at = datetime.now()
            session.exit_code = result.returncode
            session.stdout = result.stdout
            session.stderr = result.stderr

            if result.returncode == 0 and result.stdout.strip():
                # Save Claude output
                file_path = output_dir / f"claude_analysis_{session_id}.md"
                file_path.parent.mkdir(parents=True, exist_ok=True)

                try:
                    data = json.loads(result.stdout)
                    content = data.get("result", data.get("content", result.stdout))
                except json.JSONDecodeError:
                    content = result.stdout

                file_path.write_text(content if isinstance(content, str) else str(content))
                session.output_files = [file_path]

        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            session.ended_at = datetime.now()
            session.stderr = str(e)

        return session
