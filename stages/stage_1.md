# Stage 1 – MVP Essentials

Stage 1 establishes a usable CLI that can analyze a repository (local path or Git URL), run an OpenCode-powered scan, and turn the returned artifacts into a coherent documentation bundle. The current implementation already ships the end-to-end "analyze" workflow, including diagram rendering and coherence validation, while deeper analyzer intelligence and incremental update flows remain open.

## Technologies
- Python 3.9+ with Typer + Rich for the CLI shell and UX feedback
- GitPython for cloning Git URLs into `./tmp/<owner>/<repo>` with reuse + `--force-clone`
- Pydantic / pydantic-settings for global configuration (`.env` driven)
- OpenCode CLI (OpenRouter Gemini 3 Flash Preview model by default) for repository analysis
- Mermaid CLI (`mmdc`) for diagram rendering with optional auto-fix fallback via OpenCode
- Doc composition + validation utilities (`doc_composer.py`, `validate_coherence.py`)

**Planned (not yet integrated):** Tree-sitter/AST enrichment and YAML-based config profiles.

## Design Patterns
- **CLI Orchestrator / Facade:** `cli.py` wires loader → analyzer → writer, exposing Typer commands and Rich UI.
- **Service Wrapper:** `OpenCodeService` adapts the external CLI, streams JSON events, and normalizes results.
- **Pipeline Builders:** `OutputManager` and `DocComposer` compose raw artifacts into navigable docs and manifest files.
- **Strategy Hooks (Depth Modes):** `quick` dispatches a lightweight prompt while `standard`/`deep` call the architecture prompt; richer per-depth strategies remain TODO.

## Components
- `cli` – Typer app, argument parsing, header panels, verbose streaming, success/failure handling.
- `repository_loader` – resolves local paths, clones Git URLs, manages reuse/force-clone, cleanup utilities.
- `opencode_service` – runs prompts, streams JSON, surfaces availability checks.
- `output_manager` – copies raw artifacts, writes logs/metadata/summary, saves structured JSON, invokes `DocComposer`.
- `doc_composer` – renders Mermaid diagrams to SVG (with OpenCode-powered auto-fix), builds `index.md`, subpages, and `.repo-explainer/coherence.json` manifests.
- `validate_coherence.py` – CLI script that verifies documentation structure, links, diagrams, and manifests.
- `docs/` – generated entry point (`index.md`), subdirectories (`components/`, `dataflow/`, `tech-stack/`), diagrams, and raw sources.

## Functionality
- `repo-explain analyze` accepts local paths or Git URLs, cloning remotes into `./tmp` and reusing clones unless `--force-clone` is provided.
- Depth modes: `quick` triggers a fast summary prompt; `standard`/`deep` run the full architecture prompt (deep still maps to the same prompt for now).
- Verbose mode streams OpenCode tool events (files read, bash invocations, writes) directly to the console.
- OpenCode outputs (`architecture.md`, `.mermaid`, `tech-stack.txt`) are copied into `docs/src/raw/`, logged, and summarized.
- `DocComposer` automatically renders diagrams (when Mermaid CLI is present), generates human-readable pages, embeds helpful fallback notes when rendering fails, and emits `.repo-explainer/coherence.json`.
- `validate_coherence.py` checks generated docs for structural integrity.
- `repo-explain update` exists as a placeholder command (Stage 3 target).

## Agent Architecture
Single-agent sequential pipeline:
1. **Loader** prepares the repository path (local or cloned remote).
2. **OpenCodeService** executes the selected prompt and streams JSON events.
3. **OutputManager** copies artifacts, writes logs/metadata/summary, and triggers doc composition.
4. **DocComposer** renders diagrams, writes `index.md` + subpages, and produces a manifest for validation tooling.
5. **Validation** is optional via `validate_coherence.py`.

Failures short-circuit the pipeline and surface OpenCode errors to the operator.

## Deliverables
- [x] `repo-explain analyze` generates markdown docs, SVG diagrams (when `mmdc` is installed), logs, metadata, and manifests.
- [x] `.repo-explainer/coherence.json` manifest plus structured directory layout under `docs/`.
- [x] `validate_coherence.py` for structural QA of generated docs.
- [ ] `repo-explain update` incremental analysis path.
- [ ] `.opencode/commands/*` custom prompt library + Claude Code fallback documentation.
- [ ] Local analyzer enrichments (tree-sitter/AST) beyond OpenCode output.

## Diagrams
- Backend architecture: `diagrams/stage_1/backend.mmd`
- TUI interaction: `diagrams/stage_1/tui.mmd`

## Implementation Checklist

### Core Infrastructure
- [x] Project structure (`src/repo_explainer/`)
- [x] `pyproject.toml` with dependencies (typer, rich, pydantic, GitPython)
- [x] Configuration management (`config.py` with pydantic-settings)
- [x] Entry point script (`repo-explain` command)

### CLI Module
- [x] Typer-based CLI entry point (`cli.py`)
- [x] `analyze` command with depth options (quick/standard/deep)
- [x] `analyze` command accepts both local paths and Git URLs
- [x] `--force-clone` flag for re-cloning Git repositories
- [x] `update` command placeholder
- [x] Rich terminal feedback (panels, progress spinners)
- [ ] Logging configuration (beyond Rich console output)
- [ ] Config file loading (YAML)

### OpenCode Integration
- [x] OpenCode service wrapper (`opencode_service.py`)
- [x] Command execution via subprocess
- [x] JSON output parsing (line-stream parsing for verbose mode)
- [x] Availability check
- [ ] Custom command support (`.opencode/commands/*.md`)
- [ ] Session ID tracking outside of verbose-mode streaming

### Repository Loader
- [x] Local path resolution
- [x] Git clone helper with GitPython
- [x] Git URL detection (HTTPS, SSH, Git protocol)
- [x] Git URL parsing (extract owner/repo from URL)
- [x] Automatic cloning to `./tmp/owner/repo`
- [x] Clone reuse (don't re-clone if already exists)
- [x] Force re-clone support
- [x] Cleanup utilities for removing clones
- [x] Integration with CLI analyze command
- [ ] Authentication stub (currently relies on system Git credentials)

### Analyzer
- [ ] Prompt preparation abstraction for OpenCode
- [ ] Tree-sitter/AST integration for local enrichment
- [ ] Python language support (beyond OpenCode summaries)
- [ ] JavaScript/TypeScript language support (beyond OpenCode summaries)

### Documentation Generator (DocComposer)
- [x] Markdown file writer (index + subpages)
- [x] Table of contents / navigation builder (Quick Navigation section)
- [x] Index creation with metadata + diagram embeds
- [x] OpenCode artifact ingestion + normalization

### Diagram Pipeline
- [x] Mermaid → SVG rendering via Mermaid CLI (with fallback guidance)
- [x] Import of OpenCode-produced `.mermaid` files into docs/diagrams
- [ ] Local `.mmd` authoring fallback when OpenCode diagrams are missing

### Output Manager
- [x] Directory structure creation (`docs/`, `docs/src/raw`, logs, diagrams, etc.)
- [x] Metadata/log persistence (JSON + raw logs)
- [x] Analysis summary generation (Markdown)
- [x] Raw output saving
- [x] Structured JSON output parsing
- [x] OpenCode session ID recording when available (verbose mode)
- [ ] Config tracking across runs (recording effective settings)
- [ ] Diagram/artifact file organization beyond current defaults (per-depth directories)

### Claude Code Fallback
- [ ] Claude Code CLI integration
- [ ] `--allowedTools` gating
- [ ] Fallback switching logic

### Deliverables
- [x] `repo-explainer analyze` producing markdown + diagrams
- [ ] `repo-explainer update` for incremental updates
- [ ] `.opencode/commands/analyze-architecture.md`
- [ ] Quick/standard/deep command variants under `.opencode/commands`
- [ ] Claude Code equivalent documentation
- [ ] Verified prompts for Gemini 3 Flash Preview
