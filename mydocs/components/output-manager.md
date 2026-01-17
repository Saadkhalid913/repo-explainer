# Output Manager

**Type**: `module`  
**ID**: `output-manager`  
**Location**: `src/repo_explainer/output_manager.py:1-268`  

## Overview

Handles writing analysis results and managing doc output structure.

## Key Functions

### `write_analysis_result`

**Location**: `src/repo_explainer/output_manager.py:51-127`  
**Signature**:  
```
def write_analysis_result(self, result, repo_path, depth)
```

Saves analysis output and orchestrates documentation composition.

## Dependencies

### Internal Dependencies

This component depends on:

- [`Document Composer`](doc-composer.md) (`doc-composer`)

## Used By

This component is used by:

- [`CLI Module`](cli.md)
- [`Orchestrator`](orchestrator.md)

---

_Generated from component analysis_
