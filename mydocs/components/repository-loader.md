# Repository Loader

**Type**: `module`  
**ID**: `repository-loader`  
**Location**: `src/repo_explainer/repository_loader.py:1-215`  

## Overview

Responsible for loading local repositories or cloning remote ones.

## Key Functions

### `load`

**Location**: `src/repo_explainer/repository_loader.py:163-189`  
**Signature**:  
```
def load(self, path_or_url: str, force_clone: bool = False) -> Path
```

Loads a repository from a local path or Git URL.

## Dependencies

### External Dependencies

- `GitPython`

## Used By

This component is used by:

- [`CLI Module`](cli.md)
- [`Orchestrator`](orchestrator.md)

---

_Generated from component analysis_
