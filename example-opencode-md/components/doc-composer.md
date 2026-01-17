# Document Composer

**Type**: `module`  
**ID**: `doc-composer`  
**Location**: `src/repo_explainer/doc_composer.py:1-1191`  

## Overview

Composes coherent documentation from raw analysis artifacts, handles diagram rendering and subpage generation.

## Key Functions

### `compose`

**Location**: `src/repo_explainer/doc_composer.py:32-101`  
**Signature**:  
```
def compose(self, repo_path, depth, session_id, timestamp)
```

Orchestrates the conversion of raw artifacts to structured documentation.

### `_render_diagrams`

**Location**: `src/repo_explainer/doc_composer.py:103-194`  
**Signature**:  
```
def _render_diagrams(self)
```

Renders Mermaid diagrams to SVG using mermaid-cli.

## Dependencies

## Used By

This component is used by:

- [`Output Manager`](output-manager.md)

---

_Generated from component analysis_
