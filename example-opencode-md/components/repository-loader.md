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

### `clone_repository`

**Location**: `src/repo_explainer/repository_loader.py:120-162`  
**Signature**:  
```
def clone_repository(self, git_url: str, force: bool = False) -> Path
```

Clones a Git repository to the tmp directory.

### `is_git_url`

**Location**: `src/repo_explainer/repository_loader.py:28-54`  
**Signature**:  
```
def is_git_url(path_or_url: str) -> bool
```

Detects if a string is a Git URL.

## Dependencies

### External Dependencies

- `GitPython`

## Used By

This component is used by:

- [`CLI Entry Point`](cli.md)

---

_Generated from component analysis_
