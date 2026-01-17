# CLI Component

**Type**: `module`  
**ID**: `cli-component`  
**Location**: `src/repo_explainer/cli.py:1-321`  

## Overview

The primary interface for users to interact with the repository explainer tool.

## Key Functions

### `analyze`

**Location**: `src/repo_explainer/cli.py:44-284`  
**Signature**:  
```
def analyze(repo_path_or_url: str, depth: str, output: Optional[Path], force_clone: bool, verbose: bool) -> None
```

Orchestrates the full analysis pipeline from loading to documentation generation.

### `update`

**Location**: `src/repo_explainer/cli.py:287-317`  
**Signature**:  
```
def update(repo_path: Path, verbose: bool) -> None
```

Planned command for incremental documentation updates.

### `main`

**Location**: `src/repo_explainer/cli.py:33-40`  
**Signature**:  
```
def main(version: Optional[bool]) -> None
```

Global CLI entry point and callback for options.

## Dependencies

### Internal Dependencies

This component depends on:

- [`OpenCode Service`](opencode-service.md) (`opencode-service`)
- `output-manager`
- [`Repository Loader`](repository-loader.md) (`repository-loader`)
- `config-component`

### External Dependencies

- `typer`
- `rich`

## Interfaces

### CLI

**Type**: Command Line  

**Endpoints**:

- `analyze`
- `update`

## Used By

_No components currently depend on this component._

---

_Generated from component analysis_
