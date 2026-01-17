# Downstream Dependencies

This document lists what each component **depends on** (its downstream dependencies).

## [CLI Entry Point](../components/cli.md)

**Location**: `src/repo_explainer/cli.py`

### Internal Dependencies

- [`Repository Loader`](../components/repository-loader.md) - `src/repo_explainer/repository_loader.py`
- [`OpenCode Integration Service`](../components/opencode-service.md) - `src/repo_explainer/opencode_service.py`
- [`Output Manager`](../components/output-manager.md) - `src/repo_explainer/output_manager.py`
- `config`

### External Dependencies

- `typer`
- `rich`

---

## [Repository Loader](../components/repository-loader.md)

**Location**: `src/repo_explainer/repository_loader.py`

### External Dependencies

- `GitPython`

---

## [OpenCode Integration Service](../components/opencode-service.md)

**Location**: `src/repo_explainer/opencode_service.py`

### Internal Dependencies

- `config`
- `prompts`

---

## [Document Composer](../components/doc-composer.md)

**Location**: `src/repo_explainer/doc_composer.py`

_No dependencies_

---

## [Output Manager](../components/output-manager.md)

**Location**: `src/repo_explainer/output_manager.py`

### Internal Dependencies

- [`Document Composer`](../components/doc-composer.md) - `src/repo_explainer/doc_composer.py`

---

