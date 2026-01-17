# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased] - 2026-01-17

### Added
- **Team Directory**: Added `ANOTHERTEST.MD` providing comprehensive contact information and directory for engineering teams (Backend, Frontend, DevOps, etc.).
- **Documentation Update**: Updated `components.json` and `architecture.md` to include and refine the `team-directory` component.
- **Orchestrator Pattern**: Introduced a central `Orchestrator` to coordinate the analysis pipeline (loader, analyzer, AI runner, and document generation).
- **OpenCode Runner**: New execution engine that separates AI command logic from the integration service and adds support for fallback AI providers.
- **Claude CLI Fallback**: Added `ClaudeRunner` to provide analysis capabilities when the OpenCode CLI is not available.
- **Incremental Updates**: New `update` command in CLI to refresh documentation based on recent Git commits without full re-analysis.
- **HTML Documentation**: New `HTML Generator` component that converts Markdown documentation into a styled HTML website with a live preview server.
- **Update History Tracking**: HTML documentation now includes an update history page and notification banners for recent changes.
- **AI-Powered Mermaid Fixes**: `Doc Composer` now uses OpenCode to automatically fix Mermaid syntax errors during diagram rendering.
- **Enhanced Documentation Structure**:
  - API documentation with per-endpoint pages.
  - Detailed dependency mapping (upstream, downstream, and external).
  - Manifest generation (`coherence.json`) for documentation state tracking.

### Fixed
- **HTTP Server Attribute Error**: Resolved a closure issue in `html_generator.py` where the `CustomHandler` could not access `docs_dir`.

### Modified
- **CLI**: `analyze` command now supports `--generate-html`, `--html-port`, and `--no-browser` flags.
- **Doc Composer**: Major refactoring to support multi-page documentation and advanced rendering logic.
- **Config**: Added settings for `diagrams_dir` and `opencode_model`.
- **Output Management**: Improved directory structure with separate `src/raw`, `src/logs`, and themed subdirectories.

### Affected Components
- `team-directory` (ANOTHERTEST.MD) - **NEW**
- `cli` (src/repo_explainer/cli.py)
- `orchestrator` (src/repo_explainer/orchestrator.py) - **NEW**
- `opencode-runner` (src/repo_explainer/opencode_runner.py) - **NEW**
- `opencode-service` (src/repo_explainer/opencode_service.py)
- `doc-composer` (src/repo_explainer/doc_composer.py)
- `output-manager` (src/repo_explainer/output_manager.py)
- `html-generator` (src/repo_explainer/html_generator.py)
- `config` (src/repo_explainer/config.py)
