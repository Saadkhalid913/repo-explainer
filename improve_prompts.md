# Improve Prompts Plan

## Goal
Create richer, context-aware prompt files that let future orchestrator agents (per `stages/stage_2.md`) request actionable outputs, including explicit mappings between functions/components and the source files that implement them. The new prompts must directly support the onboarding outcomes outlined in `specs.md` and the quality criteria in `REQUIREMENTS.md` (FR-6.2 Prompt Engineering, FR-2.1 Progressive Analysis, FR-2.3 Pattern Detection).

## Current Gaps
- `src/repo_explainer/opencode_service.py` only exposes two prompts (`quick_scan`, `analyze_architecture`) that provide shallow overviews without file-to-component mappings or stage-specific deliverables.
- Existing prompts do not capture progressive detail, design patterns, dependency graphs, or per-file evidence, which limits how Stage 2 components (`pattern_detector`, `dependency_mapper`, `doc_structure_analyzer`, `context_manager`) can collaborate.
- There is no shared contract for orchestrator-friendly metadata (session IDs, artifact manifests, navigation hints) that later stages require for coordination and validation.

## Plan Overview
1. **Inventory & Baseline Audit**
   - Document every prompt currently referenced in the CLI, specs, and `.opencode` command placeholders. Capture purpose, inputs, and outputs to expose gaps against `REQUIREMENTS.md`.

2. **Define Orchestrator Context Contract**
   - Specify the JSON/Markdown schema that Stage 2+ orchestrators expect: repository summary, module/component index, function-to-file mappings, dependency lists, and diagram stubs.
   - Include hooks for progress reporting (session metadata, timers) per `stages/stage_2.md`.

3. **Design Prompt Families**
   - **Quick Scan v2**: lightweight inventory that still emits module/file table of contents and language detection.
   - **Architecture Deep Dive**: enriched prompt covering architecture narrative, per-component responsibilities, explicit `file_path` references for each function/class, and diagram-ready relationship tables.
   - **Pattern/Dependency Prompts**: targeted prompts for `pattern_detector` and `dependency_mapper`, referencing manifests and code samples.
   - **Documentation Composer Prompt**: ensures outputs align with onboarding goals (purpose, responsibilities, key entry points, dependencies).

4. **Map Functions/Components to Files**
   - Embed instructions that every component/function described must cite its source file(s) and line ranges when available.
   - Require the agent to emit `component_id`, `file_path`, `key_functions`, and `dependencies` arrays so downstream tooling can build precise references.

5. **Context Management Strategy**
   - Outline how prompts will request summarized snippets vs. full files, coordinating with `context_manager` requirements (chunking, caching, prioritization).
   - Include guidance for multi-language parsing (Tree-sitter, etc.) so prompts request analysis per language when necessary.

6. **Quality & Validation Hooks**
   - Define acceptance criteria for each prompt: expected artifacts, schema validation, hallucination checks, and success metrics (e.g., % of components mapped to files).
   - Plan automated tests or validation commands (e.g., `opencode run prompt --format json | jq ...`).

7. **Deliverables & Ownership**
   - Produce updated prompt templates stored under a dedicated directory (e.g., `prompts/` or `.opencode/commands/`), each accompanied by README notes on usage, inputs, and outputs.
   - Document rollout steps so later stages (Stage 2 orchestrator) can adopt the new prompts with minimal changes.

## Dependencies & Open Questions
- Confirm final location/naming scheme for prompt files (e.g., `.opencode/commands/*.md`).
- Decide whether to version prompts per stage or maintain a single evolving set.
- Determine how much of the mapping responsibility is handled by OpenCode vs. local AST analyzers, ensuring prompts instruct the LLM to defer to local evidence when available.
