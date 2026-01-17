# Stage 5 – Enhancements & Polish

**Technologies**
- `FastAPI` or `Flask` backend for serving interactive HTML outputs (optional) and exporting static directories.
- Static site generator (MkDocs, Astro, or Docusaurus) for turning structured Markdown into multi-page HTML sites.
- VS Code extension scaffolding via `yo code`/`@types/vscode` (presentation, if pursued).
- Additional LLM providers (OpenAI, Azure OpenAI, local Llama.cpp models) using provider adapters.
- SVG/PNG exports using Mermaid CLI + `Pillow` for post-processing.

**Design Patterns**
- Adapter for plugging in new LLM providers and diagram exporters.
- Decorator for augmenting documentation output with interactivity (collapsible sections, tooltips).
- Observer pattern for telemetry/usage hooks if the user opts-in to analytics.
- Plugin pattern for community-contributed analyzers and formatters.

**Components**
- `interactive_renderer`: Converts Markdown + Mermaid into HTML with navigation, search, and diagram toggles.
- `static_exporter`: Invokes an SSG (MkDocs/Astro) to transform the Markdown tree into `html/` outputs, preserving directory structure for architecture, components, patterns, etc.
- `vscode_extension`: Provides command palette access, inline doc previews, and export shortcuts.
- `provider_registry`: Manages supported LLM endpoints, credentials, and fallback logic.
- `diagram_exporter`: Adds export targets like SVG/PNG, includes ASCII fallback for CLI display.
- `telemetry_opt_in`: Module for handling user consent, anonymized tracking, and toggles.

**Functionality**
- Serve HTML-rendered documentation with navigable sections and diagram toggles for stakeholders.
- Surface VS Code commands or workflows for opening generated docs and exporting diagrams.
- Switch between LLM providers (online or local) while respecting privacy mode toggles.
- Export diagrams as SVG/PNG while keeping ASCII/Markdown fallbacks for terminal usage.
- Produce a downloadable `html/` directory via an SSG based on existing Markdown outputs (architecture, components, patterns) while keeping Markdown as the canonical source.

**Agent Architecture**
- **Pattern**: Adapter/magentic hybrid where a manager agent coordinates plugin agents (HTML renderer, VS Code, exporter) and delegates tasks to specialized plugins.
- **Orchestrator role**: `provider_registry` acts like a magentic manager, monitoring available endpoints and redirecting requests to the best-fit agent (web server, extension, or local model) while the HTML generator consumes diagrams and Markdown.
- **Tooling**: Plugin agents each own tooling (FastAPI, VS Code APIs, Mermaid CLI, SSG CLI, OpenCode sessions for regeneration, optional Claude QC runs) and report status back; the manager ensures only trusted agents handle sensitive exports, aligning with security/observability guidance.
- **Validation**: Plugin agents emit health signals that the manager can surface in CLI feedback, allowing testers to confirm that HTML rendering, exports, and provider switching all succeeded without leaking credentials.

**Deliverables**
- Optional interactive HTML documentation with search and navigation.
- VS Code extension or instructions for integration points.
- Support for multiple LLM providers including offline/local models for privacy mode.
- Diagram export tools producing shareable assets for stakeholders.

