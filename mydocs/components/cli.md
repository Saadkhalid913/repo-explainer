# CLI Module

**Type**: `module`  
**ID**: `cli`  
**Location**: `src/repo_explainer/cli.py:1-789`  

## Overview

Handles user commands, incremental updates, and HTML documentation generation.

## Key Functions

### `analyze`

**Location**: `src/repo_explainer/cli.py:45-365`  
**Signature**:  
```
def analyze(repo_path_or_url, depth, output, force_clone, generate_html, html_port, no_browser, verbose)
```

Main command for repository analysis and doc generation.

### `update`

**Location**: `src/repo_explainer/cli.py:368-610`  
**Signature**:  
```
def update(repo_path, commits, since, auto, branch, output, generate_html, verbose)
```

Incremental update command for existing documentation based on git history.

### `generate_html`

**Location**: `src/repo_explainer/cli.py:657-785`  
**Signature**:  
```
def generate_html(docs_path, output, port, no_serve, no_browser)
```

Generates HTML from markdown and starts a local server.

## Dependencies

### Internal Dependencies

This component depends on:

- [`Repository Loader`](repository-loader.md) (`repository-loader`)
- [`OpenCode Service`](opencode-service.md) (`opencode-service`)
- [`Output Manager`](output-manager.md) (`output-manager`)
- [`HTML Generator`](html-generator.md) (`html-generator`)
- `config`

### External Dependencies

- `typer`
- `rich`

## Used By

_No components currently depend on this component._

---

_Generated from component analysis_
