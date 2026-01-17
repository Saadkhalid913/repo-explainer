"""Diagram generator for Mermaid diagrams."""

import subprocess
import shutil
from pathlib import Path
from typing import Optional

from repo_explainer.models import ComponentInfo, DiagramInfo, DiagramType, RepositoryInfo


class DiagramGenerator:
    """Generates Mermaid diagrams from analysis data."""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.diagrams_dir = output_dir / "architecture" / "diagrams"
        self.diagrams_dir.mkdir(parents=True, exist_ok=True)
        self._mmdc_path = shutil.which("mmdc")

    def _convert_to_png(self, mmd_path: Path) -> Optional[Path]:
        """Convert a .mmd file to PNG using mermaid-cli."""
        if not self._mmdc_path:
            return None

        png_path = mmd_path.with_suffix(".png")
        try:
            result = subprocess.run(
                [self._mmdc_path, "-i", str(mmd_path), "-o", str(png_path), "-b", "transparent"],
                capture_output=True,
                text=True,
                timeout=60,
            )
            if result.returncode == 0 and png_path.exists():
                return png_path
        except (subprocess.TimeoutExpired, subprocess.SubprocessError):
            pass
        return None

    def generate_architecture_diagram(
        self,
        repo_info: RepositoryInfo,
        components: list[ComponentInfo],
        llm_diagram: Optional[str] = None,
    ) -> DiagramInfo:
        """Generate high-level architecture diagram."""
        if llm_diagram and self._validate_mermaid(llm_diagram):
            mermaid_code = llm_diagram
        else:
            mermaid_code = self._generate_component_flowchart(components)

        output_path = self.diagrams_dir / "high-level.mmd"
        output_path.write_text(mermaid_code)
        
        # Convert to PNG
        png_path = self._convert_to_png(output_path)

        return DiagramInfo(
            diagram_type=DiagramType.ARCHITECTURE,
            title="High-Level Architecture",
            mermaid_code=mermaid_code,
            output_path=png_path or output_path,
            related_components=[c.id for c in components],
        )

    def generate_component_diagram(
        self,
        components: list[ComponentInfo],
        llm_diagram: Optional[str] = None,
    ) -> DiagramInfo:
        """Generate component relationship diagram."""
        if llm_diagram and self._validate_mermaid(llm_diagram):
            mermaid_code = llm_diagram
        else:
            mermaid_code = self._generate_component_relationships(components)

        output_path = self.diagrams_dir / "component-diagram.mmd"
        output_path.write_text(mermaid_code)
        
        # Convert to PNG
        png_path = self._convert_to_png(output_path)

        return DiagramInfo(
            diagram_type=DiagramType.COMPONENT,
            title="Component Relationships",
            mermaid_code=mermaid_code,
            output_path=png_path or output_path,
            related_components=[c.id for c in components],
        )

    def generate_dataflow_diagram(
        self,
        components: list[ComponentInfo],
        llm_diagram: Optional[str] = None,
    ) -> DiagramInfo:
        """Generate data flow diagram."""
        if llm_diagram and self._validate_mermaid(llm_diagram):
            mermaid_code = llm_diagram
        else:
            mermaid_code = self._generate_basic_dataflow(components)

        output_path = self.diagrams_dir / "dataflow.mmd"
        output_path.write_text(mermaid_code)
        
        # Convert to PNG
        png_path = self._convert_to_png(output_path)

        return DiagramInfo(
            diagram_type=DiagramType.DATAFLOW,
            title="Data Flow",
            mermaid_code=mermaid_code,
            output_path=png_path or output_path,
            related_components=[c.id for c in components],
        )

    def _generate_component_flowchart(
        self, components: list[ComponentInfo]
    ) -> str:
        """Generate a basic component flowchart."""
        lines = ["flowchart LR"]

        # Create nodes for each component
        for component in components:
            node_id = self._sanitize_id(component.id)
            node_label = component.name
            node_type = component.component_type

            # Use different shapes based on type
            if node_type == "service":
                lines.append(f'    {node_id}["{node_label}"]')
            elif node_type == "module":
                lines.append(f'    {node_id}("{node_label}")')
            elif node_type == "package":
                lines.append(f'    {node_id}[["{node_label}"]]')
            else:
                lines.append(f'    {node_id}["{node_label}"]')

        # Add relationships based on dependencies
        for component in components:
            node_id = self._sanitize_id(component.id)
            for dep in component.dependencies:
                dep_id = self._sanitize_id(dep)
                lines.append(f"    {node_id} --> {dep_id}")

        return "\n".join(lines)

    def _generate_component_relationships(
        self, components: list[ComponentInfo]
    ) -> str:
        """Generate component relationship diagram."""
        lines = ["flowchart TD"]

        # Group by type
        services = [c for c in components if c.component_type == "service"]
        modules = [c for c in components if c.component_type == "module"]
        packages = [c for c in components if c.component_type == "package"]
        others = [
            c for c in components
            if c.component_type not in ("service", "module", "package")
        ]

        # Add subgraphs for each type
        if services:
            lines.append("    subgraph Services")
            for c in services:
                node_id = self._sanitize_id(c.id)
                lines.append(f'        {node_id}["{c.name}"]')
            lines.append("    end")

        if modules:
            lines.append("    subgraph Modules")
            for c in modules:
                node_id = self._sanitize_id(c.id)
                lines.append(f'        {node_id}("{c.name}")')
            lines.append("    end")

        if packages:
            lines.append("    subgraph Packages")
            for c in packages:
                node_id = self._sanitize_id(c.id)
                lines.append(f'        {node_id}[["{c.name}"]]')
            lines.append("    end")

        if others:
            lines.append("    subgraph Other")
            for c in others:
                node_id = self._sanitize_id(c.id)
                lines.append(f'        {node_id}["{c.name}"]')
            lines.append("    end")

        # Add edges
        for component in components:
            node_id = self._sanitize_id(component.id)
            for dep in component.dependencies:
                dep_id = self._sanitize_id(dep)
                lines.append(f"    {node_id} --> {dep_id}")

        return "\n".join(lines)

    def _generate_basic_dataflow(self, components: list[ComponentInfo]) -> str:
        """Generate a basic data flow diagram."""
        lines = [
            "flowchart TD",
            '    User["User/Client"]',
        ]

        # Add components
        for i, component in enumerate(components[:10]):  # Limit for readability
            node_id = self._sanitize_id(component.id)
            lines.append(f'    {node_id}["{component.name}"]')

        # Create simple flow
        if components:
            first = self._sanitize_id(components[0].id)
            lines.append(f"    User --> {first}")

            for i in range(len(components) - 1):
                if i >= 9:  # Respect limit
                    break
                curr = self._sanitize_id(components[i].id)
                next_c = self._sanitize_id(components[i + 1].id)
                lines.append(f"    {curr} --> {next_c}")

        return "\n".join(lines)

    def _sanitize_id(self, id_str: str) -> str:
        """Sanitize a string for use as a Mermaid node ID."""
        # Remove or replace invalid characters
        sanitized = id_str.replace("-", "_").replace(".", "_").replace("/", "_")
        # Ensure it starts with a letter
        if sanitized and not sanitized[0].isalpha():
            sanitized = "n_" + sanitized
        return sanitized or "unknown"

    def _validate_mermaid(self, diagram: str) -> bool:
        """Basic validation of Mermaid diagram syntax."""
        if not diagram or not diagram.strip():
            return False

        valid_starts = [
            "flowchart",
            "graph",
            "sequenceDiagram",
            "classDiagram",
            "erDiagram",
            "stateDiagram",
            "gantt",
            "pie",
        ]
        first_line = diagram.strip().split("\n")[0].lower()
        return any(first_line.startswith(start.lower()) for start in valid_starts)

    def import_opencode_diagram(
        self,
        diagram_path: Path,
        diagram_type: DiagramType,
        title: str,
    ) -> Optional[DiagramInfo]:
        """Import a diagram generated by OpenCode."""
        if not diagram_path.exists():
            return None

        mermaid_code = diagram_path.read_text()

        if not self._validate_mermaid(mermaid_code):
            return None

        # Copy to our diagrams directory
        dest_path = self.diagrams_dir / diagram_path.name
        dest_path.write_text(mermaid_code)
        
        # Convert to PNG
        png_path = self._convert_to_png(dest_path)

        return DiagramInfo(
            diagram_type=diagram_type,
            title=title,
            mermaid_code=mermaid_code,
            output_path=png_path or dest_path,
        )
