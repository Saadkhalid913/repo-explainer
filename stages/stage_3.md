# Stage 3 – Scaling Performance

**Technologies**
- `asyncio` and `concurrent.futures` for parallel analysis threads/processes.
- `diskcache` or custom caching layer for LLm prompts/responses and repository metadata snapshots.
- Profiling via `cProfile`/`pyinstrument` in CI to track hotspots.
- `git` hooks or watchers for detecting incremental changes via `git diff --name-only`.

**Design Patterns**
- Observer pattern for invalidation subscribers on file changes.
- Command pattern for incremental update tasks (scan, analyze diff, refresh docs).
- Flyweight for reused diagram templates and prompt snippets.
- Caching decorator for repeated LLM queries or heavy AST parsing.

**Components**
- `incremental_engine`: Watches previous analysis metadata, computes diffs, schedules reanalysis only for touched components.
- `parallel_executor`: Schedules repo parsing, LLM calls, documentation generation while respecting resource limits.
- `context_optimizer`: Dynamically sizes chunks based on file complexity, merges small files for batching.
- `cost_monitor`: Tracks token usage/costs, exposes thresholds for warnings.
- `retry_handler`: Centralizes exponential backoff for network/LLM failures.

**Functionality**
- Detect repository changes via stored metadata and re-run analysis only on altered components.
- Stream progressive documentation output, allowing early access to overviews while deeper sections finish.
- Report token/cost usage mid-run and allow graceful shutdown when user-defined limits approach.

**Agent Architecture**
- **Pattern**: Sequential flow that incorporates observer and command patterns: incremental engine acts as a controller that reruns whichever agents (analysis, diagram regen) are invalidated by diffs.
- **Orchestrator role**: `incremental_engine` monitors cached state and triggers a fan-in/fan-out to update only impacted modules, resembling a deterministic subset of Azure sequential orchestration with caching hooks.
- **Tooling**: `parallel_executor` hosts short-lived worker agents (invoking OpenCode server sessions per diff set) which fetch diffs, re-trigger pattern detection, and update docs while the orchestrator ensures context is refreshed before downstream tasks run.
- **Validation**: Task-level checkpoints mark agent success/failure, so the orchestrator can either retry individual agents or propagate a failure with context for human inspection, matching guidance on reliability and observability.

**Deliverables**

- Incremental run mode that updates docs plus logs precise changes.
- Progressive output where high-level docs appear early while deeper analysis continues.
- Token/cost dashboards and safe stop mechanism when hitting thresholds.
