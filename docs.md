# Repository Explainer - API Documentation

**Version:** 0.1.0
**Stage:** 1 - MVP Essentials
**Last Updated:** 2025-01-17 - OpenCode CLI integration working

## Changes

### v0.1.0 - Initial Release
- Fixed OpenCode CLI command syntax to use `opencode run <prompt>` instead of incorrect `-p` flag
- Removed custom command flag for now; will implement `.opencode/commands/` in next iteration
- CLI successfully invokes OpenCode and receives JSON output

## Overview

Repository Explainer is a CLI tool that analyzes repositories and generates AI-powered documentation using OpenCode.

## Table of Contents
1. [CLI Commands](#cli-commands)
2. [Configuration](#configuration)
3. [Services](#services)
4. [Testing & Troubleshooting](#testing--troubleshooting)
5. [Examples](#examples)

---

## CLI Commands

### `repo-explain analyze`

Analyze a repository and generate documentation, architecture diagrams, and technology stack information.

**Usage:**
```bash
repo-explain analyze [REPO_PATH] [OPTIONS]
```

**Arguments:**
- `REPO_PATH` (optional): Path to repository to analyze (default: current directory `.`)
  - Must be an existing directory
  - Can be absolute or relative path

**Options:**
- `--depth, -d <TEXT>`: Analysis depth mode (default: `standard`)
  - `quick`: Fast scan - basic project structure and dependencies
  - `standard`: Full architecture analysis with diagrams
  - `deep`: Deep analysis including patterns and optimization suggestions

- `--output, -o <PATH>`: Output directory for generated documentation
  - If not specified, uses configured output directory (default: `docs/`)

- `--verbose, -V`: Enable verbose output
  - Shows OpenCode session IDs
  - Displays command execution details
  - Prints full API responses

- `--help`: Show command help

**Returns:**
- Generated artifacts stored in output directory:
  - `architecture.md` - Architecture overview
  - `components.mermaid` - Component diagram
  - `dataflow.mermaid` - Data flow diagram
  - `tech-stack.txt` - Technology stack summary
  - `logs/` - Execution logs

**Example:**
```bash
# Analyze current directory (standard depth)
repo-explain analyze

# Analyze specific repo with verbose output
repo-explain analyze /path/to/repo --verbose

# Quick scan, custom output directory
repo-explain analyze ./my-project --depth quick --output ./project-docs

# Deep analysis
repo-explain analyze /absolute/path/to/repo --depth deep
```

---

### `repo-explain update`

**Status:** Coming in future iteration
Update existing documentation for changed repository files.

**Usage:**
```bash
repo-explain update [REPO_PATH] [OPTIONS]
```

**Options:**
- `--verbose, -V`: Enable verbose output

**Note:** Currently a placeholder. Will implement incremental analysis in Stage 3.

---

### Global Options

- `--version, -v`: Display application version
  ```bash
  repo-explain --version
  # Output: repo-explainer v0.1.0
  ```

- `--help`: Show main help message
  ```bash
  repo-explain --help
  ```

---

## Configuration

Configuration is managed via `pydantic-settings` and can be set through environment variables or `.env` files.

### Environment Variables

| Variable | Type | Default | Description |
|----------|------|---------|-------------|
| `REPO_EXPLAINER_OPENCODE_BINARY` | string | `opencode` | Path to OpenCode CLI binary |
| `REPO_EXPLAINER_OPENCODE_OUTPUT_FORMAT` | string | `json` | Output format from OpenCode |
| `REPO_EXPLAINER_ANALYSIS_DEPTH` | string | `standard` | Default analysis depth |
| `REPO_EXPLAINER_OUTPUT_DIR` | path | `docs/` | Default output directory |
| `REPO_EXPLAINER_DIAGRAMS_DIR` | path | `diagrams/` | Diagram output directory |
| `REPO_EXPLAINER_VERBOSE` | bool | `false` | Enable verbose output globally |

**Example `.env` file:**
```env
REPO_EXPLAINER_OPENCODE_BINARY=/usr/local/bin/opencode
REPO_EXPLAINER_VERBOSE=true
REPO_EXPLAINER_OUTPUT_DIR=./generated-docs
```

**Python API:**
```python
from repo_explainer.config import get_settings

settings = get_settings()
print(settings.opencode_binary)  # "opencode"
print(settings.output_dir)        # Path("docs")
```

---

## Services

### OpenCodeService

Service for interacting with OpenCode CLI.

**Location:** `src/repo_explainer/opencode_service.py`

**Class:** `OpenCodeService`

#### Constructor

```python
OpenCodeService(repo_path: Path)
```

**Parameters:**
- `repo_path`: Path to the repository to analyze

**Example:**
```python
from pathlib import Path
from repo_explainer.opencode_service import OpenCodeService

service = OpenCodeService(Path("/path/to/repo"))
```

#### Methods

##### `run_command(prompt: str, command: str | None = None) -> OpenCodeResult`

Execute an arbitrary OpenCode command.

**Parameters:**
- `prompt` (str): The prompt to send to OpenCode
- `command` (str, optional): Custom command name (e.g., `project:analyze-architecture`)

**Returns:** `OpenCodeResult` dataclass with fields:
- `success` (bool): Whether command succeeded
- `output` (str): Raw output from OpenCode
- `error` (str | None): Error message if failed
- `session_id` (str | None): OpenCode session ID
- `artifacts` (dict): Parsed JSON artifacts from output

**Example:**
```python
result = service.run_command(
    prompt="Analyze this repo structure",
    command="project:custom-command"
)

if result.success:
    print(f"Session: {result.session_id}")
    print(f"Artifacts: {result.artifacts}")
else:
    print(f"Error: {result.error}")
```

##### `analyze_architecture() -> OpenCodeResult`

Run full architecture analysis.

**Returns:** `OpenCodeResult` with architecture, component diagram, dataflow diagram, and tech stack

**Example:**
```python
result = service.analyze_architecture()
if result.success:
    print("Analysis complete!")
    print(result.artifacts)
```

##### `quick_scan() -> OpenCodeResult`

Run a quick scan of the repository.

**Returns:** `OpenCodeResult` with basic project information

**Example:**
```python
result = service.quick_scan()
```

##### `check_available() -> bool`

Check if OpenCode CLI is available.

**Returns:** `True` if OpenCode is accessible, `False` otherwise

**Example:**
```python
if service.check_available():
    print("OpenCode is ready")
else:
    print("OpenCode not found - install it or set REPO_EXPLAINER_OPENCODE_BINARY")
```

---

## Testing & Troubleshooting

### Testing the CLI

#### 1. Verify Installation

```bash
# Check version
repo-explain --version
# Output: repo-explainer v0.1.0

# View help
repo-explain --help

# View analyze command help
repo-explain analyze --help
```

#### 2. Test Quick Analysis (Recommended First)

Start with a quick analysis to verify OpenCode integration:

```bash
repo-explain analyze . --depth quick --verbose
```

**What to look for:**
- "OpenCode available" check passes
- No "OpenCode binary not found" error
- JSON output from OpenCode (showing `sessionID`, `tool_use`, etc.)
- Analysis completes without timeout

**Sample Output:**
```
╭──────────────────────────────────────────────────────╮
│ Repository Explainer v0.1.0                          │
│ Analyzing: /Users/saadkhalid/Projects/repo-explainer │
╰──────────────────────────────────────────────────────╯
⠇ OpenCode available

Running quick analysis...

Running: opencode run Perform a quick scan...
⠋ Analyzing repository (quick mode)...

Analysis complete!

Output:
{"type":"step_start",...}  # JSON streaming output
```

#### 3. Test Standard Analysis

```bash
repo-explain analyze . --depth standard
```

This runs a deeper analysis with architecture diagrams and component mapping.

#### 4. Test with Custom Output Directory

```bash
repo-explain analyze . --depth quick --output ./my-analysis --verbose
```

Verify that `./my-analysis/` directory is created with output files.

#### 5. Test Configuration Environment Variables

```bash
export REPO_EXPLAINER_VERBOSE=true
export REPO_EXPLAINER_OUTPUT_DIR=./generated-docs

repo-explain analyze . --depth quick
```

Verify that settings are applied from environment.

#### 6. Full Integration Test

```bash
# Clean test
rm -rf test-output

# Run analysis with all options
repo-explain analyze . \
  --depth standard \
  --output test-output \
  --verbose

# Verify output directory exists
ls -la test-output/
```

**Validation Checklist:**
- [ ] `repo-explain --version` shows v0.1.0
- [ ] `repo-explain --help` displays command list
- [ ] `repo-explain analyze --help` shows all options
- [ ] `repo-explain analyze . --depth quick --verbose` completes successfully
- [ ] OpenCode session ID is displayed in verbose output
- [ ] No timeouts or "binary not found" errors
- [ ] Custom output directory is created when specified
- [ ] Environment variables are respected
- [ ] Help text displays correctly for all commands

### Common Issues

#### OpenCode Not Found

**Error Message:**
```
Warning: OpenCode CLI not found. Please install OpenCode or ensure it's in your PATH.
Tip: Set REPO_EXPLAINER_OPENCODE_BINARY to specify a custom path.
```

**Solution:**
1. Install OpenCode CLI
2. Or set the binary path:
   ```bash
   export REPO_EXPLAINER_OPENCODE_BINARY=/path/to/opencode
   repo-explain analyze .
   ```

#### Command Timeout

**Error Message:**
```
OpenCode command timed out after 5 minutes
```

**Solution:**
- Repository might be very large
- Check system resources
- Try with `--depth quick` first

#### Output Directory Issues

**Error Message:**
```
Cannot create output directory
```

**Solution:**
- Ensure parent directories exist
- Check write permissions
- Set custom output path:
  ```bash
  repo-explain analyze . --output ./my-docs
  ```

---

## Examples

### Example 1: Quick Project Overview
```bash
repo-explain analyze ./my-python-project --depth quick --verbose
```

Output shows:
- Project language(s)
- Structure overview
- Main entry points
- Key dependencies

### Example 2: Full Analysis with Custom Output
```bash
repo-explain analyze /path/to/repo \
  --depth standard \
  --output ./project-documentation \
  --verbose
```

Generates in `project-documentation/`:
- `architecture.md` - Complete architecture
- `components.mermaid` - Component relationships
- `dataflow.mermaid` - Data flow
- `tech-stack.txt` - Technology summary

### Example 3: Using Environment Variables
```bash
export REPO_EXPLAINER_OUTPUT_DIR=./docs
export REPO_EXPLAINER_VERBOSE=true

repo-explain analyze . --depth standard
```

---

## Future API Changes

The following features are planned for future stages:

- **Stage 2**: Pattern detection, dependency mapping, richer diagrams
- **Stage 3**: Incremental analysis, caching, parallel execution
- **Stage 4**: Multi-repository analysis
- **Stage 5**: Interactive HTML output, IDE integrations, multiple LLM providers

See `stages/` directory for detailed roadmap.

---

## Contributing

When making changes to the API:
1. Update this file immediately
2. Update `.claude.md` if guidelines change
3. Update `stages/stage_1.md` checklist
4. Test changes before committing
5. Commit with clear message describing API changes
