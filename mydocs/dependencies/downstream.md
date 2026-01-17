# Downstream Dependencies

This document lists what each component **depends on** (its downstream dependencies).

## [CLI Module](../components/cli.md)

**Location**: `src/repo_explainer/cli.py`

### Internal Dependencies

- [`Repository Loader`](../components/repository-loader.md) - `src/repo_explainer/repository_loader.py`
- [`OpenCode Service`](../components/opencode-service.md) - `src/repo_explainer/opencode_service.py`
- [`Output Manager`](../components/output-manager.md) - `src/repo_explainer/output_manager.py`
- [`HTML Generator`](../components/html-generator.md) - `src/repo_explainer/html_generator.py`
- `config`

### External Dependencies

- `typer`
- `rich`

---

## [Orchestrator](../components/orchestrator.md)

**Location**: `src/repo_explainer/orchestrator.py`

### Internal Dependencies

- [`Repository Loader`](../components/repository-loader.md) - `src/repo_explainer/repository_loader.py`
- `code-analyzer`
- [`OpenCode Runner`](../components/opencode-runner.md) - `src/repo_explainer/opencode_runner.py`
- `doc-generator`
- [`Output Manager`](../components/output-manager.md) - `src/repo_explainer/output_manager.py`

### External Dependencies

- `rich`

---

## [OpenCode Runner](../components/opencode-runner.md)

**Location**: `src/repo_explainer/opencode_runner.py`

### Internal Dependencies

- `config`
- `models`

### External Dependencies

- `subprocess`
- `rich`

---

## [Repository Loader](../components/repository-loader.md)

**Location**: `src/repo_explainer/repository_loader.py`

### External Dependencies

- `GitPython`

---

## [OpenCode Service](../components/opencode-service.md)

**Location**: `src/repo_explainer/opencode_service.py`

### Internal Dependencies

- `config`
- `prompts`

---

## [Output Manager](../components/output-manager.md)

**Location**: `src/repo_explainer/output_manager.py`

### Internal Dependencies

- [`Document Composer`](../components/doc-composer.md) - `src/repo_explainer/doc_composer.py`

---

## [Document Composer](../components/doc-composer.md)

**Location**: `src/repo_explainer/doc_composer.py`

### Internal Dependencies

- [`OpenCode Service`](../components/opencode-service.md) - `src/repo_explainer/opencode_service.py`

### External Dependencies

- `mermaid-cli`

---

## [HTML Generator](../components/html-generator.md)

**Location**: `src/repo_explainer/html_generator.py`

### External Dependencies

- `markdown`
- `rich`

---

