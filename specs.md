# Development Stage Summary

This document summarizes the capabilities and deliverables captured in `stages/stage_*.md`. Each stage builds upon the previous one to grow Repository Explainer’s feature set.

## Stage 1 – MVP Essentials
**Focus**: Ship the baseline CLI that can analyze a single Python or JavaScript/TypeScript repository and produce structured markdown plus diagrams.

**Key Capabilities**
- Typer-based CLI with analyze/update commands that invoke OpenCode (`opencode -p ... -f json`) or predefined `.opencode/commands/*` to generate architecture docs/diagrams, plus deterministic orchestration across loader → OpenCode run → doc ingestion.
- Repository loader with Git clone support, AST/Tree-sitter powered analyzer for local enrichment, OpenRouter-backed LLM service, and a Markdown/doc pipeline that ingests OpenCode outputs (TOCs, metadata, logs, diagrams).
- Built-in fallback for Claude Code CLI (same prompts, `--allowedTools` gating) so the CLI can switch agents when OpenCode is unavailable.

**Deliverables**
- `repo-explainer analyze` and `repo-explainer update` producing markdown docs, logs, and at least one architecture diagram per run by calling OpenCode (`project:analyze-architecture`).
- Baseline `.opencode/commands/analyze-architecture.md` plus `quick/standard/deep` variants, alongside documented Claude Code equivalents using `--output-format json`.
- Verified prompt templates for Gemini 3 Flash Preview focused on structure detection and compatible with both OpenCode and Claude Code flows.
- Official support for Python and JavaScript/TypeScript repositories only.


## Stage 2 – Expanded Insight
**Focus**: Enrich repository understanding with pattern detection, multi-language parsing, richer diagrams, and surfaced progress metrics.

**Key Capabilities**
- Pattern detection and dependency mapping modules that inspect manifests (`package.json`, `pyproject.toml`, `go.mod`, etc.), generate prompts, and feed OpenCode/Claude sessions with targeted context to capture MVC/microservice cues plus design patterns.
- Document structure analyzer that organizes outputs into nested sections, ingesting OpenCode diagram/doc artifacts (sequence, ER, dependency, call) and providing ASCII fallbacks.
- Progress tracker and context manager providing timers, token usage, verbose CLI updates, chunked LLM inputs, and surfacing OpenCode session metadata for operators.

**Deliverables**
- `patterns/identified-patterns.md` capturing architectural and design insights.
- Complete sets of sequence/ER/dependency/call diagrams stored under `diagrams/` in both `.mmd` and ASCII formats.
- Configurable progress reporting that lets operators opt in/out of specific analyses.

## Stage 3 – Scaling Performance
**Focus**: Optimize throughput for larger repositories through incremental re-analysis, caching, and parallel execution.

**Key Capabilities**
- Incremental engine that compares prior metadata with new diffs to re-run only impacted analyzers/diagram generators and spawn scoped OpenCode sessions per diff chunk.
- Parallel executor using `asyncio`/`concurrent.futures`, context optimizer for smart chunk sizing, and caching/flyweight strategies that manage concurrent OpenCode/Claude sessions.
- Cost monitor plus centralized retry handler covering token usage thresholds, graceful shutdown, and exponential backoff for LLM/network failures, including agent CLI exits.

**Deliverables**
- Incremental run mode updating docs/logs strictly for modified components.
- Progressive output streaming so high-level docs arrive before deeper sections finish.
- Token/cost dashboards with safe-stop controls when approaching user-defined limits.

## Stage 4 – Multi-Repository Awareness
**Focus**: Accept manifests that describe multiple services and produce cross-repository documentation and diagrams.

**Key Capabilities**
- Multi-repo configuration parser defining repo lists, credentials, sequencing priorities, per-service exclusions, and OpenCode command mappings.
- Cross-service mapper and service registry that connect shared libraries, APIs, and infrastructure patterns, coordinating multiple OpenCode sessions (one per repo) plus Claude fallbacks when needed.
- System diagram generator and unified doc builder that synthesize combined indexes, comparison tables, and system-wide Mermaid/Graphviz views based on aggregated OpenCode outputs.

**Deliverables**
- Config-driven multi-repo analysis command that writes per-service outputs plus a shared system view.
- Documentation detailing inter-service communication, shared dependencies, and security constraints.
- Enforcement of per-service exclusion rules to keep sensitive code out of generated artifacts.

## Stage 5 – Enhancements & Polish
**Focus**: Refine usability with interactive outputs, IDE integrations, flexible LLM providers, and export tooling.

**Key Capabilities**
- Interactive renderer and static exporter that turn Markdown into navigable HTML sites (FastAPI/Flask hosting plus MkDocs/Astro/Docusaurus pipelines) and can re-trigger OpenCode to refresh stale artifacts.
- VS Code extension scaffolding and diagram exporter capable of producing SVG/PNG assets while retaining ASCII fallbacks, including shortcuts to launch OpenCode/Claude runs.
- Provider registry, telemetry opt-in, and plugin surface for additional LLMs, local models, and community analyzers, delegating artifact generation to OpenCode by default with Claude as schema-enforced fallback.

**Deliverables**
- Optional interactive HTML documentation bundles with search/navigation plus downloadable `html/` directories.
- VS Code extension (or documented integration hooks) for previewing docs and triggering exports.
- Support for multiple LLM providers, including offline/local options, alongside enhanced diagram export tooling for stakeholders.
