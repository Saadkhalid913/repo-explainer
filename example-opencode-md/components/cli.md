# CLI Entry Point

**Type**: `module`  
**ID**: `cli`  
**Location**: `src/repo_explainer/cli.py:1-321`  

## Overview

Main entry point for the application, handling user commands and CLI formatting.

## Key Functions

### `analyze`

**Location**: `src/repo_explainer/cli.py:44-284`  
**Signature**:  
```
def analyze(repo_path_or_url, depth, output, force_clone, verbose)
```

Main command for repository analysis and doc generation.

### `main`

**Location**: `src/repo_explainer/cli.py:33-40`  
**Signature**:  
```
def main(version)
```

Typer callback for version and global options.

## Dependencies

### Internal Dependencies

This component depends on:

- [`Repository Loader`](repository-loader.md) (`repository-loader`)
- [`OpenCode Integration Service`](opencode-service.md) (`opencode-service`)
- [`Output Manager`](output-manager.md) (`output-manager`)
- `config`

### External Dependencies

- `typer`
- `rich`

## Interfaces

### CLI

**Type**: CLI  

**Endpoints**:

- `analyze`
- `update`

## Used By

_No components currently depend on this component._

---

_Generated from component analysis_
