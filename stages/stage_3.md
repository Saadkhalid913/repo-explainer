# Stage 3 – Scaling Performance

**Technologies**
- `asyncio` and `concurrent.futures` for parallel analysis threads/processes plus concurrent OpenCode session handling.
- `diskcache` or custom caching layer for LLM prompts/responses, repository metadata snapshots, and OpenCode session manifests/results.
- Profiling via `cProfile`/`pyinstrument` in CI to track hotspots.
- `git` hooks or watchers for detecting incremental changes via `git diff --name-only`.

**Design Patterns**
- Observer pattern for invalidation subscribers on file changes.
- Command pattern for incremental update tasks (scan, analyze diff, refresh docs).
- Flyweight for reused diagram templates and prompt snippets.
- Caching decorator for repeated LLM queries or heavy AST parsing.

**Components**
- `incremental_engine`: Watches previous analysis metadata, computes diffs, schedules reanalysis only for touched components, and crafts OpenCode prompts scoped to the diff.
- `parallel_executor`: Schedules repo parsing, LLM calls, OpenCode sessions, and documentation generation while respecting resource limits; supports multiple OpenCode HTTP sessions simultaneously.
- `context_optimizer`: Dynamically sizes chunks based on file complexity, merges small files for batching, and decides when to hand context to OpenCode vs. Claude fallback.
- `cost_monitor`: Tracks token usage/costs, exposes thresholds for warnings, and logs OpenCode token/call estimates per session.
- `retry_handler`: Centralizes exponential backoff for network/LLM failures, including OpenCode and Claude CLI exit codes.

**Functionality**
- Detect repository changes via stored metadata and re-run analysis only on altered components, issuing OpenCode requests that target affected directories/files.
- Stream progressive documentation output from both local analyzers and OpenCode sessions, allowing early access to overviews while deeper sections finish.
- Report token/cost usage mid-run (including OpenCode session runtimes) and allow graceful shutdown when user-defined limits approach.

**Agent Architecture**
- **Pattern**: Sequential flow that incorporates observer and command patterns: incremental engine acts as a controller that reruns whichever agents (analysis, diagram regen) are invalidated by diffs.
- **Orchestrator role**: `incremental_engine` monitors cached state and triggers a fan-in/fan-out to update only impacted modules, resembling a deterministic subset of Azure sequential orchestration with caching hooks.
- **Tooling**: `parallel_executor` hosts short-lived worker agents (invoking OpenCode server sessions per diff set) which fetch diffs, re-trigger pattern detection, and update docs while the orchestrator ensures context is refreshed before downstream tasks run.
- **Validation**: Task-level checkpoints mark agent success/failure, so the orchestrator can either retry individual agents or propagate a failure with context for human inspection, matching guidance on reliability and observability.

**Deliverables**

- Incremental run mode that updates docs plus logs precise changes.
- Progressive output where high-level docs appear early while deeper analysis continues.
- Token/cost dashboards and safe stop mechanism when hitting thresholds.

## Diagrams
- Backend architecture: `diagrams/stage_3/backend.mmd`
- TUI interaction: `diagrams/stage_3/tui.mmd`
