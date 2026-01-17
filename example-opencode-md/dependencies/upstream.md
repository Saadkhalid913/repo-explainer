# Upstream Dependencies

This document lists what **depends on** each component (its upstream dependents).

## [CLI Entry Point](../components/cli.md)

**Location**: `src/repo_explainer/cli.py`

_No components depend on this component_

---

## [Repository Loader](../components/repository-loader.md)

**Location**: `src/repo_explainer/repository_loader.py`

### Used By

- [`CLI Entry Point`](../components/cli.md) - `src/repo_explainer/cli.py`

---

## [OpenCode Integration Service](../components/opencode-service.md)

**Location**: `src/repo_explainer/opencode_service.py`

### Used By

- [`CLI Entry Point`](../components/cli.md) - `src/repo_explainer/cli.py`

---

## [Document Composer](../components/doc-composer.md)

**Location**: `src/repo_explainer/doc_composer.py`

### Used By

- [`Output Manager`](../components/output-manager.md) - `src/repo_explainer/output_manager.py`

---

## [Output Manager](../components/output-manager.md)

**Location**: `src/repo_explainer/output_manager.py`

### Used By

- [`CLI Entry Point`](../components/cli.md) - `src/repo_explainer/cli.py`

---

