# Stage 2 – Expanded Insight

**Technologies**
- Continue using foundational Python tooling, but add `networkx` or `graphlib` for dependency graphs and advanced OpenCode command templates (e.g., `.opencode/commands/pattern-scan.md`).
- Use `mermaid-cli` for converting diagrams, `plantuml` optional for sequence/ER diagrams.
- Introduce `tree-sitter` grammars for Java, Go, Rust parsing where feasible.
- Progress reporting leverages `rich.progress` plus log streaming.

**Design Patterns**
- Observer pattern for progress reporting subscribers (status bar, logs) that also stream OpenCode task updates.
- Composite pattern for representing nested documentation sections (modules, components) with data sourced from OpenCode outputs and local enrichment.
- Chain-of-responsibility for layered analysis passes (architecture -> patterns -> summary) where OpenCode commands feed intermediate artifacts to downstream processors.
- Adapter pattern for supporting multiple diagram types (sequence, ER, dependency graphs) and mapping them to both OpenCode and Claude deliverables when needed.

**Components**
- `pattern_detector`: Detects MVC, microservice cues, identifies Singleton/Factory/Observer instantiations, and prepares OpenCode prompts to inspect relevant files.
- `dependency_mapper`: Parses package files (`package.json`, `pyproject.toml`, `go.mod`) and builds internal/external graphs, delegating visualization generation to OpenCode custom commands.
- `doc_structure_analyzer`: Grouping logic to determine natural sections (services, layers) and generate navigation hints, consuming OpenCode output files.
- `diagram_sequence_er`: Richer Mermaid sequences, ER diagrams, and optional ASCII fallback, either produced directly or imported from OpenCode.
- `progress_tracker`: Emits phases/timers, calculates token counts, supports `--verbose` mode, and surfaces OpenCode session progress plus Claude fallback usage.
- `context_manager`: Implements chunking strategies for large files, caching summaries, and coordinates which files are sent to OpenCode vs. local analyzers.

**Functionality**
- Enumerate detected architectural and design patterns, writing them to `patterns/identified-patterns.md`, using OpenCode pattern.scan commands as primary data source.
- Produce sequence, ER, dependency, and call diagrams in `.mmd` format and match them with ASCII counterparts; OpenCode handles generation, while local code validates and links them.
- Show phase/timer/token progress updates in the CLI, including verbose mode logs, with OpenCode session/task identifiers and Claude fallback logs for traceability.

**Agent Architecture**
- **Pattern**: Hybrid sequential-plus-concurrent orchestration where OpenCode commands run in parallel for pattern, dependency, and diagram tasks, but rely on a sequential backbone for data normalization.
- **Orchestrator role**: `progress_tracker` acts as a group chat-type manager, collecting insights from specialized agents, reconciling status, and pushing consolidated updates back to the CLI; it also coordinates Claude fallback invocations when OpenCode tasks fail.
- **Tooling**: Independent agents (pattern detection, dependency mapping, diagram generation) each have domain-specific prompts/tools but share “common state” summaries. OpenCode custom commands or HTTP sessions trigger these agents in parallel; Claude Code handles schema-enforced narrative summaries or quality checks when needed.
- **Validation**: The aggregating orchestrator ensures conflicting results are reconciled before writing docs, surfacing both OpenCode and Claude outputs for operator review.

**Deliverables**
- Detection of architectural/design patterns reported in `patterns/identified-patterns.md`.
- Complete sequence/ER/dependency/call diagrams stored under `diagrams/` with both `.mmd` and ASCII previews.
- Enhanced config/progress reporting for longer runs; ability to opt-in/out of certain analyses.

## Diagrams
- Backend architecture: `diagrams/stage_2/backend.mmd`
- TUI interaction: `diagrams/stage_2/tui.mmd`
