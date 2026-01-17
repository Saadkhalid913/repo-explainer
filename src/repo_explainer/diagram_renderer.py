"""Centralized diagram rendering module for Mermaid to PNG conversion."""

import json
import subprocess
from pathlib import Path

from rich.console import Console

console = Console()


class DiagramRenderer:
    """Renders Mermaid diagrams to PNG images."""

    def __init__(self, opencode_cwd: Path | None = None):
        """
        Initialize the diagram renderer.

        Args:
            opencode_cwd: Working directory for OpenCode calls (for syntax fixing)
        """
        self.opencode_cwd = opencode_cwd
        self._mmdc_available: bool | None = None

    def is_mmdc_available(self) -> bool:
        """Check if Mermaid CLI (mmdc) is available."""
        if self._mmdc_available is None:
            try:
                result = subprocess.run(
                    ["mmdc", "--version"],
                    capture_output=True,
                    text=True,
                    timeout=10,
                )
                self._mmdc_available = result.returncode == 0
            except (FileNotFoundError, subprocess.TimeoutExpired):
                self._mmdc_available = False

        return self._mmdc_available

    def render_mermaid_to_png(
        self,
        mermaid_file: Path,
        output_dir: Path,
        auto_fix: bool = True,
        max_retries: int = 2,
    ) -> Path | None:
        """
        Render a Mermaid file to PNG.

        Args:
            mermaid_file: Path to the .mermaid source file
            output_dir: Directory to write PNG output
            auto_fix: Whether to attempt auto-fixing syntax errors
            max_retries: Maximum retry attempts for auto-fix

        Returns:
            Path to rendered PNG file, or None if rendering failed
        """
        if not self.is_mmdc_available():
            console.print(
                "[yellow]  Warning: mmdc not found. Install with: npm install -g @mermaid-js/mermaid-cli[/yellow]"
            )
            return None

        output_dir.mkdir(parents=True, exist_ok=True)
        png_file = output_dir / f"{mermaid_file.stem}.png"

        for attempt in range(max_retries + 1):
            try:
                result = subprocess.run(
                    [
                        "mmdc",
                        "-i", str(mermaid_file),
                        "-o", str(png_file),
                        "-b", "white",  # White background
                        "-s", "2",  # Scale factor for high DPI
                    ],
                    capture_output=True,
                    text=True,
                    timeout=60,
                )

                if result.returncode == 0 and png_file.exists():
                    if attempt > 0:
                        console.print(
                            f"[dim]    ✓ Rendered: {mermaid_file.name} → {png_file.name} (after {attempt} fix(es))[/dim]"
                        )
                    else:
                        console.print(
                            f"[dim]    ✓ Rendered: {mermaid_file.name} → {png_file.name}[/dim]"
                        )
                    return png_file

                # Rendering failed
                if attempt < max_retries and auto_fix:
                    error_msg = result.stderr
                    console.print(
                        f"[yellow]    ⚠ Syntax error in {mermaid_file.name}, attempting auto-fix (attempt {attempt + 1}/{max_retries})...[/yellow]"
                    )

                    if self._fix_mermaid_syntax(mermaid_file, error_msg):
                        continue  # Retry rendering
                    else:
                        console.print("[yellow]      Auto-fix failed[/yellow]")
                        break
                else:
                    console.print(
                        f"[yellow]    ⚠ Failed to render {mermaid_file.name}: {result.stderr[:200]}[/yellow]"
                    )
                    break

            except subprocess.TimeoutExpired:
                console.print(f"[yellow]    ⚠ Timeout rendering {mermaid_file.name}[/yellow]")
                break
            except Exception as e:
                console.print(f"[yellow]    ⚠ Error rendering {mermaid_file.name}: {e}[/yellow]")
                break

        return None

    def render_all_in_directory(
        self,
        source_dir: Path,
        output_dir: Path,
        auto_fix: bool = True,
    ) -> dict[str, Path]:
        """
        Render all Mermaid files in a directory to PNG.

        Args:
            source_dir: Directory containing .mermaid files
            output_dir: Directory to write PNG files

        Returns:
            Dictionary mapping diagram names to PNG file paths
        """
        rendered = {}
        mermaid_files = list(source_dir.glob("*.mermaid"))

        if not mermaid_files:
            console.print("[dim]  No Mermaid diagrams to render[/dim]")
            return rendered

        console.print(f"[dim]  Rendering {len(mermaid_files)} diagram(s) to PNG...[/dim]")

        for mermaid_file in mermaid_files:
            png_path = self.render_mermaid_to_png(
                mermaid_file, output_dir, auto_fix=auto_fix
            )
            if png_path:
                rendered[mermaid_file.stem] = png_path

        success_count = len(rendered)
        failed_count = len(mermaid_files) - success_count

        if success_count > 0:
            console.print(f"[dim]  ✓ {success_count} diagram(s) rendered to PNG[/dim]")
        if failed_count > 0:
            console.print(f"[dim]  ⚠ {failed_count} diagram(s) failed to render[/dim]")

        return rendered

    def _fix_mermaid_syntax(self, mermaid_file: Path, error_msg: str) -> bool:
        """
        Attempt to fix Mermaid syntax errors using OpenCode.

        Args:
            mermaid_file: Path to the .mermaid file with syntax errors
            error_msg: Error message from the Mermaid CLI

        Returns:
            True if fixed successfully, False otherwise
        """
        try:
            content = mermaid_file.read_text()

            prompt = f"""Fix the Mermaid syntax errors in this diagram.

Error message:
{error_msg}

Mermaid source:
```mermaid
{content}
```

Please output ONLY the corrected Mermaid code without any explanation or markdown code blocks.
Just output the raw Mermaid syntax starting with the diagram type (e.g., 'graph', 'sequenceDiagram', 'classDiagram', etc.)."""

            cwd = self.opencode_cwd or mermaid_file.parent

            result = subprocess.run(
                ["opencode", "run", prompt, "--format", "json"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(cwd),
            )

            if result.returncode != 0:
                return False

            fixed_content = None
            for line in result.stdout.strip().split("\n"):
                try:
                    event = json.loads(line)
                    if event.get("type") == "text":
                        text_content = event.get("part", {}).get("text", "")
                        if text_content and any(
                            text_content.strip().startswith(t)
                            for t in [
                                "graph",
                                "sequenceDiagram",
                                "classDiagram",
                                "flowchart",
                                "erDiagram",
                                "journey",
                                "gantt",
                                "pie",
                                "gitGraph",
                            ]
                        ):
                            fixed_content = text_content.strip()
                            break
                except json.JSONDecodeError:
                    continue

            if not fixed_content:
                return False

            mermaid_file.write_text(fixed_content)
            console.print(f"[dim]    ✓ Fixed syntax in {mermaid_file.name}[/dim]")
            return True

        except Exception as e:
            console.print(f"[dim]    Failed to auto-fix {mermaid_file.name}: {e}[/dim]")
            return False


def embed_diagram_in_markdown(
    diagram_path: Path,
    alt_text: str = "Diagram",
    relative_to: Path | None = None,
) -> str:
    """
    Generate markdown image embed for a diagram.

    Args:
        diagram_path: Path to the diagram image (PNG/SVG)
        alt_text: Alt text for the image
        relative_to: Calculate relative path from this directory

    Returns:
        Markdown image embed string
    """
    if relative_to:
        try:
            rel_path = diagram_path.relative_to(relative_to)
        except ValueError:
            # Path is not relative to the given directory, use absolute
            rel_path = diagram_path
    else:
        rel_path = diagram_path

    return f"![{alt_text}]({rel_path})"
