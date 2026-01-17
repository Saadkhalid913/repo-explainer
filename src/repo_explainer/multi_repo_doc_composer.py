"""Composes multi-repository system documentation with rich diagrams."""

from datetime import datetime
from pathlib import Path

from rich.console import Console

from .repository_loader import RepoMetadata

console = Console()


class MultiRepoDocComposer:
    """Generates system-wide documentation from multi-repo analysis with embedded diagrams."""

    def __init__(
        self,
        output_dir: Path,
        repo_metadata: list[RepoMetadata],
        analysis_results: dict,
        cross_repo_data: dict,
    ):
        self.output_dir = output_dir
        self.repo_metadata = repo_metadata
        self.analysis_results = analysis_results
        self.cross_repo_data = cross_repo_data

        # Build service info for diagrams
        self._service_info = self._build_service_info()

    def _build_service_info(self) -> dict:
        """Build service info including language detection."""
        info = {}
        for meta in self.repo_metadata:
            lang = self._detect_language(meta.path)
            info[meta.name] = {
                "language": lang,
                "path": meta.path,
                "url": meta.url,
            }
        return info

    def _detect_language(self, path: Path) -> str:
        """Detect primary language of a repository."""
        if (path / "package.json").exists():
            return "Node.js"
        if (path / "go.mod").exists():
            return "Go"
        if (path / "pom.xml").exists() or (path / "build.gradle").exists():
            return "Java"
        if (path / "requirements.txt").exists() or (path / "setup.py").exists():
            return "Python"
        if (path / "Gemfile").exists():
            return "Ruby"
        if (path / "Cargo.toml").exists():
            return "Rust"
        return "Unknown"

    def compose(self) -> dict[str, Path]:
        """Generate all system-level documentation with diagrams in separate files."""
        composed_files = {}

        # Create new directory structure
        dirs = [
            "system/components",
            "system/dataflow",
            "system/api",
            "system/dependencies",
            "system/communication",
            "system/diagrams/src",  # Pure Mermaid files go here
            "services",
        ]
        for d in dirs:
            (self.output_dir / d).mkdir(parents=True, exist_ok=True)

        # Generate all diagram files first
        console.print("[dim]  Generating diagram files...[/dim]")
        self._generate_all_diagrams()

        # Phase 1: System components documentation
        console.print("[dim]  Writing component documentation...[/dim]")
        composed_files.update(self._generate_components())

        # Phase 2: Data flow documentation
        console.print("[dim]  Writing data flow documentation...[/dim]")
        composed_files.update(self._generate_dataflow())

        # Phase 3: API documentation
        console.print("[dim]  Writing API documentation...[/dim]")
        composed_files.update(self._generate_api_docs())

        # Phase 4: Dependencies documentation
        console.print("[dim]  Writing dependency documentation...[/dim]")
        composed_files.update(self._generate_dependencies())

        # Phase 5: Communication patterns documentation
        console.print("[dim]  Writing communication patterns...[/dim]")
        composed_files.update(self._generate_communication())

        # Phase 6: System overview with diagram
        console.print("[dim]  Writing system overview...[/dim]")
        composed_files["system_overview"] = self._generate_system_overview()

        # Phase 7: Main index
        console.print("[dim]  Writing index.md...[/dim]")
        composed_files["index"] = self._generate_index()

        return composed_files

    def _generate_all_diagrams(self) -> None:
        """Generate all diagram files to system/diagrams/src/."""
        diagrams_dir = self.output_dir / "system" / "diagrams" / "src"
        service_graph = self.cross_repo_data.get("service_graph", {})
        edges = service_graph.get("edges", [])

        # C4 Context Diagram - dynamic from actual services
        (diagrams_dir / "c4-context.mermaid").write_text(self._mermaid_c4_diagram())

        # Layered Architecture - dynamic from actual services
        (diagrams_dir / "layered-architecture.mermaid").write_text(
            self._mermaid_layered_architecture()
        )

        # Data Flow - dynamic from actual edges
        (diagrams_dir / "data-flow.mermaid").write_text(self._mermaid_data_flow())

        # Service Interaction Sequence - dynamic from actual edges
        (diagrams_dir / "service-interaction.mermaid").write_text(
            self._mermaid_service_interaction()
        )

        # API Topology - dynamic from actual services
        (diagrams_dir / "api-topology.mermaid").write_text(self._mermaid_api_topology())

        # Communication Pie Chart - dynamic from actual edge types
        http_count = len([e for e in edges if e.get("type") == "http"])
        event_count = len([e for e in edges if e.get("type") == "event"])
        (diagrams_dir / "communication-types.mermaid").write_text(
            self._mermaid_communication_pie(http_count, event_count)
        )

        # Event Flow - dynamic from actual event data
        event_flows = self.cross_repo_data.get("event_flows", {})
        if event_flows.get("events") or event_flows.get("publishers"):
            (diagrams_dir / "event-flow.mermaid").write_text(
                self._mermaid_event_flow()
            )

    def _diagram_link(self, filename: str, from_depth: int = 2) -> str:
        """Generate a relative link to a diagram file."""
        prefix = "../" * from_depth
        return f"[View Diagram]({prefix}diagrams/src/{filename})"

    # =========================================================================
    # MERMAID DIAGRAM CONTENT - ALL DYNAMICALLY GENERATED FROM DATA
    # =========================================================================

    def _mermaid_c4_diagram(self) -> str:
        """Generate C4-style context diagram from actual service data."""
        service_graph = self.cross_repo_data.get("service_graph", {})
        edges = service_graph.get("edges", [])

        diagram = """graph TB
    subgraph System["System Boundary"]
"""
        # Add all actual services as nodes
        for meta in self.repo_metadata:
            lang = self._service_info.get(meta.name, {}).get("language", "Unknown")
            safe_name = meta.name.replace("-", "_").replace(".", "_")
            diagram += f'        {safe_name}["{meta.name}<br/>{lang}"]\n'

        # Add actual edges
        edge_labels = {}
        for edge in edges:
            source = edge["source"].replace("-", "_").replace(".", "_")
            target = edge["target"].replace("-", "_").replace(".", "_")
            edge_type = edge.get("type", "http")
            key = f"{source}->{target}"
            if key not in edge_labels:
                edge_labels[key] = {"source": source, "target": target, "types": []}
            edge_labels[key]["types"].append(edge_type)

        for key, data in edge_labels.items():
            label = data["types"][0].upper()
            diagram += f'        {data["source"]} -->|{label}| {data["target"]}\n'

        diagram += """    end

    User([User]) --> System"""
        return diagram

    def _mermaid_layered_architecture(self) -> str:
        """Generate layered architecture diagram from actual service data."""
        service_graph = self.cross_repo_data.get("service_graph", {})
        edges = service_graph.get("edges", [])
        layers = self._categorize_service_layers(edges)

        diagram = "graph TB\n"

        if layers["presentation"]:
            diagram += "    subgraph Presentation[Presentation Layer]\n"
            for svc in layers["presentation"]:
                safe = svc.replace("-", "_").replace(".", "_")
                diagram += f"        {safe}[{svc}]\n"
            diagram += "    end\n\n"

        if layers["business"]:
            diagram += "    subgraph Business[Business Logic Layer]\n"
            for svc in layers["business"]:
                safe = svc.replace("-", "_").replace(".", "_")
                diagram += f"        {safe}[{svc}]\n"
            diagram += "    end\n\n"

        if layers["integration"]:
            diagram += "    subgraph Integration[Integration Layer]\n"
            for svc in layers["integration"]:
                safe = svc.replace("-", "_").replace(".", "_")
                diagram += f"        {safe}[{svc}]\n"
            diagram += "    end\n\n"

        if layers["infrastructure"]:
            diagram += "    subgraph Infrastructure[Infrastructure Layer]\n"
            for svc in layers["infrastructure"]:
                safe = svc.replace("-", "_").replace(".", "_")
                diagram += f"        {safe}[{svc}]\n"
            diagram += "    end\n\n"

        # Add actual edges
        seen_edges = set()
        for edge in edges:
            source = edge["source"].replace("-", "_").replace(".", "_")
            target = edge["target"].replace("-", "_").replace(".", "_")
            key = f"{source}-{target}"
            if key not in seen_edges:
                diagram += f"    {source} --> {target}\n"
                seen_edges.add(key)

        diagram += """
    classDef presentation fill:#e1f5ff,stroke:#0277bd
    classDef business fill:#fff4e1,stroke:#f57c00
    classDef integration fill:#f0e1ff,stroke:#7b1fa2
    classDef infrastructure fill:#e1ffe1,stroke:#388e3c
"""
        for layer, style in [("presentation", "presentation"), ("business", "business"),
                            ("integration", "integration"), ("infrastructure", "infrastructure")]:
            services = layers.get(layer, [])
            if services:
                safe_names = [s.replace("-", "_").replace(".", "_") for s in services]
                diagram += f"    class {','.join(safe_names)} {style}\n"

        return diagram

    def _mermaid_data_flow(self) -> str:
        """Generate data flow diagram from actual service data."""
        service_graph = self.cross_repo_data.get("service_graph", {})
        edges = service_graph.get("edges", [])
        layers = self._categorize_service_layers(edges)

        diagram = """flowchart LR
    subgraph Input[External Input]
        Client([Client])
    end

"""
        if layers["presentation"]:
            diagram += "    subgraph Presentation\n"
            for svc in layers["presentation"]:
                safe = svc.replace("-", "_").replace(".", "_")
                diagram += f"        {safe}[{svc}]\n"
            diagram += "    end\n\n"

        if layers["business"]:
            diagram += "    subgraph Processing[Business Processing]\n"
            for svc in layers["business"]:
                safe = svc.replace("-", "_").replace(".", "_")
                diagram += f"        {safe}[{svc}]\n"
            diagram += "    end\n\n"

        if layers["integration"] or layers["infrastructure"]:
            diagram += "    subgraph Backend[Backend Services]\n"
            for svc in layers["integration"] + layers["infrastructure"]:
                safe = svc.replace("-", "_").replace(".", "_")
                diagram += f"        {safe}[{svc}]\n"
            diagram += "    end\n\n"

        # Connect client to presentation layer
        if layers["presentation"]:
            for svc in layers["presentation"]:
                safe = svc.replace("-", "_").replace(".", "_")
                diagram += f"    Client --> {safe}\n"

        # Add actual service edges
        seen = set()
        for edge in edges:
            source = edge["source"].replace("-", "_").replace(".", "_")
            target = edge["target"].replace("-", "_").replace(".", "_")
            key = f"{source}-{target}"
            if key not in seen:
                diagram += f"    {source} --> {target}\n"
                seen.add(key)

        return diagram

    def _mermaid_service_interaction(self) -> str:
        """Generate service interaction sequence diagram from actual edges."""
        service_graph = self.cross_repo_data.get("service_graph", {})
        edges = service_graph.get("edges", [])

        if not edges:
            return "sequenceDiagram\n    Note over System: No service interactions detected"

        diagram = "sequenceDiagram\n"

        # Add participants (all services involved in edges)
        participants = set()
        for edge in edges:
            participants.add(edge["source"])
            participants.add(edge["target"])

        for svc in sorted(participants):
            safe = svc.replace("-", "_").replace(".", "_")
            diagram += f"    participant {safe} as {svc}\n"

        diagram += "\n"

        # Add interactions from actual edges
        for edge in edges:
            source = edge["source"].replace("-", "_").replace(".", "_")
            target = edge["target"].replace("-", "_").replace(".", "_")
            details = edge.get("details", "")
            edge_type = edge.get("type", "http")

            if details:
                diagram += f"    {source}->>{target}: {details}\n"
            else:
                diagram += f"    {source}->>{target}: {edge_type.upper()} call\n"

        return diagram

    def _mermaid_api_topology(self) -> str:
        """Generate API topology diagram from actual service data."""
        service_graph = self.cross_repo_data.get("service_graph", {})
        edges = service_graph.get("edges", [])

        diagram = """graph TB
    subgraph External[External Clients]
        Client([Client])
    end

    subgraph APIs[API Services]
"""
        for meta in self.repo_metadata:
            safe = meta.name.replace("-", "_").replace(".", "_")
            diagram += f"        {safe}[{meta.name}]\n"

        diagram += "    end\n\n"

        # Connect client to presentation layer services
        layers = self._categorize_service_layers(edges)
        for svc in layers.get("presentation", []):
            safe = svc.replace("-", "_").replace(".", "_")
            diagram += f"    Client --> {safe}\n"

        # Add inter-service connections
        seen = set()
        for edge in edges:
            source = edge["source"].replace("-", "_").replace(".", "_")
            target = edge["target"].replace("-", "_").replace(".", "_")
            key = f"{source}-{target}"
            if key not in seen:
                edge_type = edge.get("type", "http").upper()
                diagram += f"    {source} -->|{edge_type}| {target}\n"
                seen.add(key)

        return diagram

    def _mermaid_communication_pie(self, http_count: int, event_count: int) -> str:
        """Generate communication types pie chart from actual counts."""
        if http_count == 0 and event_count == 0:
            return """pie title Communication Types
    "No communications detected" : 1"""
        return f"""pie title Communication Types
    "HTTP/REST" : {http_count if http_count > 0 else 0}
    "Events/Messages" : {event_count if event_count > 0 else 0}"""

    def _mermaid_event_flow(self) -> str:
        """Generate event flow diagram from actual event data."""
        event_flows = self.cross_repo_data.get("event_flows", {})
        publishers = event_flows.get("publishers", {})
        subscribers = event_flows.get("subscribers", {})
        events = event_flows.get("events", [])

        if not publishers and not subscribers:
            return "graph LR\n    Note[No event flows detected]"

        diagram = "graph LR\n"

        # Add event bus node
        diagram += "    EventBus[Event Bus]\n\n"

        # Add publishers
        for service, published_events in publishers.items():
            safe = service.replace("-", "_").replace(".", "_")
            diagram += f"    {safe}[{service}]\n"
            for event in published_events:
                safe_event = event.replace(".", "_").replace("-", "_")
                diagram += f"    {safe} -->|publishes| EventBus\n"

        diagram += "\n"

        # Add subscribers
        for service, subscribed_events in subscribers.items():
            safe = service.replace("-", "_").replace(".", "_")
            if service not in publishers:
                diagram += f"    {safe}[{service}]\n"
            for event in subscribed_events:
                diagram += f"    EventBus -->|delivers| {safe}\n"

        diagram += "\n    style EventBus fill:#FF6B6B,color:#fff"
        return diagram

    # =========================================================================
    # COMPONENT DOCUMENTATION
    # =========================================================================

    def _generate_components(self) -> dict[str, Path]:
        """Generate system/components/ documentation."""
        files = {}
        files["components_overview"] = self._generate_components_overview()
        files["component_relationships"] = self._generate_component_relationships()
        return files

    def _generate_components_overview(self) -> Path:
        """Generate system/components/overview.md."""
        service_graph = self.cross_repo_data.get("service_graph", {})
        edges = service_graph.get("edges", [])
        layers = self._categorize_service_layers(edges)

        content = """# System Components

## Architecture Overview

This diagram shows all services within the system boundary, their technologies, and how they communicate.

**Diagram:** """ + self._diagram_link("c4-context.mermaid", from_depth=1) + """

## Components by Layer

"""
        if layers["presentation"]:
            content += "### Presentation Layer\n\n"
            for svc in layers["presentation"]:
                lang = self._service_info.get(svc, {}).get("language", "Unknown")
                content += f"- **{svc}** ({lang})\n"
            content += "\n"

        if layers["business"]:
            content += "### Business Logic Layer\n\n"
            for svc in layers["business"]:
                lang = self._service_info.get(svc, {}).get("language", "Unknown")
                content += f"- **{svc}** ({lang})\n"
            content += "\n"

        if layers["integration"]:
            content += "### Integration Layer\n\n"
            for svc in layers["integration"]:
                lang = self._service_info.get(svc, {}).get("language", "Unknown")
                content += f"- **{svc}** ({lang})\n"
            content += "\n"

        if layers["infrastructure"]:
            content += "### Infrastructure Layer\n\n"
            for svc in layers["infrastructure"]:
                lang = self._service_info.get(svc, {}).get("language", "Unknown")
                content += f"- **{svc}** ({lang})\n"
            content += "\n"

        content += self._generate_component_matrix(edges)

        file_path = self.output_dir / "system" / "components" / "overview.md"
        file_path.write_text(content)
        return file_path

    def _generate_component_relationships(self) -> Path:
        """Generate system/components/component-relationships.md."""
        service_graph = self.cross_repo_data.get("service_graph", {})
        edges = service_graph.get("edges", [])

        content = """# Component Relationships

## Interaction Diagram

This diagram shows services organized by architectural layer with their dependencies.

**Diagram:** """ + self._diagram_link("layered-architecture.mermaid", from_depth=1) + """

## Communication Patterns

"""
        http_edges = [e for e in edges if e.get("type") == "http"]
        event_edges = [e for e in edges if e.get("type") == "event"]

        if http_edges:
            content += "### Synchronous (HTTP/REST)\n\n"
            for edge in http_edges:
                details = edge.get("details", "API call")
                content += f"- **{edge['source']}** → **{edge['target']}**: {details}\n"
            content += "\n"

        if event_edges:
            content += "### Asynchronous (Events/Messages)\n\n"
            for edge in event_edges:
                details = edge.get("details", "Event")
                content += f"- **{edge['source']}** → **{edge['target']}**: {details}\n"
            content += "\n"

        if not http_edges and not event_edges:
            content += "*No inter-service communication detected.*\n"

        file_path = self.output_dir / "system" / "components" / "component-relationships.md"
        file_path.write_text(content)
        return file_path

    def _categorize_service_layers(self, edges: list) -> dict:
        """Categorize services into architectural layers based on naming and dependencies."""
        layers = {
            "presentation": [],
            "business": [],
            "integration": [],
            "infrastructure": [],
        }

        # Build dependency maps
        depends_on = {}
        used_by = {}
        for edge in edges:
            source = edge["source"]
            target = edge["target"]
            depends_on.setdefault(source, set()).add(target)
            used_by.setdefault(target, set()).add(source)

        all_services = set(m.name for m in self.repo_metadata)

        for svc in all_services:
            svc_lower = svc.lower()

            # Presentation: front-end, ui, web, gateway, portal
            if any(x in svc_lower for x in ["front", "ui", "web", "gateway", "portal", "client"]):
                layers["presentation"].append(svc)
            # Infrastructure: queue, worker, daemon, scheduler, cache
            elif any(x in svc_lower for x in ["queue", "worker", "daemon", "scheduler", "cache", "db"]):
                layers["infrastructure"].append(svc)
            # Integration: external service integrations
            elif any(x in svc_lower for x in ["payment", "shipping", "notification", "email", "sms", "external"]):
                layers["integration"].append(svc)
            # Business: everything else
            else:
                layers["business"].append(svc)

        return layers

    def _generate_component_matrix(self, edges: list) -> str:
        """Generate component interaction matrix."""
        depends_on = {}
        used_by = {}
        for edge in edges:
            source = edge["source"]
            target = edge["target"]
            depends_on.setdefault(source, set()).add(target)
            used_by.setdefault(target, set()).add(source)

        layers = self._categorize_service_layers(edges)

        content = """
## Component Interaction Matrix

| Component | Depends On | Used By | Layer |
|-----------|------------|---------|-------|
"""
        for meta in self.repo_metadata:
            svc = meta.name
            deps = sorted(depends_on.get(svc, set()))
            dependents = sorted(used_by.get(svc, set()))

            layer = "Business"
            for layer_name, services in layers.items():
                if svc in services:
                    layer = layer_name.title()
                    break

            deps_str = ", ".join(deps) if deps else "-"
            dependents_str = ", ".join(dependents) if dependents else "-"
            content += f"| {svc} | {deps_str} | {dependents_str} | {layer} |\n"

        return content

    # =========================================================================
    # DATA FLOW DOCUMENTATION
    # =========================================================================

    def _generate_dataflow(self) -> dict[str, Path]:
        """Generate system/dataflow/ documentation."""
        files = {}
        files["dataflow_overview"] = self._generate_dataflow_overview()
        files["service_interactions"] = self._generate_service_interactions()
        return files

    def _generate_dataflow_overview(self) -> Path:
        """Generate system/dataflow/overview.md."""
        service_graph = self.cross_repo_data.get("service_graph", {})
        edges = service_graph.get("edges", [])

        content = """# Data Flow Overview

## System Data Flow

This diagram shows how data flows through the system layers.

**Diagram:** """ + self._diagram_link("data-flow.mermaid", from_depth=1) + """

## Data Flow Patterns

"""
        if edges:
            flows_by_source = {}
            for edge in edges:
                source = edge["source"]
                flows_by_source.setdefault(source, []).append(edge)

            for source, flows in sorted(flows_by_source.items()):
                content += f"### From {source}\n\n"
                for flow in flows:
                    target = flow["target"]
                    flow_type = flow.get("type", "http")
                    details = flow.get("details", "")
                    if details:
                        content += f"- **→ {target}** ({flow_type}): {details}\n"
                    else:
                        content += f"- **→ {target}** ({flow_type})\n"
                content += "\n"
        else:
            content += "*No data flows detected between services.*\n"

        file_path = self.output_dir / "system" / "dataflow" / "overview.md"
        file_path.write_text(content)
        return file_path

    def _generate_service_interactions(self) -> Path:
        """Generate system/dataflow/service-interactions.md."""
        service_graph = self.cross_repo_data.get("service_graph", {})
        edges = service_graph.get("edges", [])

        content = """# Service Interactions

## Interaction Sequence

This diagram shows the sequence of interactions between services.

**Diagram:** """ + self._diagram_link("service-interaction.mermaid", from_depth=1) + """

## Interaction Details

"""
        if edges:
            content += "| Source | Target | Type | Details |\n"
            content += "|--------|--------|------|--------|\n"
            for edge in edges:
                source = edge["source"]
                target = edge["target"]
                edge_type = edge.get("type", "http")
                details = edge.get("details", "-")
                content += f"| {source} | {target} | {edge_type} | {details} |\n"
        else:
            content += "*No service interactions detected.*\n"

        file_path = self.output_dir / "system" / "dataflow" / "service-interactions.md"
        file_path.write_text(content)
        return file_path

    # =========================================================================
    # API DOCUMENTATION
    # =========================================================================

    def _generate_api_docs(self) -> dict[str, Path]:
        """Generate system/api/ documentation."""
        files = {}
        files["api_overview"] = self._generate_api_overview()
        return files

    def _generate_api_overview(self) -> Path:
        """Generate system/api/overview.md."""
        api_contracts = self.cross_repo_data.get("api_contracts", {})
        endpoints = api_contracts.get("endpoints", [])

        content = """# API Overview

## API Topology

This diagram shows all services and how they connect.

**Diagram:** """ + self._diagram_link("api-topology.mermaid", from_depth=1) + f"""

## Endpoint Summary

**Total Endpoints Detected:** {len(endpoints)}

"""
        if endpoints:
            by_service = {}
            for ep in endpoints:
                svc = ep.get("service", "unknown")
                by_service.setdefault(svc, []).append(ep)

            for svc, eps in sorted(by_service.items()):
                content += f"### {svc}\n\n"
                for ep in eps:
                    endpoint = ep.get("endpoint", "")
                    content += f"- `{endpoint}`\n"
                content += "\n"
        else:
            content += "*No API endpoints detected.*\n"

        file_path = self.output_dir / "system" / "api" / "overview.md"
        file_path.write_text(content)
        return file_path

    # =========================================================================
    # DEPENDENCIES DOCUMENTATION
    # =========================================================================

    def _generate_dependencies(self) -> dict[str, Path]:
        """Generate system/dependencies/ documentation."""
        files = {}
        files["deps_overview"] = self._generate_deps_overview()
        files["service_graph"] = self._generate_service_graph()
        files["shared_libs"] = self._generate_shared_libraries()
        return files

    def _generate_deps_overview(self) -> Path:
        """Generate system/dependencies/overview.md."""
        service_graph = self.cross_repo_data.get("service_graph", {})
        edges = service_graph.get("edges", [])
        shared_deps = self.cross_repo_data.get("shared_dependencies", {})

        content = f"""# Dependencies Overview

**Total Services:** {len(self.repo_metadata)}
**Inter-Service Dependencies:** {len(edges)}
**Shared External Packages:** {len(shared_deps)}

## Quick Links

- [Service Dependency Graph](service-graph.md)
- [Shared Libraries](shared-libraries.md)

## Dependency Summary

"""
        depends_on = {}
        used_by = {}
        for edge in edges:
            source = edge["source"]
            target = edge["target"]
            depends_on.setdefault(source, set()).add(target)
            used_by.setdefault(target, set()).add(source)

        content += "| Service | Dependencies | Dependents |\n"
        content += "|---------|--------------|------------|\n"

        for meta in self.repo_metadata:
            svc = meta.name
            deps = len(depends_on.get(svc, set()))
            dependents = len(used_by.get(svc, set()))
            content += f"| {svc} | {deps} | {dependents} |\n"

        file_path = self.output_dir / "system" / "dependencies" / "overview.md"
        file_path.write_text(content)
        return file_path

    def _generate_service_graph(self) -> Path:
        """Generate system/dependencies/service-graph.md."""
        service_graph = self.cross_repo_data.get("service_graph", {})
        edges = service_graph.get("edges", [])

        content = """# Service Dependency Graph

## Layered Architecture

**Diagram:** """ + self._diagram_link("layered-architecture.mermaid", from_depth=1) + """

## Dependency Analysis

### Upstream Dependencies (What depends on this service)

"""
        used_by = {}
        for edge in edges:
            target = edge["target"]
            source = edge["source"]
            used_by.setdefault(target, set()).add(source)

        content += "| Service | Depended On By | Count |\n"
        content += "|---------|----------------|-------|\n"

        for meta in self.repo_metadata:
            svc = meta.name
            dependents = sorted(used_by.get(svc, set()))
            count = len(dependents)
            deps_str = ", ".join(dependents) if dependents else "-"
            content += f"| {svc} | {deps_str} | {count} |\n"

        content += """

### Downstream Dependencies (What this service depends on)

"""
        depends_on = {}
        for edge in edges:
            source = edge["source"]
            target = edge["target"]
            depends_on.setdefault(source, set()).add(target)

        content += "| Service | Depends On | Count |\n"
        content += "|---------|------------|-------|\n"

        for meta in self.repo_metadata:
            svc = meta.name
            deps = sorted(depends_on.get(svc, set()))
            count = len(deps)
            deps_str = ", ".join(deps) if deps else "-"
            content += f"| {svc} | {deps_str} | {count} |\n"

        file_path = self.output_dir / "system" / "dependencies" / "service-graph.md"
        file_path.write_text(content)
        return file_path

    def _generate_shared_libraries(self) -> Path:
        """Generate system/dependencies/shared-libraries.md."""
        shared_deps = self.cross_repo_data.get("shared_dependencies", {})

        content = """# Shared Libraries

External packages used by multiple services.

"""
        if shared_deps:
            content += "| Package | Used By | Service Count |\n"
            content += "|---------|---------|---------------|\n"

            for package, services in sorted(shared_deps.items(), key=lambda x: -len(x[1])):
                services_str = ", ".join(sorted(services))
                content += f"| `{package}` | {services_str} | {len(services)} |\n"
        else:
            content += "*No shared dependencies detected across services.*\n"

        file_path = self.output_dir / "system" / "dependencies" / "shared-libraries.md"
        file_path.write_text(content)
        return file_path

    # =========================================================================
    # COMMUNICATION DOCUMENTATION
    # =========================================================================

    def _generate_communication(self) -> dict[str, Path]:
        """Generate system/communication/ documentation."""
        files = {}
        files["comm_overview"] = self._generate_communication_overview()
        return files

    def _generate_communication_overview(self) -> Path:
        """Generate system/communication/overview.md."""
        service_graph = self.cross_repo_data.get("service_graph", {})
        edges = service_graph.get("edges", [])
        event_flows = self.cross_repo_data.get("event_flows", {})

        http_count = len([e for e in edges if e.get("type") == "http"])
        event_count = len([e for e in edges if e.get("type") == "event"])
        total = http_count + event_count

        content = """# Communication Patterns

## Overview

**Diagram:** """ + self._diagram_link("communication-types.mermaid", from_depth=1) + f"""

## Statistics

| Pattern | Count | Percentage |
|---------|-------|------------|
| HTTP/REST (Sync) | {http_count} | {(http_count/total*100) if total else 0:.0f}% |
| Events (Async) | {event_count} | {(event_count/total*100) if total else 0:.0f}% |
| **Total** | **{total}** | **100%** |

## Synchronous Communication (HTTP/REST)

"""
        http_edges = [e for e in edges if e.get("type") == "http"]
        if http_edges:
            content += "| Source | Target | Details |\n"
            content += "|--------|--------|--------|\n"
            for edge in http_edges:
                details = edge.get("details", "-")
                content += f"| {edge['source']} | {edge['target']} | {details} |\n"
        else:
            content += "*No HTTP/REST communication detected.*\n"

        # Check for async communication
        publishers = event_flows.get("publishers", {})
        subscribers = event_flows.get("subscribers", {})

        if publishers or subscribers or event_count > 0:
            content += """

## Asynchronous Communication (Events)

**Diagram:** """ + self._diagram_link("event-flow.mermaid", from_depth=1) + """

"""
            if publishers:
                content += "### Publishers\n\n"
                for service, events in publishers.items():
                    content += f"- **{service}**: {', '.join(events) if events else 'Unknown events'}\n"
                content += "\n"

            if subscribers:
                content += "### Subscribers\n\n"
                for service, events in subscribers.items():
                    content += f"- **{service}**: {', '.join(events) if events else 'Unknown events'}\n"
                content += "\n"

        file_path = self.output_dir / "system" / "communication" / "overview.md"
        file_path.write_text(content)
        return file_path

    # =========================================================================
    # SYSTEM OVERVIEW & INDEX
    # =========================================================================

    def _generate_system_overview(self) -> Path:
        """Generate system/overview.md - main system page."""
        service_graph = self.cross_repo_data.get("service_graph", {})
        edges = service_graph.get("edges", [])

        http_count = len([e for e in edges if e.get("type") == "http"])
        event_count = len([e for e in edges if e.get("type") == "event"])

        content = f"""# System Architecture Overview

**Total Services:** {len(self.repo_metadata)}
**Analysis Date:** {self._get_timestamp()}

## Architecture Diagram

**Diagram:** [View Layered Architecture](diagrams/src/layered-architecture.mermaid)

## System Metrics

| Metric | Value |
|--------|-------|
| Services | {len(self.repo_metadata)} |
| Inter-Service Connections | {len(edges)} |
| HTTP/REST Calls | {http_count} |
| Event-Driven Flows | {event_count} |

## Services

"""
        for meta in self.repo_metadata:
            lang = self._service_info.get(meta.name, {}).get("language", "Unknown")
            content += f"### {meta.name}\n\n"
            content += f"- **Language:** {lang}\n"
            if meta.url:
                content += f"- **Repository:** `{meta.url}`\n"
            content += f"- **Documentation:** [View Details](../services/{meta.name}/overview.md)\n\n"

        content += """## Quick Links

- [Component Architecture](components/overview.md)
- [Data Flow](dataflow/overview.md)
- [API Documentation](api/overview.md)
- [Dependencies](dependencies/overview.md)
- [Communication Patterns](communication/overview.md)

"""
        file_path = self.output_dir / "system" / "overview.md"
        file_path.write_text(content)
        return file_path

    def _generate_index(self) -> Path:
        """Generate main index.md entry point."""
        content = f"""# System Documentation

**Analysis Date:** {self._get_timestamp()}
**Services Analyzed:** {len(self.repo_metadata)}

## System Overview

This documentation describes a distributed system with {len(self.repo_metadata)} services.

**Architecture Diagram:** [View Layered Architecture](system/diagrams/src/layered-architecture.mermaid)

## Documentation Structure

### System-Level Documentation

| Section | Description |
|---------|-------------|
| [System Overview](system/overview.md) | High-level architecture and metrics |
| [Components](system/components/overview.md) | Service components and relationships |
| [Data Flow](system/dataflow/overview.md) | Data movement through the system |
| [API Documentation](system/api/overview.md) | API endpoints and interaction flows |
| [Dependencies](system/dependencies/overview.md) | Service dependency analysis |
| [Communication](system/communication/overview.md) | Communication patterns |

### Individual Services

"""
        for meta in self.repo_metadata:
            lang = self._service_info.get(meta.name, {}).get("language", "Unknown")
            content += f"- [{meta.name}](services/{meta.name}/index.md) ({lang})\n"

        content += """

---
*Generated by repo-explainer*
"""
        file_path = self.output_dir / "index.md"
        file_path.write_text(content)
        return file_path

    def _get_timestamp(self) -> str:
        """Get current timestamp string."""
        return datetime.now().strftime("%Y-%m-%d")
