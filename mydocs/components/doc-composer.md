# Document Composer

**Type**: `module`  
**ID**: `doc-composer`  
**Location**: `src/repo_explainer/doc_composer.py:1-1246`  

## Overview

Composes comprehensive documentation, renders diagrams, and performs AI-assisted Mermaid syntax fixes.

## Key Functions

### `compose`

**Location**: `src/repo_explainer/doc_composer.py:32-101`  
**Signature**:  
```
def compose(self, repo_path, depth, session_id, timestamp)
```

Orchestrates the conversion of raw artifacts to structured documentation.

### `_fix_mermaid_syntax`

**Location**: `src/repo_explainer/doc_composer.py:251-315`  
**Signature**:  
```
def _fix_mermaid_syntax(self, mermaid_file, error_msg)
```

Attempts to fix Mermaid syntax errors using OpenCode.

## Dependencies

### Internal Dependencies

This component depends on:

- [`OpenCode Service`](opencode-service.md) (`opencode-service`)

### External Dependencies

- `mermaid-cli`

## Used By

This component is used by:

- [`Output Manager`](output-manager.md)

---

_Generated from component analysis_
