"""Document composer for generating coherent, navigable documentation."""

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console

from .diagram_renderer import DiagramRenderer

console = Console()


class DocComposer:
    """Composes coherent documentation from OpenCode artifacts."""

    def __init__(self, output_dir: Path, repo_path: Path | None = None):
        """
        Initialize the document composer.

        Args:
            output_dir: Directory containing OpenCode artifacts
            repo_path: Path to the repository being analyzed (optional)
        """
        self.output_dir = output_dir
        self.repo_path = repo_path or Path.cwd()
        self.src_dir = output_dir / "src"
        self.raw_dir = output_dir / "src" / "raw"
        self.diagrams_dir = output_dir / "diagrams"
        self._diagram_renderer = DiagramRenderer(opencode_cwd=self.raw_dir)

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

        console.print(
            "\n[bold cyan]📚 Composing coherent documentation...[/bold cyan]")

        # Ensure diagrams directory exists
        self.diagrams_dir.mkdir(parents=True, exist_ok=True)

        composed_files = {}

        # 1. Render diagrams (Mermaid -> SVG)
        diagram_files = self._render_diagrams()
        composed_files.update(diagram_files)

        # 2. Parse component data if available
        components_data = self._parse_components_data()

        # 3. Generate detailed component files
        component_files = self._generate_component_files(
            components_data, diagram_files)
        composed_files.update(component_files)

        # 4. Generate dependencies documentation
        dependency_files = self._generate_dependencies_section(components_data)
        composed_files.update(dependency_files)

        # 5. Generate API documentation if endpoints detected
        api_files = self._generate_api_documentation(components_data)
        composed_files.update(api_files)

        # 6. Generate subpages (overviews)
        subpages = self._generate_subpages(diagram_files, components_data)
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
        Render Mermaid diagrams to PNG format using DiagramRenderer.

        Returns:
            Dictionary mapping diagram names to PNG file paths (or .mermaid paths if rendering failed)
        """
        diagram_files = {}

        # Find all .mermaid files in src/raw/ directory
        mermaid_files = list(self.raw_dir.glob("*.mermaid"))

        if not mermaid_files:
            console.print("[dim]  No Mermaid diagrams to render[/dim]")
            return diagram_files

        # Use the centralized diagram renderer to render to PNG
        rendered = self._diagram_renderer.render_all_in_directory(
            self.raw_dir, self.diagrams_dir, auto_fix=True
        )

        # Add rendered diagrams
        diagram_files.update(rendered)

        # Track any failed diagrams (files not in rendered dict)
        for mermaid_file in mermaid_files:
            if mermaid_file.stem not in rendered:
                diagram_files[mermaid_file.stem] = mermaid_file
                console.print(
                    f"[dim]      Source available at {mermaid_file.name}[/dim]")

        return diagram_files

    def _generate_subpages(self, diagram_files: dict[str, Path], components_data: dict[str, Any]) -> dict[str, Path]:
        """
        Generate normalized subpages (overviews) from raw artifacts.

        Args:
            diagram_files: Dictionary of rendered diagram files
            components_data: Parsed components data

        Returns:
            Dictionary mapping subpage names to file paths
        """
        subpages = {}

        # Generate components overview
        if (self.output_dir / "architecture.md").exists() or "components" in diagram_files or components_data.get("components"):
            components_file = self._generate_components_page(
                diagram_files, components_data)
            if components_file:
                subpages["components_overview"] = components_file

        # Generate dataflow.md
        if "dataflow" in diagram_files:
            dataflow_file = self._generate_dataflow_page(diagram_files)
            if dataflow_file:
                subpages["dataflow"] = dataflow_file

        # Generate tech-stack.md
        if (self.raw_dir / "tech-stack.txt").exists():
            tech_stack_file = self._generate_tech_stack_page()
            if tech_stack_file:
                subpages["tech-stack"] = tech_stack_file

        return subpages

    def _generate_components_page(self, diagram_files: dict[str, Path], components_data: dict[str, Any]) -> Path | None:
        """Generate components/overview.md subpage with links to individual component files."""
        components_file = self.output_dir / "components" / "overview.md"

        content = "# Components Overview\n\n"

        # List individual component files if available
        components = components_data.get("components", [])
        if components:
            content += f"This repository contains **{len(components)} component(s)**. Click on any component below for detailed documentation.\n\n"
            content += "## Components\n\n"

            for component in components:
                comp_id = component.get(
                    "component_id", component.get("name", "unknown"))
                comp_name = component.get("name", comp_id)
                comp_type = component.get("type", "module")
                comp_file = component.get("file_path", "")
                comp_desc = component.get("description", "")

                safe_id = re.sub(r'[^a-zA-Z0-9_-]', '-', comp_id.lower())

                content += f"### [{comp_name}]({safe_id}.md)\n\n"
                content += f"**Type**: `{comp_type}`  \n"
                if comp_file:
                    content += f"**Location**: `{comp_file}`  \n"
                if comp_desc:
                    # Take first sentence only for overview
                    first_sentence = comp_desc.split(
                        '.')[0] + '.' if '.' in comp_desc else comp_desc
                    content += f"\n{first_sentence}\n"
                content += "\n"

            content += "---\n\n"

        content += "## Architecture Overview\n\n"

        # Add architecture overview if available
        arch_file = self.raw_dir / "architecture.md"
        if arch_file.exists():
            arch_content = arch_file.read_text()

            # Extract components section if it exists
            components_section = self._extract_section(
                arch_content, "Components")
            if components_section:
                content += components_section + "\n\n"
            else:
                # Include full architecture content
                content += "## Architecture Overview\n\n"
                content += arch_content + "\n\n"

        # Embed component diagram
        if "components" in diagram_files:
            diagram_path = diagram_files["components"]
            # Calculate relative path from components/ to diagrams/
            relative_path = "../" + \
                str(diagram_path.relative_to(self.output_dir))

            content += "## Component Diagram\n\n"

            # Embed rendered image if it's PNG or SVG
            if diagram_path.suffix in (".png", ".svg"):
                content += f"![Component Diagram]({relative_path})\n\n"
            elif diagram_path.suffix == ".mermaid":
                # Rendering failed, show helpful message
                content += "> **Note:** Diagram rendering failed. The source diagram is available below.\n\n"

            # Include Mermaid source as collapsible
            mermaid_source = self.raw_dir / "components.mermaid"
            if mermaid_source.exists():
                content += "<details>\n<summary>View Mermaid Source</summary>\n\n"
                content += "```mermaid\n"
                content += mermaid_source.read_text()
                content += "\n```\n</details>\n\n"

        components_file.write_text(content)
        console.print(f"[dim]  Created: components/overview.md[/dim]")
        return components_file

    def _generate_dataflow_page(self, diagram_files: dict[str, Path]) -> Path | None:
        """Generate dataflow/overview.md subpage."""
        dataflow_file = self.output_dir / "dataflow" / "overview.md"

        content = "# Data Flow\n\n"
        content += "This page visualizes how data flows through the system.\n\n"

        # Embed dataflow diagram
        if "dataflow" in diagram_files:
            diagram_path = diagram_files["dataflow"]
            # Calculate relative path from dataflow/ to diagrams/
            relative_path = "../" + \
                str(diagram_path.relative_to(self.output_dir))

            content += "## Data Flow Diagram\n\n"

            # Embed rendered image if it's PNG or SVG
            if diagram_path.suffix in (".png", ".svg"):
                content += f"![Data Flow Diagram]({relative_path})\n\n"
            elif diagram_path.suffix == ".mermaid":
                # Rendering failed, show helpful message
                content += "> **Note:** Diagram rendering failed. The source diagram is available below.\n\n"

            # Include Mermaid source as collapsible
            mermaid_source = self.raw_dir / "dataflow.mermaid"
            if mermaid_source.exists():
                content += "<details>\n<summary>View Mermaid Source</summary>\n\n"
                content += "```mermaid\n"
                content += mermaid_source.read_text()
                content += "\n```\n</details>\n\n"

        # Extract data flow section from architecture.md if available
        arch_file = self.raw_dir / "architecture.md"
        if arch_file.exists():
            arch_content = arch_file.read_text()
            dataflow_section = self._extract_section(arch_content, "Data Flow")
            if dataflow_section:
                content += "## Description\n\n"
                content += dataflow_section + "\n"

        dataflow_file.write_text(content)
        console.print(f"[dim]  Created: dataflow/overview.md[/dim]")
        return dataflow_file

    def _generate_tech_stack_page(self) -> Path | None:
        """Generate tech-stack/overview.md subpage from tech-stack.txt."""
        tech_stack_txt = self.raw_dir / "tech-stack.txt"
        if not tech_stack_txt.exists():
            return None

        tech_stack_file = self.output_dir / "tech-stack" / "overview.md"

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
        console.print(f"[dim]  Created: tech-stack/overview.md[/dim]")
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

        if "components_overview" in subpages or "components" in subpages:
            content += "- 📦 [Components](components/overview.md) - System components and architecture\n"

        if "dataflow" in subpages:
            content += "- 🔄 [Data Flow](dataflow/overview.md) - How data moves through the system\n"

        # Check if dependencies section exists
        if (self.output_dir / "dependencies" / "overview.md").exists():
            content += "- 🔗 [Dependencies](dependencies/overview.md) - Upstream, downstream, and external dependencies\n"

        # Check if API section exists
        if (self.output_dir / "api" / "overview.md").exists():
            content += "- 🌐 [API Documentation](api/overview.md) - Endpoints and interfaces\n"

        if "tech-stack" in subpages:
            content += "- 🛠️ [Technology Stack](tech-stack/overview.md) - Technologies and frameworks used\n"

        if (self.raw_dir / "architecture.md").exists():
            content += "- 📐 [Architecture Details](src/raw/architecture.md) - Full architecture analysis\n"

        content += "\n"

        # Embed diagrams in the index
        if diagram_files:
            content += "## Visualizations\n\n"

            # Components diagram
            if "components" in diagram_files:
                diagram_path = diagram_files["components"]
                relative_path = diagram_path.relative_to(self.output_dir)
                content += "### Component Structure\n\n"
                if diagram_path.suffix in (".png", ".svg"):
                    content += f"![Component Diagram]({relative_path})\n\n"
                elif diagram_path.suffix == ".mermaid":
                    content += "> Diagram not rendered. View source in [components/overview.md](components/overview.md)\n\n"
                content += "[View detailed component documentation →](components/overview.md)\n\n"

            # Dataflow diagram
            if "dataflow" in diagram_files:
                diagram_path = diagram_files["dataflow"]
                relative_path = diagram_path.relative_to(self.output_dir)
                content += "### Data Flow\n\n"
                if diagram_path.suffix in (".png", ".svg"):
                    content += f"![Data Flow Diagram]({relative_path})\n\n"
                elif diagram_path.suffix == ".mermaid":
                    content += "> Diagram not rendered. View source in [dataflow/overview.md](dataflow/overview.md)\n\n"
                content += "[View detailed data flow documentation →](dataflow/overview.md)\n\n"

        # Key metrics section
        content += "## Analysis Artifacts\n\n"
        content += "This analysis generated the following artifacts:\n\n"

        artifacts_list = []
        if (self.raw_dir / "architecture.md").exists():
            artifacts_list.append(
                "- `src/raw/architecture.md` - Detailed architecture analysis")
        if (self.raw_dir / "components.mermaid").exists():
            artifacts_list.append(
                "- `src/raw/components.mermaid` - Component diagram source")
        if (self.raw_dir / "dataflow.mermaid").exists():
            artifacts_list.append(
                "- `src/raw/dataflow.mermaid` - Data flow diagram source")
        if (self.raw_dir / "tech-stack.txt").exists():
            artifacts_list.append(
                "- `src/raw/tech-stack.txt` - Raw technology stack")

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

    def _parse_components_data(self) -> dict[str, Any]:
        """
        Parse components.json if available to extract detailed component information.

        Returns:
            Dictionary containing components data, or empty dict if not found
        """
        # Try to find components.json in the repository root
        components_json = self.repo_path / "components.json"

        if not components_json.exists():
            # Try in raw directory
            components_json = self.raw_dir / "components.json"

        if components_json.exists():
            try:
                data = json.loads(components_json.read_text())
                console.print(
                    f"[dim]  Found components data: {len(data.get('components', []))} component(s)[/dim]")
                return data
            except json.JSONDecodeError:
                console.print(
                    "[yellow]  Warning: Could not parse components.json[/yellow]")
                return {}

        return {}

    def _generate_component_files(
        self, components_data: dict[str, Any], diagram_files: dict[str, Path]
    ) -> dict[str, Path]:
        """
        Generate individual markdown files for each component.

        Args:
            components_data: Parsed components data
            diagram_files: Dictionary of diagram files

        Returns:
            Dictionary mapping component file keys to paths
        """
        component_files = {}

        components = components_data.get("components", [])
        if not components:
            # Try to extract from architecture.md
            arch_file = self.raw_dir / "architecture.md"
            if arch_file.exists():
                components = self._extract_components_from_architecture(
                    arch_file)

        if not components:
            console.print("[dim]  No detailed component data available[/dim]")
            return component_files

        console.print(
            f"[dim]  Generating {len(components)} component files...[/dim]")

        for component in components:
            component_id = component.get(
                "component_id", component.get("name", "unknown"))
            # Sanitize filename
            safe_id = re.sub(r'[^a-zA-Z0-9_-]', '-', component_id.lower())
            component_file = self.output_dir / "components" / f"{safe_id}.md"

            # Generate component documentation
            content = self._generate_component_content(
                component, components_data)
            component_file.write_text(content)

            component_files[f"component_{safe_id}"] = component_file

        console.print(
            f"[dim]    ✓ Created {len(component_files)} component files[/dim]")
        return component_files

    def _generate_component_content(self, component: dict[str, Any], components_data: dict[str, Any]) -> str:
        """
        Generate detailed markdown content for a single component.

        Args:
            component: Component data dictionary
            components_data: Full components data for cross-references

        Returns:
            Markdown content for the component
        """
        name = component.get("name", "Unknown Component")
        component_id = component.get("component_id", "")
        comp_type = component.get("type", "module")
        file_path = component.get("file_path", "")
        line_range = component.get("line_range", {})
        description = component.get("description", "No description available")

        content = f"# {name}\n\n"
        content += f"**Type**: `{comp_type}`  \n"
        content += f"**ID**: `{component_id}`  \n"

        if file_path:
            if line_range:
                start = line_range.get("start", "")
                end = line_range.get("end", "")
                content += f"**Location**: `{file_path}:{start}-{end}`  \n"
            else:
                content += f"**Location**: `{file_path}`  \n"

        content += "\n## Overview\n\n"
        content += f"{description}\n\n"

        # Responsibilities
        responsibilities = component.get("responsibilities", [])
        if responsibilities:
            content += "## Responsibilities\n\n"
            for resp in responsibilities:
                content += f"- {resp}\n"
            content += "\n"

        # Key Functions
        key_functions = component.get("key_functions", [])
        if key_functions:
            content += "## Key Functions\n\n"
            for func in key_functions:
                func_name = func.get("name", "unknown")
                func_file = func.get("file_path", file_path)
                func_range = func.get("line_range", {})
                func_sig = func.get("signature", "")
                func_purpose = func.get("purpose", "")

                content += f"### `{func_name}`\n\n"

                if func_range:
                    start = func_range.get("start", "")
                    end = func_range.get("end", "")
                    content += f"**Location**: `{func_file}:{start}-{end}`  \n"
                elif func_file:
                    content += f"**Location**: `{func_file}`  \n"

                if func_sig:
                    content += f"**Signature**:  \n```\n{func_sig}\n```\n\n"

                if func_purpose:
                    content += f"{func_purpose}\n\n"

        # Dependencies
        dependencies = component.get("dependencies", {})
        if dependencies:
            content += "## Dependencies\n\n"

            internal_deps = dependencies.get("internal", [])
            if internal_deps:
                content += "### Internal Dependencies\n\n"
                content += "This component depends on:\n\n"
                for dep_id in internal_deps:
                    # Find the component details
                    dep_component = next(
                        (c for c in components_data.get("components", [])
                         if c.get("component_id") == dep_id),
                        None
                    )
                    if dep_component:
                        dep_name = dep_component.get("name", dep_id)
                        safe_id = re.sub(r'[^a-zA-Z0-9_-]',
                                         '-', dep_id.lower())
                        content += f"- [`{dep_name}`]({safe_id}.md) (`{dep_id}`)\n"
                    else:
                        content += f"- `{dep_id}`\n"
                content += "\n"

            external_deps = dependencies.get("external", [])
            if external_deps:
                content += "### External Dependencies\n\n"
                for dep in external_deps:
                    content += f"- `{dep}`\n"
                content += "\n"

        # Interfaces
        interfaces = component.get("interfaces", [])
        if interfaces:
            content += "## Interfaces\n\n"
            for interface in interfaces:
                iface_name = interface.get("name", "")
                iface_type = interface.get("type", "")
                endpoints = interface.get("endpoints", [])

                if iface_name:
                    content += f"### {iface_name}\n\n"
                if iface_type:
                    content += f"**Type**: {iface_type}  \n\n"

                if endpoints:
                    content += "**Endpoints**:\n\n"
                    for endpoint in endpoints:
                        content += f"- `{endpoint}`\n"
                    content += "\n"

        # Depended by (reverse dependencies)
        content += "## Used By\n\n"
        dependents = self._find_dependents(component_id, components_data)
        if dependents:
            content += "This component is used by:\n\n"
            for dep_id, dep_name in dependents:
                safe_id = re.sub(r'[^a-zA-Z0-9_-]', '-', dep_id.lower())
                content += f"- [`{dep_name}`]({safe_id}.md)\n"
        else:
            content += "_No components currently depend on this component._\n"

        content += "\n---\n\n"
        content += "_Generated from component analysis_\n"

        return content

    def _find_dependents(self, component_id: str, components_data: dict[str, Any]) -> list[tuple[str, str]]:
        """
        Find components that depend on the given component.

        Args:
            component_id: ID of the component to find dependents for
            components_data: Full components data

        Returns:
            List of tuples (dependent_id, dependent_name)
        """
        dependents = []
        for component in components_data.get("components", []):
            internal_deps = component.get(
                "dependencies", {}).get("internal", [])
            if component_id in internal_deps:
                dependents.append((
                    component.get("component_id", ""),
                    component.get("name", component.get(
                        "component_id", "Unknown"))
                ))
        return dependents

    def _extract_components_from_architecture(self, arch_file: Path) -> list[dict[str, Any]]:
        """
        Extract component information from architecture.md if components.json doesn't exist.

        Args:
            arch_file: Path to architecture.md

        Returns:
            List of component dictionaries
        """
        # This is a fallback - try to parse architecture.md for component information
        # For now, return empty list - this could be enhanced with regex parsing
        return []

    def _generate_dependencies_section(self, components_data: dict[str, Any]) -> dict[str, Path]:
        """
        Generate dependencies documentation with upstream, downstream, and external dependencies.

        Args:
            components_data: Parsed components data

        Returns:
            Dictionary mapping dependency file keys to paths
        """
        dependency_files = {}
        components = components_data.get("components", [])

        if not components:
            console.print("[dim]  No dependency data available[/dim]")
            return dependency_files

        console.print("[dim]  Generating dependencies documentation...[/dim]")

        # Generate overview
        overview_file = self.output_dir / "dependencies" / "overview.md"
        overview_content = self._generate_dependencies_overview(
            components_data)
        overview_file.write_text(overview_content)
        dependency_files["dependencies_overview"] = overview_file

        # Generate upstream dependencies (what each component depends on)
        downstream_file = self.output_dir / "dependencies" / "downstream.md"
        downstream_content = self._generate_downstream_dependencies(
            components_data)
        downstream_file.write_text(downstream_content)
        dependency_files["dependencies_downstream"] = downstream_file

        # Generate downstream dependencies (what depends on each component)
        upstream_file = self.output_dir / "dependencies" / "upstream.md"
        upstream_content = self._generate_upstream_dependencies(
            components_data)
        upstream_file.write_text(upstream_content)
        dependency_files["dependencies_upstream"] = upstream_file

        # Generate external dependencies
        external_file = self.output_dir / "dependencies" / "external.md"
        external_content = self._generate_external_dependencies(
            components_data)
        external_file.write_text(external_content)
        dependency_files["dependencies_external"] = external_file

        console.print("[dim]    ✓ Created dependencies documentation[/dim]")
        return dependency_files

    def _generate_dependencies_overview(self, components_data: dict[str, Any]) -> str:
        """Generate dependencies overview content."""
        components = components_data.get("components", [])

        content = "# Dependencies Overview\n\n"
        content += "This section provides a comprehensive view of all dependencies in the repository.\n\n"

        # Count dependencies
        total_components = len(components)
        total_internal = sum(
            len(c.get("dependencies", {}).get("internal", []))
            for c in components
        )
        total_external = len(set(
            dep
            for c in components
            for dep in c.get("dependencies", {}).get("external", [])
        ))

        content += "## Summary\n\n"
        content += f"- **Total Components**: {total_components}\n"
        content += f"- **Internal Dependencies**: {total_internal} connections\n"
        content += f"- **External Packages**: {total_external} unique packages\n\n"

        content += "## Navigation\n\n"
        content += "- [Downstream Dependencies](downstream.md) - What each component depends on\n"
        content += "- [Upstream Dependencies](upstream.md) - What depends on each component\n"
        content += "- [External Dependencies](external.md) - External packages used\n\n"

        content += "## Dependency Graph\n\n"
        content += "See `../diagrams/` for visual dependency diagrams.\n\n"

        return content

    def _generate_downstream_dependencies(self, components_data: dict[str, Any]) -> str:
        """Generate downstream dependencies (what each component depends on)."""
        components = components_data.get("components", [])

        content = "# Downstream Dependencies\n\n"
        content += "This document lists what each component **depends on** (its downstream dependencies).\n\n"

        for component in components:
            comp_id = component.get("component_id", "")
            comp_name = component.get("name", comp_id)
            comp_file = component.get("file_path", "")

            safe_id = re.sub(r'[^a-zA-Z0-9_-]', '-', comp_id.lower())
            content += f"## [{comp_name}](../components/{safe_id}.md)\n\n"

            if comp_file:
                content += f"**Location**: `{comp_file}`\n\n"

            dependencies = component.get("dependencies", {})
            internal_deps = dependencies.get("internal", [])
            external_deps = dependencies.get("external", [])

            if internal_deps:
                content += "### Internal Dependencies\n\n"
                for dep_id in internal_deps:
                    dep_comp = next(
                        (c for c in components if c.get("component_id") == dep_id),
                        None
                    )
                    if dep_comp:
                        dep_name = dep_comp.get("name", dep_id)
                        dep_file = dep_comp.get("file_path", "")
                        safe_dep_id = re.sub(
                            r'[^a-zA-Z0-9_-]', '-', dep_id.lower())
                        content += f"- [`{dep_name}`](../components/{safe_dep_id}.md)"
                        if dep_file:
                            content += f" - `{dep_file}`"
                        content += "\n"
                    else:
                        content += f"- `{dep_id}`\n"
                content += "\n"

            if external_deps:
                content += "### External Dependencies\n\n"
                for dep in external_deps:
                    content += f"- `{dep}`\n"
                content += "\n"

            if not internal_deps and not external_deps:
                content += "_No dependencies_\n\n"

            content += "---\n\n"

        return content

    def _generate_upstream_dependencies(self, components_data: dict[str, Any]) -> str:
        """Generate upstream dependencies (what depends on each component)."""
        components = components_data.get("components", [])

        content = "# Upstream Dependencies\n\n"
        content += "This document lists what **depends on** each component (its upstream dependents).\n\n"

        for component in components:
            comp_id = component.get("component_id", "")
            comp_name = component.get("name", comp_id)
            comp_file = component.get("file_path", "")

            safe_id = re.sub(r'[^a-zA-Z0-9_-]', '-', comp_id.lower())
            content += f"## [{comp_name}](../components/{safe_id}.md)\n\n"

            if comp_file:
                content += f"**Location**: `{comp_file}`\n\n"

            # Find dependents
            dependents = self._find_dependents(comp_id, components_data)

            if dependents:
                content += "### Used By\n\n"
                for dep_id, dep_name in dependents:
                    # Find the dependent component to get its file path
                    dep_comp = next(
                        (c for c in components if c.get("component_id") == dep_id),
                        None
                    )
                    safe_dep_id = re.sub(
                        r'[^a-zA-Z0-9_-]', '-', dep_id.lower())
                    content += f"- [`{dep_name}`](../components/{safe_dep_id}.md)"
                    if dep_comp and dep_comp.get("file_path"):
                        content += f" - `{dep_comp.get('file_path')}`"
                    content += "\n"
                content += "\n"
            else:
                content += "_No components depend on this component_\n\n"

            content += "---\n\n"

        return content

    def _generate_external_dependencies(self, components_data: dict[str, Any]) -> str:
        """Generate external dependencies documentation."""
        components = components_data.get("components", [])

        content = "# External Dependencies\n\n"
        content += "This document lists all external packages used in the repository.\n\n"

        # Collect all external dependencies
        external_deps = {}
        for component in components:
            comp_id = component.get("component_id", "")
            comp_name = component.get("name", comp_id)
            for dep in component.get("dependencies", {}).get("external", []):
                if dep not in external_deps:
                    external_deps[dep] = []
                external_deps[dep].append((comp_id, comp_name))

        if not external_deps:
            content += "_No external dependencies detected_\n"
            return content

        content += f"**Total External Packages**: {len(external_deps)}\n\n"

        # Sort by package name
        for package in sorted(external_deps.keys()):
            users = external_deps[package]
            content += f"## `{package}`\n\n"
            content += f"**Used by {len(users)} component(s)**:\n\n"

            for comp_id, comp_name in users:
                safe_id = re.sub(r'[^a-zA-Z0-9_-]', '-', comp_id.lower())
                content += f"- [`{comp_name}`](../components/{safe_id}.md)\n"
            content += "\n"

        return content

    def _generate_api_documentation(self, components_data: dict[str, Any]) -> dict[str, Path]:
        """
        Generate per-endpoint API documentation if APIs are detected.

        Args:
            components_data: Parsed components data

        Returns:
            Dictionary mapping API file keys to paths
        """
        api_files = {}
        components = components_data.get("components", [])

        # Collect all endpoints from all components
        all_endpoints = []
        for component in components:
            interfaces = component.get("interfaces", [])
            for interface in interfaces:
                iface_type = interface.get("type", "")
                endpoints = interface.get("endpoints", [])
                for endpoint in endpoints:
                    all_endpoints.append({
                        "endpoint": endpoint,
                        "type": iface_type,
                        "component_id": component.get("component_id", ""),
                        "component_name": component.get("name", ""),
                        "component_file": component.get("file_path", ""),
                        "interface_name": interface.get("name", ""),
                    })

        if not all_endpoints:
            return api_files

        console.print(
            f"[dim]  Generating API documentation for {len(all_endpoints)} endpoint(s)...[/dim]")

        # Generate overview
        overview_file = self.output_dir / "api" / "overview.md"
        overview_content = self._generate_api_overview(all_endpoints)
        overview_file.write_text(overview_content)
        api_files["api_overview"] = overview_file

        # Generate per-endpoint files
        for idx, endpoint_data in enumerate(all_endpoints):
            endpoint = endpoint_data["endpoint"]
            # Sanitize endpoint for filename
            safe_name = re.sub(r'[^a-zA-Z0-9_-]', '-',
                               endpoint.replace('/', '-'))
            if safe_name.startswith('-'):
                safe_name = safe_name[1:]

            endpoint_file = self.output_dir / "api" / f"{safe_name}.md"
            endpoint_content = self._generate_endpoint_content(endpoint_data)
            endpoint_file.write_text(endpoint_content)
            api_files[f"api_endpoint_{idx}"] = endpoint_file

        console.print(f"[dim]    ✓ Created API documentation[/dim]")
        return api_files

    def _generate_api_overview(self, all_endpoints: list[dict[str, Any]]) -> str:
        """Generate API overview content."""
        content = "# API Overview\n\n"
        content += f"This repository exposes **{len(all_endpoints)} endpoint(s)**.\n\n"

        # Group by type
        by_type = {}
        for endpoint_data in all_endpoints:
            api_type = endpoint_data["type"] or "Unknown"
            if api_type not in by_type:
                by_type[api_type] = []
            by_type[api_type].append(endpoint_data)

        for api_type in sorted(by_type.keys()):
            endpoints = by_type[api_type]
            content += f"## {api_type} Endpoints\n\n"

            for endpoint_data in endpoints:
                endpoint = endpoint_data["endpoint"]
                comp_name = endpoint_data["component_name"]
                safe_name = re.sub(r'[^a-zA-Z0-9_-]', '-',
                                   endpoint.replace('/', '-'))
                if safe_name.startswith('-'):
                    safe_name = safe_name[1:]

                content += f"- [`{endpoint}`]({safe_name}.md) - {comp_name}\n"
            content += "\n"

        return content

    def _generate_endpoint_content(self, endpoint_data: dict[str, Any]) -> str:
        """Generate content for a single endpoint."""
        endpoint = endpoint_data["endpoint"]
        api_type = endpoint_data["type"] or "Unknown"
        comp_id = endpoint_data["component_id"]
        comp_name = endpoint_data["component_name"]
        comp_file = endpoint_data["component_file"]
        iface_name = endpoint_data["interface_name"]

        content = f"# {endpoint}\n\n"
        content += f"**Type**: {api_type}  \n"

        if iface_name:
            content += f"**Interface**: {iface_name}  \n"

        content += "\n## Component\n\n"
        safe_comp_id = re.sub(r'[^a-zA-Z0-9_-]', '-', comp_id.lower())
        content += f"**Provided by**: [`{comp_name}`](../components/{safe_comp_id}.md)  \n"

        if comp_file:
            content += f"**Source**: `{comp_file}`  \n"

        content += "\n## Description\n\n"
        content += f"This endpoint is part of the {comp_name} component.\n\n"

        content += "## Implementation\n\n"
        if comp_file:
            content += f"See [`{comp_file}`](../components/{safe_comp_id}.md) for implementation details.\n"
        else:
            content += "_Implementation details not available_\n"

        content += "\n---\n\n"
        content += "_Generated from API analysis_\n"

        return content

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
