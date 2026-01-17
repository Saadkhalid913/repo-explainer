"""Composes multi-repository system documentation."""

import json
from datetime import datetime
from pathlib import Path

from rich.console import Console

from .repository_loader import RepoMetadata

console = Console()


class MultiRepoDocComposer:
    """Generates system-wide documentation from multi-repo analysis."""

    def __init__(
        self,
        output_dir: Path,
        repo_metadata: list[RepoMetadata],
        analysis_results: dict,
        cross_repo_data: dict,
    ):
        """
        Initialize the multi-repo doc composer.

        Args:
            output_dir: Output directory for documentation
            repo_metadata: List of repository metadata
            analysis_results: Dictionary of analysis results per repo
            cross_repo_data: Cross-repo analysis data
        """
        self.output_dir = output_dir
        self.repo_metadata = repo_metadata
        self.analysis_results = analysis_results
        self.cross_repo_data = cross_repo_data

    def compose(self) -> dict[str, Path]:
        """
        Generate all system-level documentation.

        Returns:
            Dictionary mapping document types to file paths
        """
        composed_files = {}

        # Create directory structure
        (self.output_dir / "system").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "diagrams").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "dependencies").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "apis").mkdir(parents=True, exist_ok=True)
        (self.output_dir / "src" / "raw").mkdir(parents=True, exist_ok=True)

        # Generate system overview
        console.print("[dim]  Writing system overview...[/dim]")
        composed_files["system_overview"] = self._generate_system_overview()

        # Generate service mesh documentation
        console.print("[dim]  Writing service mesh documentation...[/dim]")
        composed_files["service_mesh"] = self._generate_service_mesh()

        # Generate cross-service data flows
        console.print("[dim]  Writing data flow documentation...[/dim]")
        composed_files["dataflow"] = self._generate_dataflow()

        # Generate aggregated tech stack
        console.print("[dim]  Writing tech stack summary...[/dim]")
        composed_files["tech_stack"] = self._generate_tech_stack()

        # Generate dependency documentation
        console.print("[dim]  Writing dependency documentation...[/dim]")
        composed_files.update(self._generate_dependencies())

        # Generate API contracts
        console.print("[dim]  Writing API contracts...[/dim]")
        composed_files.update(self._generate_api_contracts())

        # Generate system diagrams (Mermaid)
        console.print("[dim]  Writing system diagrams...[/dim]")
        composed_files.update(self._generate_diagrams())

        # Generate main index
        console.print("[dim]  Writing index.md...[/dim]")
        composed_files["index"] = self._generate_index()

        return composed_files

    def _generate_system_overview(self) -> Path:
        """Generate system/overview.md."""
        service_graph = self.cross_repo_data.get("service_graph", {})
        edges = service_graph.get("edges", [])

        http_count = len([e for e in edges if e.get("type") == "http"])
        event_count = len([e for e in edges if e.get("type") == "event"])

        content = f"""# System Architecture Overview

**Total Services:** {len(self.repo_metadata)}
**Analysis Date:** {self._get_timestamp()}

## Services

"""
        for meta in self.repo_metadata:
            content += f"### {meta.name}\n\n"
            if meta.url:
                content += f"- **Repository:** `{meta.url}`\n"
            else:
                content += f"- **Path:** `{meta.path}`\n"
            content += f"- **Documentation:** [View Details](../services/{meta.name}/overview.md)\n\n"

        # Add architecture summary
        content += f"\n## Communication Patterns\n\n"
        content += f"- **Total Interactions:** {len(edges)}\n"
        content += f"- **HTTP/REST calls:** {http_count}\n"
        content += f"- **Event-driven:** {event_count}\n\n"

        content += "## Diagrams\n\n"
        content += "- [Service Mesh](../diagrams/service-mesh.mermaid) - Service dependency graph\n"
        content += "- [System Architecture](../diagrams/system-architecture.mermaid) - Complete system view\n\n"

        file_path = self.output_dir / "system" / "overview.md"
        file_path.write_text(content)
        return file_path

    def _generate_service_mesh(self) -> Path:
        """Generate system/service-mesh.md."""
        mesh_data = self.cross_repo_data.get("service_mesh", {})

        content = "# Service Mesh\n\n"
        content += "This document describes how services communicate with each other.\n\n"
        content += "## Communication Patterns\n\n"

        # HTTP calls
        http_calls = mesh_data.get("http_calls", [])
        if http_calls:
            content += "### Synchronous (HTTP/REST)\n\n"
            for call in http_calls:
                caller = call.get("caller", "unknown")
                callee = call.get("callee", "unknown")
                method = call.get("method", "GET")
                endpoint = call.get("endpoint", "")
                content += f"- **{caller} → {callee}**: `{method} {endpoint}`\n"
            content += "\n"
        else:
            content += "### Synchronous (HTTP/REST)\n\n"
            content += "*No HTTP/REST communication detected*\n\n"

        # Event flows
        event_flows = self.cross_repo_data.get("event_flows", {})
        publishers = event_flows.get("publishers", {})
        if any(publishers.values()):
            content += "### Asynchronous (Events)\n\n"
            for service, events in publishers.items():
                for event in events:
                    content += f"- **{service} → Event Bus**: `{event}` event\n"
            content += "\n"
        else:
            content += "### Asynchronous (Events)\n\n"
            content += "*No event-driven communication detected*\n\n"

        # Service dependency diagram
        content += "## Service Dependencies\n\n"
        content += "See [service mesh diagram](../diagrams/service-mesh.mermaid) for visual representation.\n\n"

        file_path = self.output_dir / "system" / "service-mesh.md"
        file_path.write_text(content)
        return file_path

    def _generate_dataflow(self) -> Path:
        """Generate system/dataflow.md."""
        content = "# Cross-Service Data Flows\n\n"

        service_graph = self.cross_repo_data.get("service_graph", {})
        edges = service_graph.get("edges", [])

        if edges:
            content += "## Data Flow Patterns\n\n"

            # Group by source service
            flows_by_source = {}
            for edge in edges:
                source = edge.get("source")
                if source not in flows_by_source:
                    flows_by_source[source] = []
                flows_by_source[source].append(edge)

            for source, flows in sorted(flows_by_source.items()):
                content += f"### {source}\n\n"
                for flow in flows:
                    target = flow.get("target")
                    flow_type = flow.get("type")
                    details = flow.get("details", "")
                    content += f"- **→ {target}** ({flow_type}): {details}\n"
                content += "\n"
        else:
            content += "*No cross-service data flows detected*\n\n"

        file_path = self.output_dir / "system" / "dataflow.md"
        file_path.write_text(content)
        return file_path

    def _generate_tech_stack(self) -> Path:
        """Aggregate tech stacks from all services."""
        content = "# System Technology Stack\n\n"

        # Collect languages from all services
        languages = set()
        frameworks = set()

        for meta in self.repo_metadata:
            # Try to detect language from files
            if (meta.path / "package.json").exists():
                languages.add("JavaScript/Node.js")
            if (meta.path / "requirements.txt").exists() or (meta.path / "setup.py").exists():
                languages.add("Python")
            if (meta.path / "go.mod").exists():
                languages.add("Go")
            if (meta.path / "pom.xml").exists() or (meta.path / "build.gradle").exists():
                languages.add("Java")
            if (meta.path / "Gemfile").exists():
                languages.add("Ruby")

        content += "## Languages\n\n"
        if languages:
            for lang in sorted(languages):
                content += f"- {lang}\n"
        else:
            content += "*No language information detected*\n"
        content += "\n"

        content += "## By Service\n\n"
        for meta in self.repo_metadata:
            content += f"### {meta.name}\n\n"

            # Check for tech stack file in service docs
            tech_file = self.output_dir / "services" / meta.name / "src" / "raw" / "tech-stack.txt"
            if tech_file.exists():
                content += f"See [detailed tech stack](../services/{meta.name}/tech-stack/overview.md)\n\n"
            else:
                content += "*Tech stack information not available*\n\n"

        file_path = self.output_dir / "system" / "tech-stack.md"
        file_path.write_text(content)
        return file_path

    def _generate_dependencies(self) -> dict[str, Path]:
        """Generate dependency documentation."""
        files = {}

        # Inter-service dependencies
        content = "# Inter-Service Dependencies\n\n"
        content += "This document shows how services depend on each other.\n\n"

        service_graph = self.cross_repo_data.get("service_graph", {})
        edges = service_graph.get("edges", [])

        # Build dependency map
        depends_on = {}  # service -> [services it depends on]
        used_by = {}     # service -> [services that depend on it]

        for edge in edges:
            source = edge["source"]
            target = edge["target"]

            if source not in depends_on:
                depends_on[source] = []
            depends_on[source].append(target)

            if target not in used_by:
                used_by[target] = []
            used_by[target].append(source)

        for meta in self.repo_metadata:
            content += f"## {meta.name}\n\n"

            # Dependencies
            deps = list(set(depends_on.get(meta.name, [])))
            content += f"**Depends on:** {', '.join(deps) if deps else 'None (leaf service)'}\n\n"

            # Dependents
            dependents = list(set(used_by.get(meta.name, [])))
            content += f"**Used by:** {', '.join(dependents) if dependents else 'None'}\n\n"

        inter_service_file = self.output_dir / "dependencies" / "inter-service.md"
        inter_service_file.write_text(content)
        files["inter_service_deps"] = inter_service_file

        # Shared libraries
        shared_deps = self.cross_repo_data.get("shared_dependencies", {})
        content = "# Shared Libraries\n\n"
        content += "External packages used by multiple services:\n\n"

        if shared_deps:
            for package, services in sorted(shared_deps.items()):
                content += f"## `{package}`\n\n"
                content += f"**Used by:** {', '.join(services)}\n\n"
        else:
            content += "*No shared dependencies detected across services*\n\n"

        shared_file = self.output_dir / "dependencies" / "shared-libraries.md"
        shared_file.write_text(content)
        files["shared_libraries"] = shared_file

        # Dependencies overview
        overview_content = "# Dependencies Overview\n\n"
        overview_content += f"**Total Services:** {len(self.repo_metadata)}\n"
        overview_content += f"**Shared External Packages:** {len(shared_deps)}\n\n"

        overview_content += "## Documentation\n\n"
        overview_content += "- [Inter-Service Dependencies](inter-service.md) - How services depend on each other\n"
        overview_content += "- [Shared Libraries](shared-libraries.md) - Common external packages\n\n"

        overview_file = self.output_dir / "dependencies" / "overview.md"
        overview_file.write_text(overview_content)
        files["dependencies_overview"] = overview_file

        return files

    def _generate_api_contracts(self) -> dict[str, Path]:
        """Generate API contract documentation."""
        files = {}

        api_contracts = self.cross_repo_data.get("api_contracts", {})
        endpoints = api_contracts.get("endpoints", [])

        content = "# API Contracts\n\n"
        content += f"**Total Endpoints:** {len(endpoints)}\n\n"

        if endpoints:
            # Group by service
            by_service = {}
            for endpoint in endpoints:
                service = endpoint.get("service", "unknown")
                if service not in by_service:
                    by_service[service] = []
                by_service[service].append(endpoint)

            for service, service_endpoints in sorted(by_service.items()):
                content += f"## {service}\n\n"
                for ep in service_endpoints:
                    endpoint_name = ep.get("endpoint", "")
                    component = ep.get("component", "")
                    content += f"- `{endpoint_name}`"
                    if component:
                        content += f" (from {component})"
                    content += "\n"
                content += "\n"
        else:
            content += "*No API endpoints detected*\n\n"

        api_file = self.output_dir / "apis" / "overview.md"
        api_file.write_text(content)
        files["api_overview"] = api_file

        return files

    def _generate_diagrams(self) -> dict[str, Path]:
        """Generate and save system-level diagrams (Mermaid)."""
        files = {}

        # Service mesh diagram
        mermaid_content = self._generate_service_mesh_mermaid()
        mermaid_file = self.output_dir / "diagrams" / "service-mesh.mermaid"
        mermaid_file.write_text(mermaid_content)
        files["service_mesh_diagram"] = mermaid_file

        # System architecture diagram
        arch_content = self._generate_system_architecture_mermaid()
        arch_file = self.output_dir / "diagrams" / "system-architecture.mermaid"
        arch_file.write_text(arch_content)
        files["system_architecture_diagram"] = arch_file

        # Note: SVG rendering would be done by mmdc if available
        # For now, we just generate the .mermaid source files

        return files

    def _generate_index(self) -> Path:
        """Generate main index.md."""
        content = "# System Documentation\n\n"
        content += f"**Analysis Date:** {self._get_timestamp()}\n"
        content += f"**Services Analyzed:** {len(self.repo_metadata)}\n\n"

        content += "## Services\n\n"
        for meta in self.repo_metadata:
            content += f"- [{meta.name}](services/{meta.name}/index.md)\n"
        content += "\n"

        content += "## System Views\n\n"
        content += "- [System Architecture](system/overview.md) - Complete system overview\n"
        content += "- [Service Mesh](system/service-mesh.md) - Inter-service communication\n"
        content += "- [Data Flows](system/dataflow.md) - Cross-service data flows\n"
        content += "- [Technology Stack](system/tech-stack.md) - Aggregated tech stack\n\n"

        content += "## Dependencies\n\n"
        content += "- [Overview](dependencies/overview.md) - Dependency summary\n"
        content += "- [Inter-Service Dependencies](dependencies/inter-service.md) - Service dependencies\n"
        content += "- [Shared Libraries](dependencies/shared-libraries.md) - Common packages\n\n"

        content += "## API Contracts\n\n"
        content += "- [API Overview](apis/overview.md) - All API endpoints\n\n"

        content += "## Diagrams\n\n"
        content += "- [Service Mesh](diagrams/service-mesh.mermaid) - Service dependency graph\n"
        content += "- [System Architecture](diagrams/system-architecture.mermaid) - System overview\n\n"

        file_path = self.output_dir / "index.md"
        file_path.write_text(content)
        return file_path

    def _generate_service_mesh_mermaid(self) -> str:
        """Generate Mermaid diagram for service mesh."""
        service_graph = self.cross_repo_data.get("service_graph", {})
        nodes = service_graph.get("nodes", [])
        edges = service_graph.get("edges", [])

        mermaid = "graph LR\n"

        # Add nodes
        node_ids = {}
        for i, node in enumerate(nodes):
            node_id = f"S{i}"
            node_ids[node] = node_id
            safe_name = node.replace("-", "_").replace(" ", "_")
            mermaid += f"    {node_id}[{node}]\n"

        # Add edges
        for edge in edges:
            source = node_ids.get(edge["source"])
            target = node_ids.get(edge["target"])

            if source and target:
                edge_type = edge.get("type", "")
                label = f"|{edge_type}|" if edge_type else ""
                mermaid += f"    {source} -->{label} {target}\n"

        if not edges:
            mermaid += "    note[No inter-service dependencies detected]\n"

        return mermaid

    def _generate_system_architecture_mermaid(self) -> str:
        """Generate comprehensive system architecture diagram."""
        # Same as service mesh for now, could be enhanced later
        return self._generate_service_mesh_mermaid()

    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        return datetime.now().strftime("%Y-%m-%d")
