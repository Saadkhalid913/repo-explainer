# Stage 1 – MVP Essentials

**Technologies**
- Python 3.9+ core, `typer` for CLI, `GitPython` for repository operations, `pydantic`/`dataclasses` for structs, `PyYAML` for config, `rich` for terminal feedback.
- `openrouter` client or `requests` wrapper for Gemini 2.5 Flash access and prompt submission.
- `tree-sitter` (or `ast`/`lib2to3` as fallback) for language parsing of Python and JS/TS.
- Mermaid diagram generation via Mermaid CLI invocation (optional) and plain `.mmd` writers.

**Design Patterns**
- CLI command pattern using `typer` commands and subcommands.
- Builder/facade pattern for orchestrating stages: repository loader → analyzer → documentation generator.
- Strategy pattern for handling different analysis depth (`quick`, `standard`, `deep`).
- Singleton/config manager for global config access (via `pydantic` settings).

**Components**
- `cli` module: entry point, argument parsing, config loading, logging.
- `repository_loader`: local path resolution, Git clone helper, authentication stub.
- `analyzer`: scans directories, summarizes structure, defers to `tree-sitter`/AST per language.
- `llm_service`: prompt templates, OpenRouter integration helper, response validation.
- `doc_generator`: Markdown file writer, table of contents builder, index creation.
- `diagram_generator`: Emit basic Mermaid component diagrams, store `.mmd` files.
- `output_manager`: Ensures directories exist, writes metadata/logs, tracks config.

**Functionality**
- Run `repo-explainer analyze` against a Python or JS/TS repo and produce structured markdown with TOCs.
- Generate a basic Mermaid architecture diagram reflecting the repository’s primary components.
- Persist metadata/log files showing the analyzed repo path and configuration used.

**Agent Architecture**
- **Pattern**: Single-agent sequential pipeline where `cli` orchestrator feeds each responder in order (loader → analyzer → LLM prompt → doc writer).
- **Orchestrator role**: `cli` command maintains deterministic flow, passing intermediate summaries (common state) downstream, akin to Azure’s sequential orchestration guidance.
- **Tooling**: CLI agent exposes intents (analyze/update) and feeds each stage with adapters (Git, parser, LLM) while monitoring for retryable failures. OpenCode headless commands can seed initial docs/diagrams so the CLI can focus on incremental refinement.
- **Validation**: Failures short-circuit later stages, enabling quick retries and keeping developer experience predictable.

**Deliverables**
- `repo-explainer analyze/update` commands producing markdown docs, logs, and at least one architecture diagram.
- Support for Python and JavaScript/TypeScript repositories only.
- Initial prompts tuned for structure detection, verifying outputs against static summaries.

## Diagrams
- Backend architecture: `diagrams/stage_1/backend.mmd`
- TUI interaction: `diagrams/stage_1/tui.mmd`
