# Repository Explainer - API Documentation

**Version:** 0.1.0
**Stage:** 1 - MVP Essentials
**Last Updated:** 2026-01-17 - Coherent docs, diagram pipeline, Git URL loader

## Changes

### v0.1.0 - Coherent Documentation + Git URL Workflow
- **NEW**: Repository cloning pipeline supports local paths or Git URLs with automatic caching under `./tmp/<owner>/<repo>`
- **NEW**: `--force-clone` flag to refresh remote repositories
- **NEW**: Rich CLI UX (panels, spinners, verbose event streaming)
- **NEW**: Coherent documentation generation with `index.md` as the entry point
- **NEW**: `DocComposer` module renders Mermaid diagrams to SVG, emits subpages (components/dataflow/tech-stack), and records `.repo-explainer/coherence.json`
- **NEW**: Validation script (`validate_coherence.py`) for documentation structure
- **NEW**: Improved CLI output highlighting coherent docs first, with technical artifacts listed separately
- Added Git URL detection/parsing + clone reuse via `RepositoryLoader`
- CLI successfully invokes OpenCode via `opencode run <prompt> --format json --model openrouter/google/gemini-3-flash-preview`

## Overview

Repository Explainer is a Typer-based CLI tool that analyzes repositories using OpenCode, then emits a fully navigable documentation bundle. It supports both **local repositories** and **remote Git URLs** and automatically renders diagrams when Mermaid CLI is available.

## Quick Reference

**Analyze local repository:**
```bash
repo-explain analyze ./my-project --depth quick
```

**Analyze remote repository:**
```bash
repo-explain analyze https://github.com/user/repo --depth quick
```

**Force re-clone:**
```bash
repo-explain analyze https://github.com/user/repo --force-clone
```

**Get help:**
```bash
repo-explain --help
repo-explain analyze --help
```

## Table of Contents
1. [CLI Commands](#cli-commands)
2. [Configuration](#configuration)
3. [Services](#services)
4. [Testing & Troubleshooting](#testing--troubleshooting)
5. [Examples](#examples)
6. [Future API Changes](#future-api-changes)
7. [Contributing](#contributing)

---

## CLI Commands

### `repo-explain analyze`

Analyze a repository and generate documentation, architecture diagrams, technology stack summaries, and a coherent navigation layer.

Accepts either a **local path** or a **Git URL**. Git URLs are cloned to `./tmp/<owner>/<repo>` and reused across runs unless `--force-clone` is set.

**Usage:**
```bash
repo-explain analyze [REPO_PATH_OR_URL] [OPTIONS]
```

**Arguments:**
- `REPO_PATH_OR_URL` (optional): Local path or Git URL to analyze (default: current directory `.`)
  - **Local path**: Relative or absolute path to an existing directory
  - **Git URL**: HTTPS, SSH, or Git protocol URL
    - HTTPS: `https://github.com/user/repo`
    - SSH: `git@github.com:user/repo.git`
    - Git: `git://example.com/repo.git`
  - Git URLs are cloned to `./tmp/<owner>/<repo>` with reuse between runs

**Options:**
- `--depth, -d [quick|standard|deep]`: Analysis depth (default: `standard`)
  - `quick`: Fast scan – languages, structure, dependencies
  - `standard`: Full architecture prompt (currently same as deep)
  - `deep`: Reserved for enriched analysis in later stages
- `--output, -o PATH`: Output directory for generated documentation (default: `docs/`)
- `--force-clone`: Remove existing clone for Git URLs before analyzing
- `--verbose, -V`: Stream OpenCode tool events (files read, commands run, writes)
- `--help`: Show command help

**Workflow:**
1. Resolve or clone repository via `RepositoryLoader`
2. Check OpenCode CLI availability
3. Run selected analysis depth (quick vs architecture prompt)
4. Copy raw artifacts, logs, metadata, structured JSON into `output/src/`
5. Compose coherent docs (index + subpages + diagrams) and render `.svg` diagrams when `mmdc` is installed
6. Print success panel with output location and session data

**Output Layout (default `docs/`):**
```
docs/
├── index.md                    # Main entry point
├── components/overview.md      # Component architecture + diagram embeds
├── dataflow/overview.md        # Sequence diagrams, narrative
├── tech-stack/overview.md      # Normalized tech stack
├── diagrams/
│   ├── components.svg
│   └── dataflow.svg
└── src/
    ├── raw/
    │   ├── architecture.md
    │   ├── components.mermaid
    │   ├── dataflow.mermaid
    │   └── tech-stack.txt
    ├── ANALYSIS_SUMMARY.md
    ├── analysis_<depth>.json
    └── logs/
        ├── analysis_<timestamp>.txt
        └── metadata_<timestamp>.json
```

**Terminal Output Sections:**
- 📚 Coherent Documentation – human-readable entry points (index + subpages)
- 🔧 Technical Artifacts – raw/structured files for debugging
- 💡 Tip – points to `index.md` or `ANALYSIS_SUMMARY.md`

**Examples:**

_Local Repositories_
```bash
repo-explain analyze
repo-explain analyze /path/to/repo --depth quick --output ./project-docs
repo-explain analyze . --depth deep --verbose
```

_Remote Git URLs_
```bash
repo-explain analyze https://github.com/torvalds/linux --depth quick
repo-explain analyze git@github.com:user/repo.git --force-clone
repo-explain analyze https://github.com/facebook/react --depth standard --verbose
```

**Clone Location Diagnostics:**
```bash
repo-explain analyze https://github.com/octocat/Hello-World
# -> ./tmp/octocat/Hello-World

repo-explain analyze https://github.com/octocat/Hello-World --force-clone
# Outputs "Removing existing clone" then reclones
```

### `repo-explain update`

**Status:** Placeholder – incremental update support planned for Stage 3.

Displays a Rich panel explaining the feature is coming soon.

**Usage:**
```bash
repo-explain update [REPO_PATH] [OPTIONS]
```

**Options:**
- `--verbose, -V`: Enable verbose output

### Global Options

- `--version, -v`: Display application version
  ```bash
  repo-explain --version
  # repo-explainer v0.1.0
  ```
- `--help`: Show main help message

---

## Configuration

Configuration is managed through `pydantic-settings` (env vars or `.env`).

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `REPO_EXPLAINER_OPENCODE_BINARY` | string | `opencode` | Path to OpenCode CLI binary |
| `REPO_EXPLAINER_OPENCODE_OUTPUT_FORMAT` | string | `json` | Output format (`json` required for event streaming) |
| `REPO_EXPLAINER_OPENCODE_MODEL` | string | `openrouter/google/gemini-3-flash-preview` | Default OpenCode model |
| `REPO_EXPLAINER_ANALYSIS_DEPTH` | string | `standard` | Default depth |
| `REPO_EXPLAINER_OUTPUT_DIR` | path | `docs/` | Where results are written |
| `REPO_EXPLAINER_DIAGRAMS_DIR` | path | `diagrams/` | (Reserved for future multi-doc workflows) |
| `REPO_EXPLAINER_VERBOSE` | bool | `false` | Verbose streaming toggle |

**Example `.env`:**
```env
REPO_EXPLAINER_OPENCODE_BINARY=/usr/local/bin/opencode
REPO_EXPLAINER_OPENCODE_MODEL=openrouter/google/gemini-3-flash-preview
REPO_EXPLAINER_VERBOSE=true
REPO_EXPLAINER_OUTPUT_DIR=./generated-docs
```

**Python API:**
```python
from repo_explainer.config import get_settings
settings = get_settings()
print(settings.output_dir)
```

---

## Services

### RepositoryLoader (`src/repo_explainer/repository_loader.py`)

Handles local path resolution and Git URL cloning to `./tmp`. Reuses existing clones unless `force_clone=True`.

Key methods:
- `load(path_or_url, force_clone=False) -> Path`
- `is_git_url(path_or_url) -> bool`
- `parse_git_url(git_url) -> (owner, repo)`
- `get_clone_path(git_url) -> Path`
- `clone_repository(git_url, force=False)`
- `cleanup(owner=None, repo=None)`

### OpenCodeService (`src/repo_explainer/opencode_service.py`)

Wrapper around the `opencode` CLI with line-by-line JSON streaming.

Key capabilities:
- `check_available()` – verifies `opencode --version`
- `quick_scan()` – light prompt for languages/structure
- `analyze_architecture()` – architecture prompt requesting markdown + mermaid + tech stack
- `run_command(prompt, command=None, event_callback=None)` – base executor (used for depth variants)

### OutputManager (`src/repo_explainer/output_manager.py`)

Responsible for copying artifacts from the analyzed repo into the output directory, writing logs/metadata/summaries, storing structured JSON, and invoking `DocComposer`.

### DocComposer (`src/repo_explainer/doc_composer.py`)

Transforms raw artifacts into coherent docs.
- Renders `.mermaid` → `.svg` via Mermaid CLI with retry + OpenCode auto-fix fallback
- Creates `index.md`, `components/overview.md`, `dataflow/overview.md`, `tech-stack/overview.md`
- Embeds diagrams / includes helpful fallback instructions if rendering fails
- Produces `.repo-explainer/coherence.json` manifest for validation

### validate_coherence (`validate_coherence.py`)

Standalone validator that ensures generated docs follow the expected structure.

---

## Testing & Troubleshooting

### Testing the CLI

1. **Verify Installation**
```bash
repo-explain --version
repo-explain --help
repo-explain analyze --help
```

2. **Quick Analysis Smoke Test**
```bash
repo-explain analyze . --depth quick --verbose
```
Check that OpenCode is available, JSON events stream, and the run completes.

3. **Standard Analysis**
```bash
repo-explain analyze . --depth standard
```

4. **Custom Output Directory**
```bash
repo-explain analyze . --depth quick --output ./my-analysis --verbose
ls -la ./my-analysis
```

5. **Environment Variable Overrides**
```bash
export REPO_EXPLAINER_VERBOSE=true
export REPO_EXPLAINER_OUTPUT_DIR=./generated-docs
repo-explain analyze . --depth quick
```

6. **Full Integration Script**
```bash
bash test_cli.sh
```
Runs version/help tests, quick analysis, Git URL clone/reuse/force-clone scenarios.

7. **Validate Coherent Docs**
```bash
python validate_coherence.py docs
```
Ensures index/subpages/diagrams/manifest exist and links resolve.

### Troubleshooting

**OpenCode Not Found**
```
Warning: OpenCode CLI not found...
```
- Install OpenCode CLI or set `REPO_EXPLAINER_OPENCODE_BINARY`

**Command Timeout**
```
OpenCode command timed out after 5 minutes
```
- Large repos: start with `--depth quick`

**Output Directory Issues**
```
Cannot create output directory
```
- Ensure parent exists / permissions ok / set `--output`

**Git Clone Failures**
- Validate URL, credentials, network, disk space
- Use `repo-explain analyze <url> --force-clone` after cleanup

**Mermaid CLI Missing**
- Install via `npm install -g @mermaid-js/mermaid-cli`
- Docs still generate; `.mermaid` sources are linked with instructions

**Mermaid Syntax Errors**
- DocComposer auto-fixes via OpenCode when possible
- Fallback instructions appear inside components/dataflow pages

---

## Examples

1. **Quick Project Overview**
```bash
repo-explain analyze ./my-python-project --depth quick --verbose
```

2. **Full Analysis with Custom Output**
```bash
repo-explain analyze /path/to/repo \
  --depth standard \
  --output ./project-documentation \
  --verbose
```

3. **Environment Variables**
```bash
REPO_EXPLAINER_OUTPUT_DIR=./docs REPO_EXPLAINER_VERBOSE=true \
  repo-explain analyze . --depth standard
```

4. **Remote GitHub Repository**
```bash
repo-explain analyze https://github.com/facebook/react --depth quick
```

5. **Force Re-clone**
```bash
repo-explain analyze https://github.com/torvalds/linux \
  --force-clone --depth standard --verbose
```

6. **Multiple Repositories in a Loop**
```bash
for repo in ...; do
  repo-explain analyze "$repo" --depth quick
```

7. **SSH URL for Private Repo**
```bash
repo-explain analyze git@github.com:myorg/private-repo.git --depth standard
```

---

## Future API Changes

- **Stage 2:** Pattern detection, dependency mapping, richer diagrams
- **Stage 3:** Incremental `update` command, caching/intelligent diffs
- **Stage 4:** Multi-repository analysis
- **Stage 5:** Interactive HTML output, IDE integrations, multi-LLM provider support

Roadmap details live in `stages/`.

---

## Contributing

1. Update `docs.md` for any API changes
2. Update `.claude.md` if guidelines change
3. Update `stages/stage_1.md` checklist
4. Run `bash test_cli.sh` (or relevant subset)
5. Submit concise commit with summary of changes
