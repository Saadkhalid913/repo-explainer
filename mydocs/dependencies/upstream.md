# Upstream Dependencies

This document lists what **depends on** each component (its upstream dependents).

## [CLI Module](../components/cli.md)

**Location**: `src/repo_explainer/cli.py`

_No components depend on this component_

---

## [Orchestrator](../components/orchestrator.md)

**Location**: `src/repo_explainer/orchestrator.py`

_No components depend on this component_

---

## [OpenCode Runner](../components/opencode-runner.md)

**Location**: `src/repo_explainer/opencode_runner.py`

### Used By

- [`Orchestrator`](../components/orchestrator.md) - `src/repo_explainer/orchestrator.py`

---

## [Repository Loader](../components/repository-loader.md)

**Location**: `src/repo_explainer/repository_loader.py`

### Used By

- [`CLI Module`](../components/cli.md) - `src/repo_explainer/cli.py`
- [`Orchestrator`](../components/orchestrator.md) - `src/repo_explainer/orchestrator.py`

---

## [OpenCode Service](../components/opencode-service.md)

**Location**: `src/repo_explainer/opencode_service.py`

### Used By

- [`CLI Module`](../components/cli.md) - `src/repo_explainer/cli.py`
- [`Document Composer`](../components/doc-composer.md) - `src/repo_explainer/doc_composer.py`

---

## [Output Manager](../components/output-manager.md)

**Location**: `src/repo_explainer/output_manager.py`

### Used By

- [`CLI Module`](../components/cli.md) - `src/repo_explainer/cli.py`
- [`Orchestrator`](../components/orchestrator.md) - `src/repo_explainer/orchestrator.py`

---

## [Document Composer](../components/doc-composer.md)

**Location**: `src/repo_explainer/doc_composer.py`

### Used By

- [`Output Manager`](../components/output-manager.md) - `src/repo_explainer/output_manager.py`

---

## [HTML Generator](../components/html-generator.md)

**Location**: `src/repo_explainer/html_generator.py`

### Used By

- [`CLI Module`](../components/cli.md) - `src/repo_explainer/cli.py`

---

## [Team Playbook](../components/team-playbook.md)

**Location**: `TeamPlayBook.MD`

_No components depend on this component_

---

