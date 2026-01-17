# OpenCode Integration Service

**Type**: `module`  
**ID**: `opencode-service`  
**Location**: `src/repo_explainer/opencode_service.py:1-242`  

## Overview

Manages communication with the OpenCode CLI, handles streaming output, and parses JSON events.

## Key Functions

### `run_command`

**Location**: `src/repo_explainer/opencode_service.py:56-148`  
**Signature**:  
```
def run_command(self, prompt, command, event_callback)
```

Executes OpenCode CLI commands and monitors output.

### `analyze_architecture`

**Location**: `src/repo_explainer/opencode_service.py:150-167`  
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

- [`CLI Entry Point`](cli.md)

---

_Generated from component analysis_
