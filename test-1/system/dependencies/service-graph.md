# Service Dependency Graph

## Layered Architecture

This diagram shows all services organized by layer with color-coded styling.

**Diagram:** [View Diagram](../diagrams/src/layered-architecture.mermaid)

## Dependency Analysis

### Upstream Dependencies (What depends on this service)

| Service | Depended On By | Count |
|---------|----------------|-------|
| front-end | - | 0 |
| orders | front-end | 1 |
| payment | orders | 1 |


### Downstream Dependencies (What this service depends on)

| Service | Depends On | Count |
|---------|------------|-------|
| front-end | orders | 1 |
| orders | payment | 1 |
| payment | - | 0 |
