# Stage 2 – Expanded Insight

**Technologies**
- Continue using foundational Python tooling, but add `networkx` or `graphlib` for dependency graphs.
- Use `mermaid-cli` for converting diagrams, `plantuml` optional for sequence/ER diagrams.
- Introduce `tree-sitter` grammars for Java, Go, Rust parsing where feasible.
- Progress reporting leverages `rich.progress` plus log streaming.

**Design Patterns**
- Observer pattern for progress reporting subscribers (status bar, logs).
- Composite pattern for representing nested documentation sections (modules, components).
- Chain-of-responsibility for layered analysis passes (architecture -> patterns -> summary).
- Adapter pattern for supporting multiple diagram types (sequence, ER, dependency graphs).

**Components**
- `pattern_detector`: Detects MVC, microservice cues, identifies Singleton/Factory/Observer instantiations.
- `dependency_mapper`: Parses package files (`package.json`, `pyproject.toml`, `go.mod`) and builds internal/external graphs.
- `doc_structure_analyzer`: Grouping logic to determine natural sections (services, layers) and generate navigation hints.
- `diagram_sequence_er`: Richer Mermaid sequences, ER diagrams, and optional ASCII fallback.
- `progress_tracker`: Emits phases/timers, calculates token counts, supports `--verbose` mode.
- `context_manager`: Implements chunking strategies for large files, caching summaries.

**Functionality**
- Enumerate detected architectural and design patterns, writing them to `patterns/identified-patterns.md`.
- Produce sequence, ER, dependency, and call diagrams in `.mmd` format and match them with ASCII counterparts.
- Show phase/timer/token progress updates in the CLI, including verbose mode logs.

**Agent Architecture**
- **Pattern**: Hybrid sequential-plus-concurrent orchestration where analysis agents run in parallel (e.g., pattern detector, diagram generator) but rely on a sequential backbone for data normalization.
- **Orchestrator role**: `progress_tracker` acts as a group chat-type manager, collecting insights from specialized agents, reconciling status, and pushing consolidated updates back to the CLI.
- **Tooling**: Independent agents (pattern detection, dependency mapping, diagram generation) each have domain-specific prompts/tools but share “common state” summaries. OpenCode custom commands or HTTP sessions trigger these agents in parallel, while Claude Code can validate narrative summaries before publishing.
- **Validation**: The aggregating orchestrator ensures conflicting results are reconciled before writing docs, supporting Azure’s group chat recommendations for transparency while keeping deterministic outcomes.

**Deliverables**
- Detection of architectural/design patterns reported in `patterns/identified-patterns.md`.
- Complete sequence/ER/dependency/call diagrams stored under `diagrams/` with both `.mmd` and ASCII previews.
- Enhanced config/progress reporting for longer runs; ability to opt-in/out of certain analyses.

## Diagrams
- Backend architecture: `diagrams/stage_2/backend.mmd`
- TUI interaction: `diagrams/stage_2/tui.mmd`
