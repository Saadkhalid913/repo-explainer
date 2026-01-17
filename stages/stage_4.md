# Stage 4 – Multi-Repository Awareness

**Technologies**
- `tomli`/`pyyaml` for reading multi-repo config manifests.
- Graph visualization tools (e.g., `graphviz` via `python-graphviz`) for cross-service dependency views.
- Enhanced Mermaid templates for system-wide overviews.

**Design Patterns**
- Facade for multi-repo orchestration, encapsulating each repo’s loader/analyzer.
- Visitor for traversing service graphs and collecting dependencies.
- Factory for creating per-repo analyzers based on language mix.
- Repository pattern for storing aggregated metadata about inter-service relations.

**Components**
- `multi_repo_config`: Defines repo list, shared credentials, service relationships, sequence priorities, and OpenCode command mappings per service.
- `cross_service_mapper`: Links API endpoints, shared libraries, infrastructure patterns between repos, and coordinates multi-session OpenCode runs to gather cross-service evidence.
- `system_diagram_generator`: Produces high-level system architecture with interactions and shared services, combining Graphviz/Mermaid outputs sourced from OpenCode or Claude fallback sessions.
- `unified_doc_builder`: Synthesizes documentation across repos with combined indexes and comparison tables, importing artifacts from each service’s OpenCode outputs.
- `service_registry`: Captures per-service metadata (version, primary language, dependencies) plus OpenCode/Claude session IDs for traceability.

**Functionality**
- Accept a multi-repo manifest and analyze each service, producing per-repo outputs plus a shared system view by orchestrating multiple OpenCode sessions (one per repo) and aggregating results.
- Correlate service dependencies, shared libraries, and API interactions across repositories, merging OpenCode facts and locally computed diffs.
- Allow per-service exclusion rules to keep sensitive code out of analysis outputs, propagating those rules into OpenCode command prompts and Claude fallbacks.

**Agent Architecture**
- **Pattern**: Facade for multi-repo orchestration, combining concurrent execution with a deterministic aggregation layer — akin to Azure’s concurrent orchestration with an aggregating collector.
- **Orchestrator role**: `multi_repo_config` orchestrates per-repo factories while `cross_service_mapper` serves as the aggregation agent that resolves interdependencies and enforces security constraints before stitching system diagrams.
- **Tooling**: Each repository spins up a specialized agent chain (loader → analyzer → doc builder) managed by the `service_registry`, with OpenCode commands per service automating doc/diagram extraction; the orchestrator consolidates outputs to prevent conflicting state.
- **Validation**: Aggregator waits for per-repo completion (similar to fan-in) before generating system-wide docs, ensuring cross-service relationships only appear once all local analyses are validated.

**Deliverables**

- Config-driven multi-repo analysis command with shared output directory.
- Documentation set describing inter-service communication, shared patterns, and system-wide diagrams.
- Ability to exclude sensitive services/files per repo with inheritance.

## Diagrams
- Backend architecture: `diagrams/stage_4/backend.mmd`
- TUI interaction: `diagrams/stage_4/tui.mmd`
