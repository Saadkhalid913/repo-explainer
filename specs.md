# Development Stages & Requirements Mapping

This document summarizes the planned development phases for **Repository Explainer** and maps the primary **functional** and **non-functional** requirements that each phase addresses.

---

## Phase 1 – MVP (4-6 weeks)
**Goal**: Deliver basic single-repository analysis with well-structured markdown output.

**Functional focus**
- `FR-1.1`, `FR-1.2`: Local and remote repository ingestion plus handling small-to-medium repo sizes for the first analyses.
- `FR-2.1`, `FR-2.2`: Provide Level 1/2 progressive analysis and multi-language support for Python and JavaScript/TypeScript.
- `FR-3.1`, `FR-4.1`: Generate hierarchical markdown docs and a simple architecture diagram (Mermaid) per component.
- `FR-5.1`: Implement the core CLI commands (`analyze`, `update`) with depth/format options.
- `FR-6.1`, `FR-6.2`: Integrate with OpenRouter (Gemini 2.5 Flash) and craft prompts for architectural documentation.

**Non-functional focus**
- `NFR-1.1`, `NFR-1.2`: Keep runtime within minutes for small repos and manage resource usage under 2GB.
- `NFR-2.1`, `NFR-2.2`: Gracefully handle network/LLM errors and validate documentation quality.
- `NFR-3.1`, `NFR-3.2`: Deliver readable Markdown outputs that render in standard viewers and run on macOS/Linux/Windows.
- `NFR-4.1`, `NFR-4.2`: Never store credentials, respect `.gitignore`, and allow excluding sensitive files.
- `NFR-5.1`: Maintain code quality with proper typing and modular structure.

---

## Phase 2 – Enhanced Analysis (4-6 weeks)
**Goal**: Expand analysis depth, diagram types, and pattern detection.

**Functional focus**
- `FR-2.3`, `FR-2.4`: Detect architectural/design patterns and map dependencies internally and externally.
- `FR-3.2`, `FR-4.2`, `FR-4.3`, `FR-4.4`: Automatically organize documentation and produce sequence, ER, and dependency/call graphs.
- `FR-5.3`: Surface detailed progress reporting (phase, time, token usage) for long-running runs.
- `FR-6.3`: Manage context for targeted deep dives and chunk large files.

**Non-functional focus**
- `NFR-1.1`, `NFR-1.2`: Scale timing targets to medium repos and keep disk/output ratios sensible.
- `NFR-2.1`, `NFR-2.2`: Improve reliability and add validation layers for generated diagrams.
- `NFR-3.1`: Ensure outputs remain clear despite added diagram complexity.
- `NFR-5.2`: Begin architecting for extensibility (plugin points) to add new analyzers.

---

## Phase 3 – Scale & Performance (3-4 weeks)
**Goal**: Improve throughput on large repositories through optimization.

**Functional focus**
- `FR-1.3`: Support incremental updates and selective reanalysis.
- `FR-2.1`, `FR-6.3`: Optimize progressive analysis scheduling and context management for large codebases.
- `FR-6.2`: Optimize prompts for token efficiency when sampling large files.

**Non-functional focus**
- `NFR-1.1`: Meet long-term timing targets for large repos (full analysis < 1 hour with progressive output).
- `NFR-1.2`: Enable parallelism without exceeding memory limits and keep disk usage bounded.
- `NFR-2.1`: Harden retries/backoffs around LLM calls and git fetches.
- `NFR-4.x`: Continue to protect credentials and sensitive data while scaling.

---

## Phase 4 – Multi-Repository Support (4-6 weeks)
**Goal**: Analyze interconnected repositories (microservices/monorepos) and document system-wide views.

**Functional focus**
- `FR-3.3`: Accept multiple repos and capture their relationships.
- `FR-4.1`–`FR-4.5`: Expand diagrams to show inter-service and dependency mappings across repositories.
- `FR-5.2`: Add configuration to manage multi-repo runs and shared credentials.

**Non-functional focus**
- `NFR-3.2`: Maintain compatibility as outputs span multiple repos.
- `NFR-4.2`: Clarify what code is shared with LLM APIs and allow per-service exclusions.
- `NFR-5.2`: Extend plugin architecture to orchestrate multi-repo analyzers.

---

## Phase 5 – Enhancements & Polish (ongoing)
**Goal**: Refine usability, add integrations, and support future feature ideas.

**Functional focus**
- `FR-5.1` additions: Interactive HTML output, VS Code extension hooks, flexible config overrides.
- `FR-6.1`: Add more LLM providers and optional local models.
- `FR-4.5`: Add export options (SVG/PNG) for diagrams.

**Non-functional focus**
- `NFR-3.1`: Polish output readability for broader audiences.
- `NFR-1.2`: Optimize existing tooling (caching, cost tracking) for long-term maintainability.
- `NFR-5.1`, `NFR-5.2`: Keep codebase testable, modular, and extensible for new integrations.

---

## Cross-Phase Notes
- **Security & Privacy** (`NFR-4.x`) remain continuous concerns; every phase must avoid leaking credentials, respect excludes, and disclose API usage.
- **Success metrics** (accuracy, completeness, diagram correctness, cost efficiency) should be validated during each phase for regression detection.
- **Open questions** (tests, auth priorities, cost limits, versioning) should inform planning checkpoints before starting each new phase.

## Automation & Agent Tooling Strategy
- **Primary tooling**: Adopt **OpenCode** for repo exploration and automated documentation tasks because it offers non-interactive mode with auto-approved tools, HTTP server APIs, and reusable `.opencode/commands`, which align with our progressive analysis workflows. Claude Code remains a secondary option when structured JSON schema enforcement is required.
- **Phase alignment**:
  - *Phase 1*: Run OpenCode headless commands to bootstrap baseline docs/diagrams from the local repo so devs can iterate on output formatting rather than manual extraction.
  - *Phase 2*: Introduce parameterized OpenCode commands (or HTTP sessions) that trigger pattern detection, dependency graphs, and ASCII/Mermaid generation; leverage Claude Code for schema-validated summaries if we need guaranteed JSON structures.
  - *Phase 3*: Host OpenCode in server mode to enable incremental re-analysis jobs driven by our orchestration layer; cache session IDs for change-aware reruns.
  - *Phase 4*: Use OpenCode custom commands per service to parallelize multi-repo analysis and aggregate outputs inside our orchestrator.
  - *Phase 5*: Integrate OpenCode sessions with the `static_exporter` pipeline to regenerate both Markdown and HTML bundles automatically; Claude Code can remain an optional quality gate for narrative polishing.
- **Operational considerations**: Store OpenCode/Claude prompts with the repo (under `.opencode/commands/` or docs) for repeatability, and surface their outputs via metadata logs to keep change history auditable.
