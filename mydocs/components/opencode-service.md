# OpenCode Service

**Type**: `module`  
**ID**: `opencode-service`  
**Location**: `src/repo_explainer/opencode_service.py:1-282`  

## Overview

Manages communication with OpenCode CLI and provides incremental analysis capabilities.

## Key Functions

### `analyze_changes`

**Location**: `src/repo_explainer/opencode_service.py:231-268`  
**Signature**:  
```
def analyze_changes(self, changed_files, existing_docs_path, event_callback)
```

Runs incremental analysis on a subset of files.

### `analyze_architecture`

**Location**: `src/repo_explainer/opencode_service.py:151-168`  
**Signature**:  
```
def analyze_architecture(self, event_callback)
```

Runs comprehensive architecture analysis.

## Dependencies

### Internal Dependencies

This component depends on:

- `config`
- `prompts`

## Used By

This component is used by:

- [`CLI Module`](cli.md)
- [`Document Composer`](doc-composer.md)

---

_Generated from component analysis_
