# Orchestrator

**Type**: `module`  
**ID**: `orchestrator`  
**Location**: `src/repo_explainer/orchestrator.py:1-424`  

## Overview

Coordinates the analysis pipeline: loader, analyzer, AI runner, and document generation.

## Key Functions

### `run`

**Location**: `src/repo_explainer/orchestrator.py:89-146`  
**Signature**:  
```
def run(self) -> AnalysisResult
```

Executes the full analysis pipeline sequentially.

## Dependencies

### Internal Dependencies

This component depends on:

- [`Repository Loader`](repository-loader.md) (`repository-loader`)
- `code-analyzer`
- [`OpenCode Runner`](opencode-runner.md) (`opencode-runner`)
- `doc-generator`
- [`Output Manager`](output-manager.md) (`output-manager`)

### External Dependencies

- `rich`

## Used By

_No components currently depend on this component._

---

_Generated from component analysis_
