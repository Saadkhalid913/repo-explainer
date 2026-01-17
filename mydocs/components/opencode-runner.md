# OpenCode Runner

**Type**: `module`  
**ID**: `opencode-runner`  
**Location**: `src/repo_explainer/opencode_runner.py:1-374`  

## Overview

Handles execution of OpenCode CLI commands and provides fallback to Claude CLI.

## Key Functions

### `run_analysis`

**Location**: `src/repo_explainer/opencode_runner.py:75-148`  
**Signature**:  
```
def run_analysis(self, repo_path, depth, output_dir, context)
```

Runs OpenCode analysis with automatic prompt building.

## Dependencies

### Internal Dependencies

This component depends on:

- `config`
- `models`

### External Dependencies

- `subprocess`
- `rich`

## Used By

This component is used by:

- [`Orchestrator`](orchestrator.md)

---

_Generated from component analysis_
