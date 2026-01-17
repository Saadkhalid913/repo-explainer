"""Detects cross-repository patterns and dependencies."""

import json
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from rich.console import Console

from .opencode_service import OpenCodeService
from .repository_loader import RepoMetadata

console = Console()

# Max parallel OpenCode instances
MAX_PARALLEL_OPENCODE = 8


class CrossRepoAnalyzer:
    """Analyzes interactions and dependencies across multiple repositories."""

    def __init__(
        self,
        repo_metadata: list[RepoMetadata],
        analysis_results: dict,
        verbose: bool = False,
    ):
        """
        Initialize the cross-repo analyzer.

        Args:
            repo_metadata: List of repository metadata
            analysis_results: Dictionary of analysis results per repo
            verbose: Whether to show verbose output
        """
        self.repo_metadata = repo_metadata
        self.analysis_results = analysis_results
        self.verbose = verbose

    def analyze(self) -> dict:
        """
        Perform cross-repository analysis (parallelized where possible).

        Returns:
            Dictionary with:
            - service_mesh: Inter-service communication patterns
            - api_contracts: Detected API endpoints and consumers
            - event_flows: Event-driven communication
            - shared_dependencies: Common external packages
            - service_graph: Service dependency graph
        """
        # These can run in parallel (they both use OpenCode)
        console.print(
            "[dim]  Analyzing service mesh and events in parallel...[/dim]")

        with ThreadPoolExecutor(max_workers=2) as executor:
            mesh_future = executor.submit(self._detect_service_mesh)
            events_future = executor.submit(self._detect_event_flows)

            service_mesh = mesh_future.result()
            event_flows = events_future.result()

        # These are fast local operations, run sequentially
        console.print("[dim]  Mapping API contracts...[/dim]")
        api_contracts = self._detect_api_contracts()

        console.print("[dim]  Identifying shared dependencies...[/dim]")
        shared_deps = self._detect_shared_dependencies()

        console.print("[dim]  Building service dependency graph...[/dim]")
        service_graph = self._build_service_graph(service_mesh, event_flows)

        return {
            "service_mesh": service_mesh,
            "api_contracts": api_contracts,
            "event_flows": event_flows,
            "shared_dependencies": shared_deps,
            "service_graph": service_graph,
        }

    def _detect_service_mesh(self) -> dict:
        """
        Detect how services communicate with each other (parallelized).

        Strategy:
        1. Search for HTTP client usage (requests, httpx, fetch, axios)
        2. Search for gRPC client/server definitions
        3. Extract base URLs and endpoint patterns

        Returns:
            Dictionary with http_calls and grpc_calls
        """
        service_mesh = {
            "http_calls": [],
            "grpc_calls": [],
        }

        # Filter to valid repos
        valid_repos = [
            meta for meta in self.repo_metadata
            if self.analysis_results.get(meta.name) and self.analysis_results[meta.name]["result"].success
        ]

        def analyze_repo_mesh(meta: RepoMetadata) -> dict:
            """Analyze a single repo for service mesh patterns."""
            prompt = self._get_service_mesh_prompt(meta.name)
            service = OpenCodeService(repo_path=meta.path)
            result = {"http_calls": [], "grpc_calls": [], "name": meta.name}

            analysis_result = service.run_command(prompt)

            if analysis_result.success:
                mesh_file = meta.path / f"service-mesh-{meta.name}.json"
                if mesh_file.exists():
                    try:
                        mesh_data = json.loads(mesh_file.read_text())
                        result["http_calls"] = mesh_data.get("http_calls", [])
                        result["grpc_calls"] = mesh_data.get("grpc_calls", [])
                    except json.JSONDecodeError:
                        pass
            return result

        # Run in parallel
        with ThreadPoolExecutor(max_workers=MAX_PARALLEL_OPENCODE) as executor:
            futures = {executor.submit(
                analyze_repo_mesh, meta): meta for meta in valid_repos}

            for future in as_completed(futures):
                meta = futures[future]
                try:
                    result = future.result()
                    service_mesh["http_calls"].extend(result["http_calls"])
                    service_mesh["grpc_calls"].extend(result["grpc_calls"])
                    if self.verbose:
                        console.print(
                            f"    [dim]✓ {meta.name} mesh analyzed[/dim]")
                except Exception as e:
                    console.print(
                        f"[yellow]Warning:[/yellow] Service mesh analysis failed for {meta.name}: {e}")

        return service_mesh

    def _detect_api_contracts(self) -> dict:
        """
        Map all API endpoints and their consumers.

        Strategy:
        1. Extract API routes from each service
        2. Build producer-consumer relationships

        Returns:
            Dictionary with endpoints and consumers
        """
        api_contracts = {
            "endpoints": [],
            "consumers": {},
        }

        for meta in self.repo_metadata:
            result = self.analysis_results.get(meta.name)
            if not result or not result["result"].success:
                continue

            # Load components.json for this service if it exists
            components_file = meta.path / "components.json"
            if components_file.exists():
                try:
                    data = json.loads(components_file.read_text())

                    # Extract API endpoints from component interfaces
                    for component in data.get("components", []):
                        for interface in component.get("interfaces", []):
                            if interface.get("type") in ["REST", "HTTP", "API", "function"]:
                                for endpoint in interface.get("endpoints", []):
                                    api_contracts["endpoints"].append({
                                        "service": meta.name,
                                        "endpoint": endpoint,
                                        "component": component.get("name"),
                                    })
                except json.JSONDecodeError:
                    console.print(
                        f"[yellow]Warning:[/yellow] Could not parse components.json for {meta.name}")

        return api_contracts

    def _detect_event_flows(self) -> dict:
        """
        Detect event-driven communication patterns (parallelized).

        Strategy:
        1. Search for event publishing (Kafka, RabbitMQ, Redis pub/sub)
        2. Search for event subscriptions/listeners
        3. Map event types to publishers and subscribers

        Returns:
            Dictionary with publishers and subscribers
        """
        event_flows = {
            "publishers": {},
            "subscribers": {},
            "events": [],
        }

        # Filter to valid repos
        valid_repos = [
            meta for meta in self.repo_metadata
            if self.analysis_results.get(meta.name) and self.analysis_results[meta.name]["result"].success
        ]

        def analyze_repo_events(meta: RepoMetadata) -> dict:
            """Analyze a single repo for event patterns."""
            prompt = self._get_event_detection_prompt(meta.name)
            service = OpenCodeService(repo_path=meta.path)
            result = {"name": meta.name, "published": [], "subscribed": []}

            analysis_result = service.run_command(prompt)

            if analysis_result.success:
                events_file = meta.path / f"events-{meta.name}.json"
                if events_file.exists():
                    try:
                        events = json.loads(events_file.read_text())
                        result["published"] = events.get("published", [])
                        result["subscribed"] = events.get("subscribed", [])
                    except json.JSONDecodeError:
                        pass
            return result

        # Run in parallel
        with ThreadPoolExecutor(max_workers=MAX_PARALLEL_OPENCODE) as executor:
            futures = {executor.submit(
                analyze_repo_events, meta): meta for meta in valid_repos}

            for future in as_completed(futures):
                meta = futures[future]
                try:
                    result = future.result()
                    event_flows["publishers"][result["name"]
                                              ] = result["published"]
                    event_flows["subscribers"][result["name"]
                                               ] = result["subscribed"]

                    # Add to global event list
                    for event in result["published"]:
                        if event not in event_flows["events"]:
                            event_flows["events"].append(event)

                    if self.verbose:
                        console.print(
                            f"    [dim]✓ {meta.name} events analyzed[/dim]")
                except Exception as e:
                    console.print(
                        f"[yellow]Warning:[/yellow] Event analysis failed for {meta.name}: {e}")

        return event_flows

    def _detect_shared_dependencies(self) -> dict:
        """
        Find external packages used across multiple services.

        Returns:
            Dictionary mapping package names to list of services using them
        """
        shared_deps = {}

        for meta in self.repo_metadata:
            result = self.analysis_results.get(meta.name)
            if not result:
                continue

            # Check for common dependency files
            dependency_files = [
                meta.path / "package.json",  # Node.js
                meta.path / "requirements.txt",  # Python
                meta.path / "go.mod",  # Go
                meta.path / "pom.xml",  # Java Maven
                meta.path / "build.gradle",  # Java Gradle
                meta.path / "Gemfile",  # Ruby
            ]

            for dep_file in dependency_files:
                if dep_file.exists():
                    # Simple parsing - just extract package names
                    content = dep_file.read_text()

                    if dep_file.name == "package.json":
                        # Parse package.json dependencies
                        try:
                            data = json.loads(content)
                            deps = list(data.get("dependencies", {}).keys())
                            deps.extend(data.get("devDependencies", {}).keys())
                        except json.JSONDecodeError:
                            continue
                    elif dep_file.name == "requirements.txt":
                        # Parse requirements.txt
                        deps = []
                        for line in content.split("\n"):
                            line = line.strip()
                            if line and not line.startswith("#"):
                                # Extract package name (before ==, >=, etc.)
                                match = re.match(r"^([a-zA-Z0-9_-]+)", line)
                                if match:
                                    deps.append(match.group(1))
                    else:
                        # For other formats, skip for now
                        continue

                    # Add to shared deps
                    for package in deps:
                        if package not in shared_deps:
                            shared_deps[package] = []
                        if meta.name not in shared_deps[package]:
                            shared_deps[package].append(meta.name)

        # Filter to only packages used by 2+ services
        return {
            pkg: services
            for pkg, services in shared_deps.items()
            if len(services) >= 2
        }

    def _build_service_graph(self, service_mesh: dict, event_flows: dict) -> dict:
        """
        Build directed graph of service dependencies.

        Args:
            service_mesh: Service mesh data
            event_flows: Event flow data

        Returns:
            Dictionary with nodes and edges
        """
        nodes = [meta.name for meta in self.repo_metadata]
        edges = []

        # Add edges from HTTP calls
        for call in service_mesh.get("http_calls", []):
            edges.append({
                "source": call.get("caller"),
                "target": call.get("callee"),
                "type": "http",
                "details": call.get("endpoint", ""),
            })

        # Add edges from event flows (simplified - publisher to all subscribers of that event)
        publishers = event_flows.get("publishers", {})
        subscribers = event_flows.get("subscribers", {})

        for publisher, events in publishers.items():
            for event in events:
                for subscriber, sub_events in subscribers.items():
                    if event in sub_events and publisher != subscriber:
                        edges.append({
                            "source": publisher,
                            "target": subscriber,
                            "type": "event",
                            "details": event,
                        })

        return {"nodes": nodes, "edges": edges}

    def _get_service_mesh_prompt(self, service_name: str) -> str:
        """Generate prompt for detecting service mesh patterns."""
        return f"""Analyze the {service_name} repository to detect outbound service calls.

Search for:
1. **HTTP/REST calls** - requests, httpx, axios, fetch, http.Get usage
2. **gRPC calls** - gRPC client definitions
3. **Service URLs** - Base URLs or service names being called

For each detected call, provide:
- Target service name (if detectable from URL/config)
- HTTP method and endpoint pattern
- File location (file_path:line_number)

Output format (JSON):
{{
  "http_calls": [
    {{
      "caller": "{service_name}",
      "callee": "target-service",
      "method": "POST",
      "endpoint": "/api/v1/resource",
      "file_path": "src/client.py",
      "line_number": 42
    }}
  ],
  "grpc_calls": []
}}

Write the result to `service-mesh-{service_name}.json`.
"""

    def _get_event_detection_prompt(self, service_name: str) -> str:
        """Generate prompt for detecting event patterns."""
        return f"""Analyze the {service_name} repository to detect event-driven communication.

Search for:
1. **Event publishing** - Kafka producers, RabbitMQ publish, Redis pub/sub, EventEmitter.emit
2. **Event subscription** - Kafka consumers, RabbitMQ subscribe, EventEmitter.on

For each event, provide:
- Event name/topic
- Whether published or subscribed
- File location (file_path:line_number)

Output format (JSON):
{{
  "published": ["user.created", "payment.completed"],
  "subscribed": ["order.placed", "user.updated"]
}}

Write the result to `events-{service_name}.json`.
"""
