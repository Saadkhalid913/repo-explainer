# Coherence Plan

This plan defines how we turn the current raw documentation outputs under `docs/` into a coherent, navigable Markdown site (to be converted into static HTML later). The goal is to ensure every analysis run produces an `index.md` landing page that links to structured subpages, embeds rendered diagrams, and keeps Mermaid source files alongside their image exports. We are making these changes so that:
- Stakeholders get a single, human-readable entry point instead of hunting across scattered files.
- Later stages (multi-repo, interactive exports) can plug into a predictable information architecture.
- Diagrams and component pages stay synchronized with underlying Mermaid sources, enabling automated site generation.

## Current State Snapshot
- Files: `architecture.md`, `components.mermaid`, `dataflow.mermaid`, `tech-stack.txt`, `analysis_*.json`, logs.
- Issues: No central index, no consistent navigation links, diagrams are Mermaid source only (no rendered PNG/SVG), and outputs look like isolated dumps rather than a cohesive report.

## Desired Information Architecture
1. **`docs/index.md`** – entry point with:
   - Executive summary + key metrics (repo, depth, timestamp, session IDs).
   - Embedded diagrams (PNG/SVG) with inline Mermaid code blocks for reference.
   - Links to subpages for each component/section.
2. **Subpages** (living under `docs/`), tailored to the project’s logical structure:
   - `architecture/` directory hosting domain-specific pages (e.g., `architecture/job_server.md`, `architecture/cli.md`) generated from the analyzer’s component graph.
   - `components.md` – textual explanation of the class diagram plus a rendered image; links fan out to deeper architecture pages when necessary.
   - `dataflow.md` – narrative + rendered flow diagram, with anchors per workflow.
   - `tech-stack.md` – normalized list (converted from `tech-stack.txt`).
   - Optional `analysis-summary.md` linking logs/JSON outputs for traceability.
3. **Diagrams directory**: keep `.mermaid` sources plus rendered `.svg`/`.png` siblings (e.g., `components.mermaid` + `components.svg`). Each architecture subpage can embed diagrams stored within its subfolder.

## Agent Strategy
- **Reuse OpenCode** as the primary analysis + composition agent.
  - Reason: already integrated in Stage 1, supports non-interactive runs, and can execute templated custom commands.
- **Add a new custom OpenCode command** `project:compose-coherent-docs` that:
  1. Reads `architecture.md`, `components.mermaid`, `dataflow.mermaid`, `tech-stack.txt`, and log metadata.
  2. Generates normalized Markdown subpages (components/dataflow/tech-stack) and `index.md` according to the structure above.
  3. Emits a manifest describing created files for the CLI to ingest.
- **Introduce a DocComposer sub-agent** built on OpenCode or a lightweight local pipeline:
  - Responsible for inspecting architecture outputs and deciding when to create deeper directories (e.g., `docs/architecture/job_server.md`).
  - Accepts a schema describing component hierarchy so additional stages can plug in new sections without editing templates manually.
- **Rendering pipeline** (non-agent): use Mermaid CLI (`mmdc`) from the CLI/DocComposer step to create `.svg`/`.png` files referenced in `index.md`. This keeps agent responsibilities focused on content composition while deterministic tooling handles rendering.

## Bottom-Up Generation Workflow
1. **Run analysis** (`project:analyze-architecture` or depth variants) → produces raw docs + Mermaid files.
2. **Invoke DocComposer (new internal module)**:
   - Parses OpenCode manifest & `tech-stack.txt`.
   - Normalizes section headings, adds metadata front-matter (timestamp, repo, session id).
   - Writes `components.md`, `dataflow.md`, etc., embedding relative links to Mermaid source files.
   - Creates architecture subdirectories (e.g., `architecture/job_server.md`) by slicing the component graph into logical groups.
3. **Render diagrams** via `mmdc` (batch): create `.svg` siblings stored beside sources (e.g., `docs/components.svg` or `docs/architecture/job_server.svg`).
4. **Generate `index.md`**:
   - Summaries for Architecture, Components, Data Flow, Tech Stack.
   - Inline images referencing `./components.svg`, `./dataflow.svg`, and sectional diagrams.
   - Links to subpages (`[Components](components.md)`, `[Job Server](architecture/job_server.md)`, etc.).
   - Table of artifacts (logs, JSON outputs) for traceability.
5. **Emit manifest** capturing all produced files with hashes; store under `.repo-explainer/runs/<timestamp>/coherence.json` for future automation and Stage 2 linkage.

## Implementation Steps (Stage 1 scope)
1. **DocComposer Module**
   - Consume OpenCode outputs + metadata JSON.
   - Normalize and rewrite Markdown subpages.
   - Produce `index.md` with navigation + embedded diagrams.
2. **Diagram Rendering Utility**
   - Wrap Mermaid CLI invocation (configurable output format) and ensure outputs land next to source files.
3. **OpenCode Command Updates**
   - Add `.opencode/commands/compose-coherence.md` that invokes DocComposer + rendering utility.
   - Extend `analyze` CLI flow: after OpenCode analysis, automatically run the coherence command.
4. **Validation**
   - Ensure `tree docs/` now shows `index.md`, subpages, `.svg` diagrams, architecture subdirectories (e.g., `architecture/job_server.md`), and original Mermaid sources.
   - Add smoke test verifying all links in `index.md` resolve and referenced diagrams exist.
   - Add structural test ensuring every architecture subpage includes both narrative text and at least one embedded diagram/image link.

Following this plan keeps Stage 1 deliverables focused yet sets a clear foundation for later static-site conversion and Stage 2 documentation enhancements.
