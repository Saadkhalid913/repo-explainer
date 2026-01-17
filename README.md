# Repository Explainer

AI-powered repository documentation generator using OpenCode.

## Installation

```bash
pip install -e .
```

## Usage

```bash
# Analyze a repository
repo-explain analyze /path/to/repo

# Quick scan
repo-explain analyze /path/to/repo --depth quick

# With verbose output
repo-explain analyze /path/to/repo --verbose
```

## Configuration

Environment variables:
- `REPO_EXPLAINER_OPENCODE_BINARY`: Path to OpenCode binary (default: `opencode`)
- `REPO_EXPLAINER_VERBOSE`: Enable verbose output (default: `false`)
