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
        """Generate all system-level documentation with embedded diagrams."""
        composed_files = {}

        # Create new directory structure
        dirs = [
            "system/components",
            "system/dataflow",
            "system/api",
            "system/dependencies",
            "system/communication",
            "services",
        ]
        for d in dirs:
            (self.output_dir / d).mkdir(parents=True, exist_ok=True)

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

    # =========================================================================
    # COMPONENT DOCUMENTATION
    # =========================================================================

    def _generate_components(self) -> dict[str, Path]:
        """Generate system/components/ documentation."""
        files = {}

        # Component overview with C4 context diagram
        files["components_overview"] = self._generate_components_overview()

        # Component relationships with interaction diagram
        files["component_relationships"] = self._generate_component_relationships()

        return files

    def _generate_components_overview(self) -> Path:
        """Generate system/components/overview.md with C4 diagram."""
        service_graph = self.cross_repo_data.get("service_graph", {})
        nodes = service_graph.get("nodes", [])
        edges = service_graph.get("edges", [])

        # Build layers based on dependencies
        layers = self._categorize_service_layers(edges)

        content = """# System Components

## Architecture Overview

"""
        # C4 Context Diagram
        content += self._generate_c4_diagram()

        content += """

## Components by Layer

"""
        # Presentation Layer
        if layers["presentation"]:
            content += "### Presentation Layer\n\n"
            for svc in layers["presentation"]:
                lang = self._service_info.get(svc, {}).get("language", "Unknown")
                content += f"- **{svc}** ({lang}) - Customer-facing interface\n"
            content += "\n"

        # Business Logic Layer
        if layers["business"]:
            content += "### Business Logic Layer\n\n"
            for svc in layers["business"]:
                lang = self._service_info.get(svc, {}).get("language", "Unknown")
                content += f"- **{svc}** ({lang}) - Core business operations\n"
            content += "\n"

        # Integration Layer
        if layers["integration"]:
            content += "### Integration Layer\n\n"
            for svc in layers["integration"]:
                lang = self._service_info.get(svc, {}).get("language", "Unknown")
                content += f"- **{svc}** ({lang}) - External integrations\n"
            content += "\n"

        # Infrastructure Layer
        if layers["infrastructure"]:
            content += "### Infrastructure Layer\n\n"
            for svc in layers["infrastructure"]:
                lang = self._service_info.get(svc, {}).get("language", "Unknown")
                content += f"- **{svc}** ({lang}) - Infrastructure services\n"
            content += "\n"

        # Component Matrix
        content += self._generate_component_matrix(edges)

        file_path = self.output_dir / "system" / "components" / "overview.md"
        file_path.write_text(content)
        return file_path

    def _generate_c4_diagram(self) -> str:
        """Generate C4-style context diagram."""
        service_graph = self.cross_repo_data.get("service_graph", {})
        edges = service_graph.get("edges", [])

        diagram = """```mermaid
graph TB
    subgraph System["System Boundary"]
"""
        # Add all services as nodes
        for meta in self.repo_metadata:
            lang = self._service_info.get(meta.name, {}).get("language", "Unknown")
            safe_name = meta.name.replace("-", "_")
            diagram += f'        {safe_name}["{meta.name}<br/>{lang}"]\n'

        # Add edges with labels
        edge_labels = {}
        for edge in edges:
            source = edge["source"].replace("-", "_")
            target = edge["target"].replace("-", "_")
            edge_type = edge.get("type", "http")
            key = f"{source}->{target}"
            if key not in edge_labels:
                edge_labels[key] = {"source": source, "target": target, "types": []}
            edge_labels[key]["types"].append(edge_type)

        for key, data in edge_labels.items():
            label = data["types"][0].upper()
            diagram += f'        {data["source"]} -->|{label}| {data["target"]}\n'

        diagram += """    end

    User([Customer]) --> System
```"""
        return diagram

    def _generate_component_relationships(self) -> Path:
        """Generate system/components/component-relationships.md."""
        service_graph = self.cross_repo_data.get("service_graph", {})
        edges = service_graph.get("edges", [])

        content = """# Component Relationships

## Interaction Diagram

"""
        # Generate layered architecture diagram
        content += self._generate_layered_architecture_diagram()

        content += """

## Communication Patterns

"""
        # Group edges by type
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

        file_path = self.output_dir / "system" / "components" / "component-relationships.md"
        file_path.write_text(content)
        return file_path

    def _generate_layered_architecture_diagram(self) -> str:
        """Generate layered architecture diagram."""
        service_graph = self.cross_repo_data.get("service_graph", {})
        edges = service_graph.get("edges", [])
        layers = self._categorize_service_layers(edges)

        diagram = """```mermaid
graph TB
"""
        # Define layer subgraphs
        if layers["presentation"]:
            diagram += "    subgraph Presentation[Presentation Layer]\n"
            for svc in layers["presentation"]:
                safe = svc.replace("-", "_")
                diagram += f"        {safe}[{svc}]\n"
            diagram += "    end\n\n"

        if layers["business"]:
            diagram += "    subgraph Business[Business Logic Layer]\n"
            for svc in layers["business"]:
                safe = svc.replace("-", "_")
                diagram += f"        {safe}[{svc}]\n"
            diagram += "    end\n\n"

        if layers["integration"]:
            diagram += "    subgraph Integration[Integration Layer]\n"
            for svc in layers["integration"]:
                safe = svc.replace("-", "_")
                diagram += f"        {safe}[{svc}]\n"
            diagram += "    end\n\n"

        if layers["infrastructure"]:
            diagram += "    subgraph Infrastructure[Infrastructure Layer]\n"
            for svc in layers["infrastructure"]:
                safe = svc.replace("-", "_")
                diagram += f"        {safe}[{svc}]\n"
            diagram += "    end\n\n"

        # Add edges
        seen_edges = set()
        for edge in edges:
            source = edge["source"].replace("-", "_")
            target = edge["target"].replace("-", "_")
            key = f"{source}-{target}"
            if key not in seen_edges:
                diagram += f"    {source} --> {target}\n"
                seen_edges.add(key)

        # Style layers
        diagram += """
    classDef presentation fill:#e1f5ff,stroke:#0277bd
    classDef business fill:#fff4e1,stroke:#f57c00
    classDef integration fill:#f0e1ff,stroke:#7b1fa2
    classDef infrastructure fill:#e1ffe1,stroke:#388e3c
"""
        # Apply styles
        for layer, style in [("presentation", "presentation"), ("business", "business"),
                            ("integration", "integration"), ("infrastructure", "infrastructure")]:
            services = layers.get(layer, [])
            if services:
                safe_names = [s.replace("-", "_") for s in services]
                diagram += f"    class {','.join(safe_names)} {style}\n"

        diagram += "```"
        return diagram

    def _categorize_service_layers(self, edges: list) -> dict:
        """Categorize services into architectural layers."""
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
            deps = depends_on.get(svc, set())
            dependents = used_by.get(svc, set())

            # Heuristics for layer categorization
            svc_lower = svc.lower()

            # Presentation: has many deps, no dependents, or named front-end/ui/web
            if "front" in svc_lower or "ui" in svc_lower or "web" in svc_lower:
                layers["presentation"].append(svc)
            # Infrastructure: queue, worker, daemon
            elif "queue" in svc_lower or "worker" in svc_lower or "daemon" in svc_lower:
                layers["infrastructure"].append(svc)
            # Integration: payment, shipping, notification (external integrations)
            elif any(x in svc_lower for x in ["payment", "shipping", "notification", "email", "sms"]):
                layers["integration"].append(svc)
            # Business: everything else
            else:
                layers["business"].append(svc)

        return layers

    def _generate_component_matrix(self, edges: list) -> str:
        """Generate component interaction matrix."""
        # Build maps
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

            # Determine layer
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

        # Data flow overview
        files["dataflow_overview"] = self._generate_dataflow_overview()

        # User journey documentation
        files["user_journey"] = self._generate_user_journey()

        # Request/response patterns
        files["request_response"] = self._generate_request_response()

        return files

    def _generate_dataflow_overview(self) -> Path:
        """Generate system/dataflow/overview.md."""
        service_graph = self.cross_repo_data.get("service_graph", {})
        edges = service_graph.get("edges", [])

        content = """# Data Flow Overview

## System Data Flow

"""
        # High-level data flow diagram
        content += self._generate_data_flow_diagram()

        content += """

## Data Flow Patterns

"""
        # Group by source
        flows_by_source = {}
        for edge in edges:
            source = edge["source"]
            flows_by_source.setdefault(source, []).append(edge)

        for source, flows in sorted(flows_by_source.items()):
            content += f"### From {source}\n\n"
            for flow in flows:
                target = flow["target"]
                flow_type = flow.get("type", "http")
                details = flow.get("details", "Data transfer")
                content += f"- **→ {target}** ({flow_type}): {details}\n"
            content += "\n"

        file_path = self.output_dir / "system" / "dataflow" / "overview.md"
        file_path.write_text(content)
        return file_path

    def _generate_data_flow_diagram(self) -> str:
        """Generate high-level data flow diagram."""
        service_graph = self.cross_repo_data.get("service_graph", {})
        edges = service_graph.get("edges", [])

        diagram = """```mermaid
flowchart LR
    subgraph Input[User Input]
        Browser([Browser])
    end

"""
        # Group services by their role
        layers = self._categorize_service_layers(edges)

        if layers["presentation"]:
            diagram += "    subgraph Presentation\n"
            for svc in layers["presentation"]:
                safe = svc.replace("-", "_")
                diagram += f"        {safe}[{svc}]\n"
            diagram += "    end\n\n"

        if layers["business"]:
            diagram += "    subgraph Processing[Business Processing]\n"
            for svc in layers["business"]:
                safe = svc.replace("-", "_")
                diagram += f"        {safe}[{svc}]\n"
            diagram += "    end\n\n"

        if layers["integration"] or layers["infrastructure"]:
            diagram += "    subgraph Backend[Backend Services]\n"
            for svc in layers["integration"] + layers["infrastructure"]:
                safe = svc.replace("-", "_")
                diagram += f"        {safe}[{svc}]\n"
            diagram += "    end\n\n"

        # Connect browser to presentation
        if layers["presentation"]:
            for svc in layers["presentation"]:
                safe = svc.replace("-", "_")
                diagram += f"    Browser --> {safe}\n"

        # Add service edges
        seen = set()
        for edge in edges:
            source = edge["source"].replace("-", "_")
            target = edge["target"].replace("-", "_")
            key = f"{source}-{target}"
            if key not in seen:
                diagram += f"    {source} --> {target}\n"
                seen.add(key)

        diagram += "```"
        return diagram

    def _generate_user_journey(self) -> Path:
        """Generate system/dataflow/user-journey.md with journey diagrams."""
        service_graph = self.cross_repo_data.get("service_graph", {})
        edges = service_graph.get("edges", [])

        content = """# End-to-End User Journeys

## Typical User Flow

"""
        # Generate user journey diagram
        content += self._generate_user_journey_diagram()

        content += """

## Journey Steps

### 1. Browse Products
User browses the catalog through the front-end service.

### 2. Add to Cart
Items are added to the shopping cart.

### 3. Checkout
Order is placed, triggering orchestration across multiple services.

### 4. Fulfillment
Payment is processed and shipping is scheduled.

"""
        file_path = self.output_dir / "system" / "dataflow" / "user-journey.md"
        file_path.write_text(content)
        return file_path

    def _generate_user_journey_diagram(self) -> str:
        """Generate user journey flowchart."""
        return """```mermaid
graph TB
    subgraph Browse[Browse Phase]
        A[Customer lands] --> B[View Catalogue]
        B --> C[View Product Details]
    end

    subgraph Cart[Cart Phase]
        C --> D[Add to Cart]
        D --> E[View Cart]
        E --> F{Continue Shopping?}
        F -->|Yes| B
        F -->|No| G[Proceed to Checkout]
    end

    subgraph Checkout[Checkout Phase]
        G --> H[Login/Register]
        H --> I[Select Address]
        I --> J[Select Payment Method]
        J --> K[Place Order]
    end

    subgraph Processing[Processing Phase]
        K --> L[Validate User]
        L --> M[Process Payment]
        M --> N[Create Shipping]
        N --> O[Confirm Order]
    end

    O --> P[Customer Notification]

    style Browse fill:#e1f5ff
    style Cart fill:#fff4e1
    style Checkout fill:#f0e1ff
    style Processing fill:#e1ffe1
```"""

    def _generate_request_response(self) -> Path:
        """Generate system/dataflow/request-response.md with sequence diagrams."""
        content = """# Request/Response Patterns

## Order Processing Sequence

"""
        # Generate checkout sequence diagram
        content += self._generate_checkout_sequence_diagram()

        content += """

## API Gateway Pattern

The front-end acts as an API gateway, routing requests to backend services.

"""
        content += self._generate_gateway_diagram()

        file_path = self.output_dir / "system" / "dataflow" / "request-response.md"
        file_path.write_text(content)
        return file_path

    def _generate_checkout_sequence_diagram(self) -> str:
        """Generate checkout flow sequence diagram."""
        return """```mermaid
sequenceDiagram
    actor Customer
    participant FE as Front-End
    participant Orders
    participant User
    participant Cart
    participant Payment
    participant Shipping

    Customer->>FE: POST /orders
    FE->>Orders: POST /orders

    par Fetch User Data
        Orders->>User: GET /customers/{id}
        Orders->>User: GET /addresses/{id}
        Orders->>User: GET /cards/{id}
    and Fetch Cart
        Orders->>Cart: GET /carts/{id}/items
    end

    Orders->>Payment: POST /paymentAuth
    Payment-->>Orders: Payment authorized

    Orders->>Shipping: POST /shipping
    Shipping-->>Orders: Shipping created

    Orders-->>FE: Order created
    FE-->>Customer: Order confirmation
```"""

    def _generate_gateway_diagram(self) -> str:
        """Generate API gateway pattern diagram."""
        layers = self._categorize_service_layers(
            self.cross_repo_data.get("service_graph", {}).get("edges", [])
        )

        diagram = """```mermaid
graph LR
    Client[Customer Browser]
"""
        if layers["presentation"]:
            fe = layers["presentation"][0].replace("-", "_")
            diagram += f"    Client --> {fe}[Front-End Gateway]\n\n"

            # Connect to business services
            for svc in layers["business"]:
                safe = svc.replace("-", "_")
                diagram += f"    {fe} -->|Route| {safe}[{svc}]\n"

        diagram += "```"
        return diagram

    # =========================================================================
    # API DOCUMENTATION
    # =========================================================================

    def _generate_api_docs(self) -> dict[str, Path]:
        """Generate system/api/ documentation."""
        files = {}

        # API overview with topology
        files["api_overview"] = self._generate_api_overview()

        # API flows with sequence diagrams
        files["api_flows"] = self._generate_api_flows()

        return files

    def _generate_api_overview(self) -> Path:
        """Generate system/api/overview.md."""
        api_contracts = self.cross_repo_data.get("api_contracts", {})
        endpoints = api_contracts.get("endpoints", [])

        content = """# API Overview

## API Topology

"""
        content += self._generate_api_topology_diagram()

        content += f"""

## Endpoint Summary

**Total Endpoints Detected:** {len(endpoints)}

"""
        # Group by service
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

        file_path = self.output_dir / "system" / "api" / "overview.md"
        file_path.write_text(content)
        return file_path

    def _generate_api_topology_diagram(self) -> str:
        """Generate API topology diagram."""
        service_graph = self.cross_repo_data.get("service_graph", {})
        edges = service_graph.get("edges", [])

        diagram = """```mermaid
graph TB
    subgraph External[External Clients]
        Browser([Browser/Mobile])
    end

    subgraph APIs[API Services]
"""
        for meta in self.repo_metadata:
            safe = meta.name.replace("-", "_")
            diagram += f"        {safe}[{meta.name} API]\n"

        diagram += "    end\n\n"

        # Connect browser to front-facing services
        layers = self._categorize_service_layers(edges)
        for svc in layers.get("presentation", []):
            safe = svc.replace("-", "_")
            diagram += f"    Browser -->|HTTPS| {safe}\n"

        # Add inter-service connections
        seen = set()
        for edge in edges:
            source = edge["source"].replace("-", "_")
            target = edge["target"].replace("-", "_")
            key = f"{source}-{target}"
            if key not in seen:
                edge_type = edge.get("type", "http").upper()
                diagram += f"    {source} -->|{edge_type}| {target}\n"
                seen.add(key)

        diagram += "```"
        return diagram

    def _generate_api_flows(self) -> Path:
        """Generate system/api/api-flows.md with sequence diagrams."""
        content = """# API Interaction Flows

## Common API Patterns

### Gateway Pattern

Front-end routes all customer requests to backend services.

"""
        content += self._generate_gateway_diagram()

        content += """

### Orchestration Pattern

Orders service orchestrates multiple services for order processing.

"""
        content += self._generate_orchestration_diagram()

        content += """

## Key API Flows

### User Registration Flow

"""
        content += self._generate_registration_sequence()

        content += """

### Checkout Flow

"""
        content += self._generate_checkout_sequence_diagram()

        file_path = self.output_dir / "system" / "api" / "api-flows.md"
        file_path.write_text(content)
        return file_path

    def _generate_orchestration_diagram(self) -> str:
        """Generate orchestration pattern diagram."""
        return """```mermaid
graph TD
    Orders[Orders Service<br/>Orchestrator]

    Orders -->|1. Validate| User[User Service]
    Orders -->|2. Get Items| Cart[Cart Service]
    Orders -->|3. Process| Payment[Payment Service]
    Orders -->|4. Schedule| Shipping[Shipping Service]

    style Orders fill:#ff9800,color:#fff
```"""

    def _generate_registration_sequence(self) -> str:
        """Generate user registration sequence diagram."""
        return """```mermaid
sequenceDiagram
    actor Customer
    participant FE as Front-End
    participant User as User Service

    Customer->>FE: POST /register
    FE->>User: POST /register
    User-->>FE: 201 Created
    FE-->>Customer: Registration success
```"""

    # =========================================================================
    # DEPENDENCIES DOCUMENTATION
    # =========================================================================

    def _generate_dependencies(self) -> dict[str, Path]:
        """Generate system/dependencies/ documentation."""
        files = {}

        # Dependency overview
        files["deps_overview"] = self._generate_deps_overview()

        # Service dependency graph
        files["service_graph"] = self._generate_service_graph()

        # Shared libraries
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

- [Service Dependency Graph](service-graph.md) - Visual dependency relationships
- [Shared Libraries](shared-libraries.md) - Common external packages

## Dependency Summary

"""
        # Build maps
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
        """Generate system/dependencies/service-graph.md with layered diagram."""
        service_graph = self.cross_repo_data.get("service_graph", {})
        edges = service_graph.get("edges", [])

        content = """# Service Dependency Graph

## Layered Architecture

"""
        content += self._generate_layered_architecture_diagram()

        content += """

## Dependency Analysis

### Upstream Dependencies (What depends on this service)

"""
        # Build maps
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

        # Communication overview
        files["comm_overview"] = self._generate_communication_overview()

        return files

    def _generate_communication_overview(self) -> Path:
        """Generate system/communication/overview.md."""
        service_graph = self.cross_repo_data.get("service_graph", {})
        edges = service_graph.get("edges", [])

        http_count = len([e for e in edges if e.get("type") == "http"])
        event_count = len([e for e in edges if e.get("type") == "event"])
        total = http_count + event_count

        content = """# Communication Patterns

## Overview

"""
        # Communication type pie chart
        content += f"""```mermaid
pie title Communication Types
    "HTTP/REST" : {http_count}
    "Events/Messages" : {event_count if event_count > 0 else 1}
```

## Statistics

| Pattern | Count | Percentage |
|---------|-------|------------|
| HTTP/REST (Sync) | {http_count} | {(http_count/total*100) if total else 0:.0f}% |
| Events (Async) | {event_count} | {(event_count/total*100) if total else 0:.0f}% |
| **Total** | **{total}** | **100%** |

## Synchronous Communication (HTTP/REST)

### API Gateway Pattern

"""
        content += self._generate_gateway_diagram()

        content += """

### Service Orchestration

"""
        content += self._generate_orchestration_sequence()

        if event_count > 0:
            content += """

## Asynchronous Communication (Events)

### Event-Driven Pattern

"""
            content += self._generate_event_pattern_diagram()

        file_path = self.output_dir / "system" / "communication" / "overview.md"
        file_path.write_text(content)
        return file_path

    def _generate_orchestration_sequence(self) -> str:
        """Generate orchestration sequence diagram."""
        return """```mermaid
sequenceDiagram
    Front-End->>Orders: POST /orders

    rect rgb(200, 220, 240)
        Note over Orders: Orchestration Phase
        par Parallel Fetches
            Orders->>User: GET /customers/{id}
            Orders->>Cart: GET /carts/{id}/items
        end

        Orders->>Payment: POST /paymentAuth
        Orders->>Shipping: POST /shipping
    end

    Orders-->>Front-End: Order created
```"""

    def _generate_event_pattern_diagram(self) -> str:
        """Generate event-driven pattern diagram."""
        return """```mermaid
graph LR
    Shipping[Shipping Service]
    RMQ[RabbitMQ<br/>Event Bus]
    QM[Queue Master]
    Docker[Docker Daemon]

    Shipping -->|Publish| RMQ
    RMQ -->|shipping-task| QM
    QM -->|Spawn Container| Docker

    style RMQ fill:#FF6B6B,color:#fff
```"""

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

"""
        content += self._generate_layered_architecture_diagram()

        content += f"""

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

- [Component Architecture](components/overview.md) - Services as system components
- [Data Flow](dataflow/overview.md) - How data moves through the system
- [API Documentation](api/overview.md) - API endpoints and flows
- [Dependencies](dependencies/overview.md) - Service dependency graph
- [Communication Patterns](communication/overview.md) - Sync vs async patterns

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

"""
        # Include a summary diagram in the index
        content += self._generate_layered_architecture_diagram()

        content += """

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
