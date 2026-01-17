# Repository Explainer - API Documentation

**Version:** 0.1.0
**Stage:** 1 - MVP Essentials
**Last Updated:** 2025-01-17 - Git URL support added

## Changes

### v0.1.0 - Git URL Support
- **NEW**: Added Git URL support - analyze remote repositories without cloning manually
- **NEW**: Repositories are automatically cloned to `./tmp/owner/repo`
- **NEW**: `--force-clone` flag to re-clone existing repositories
- **NEW**: `RepositoryLoader` service handles both local paths and Git URLs
- Fixed OpenCode CLI command syntax to use `opencode run <prompt>`
- CLI successfully invokes OpenCode and receives JSON output

## Overview

Repository Explainer is a CLI tool that analyzes repositories and generates AI-powered documentation using OpenCode. It supports both **local repositories** and **remote Git URLs** with automatic cloning.

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

Analyze a repository and generate documentation, architecture diagrams, and technology stack information.

Accepts either a **local path** or a **Git URL**. Git URLs are automatically cloned to `./tmp/owner/repo`.

**Usage:**
```bash
repo-explain analyze [REPO_PATH_OR_URL] [OPTIONS]
```

**Arguments:**
- `REPO_PATH_OR_URL` (optional): Local path or Git URL to analyze (default: current directory `.`)
  - **Local path**: Relative or absolute path to existing directory
  - **Git URL**: HTTPS, SSH, or Git protocol URL
    - HTTPS: `https://github.com/user/repo`
    - SSH: `git@github.com:user/repo.git`
    - Git: `git://example.com/repo.git`
  - Git URLs are cloned to `./tmp/owner/repo`

**Options:**
- `--depth, -d <TEXT>`: Analysis depth mode (default: `standard`)
  - `quick`: Fast scan - basic project structure and dependencies
  - `standard`: Full architecture analysis with diagrams
  - `deep`: Deep analysis including patterns and optimization suggestions

- `--output, -o <PATH>`: Output directory for generated documentation
  - If not specified, uses configured output directory (default: `docs/`)

- `--force-clone`: Force re-clone if repository already exists in tmp
  - Only applicable when using Git URLs
  - Removes existing clone and re-clones from remote
  - Useful to get latest changes from remote repository

- `--verbose, -V`: Enable verbose output
  - Shows OpenCode session IDs
  - Displays command execution details
  - Prints full API responses
  - Shows clone status for Git URLs

- `--help`: Show command help

**Returns:**
Generated files in the output directory (default: `./docs/`):

**Core Files:**
- `ANALYSIS_SUMMARY.md` - Quick overview of the analysis
- `analysis_{depth}.json` - Structured JSON output (parsed OpenCode events)

**Logs Directory:**
- `logs/analysis_{timestamp}.txt` - Raw OpenCode output
- `logs/metadata_{timestamp}.json` - Analysis metadata (session ID, timestamp, etc.)

**Future (Coming Soon):**
- `architecture.md` - Architecture overview
- `components.mermaid` - Component diagram
- `dataflow.mermaid` - Data flow diagram
- `tech-stack.txt` - Technology stack summary

**Examples:**

**Local Repositories:**
```bash
# Analyze current directory (standard depth)
repo-explain analyze

# Analyze specific local repo with verbose output
repo-explain analyze /path/to/repo --verbose

# Quick scan, custom output directory
repo-explain analyze ./my-project --depth quick --output ./project-docs
```

**Git URLs:**
```bash
# Analyze remote GitHub repository
repo-explain analyze https://github.com/torvalds/linux --depth quick

# Analyze with SSH URL
repo-explain analyze git@github.com:user/repo.git

# Force re-clone to get latest changes
repo-explain analyze https://github.com/user/repo --force-clone

# Deep analysis of remote repo with verbose output
repo-explain analyze https://github.com/facebook/react --depth deep --verbose
```

**Clone Location:**
```bash
# Git URLs are cloned to ./tmp/owner/repo
repo-explain analyze https://github.com/octocat/Hello-World
# Clones to: ./tmp/octocat/Hello-World

# Subsequent runs reuse the existing clone
repo-explain analyze https://github.com/octocat/Hello-World
# Output: "Using existing clone: tmp/octocat/Hello-World"

# Force re-clone
repo-explain analyze https://github.com/octocat/Hello-World --force-clone
# Output: "Removing existing clone" then "Cloning repository"
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

### RepositoryLoader

Service for loading repositories from local paths or Git URLs.

**Location:** `src/repo_explainer/repository_loader.py`

**Class:** `RepositoryLoader`

#### Constructor

```python
RepositoryLoader(tmp_dir: Path = Path("./tmp"))
```

**Parameters:**
- `tmp_dir` (Path, optional): Directory to store cloned repositories (default: `./tmp`)

**Example:**
```python
from pathlib import Path
from repo_explainer.repository_loader import RepositoryLoader

loader = RepositoryLoader(tmp_dir=Path("./my-tmp"))
```

#### Methods

##### `load(path_or_url: str, force_clone: bool = False) -> Path`

Load a repository from a local path or Git URL. This is the main method you'll use.

**Parameters:**
- `path_or_url` (str): Local path or Git URL
- `force_clone` (bool): If True, remove and re-clone existing repositories

**Returns:** Path to the repository (either the input path or cloned path)

**Example:**
```python
loader = RepositoryLoader()

# Load local path
local_path = loader.load("./my-project")
# Returns: Path('./my-project')

# Load Git URL (clones to ./tmp/user/repo)
remote_path = loader.load("https://github.com/user/repo")
# Returns: Path('./tmp/user/repo')

# Force re-clone
fresh_clone = loader.load("https://github.com/user/repo", force_clone=True)
```

##### `is_git_url(path_or_url: str) -> bool` (static)

Check if a string is a Git URL.

**Parameters:**
- `path_or_url` (str): String to check

**Returns:** True if it's a Git URL, False otherwise

**Example:**
```python
RepositoryLoader.is_git_url("https://github.com/user/repo")  # True
RepositoryLoader.is_git_url("git@github.com:user/repo.git")  # True
RepositoryLoader.is_git_url("./local/path")  # False
```

##### `parse_git_url(git_url: str) -> Tuple[str, str]` (static)

Parse a Git URL to extract owner and repository name.

**Parameters:**
- `git_url` (str): Git URL to parse

**Returns:** Tuple of (owner, repo_name)

**Example:**
```python
owner, repo = RepositoryLoader.parse_git_url("https://github.com/torvalds/linux")
# owner = "torvalds", repo = "linux"

owner, repo = RepositoryLoader.parse_git_url("git@github.com:user/repo.git")
# owner = "user", repo = "repo"
```

##### `get_clone_path(git_url: str) -> Path`

Get the local path where a Git URL will be cloned.

**Parameters:**
- `git_url` (str): Git URL

**Returns:** Path where the repository will be cloned

**Example:**
```python
loader = RepositoryLoader()
path = loader.get_clone_path("https://github.com/torvalds/linux")
# Returns: Path('./tmp/torvalds/linux')
```

##### `clone_repository(git_url: str, force: bool = False) -> Path`

Clone a Git repository to the tmp directory.

**Parameters:**
- `git_url` (str): Git URL to clone
- `force` (bool): If True, remove existing directory and re-clone

**Returns:** Path to the cloned repository

**Example:**
```python
loader = RepositoryLoader()

# Clone repository
path = loader.clone_repository("https://github.com/octocat/Hello-World")
# Clones to: ./tmp/octocat/Hello-World

# Re-clone
path = loader.clone_repository("https://github.com/octocat/Hello-World", force=True)
```

##### `cleanup(owner: str | None = None, repo: str | None = None) -> None`

Clean up cloned repositories.

**Parameters:**
- `owner` (str, optional): If provided, only clean this owner's repos
- `repo` (str, optional): If provided (with owner), only clean this specific repo

**Example:**
```python
loader = RepositoryLoader()

# Clean specific repo
loader.cleanup(owner="torvalds", repo="linux")

# Clean all repos for owner
loader.cleanup(owner="torvalds")

# Clean entire tmp directory
loader.cleanup()
```

---

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
- [ ] Git URLs are cloned to ./tmp/owner/repo
- [ ] Existing clones are reused
- [ ] `--force-clone` re-clones repositories

#### 7. Test Git URL Support

**Test with a small public repository:**
```bash
# Clone and analyze
repo-explain analyze https://github.com/octocat/Hello-World --depth quick

# Verify clone location
ls -la tmp/octocat/Hello-World/

# Test reuse of existing clone
repo-explain analyze https://github.com/octocat/Hello-World --depth quick
# Should output: "Using existing clone: tmp/octocat/Hello-World"

# Test force re-clone
repo-explain analyze https://github.com/octocat/Hello-World --force-clone --depth quick
# Should output: "Removing existing clone" then "Cloning repository"
```

**Expected Output (first run):**
```
Cloning repository: https://github.com/octocat/Hello-World
Destination: tmp/octocat/Hello-World
Clone successful!
╭────────────────────────────────────╮
│ Repository Explainer v0.1.0        │
│ Analyzing: tmp/octocat/Hello-World │
╰────────────────────────────────────╯
⠇ OpenCode available

Running quick analysis...
...
Analysis complete!
```

**Expected Output (subsequent runs):**
```
Using existing clone: tmp/octocat/Hello-World
╭────────────────────────────────────╮
│ Repository Explainer v0.1.0        │
│ Analyzing: tmp/octocat/Hello-World │
╰────────────────────────────────────╯
...
```

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

#### Git Clone Failures

**Error Message:**
```
Error loading repository: Failed to clone repository: ...
```

**Common Causes & Solutions:**

1. **Invalid Git URL:**
   - Check URL format is correct
   - Supported formats: `https://`, `git@`, `ssh://`, `git://`

2. **Authentication Required:**
   - For private repos, ensure SSH keys are set up
   - Or use HTTPS with credentials
   - Git credentials must be configured on your system

3. **Network Issues:**
   - Check internet connection
   - Try cloning manually: `git clone <url>`
   - Some firewalls may block git:// protocol

4. **Disk Space:**
   - Ensure sufficient disk space in ./tmp directory
   - Large repos may need significant space

**Clean up clones:**
```bash
# Remove specific repo
rm -rf tmp/owner/repo

# Remove all clones
rm -rf tmp/
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

### Example 4: Analyzing Remote GitHub Repository
```bash
# Quick scan of a popular open-source project
repo-explain analyze https://github.com/facebook/react --depth quick
```

**What happens:**
1. Repository is cloned to `./tmp/facebook/react`
2. Quick analysis runs on the cloned repository
3. Results are displayed in terminal
4. Clone is preserved for future runs

### Example 5: Force Re-clone for Latest Changes
```bash
# Get latest changes and re-analyze
repo-explain analyze https://github.com/torvalds/linux \
  --force-clone \
  --depth standard \
  --verbose
```

**When to use:**
- Repository has been updated remotely
- You want to ensure you're analyzing the latest code
- Previous clone may be corrupted

### Example 6: Analyzing Multiple Repositories
```bash
# Analyze several repos in sequence
for repo in \
  "https://github.com/user/repo1" \
  "https://github.com/user/repo2" \
  "https://github.com/user/repo3"; do
  repo-explain analyze "$repo" --depth quick
done
```

**Result:**
```
./tmp/
├── user/
│   ├── repo1/  # Cloned and analyzed
│   ├── repo2/  # Cloned and analyzed
│   └── repo3/  # Cloned and analyzed
```

### Example 7: Using SSH URLs (Private Repos)
```bash
# Analyze private repository with SSH
repo-explain analyze git@github.com:myorg/private-repo.git \
  --depth standard

# Prerequisites:
# - SSH key added to GitHub
# - ssh-agent running with key loaded
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
