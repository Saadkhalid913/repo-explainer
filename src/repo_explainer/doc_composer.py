"""Document composer for generating coherent, navigable documentation."""

import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console

console = Console()


class DocComposer:
    """Composes coherent documentation from OpenCode artifacts."""

    def __init__(self, output_dir: Path):
        """
        Initialize the document composer.

        Args:
            output_dir: Directory containing OpenCode artifacts
        """
        self.output_dir = output_dir
        self.diagrams_dir = output_dir / "diagrams"

    def compose(
        self,
        repo_path: Path,
        depth: str,
        session_id: str | None = None,
        timestamp: str | None = None,
    ) -> dict[str, Path]:
        """
        Compose coherent documentation from raw artifacts.

        Args:
            repo_path: Path to analyzed repository
            depth: Analysis depth
            session_id: OpenCode session ID
            timestamp: Analysis timestamp

        Returns:
            Dictionary mapping document types to file paths
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        console.print("\n[bold cyan]📚 Composing coherent documentation...[/bold cyan]")

        # Ensure diagrams directory exists
        self.diagrams_dir.mkdir(parents=True, exist_ok=True)

        composed_files = {}

        # 1. Render diagrams (Mermaid -> SVG)
        diagram_files = self._render_diagrams()
        composed_files.update(diagram_files)

        # 2. Generate subpages
        subpages = self._generate_subpages(diagram_files)
        composed_files.update(subpages)

        # 3. Generate index.md
        index_file = self._generate_index(
            repo_path=repo_path,
            depth=depth,
            session_id=session_id,
            timestamp=timestamp,
            diagram_files=diagram_files,
            subpages=subpages,
        )
        composed_files["index"] = index_file

        # 4. Generate manifest
        manifest_file = self._generate_manifest(composed_files, timestamp)
        composed_files["manifest"] = manifest_file

        console.print("[green]✓[/green] Documentation composition complete")

        return composed_files

    def _render_diagrams(self) -> dict[str, Path]:
        """
        Render Mermaid diagrams to SVG format.

        Returns:
            Dictionary mapping diagram names to SVG file paths
        """
        diagram_files = {}

        # Find all .mermaid files in output directory
        mermaid_files = list(self.output_dir.glob("*.mermaid"))

        if not mermaid_files:
            console.print("[dim]  No Mermaid diagrams to render[/dim]")
            return diagram_files

        console.print(f"[dim]  Rendering {len(mermaid_files)} diagram(s)...[/dim]")

        for mermaid_file in mermaid_files:
            svg_file = self.diagrams_dir / f"{mermaid_file.stem}.svg"

            try:
                # Use Mermaid CLI (mmdc) to render
                result = subprocess.run(
                    ["mmdc", "-i", str(mermaid_file), "-o", str(svg_file)],
                    capture_output=True,
                    text=True,
                    timeout=30,
                )

                if result.returncode == 0:
                    diagram_files[mermaid_file.stem] = svg_file
                    console.print(f"[dim]    ✓ Rendered: {mermaid_file.name} → {svg_file.name}[/dim]")
                else:
                    console.print(
                        f"[yellow]    ⚠ Failed to render {mermaid_file.name}: {result.stderr}[/yellow]"
                    )

            except FileNotFoundError:
                console.print(
                    "[yellow]  ⚠ Mermaid CLI (mmdc) not found. Install with: npm install -g @mermaid-js/mermaid-cli[/yellow]"
                )
                # Still track the mermaid file even if we can't render it
                diagram_files[mermaid_file.stem] = mermaid_file
                break
            except subprocess.TimeoutExpired:
                console.print(f"[yellow]    ⚠ Timeout rendering {mermaid_file.name}[/yellow]")
            except Exception as e:
                console.print(f"[yellow]    ⚠ Error rendering {mermaid_file.name}: {e}[/yellow]")

        return diagram_files

    def _generate_subpages(self, diagram_files: dict[str, Path]) -> dict[str, Path]:
        """
        Generate normalized subpages from raw artifacts.

        Args:
            diagram_files: Dictionary of rendered diagram files

        Returns:
            Dictionary mapping subpage names to file paths
        """
        subpages = {}

        # Generate components.md
        if (self.output_dir / "architecture.md").exists() or "components" in diagram_files:
            components_file = self._generate_components_page(diagram_files)
            if components_file:
                subpages["components"] = components_file

        # Generate dataflow.md
        if "dataflow" in diagram_files:
            dataflow_file = self._generate_dataflow_page(diagram_files)
            if dataflow_file:
                subpages["dataflow"] = dataflow_file

        # Generate tech-stack.md
        if (self.output_dir / "tech-stack.txt").exists():
            tech_stack_file = self._generate_tech_stack_page()
            if tech_stack_file:
                subpages["tech-stack"] = tech_stack_file

        return subpages

    def _generate_components_page(self, diagram_files: dict[str, Path]) -> Path | None:
        """Generate components.md subpage."""
        components_file = self.output_dir / "components.md"

        content = "# Components\n\n"

        # Add architecture overview if available
        arch_file = self.output_dir / "architecture.md"
        if arch_file.exists():
            arch_content = arch_file.read_text()

            # Extract components section if it exists
            components_section = self._extract_section(arch_content, "Components")
            if components_section:
                content += components_section + "\n\n"
            else:
                # Include full architecture content
                content += "## Architecture Overview\n\n"
                content += arch_content + "\n\n"

        # Embed component diagram
        if "components" in diagram_files:
            diagram_path = diagram_files["components"]
            relative_path = diagram_path.relative_to(self.output_dir)

            content += "## Component Diagram\n\n"

            # Embed rendered image if it's SVG
            if diagram_path.suffix == ".svg":
                content += f"![Component Diagram]({relative_path})\n\n"

            # Include Mermaid source
            mermaid_source = self.output_dir / "components.mermaid"
            if mermaid_source.exists():
                content += "<details>\n<summary>View Mermaid Source</summary>\n\n"
                content += "```mermaid\n"
                content += mermaid_source.read_text()
                content += "\n```\n</details>\n\n"

        components_file.write_text(content)
        console.print(f"[dim]  Created: components.md[/dim]")
        return components_file

    def _generate_dataflow_page(self, diagram_files: dict[str, Path]) -> Path | None:
        """Generate dataflow.md subpage."""
        dataflow_file = self.output_dir / "dataflow.md"

        content = "# Data Flow\n\n"
        content += "This page visualizes how data flows through the system.\n\n"

        # Embed dataflow diagram
        if "dataflow" in diagram_files:
            diagram_path = diagram_files["dataflow"]
            relative_path = diagram_path.relative_to(self.output_dir)

            content += "## Data Flow Diagram\n\n"

            # Embed rendered image if it's SVG
            if diagram_path.suffix == ".svg":
                content += f"![Data Flow Diagram]({relative_path})\n\n"

            # Include Mermaid source
            mermaid_source = self.output_dir / "dataflow.mermaid"
            if mermaid_source.exists():
                content += "<details>\n<summary>View Mermaid Source</summary>\n\n"
                content += "```mermaid\n"
                content += mermaid_source.read_text()
                content += "\n```\n</details>\n\n"

        # Extract data flow section from architecture.md if available
        arch_file = self.output_dir / "architecture.md"
        if arch_file.exists():
            arch_content = arch_file.read_text()
            dataflow_section = self._extract_section(arch_content, "Data Flow")
            if dataflow_section:
                content += "## Description\n\n"
                content += dataflow_section + "\n"

        dataflow_file.write_text(content)
        console.print(f"[dim]  Created: dataflow.md[/dim]")
        return dataflow_file

    def _generate_tech_stack_page(self) -> Path | None:
        """Generate tech-stack.md subpage from tech-stack.txt."""
        tech_stack_txt = self.output_dir / "tech-stack.txt"
        if not tech_stack_txt.exists():
            return None

        tech_stack_file = self.output_dir / "tech-stack.md"

        content = "# Technology Stack\n\n"

        # Read and normalize tech-stack.txt
        raw_content = tech_stack_txt.read_text()

        # Convert to markdown list if it's plain text
        if not raw_content.strip().startswith("#"):
            lines = raw_content.strip().split("\n")
            content += "## Technologies Detected\n\n"
            for line in lines:
                line = line.strip()
                if line and not line.startswith("-"):
                    content += f"- {line}\n"
                else:
                    content += f"{line}\n"
        else:
            # Already markdown formatted
            content += raw_content

        tech_stack_file.write_text(content)
        console.print(f"[dim]  Created: tech-stack.md[/dim]")
        return tech_stack_file

    def _generate_index(
        self,
        repo_path: Path,
        depth: str,
        session_id: str | None,
        timestamp: str,
        diagram_files: dict[str, Path],
        subpages: dict[str, Path],
    ) -> Path:
        """
        Generate index.md landing page.

        Args:
            repo_path: Path to analyzed repository
            depth: Analysis depth
            session_id: OpenCode session ID
            timestamp: Analysis timestamp
            diagram_files: Dictionary of rendered diagrams
            subpages: Dictionary of generated subpages

        Returns:
            Path to generated index.md
        """
        index_file = self.output_dir / "index.md"

        content = f"""# Repository Analysis

**Repository:** `{repo_path.name}`
**Path:** `{repo_path}`
**Analysis Depth:** {depth}
**Timestamp:** {timestamp}
"""

        if session_id:
            content += f"**Session ID:** `{session_id}`\n"

        content += "\n---\n\n"

        # Executive summary
        content += "## Overview\n\n"
        content += "This documentation provides a comprehensive analysis of the repository structure, "
        content += "components, data flow, and technology stack.\n\n"

        # Quick navigation
        content += "## Quick Navigation\n\n"

        if "components" in subpages:
            content += "- 📦 [Components](components.md) - System components and architecture\n"

        if "dataflow" in subpages:
            content += "- 🔄 [Data Flow](dataflow.md) - How data moves through the system\n"

        if "tech-stack" in subpages:
            content += "- 🛠️ [Technology Stack](tech-stack.md) - Technologies and frameworks used\n"

        if (self.output_dir / "architecture.md").exists():
            content += "- 📐 [Architecture Details](architecture.md) - Full architecture analysis\n"

        content += "\n"

        # Embed diagrams in the index
        if diagram_files:
            content += "## Visualizations\n\n"

            # Components diagram
            if "components" in diagram_files:
                diagram_path = diagram_files["components"]
                relative_path = diagram_path.relative_to(self.output_dir)
                content += "### Component Structure\n\n"
                if diagram_path.suffix == ".svg":
                    content += f"![Component Diagram]({relative_path})\n\n"
                content += "[View detailed component documentation →](components.md)\n\n"

            # Dataflow diagram
            if "dataflow" in diagram_files:
                diagram_path = diagram_files["dataflow"]
                relative_path = diagram_path.relative_to(self.output_dir)
                content += "### Data Flow\n\n"
                if diagram_path.suffix == ".svg":
                    content += f"![Data Flow Diagram]({relative_path})\n\n"
                content += "[View detailed data flow documentation →](dataflow.md)\n\n"

        # Key metrics section
        content += "## Analysis Artifacts\n\n"
        content += "This analysis generated the following artifacts:\n\n"

        artifacts_list = []
        if (self.output_dir / "architecture.md").exists():
            artifacts_list.append("- `architecture.md` - Detailed architecture analysis")
        if (self.output_dir / "components.mermaid").exists():
            artifacts_list.append("- `components.mermaid` - Component diagram source")
        if (self.output_dir / "dataflow.mermaid").exists():
            artifacts_list.append("- `dataflow.mermaid` - Data flow diagram source")
        if (self.output_dir / "tech-stack.txt").exists():
            artifacts_list.append("- `tech-stack.txt` - Raw technology stack")

        for artifact in artifacts_list:
            content += artifact + "\n"

        content += "\n"

        # Footer with metadata
        content += "---\n\n"
        content += "*Generated by [repo-explainer](https://github.com/yourusername/repo-explainer) "
        content += f"on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"

        index_file.write_text(content)
        console.print(f"[dim]  Created: index.md[/dim]")
        return index_file

    def _generate_manifest(self, composed_files: dict[str, Path], timestamp: str) -> Path:
        """
        Generate manifest of all composed files.

        Args:
            composed_files: Dictionary of composed file paths
            timestamp: Analysis timestamp

        Returns:
            Path to manifest file
        """
        manifest_file = self.output_dir / ".repo-explainer" / "coherence.json"
        manifest_file.parent.mkdir(parents=True, exist_ok=True)

        manifest = {
            "timestamp": timestamp,
            "files": {name: str(path) for name, path in composed_files.items()},
            "version": "1.0",
        }

        manifest_file.write_text(json.dumps(manifest, indent=2))
        console.print(f"[dim]  Created: .repo-explainer/coherence.json[/dim]")
        return manifest_file

    def _extract_section(self, content: str, section_name: str) -> str | None:
        """
        Extract a specific section from markdown content.

        Args:
            content: Full markdown content
            section_name: Name of section to extract

        Returns:
            Section content or None if not found
        """
        # Try to find section with ## heading
        pattern = rf"##\s+{re.escape(section_name)}\s*\n(.*?)(?=\n##|\Z)"
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)

        if match:
            return match.group(1).strip()

        return None
