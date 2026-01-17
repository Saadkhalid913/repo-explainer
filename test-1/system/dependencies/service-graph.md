# Service Dependency Graph

## Layered Architecture

**Diagram:** [View Diagram](../diagrams/src/layered-architecture.mermaid)

## Dependency Analysis

### Upstream Dependencies (What depends on this service)

| Service | Depended On By | Count |
|---------|----------------|-------|
| api-gateway | - | 0 |
| account-service | api-gateway | 1 |
| transaction-processor | api-gateway | 1 |
| notification-service | transaction-processor | 1 |


### Downstream Dependencies (What this service depends on)

| Service | Depends On | Count |
|---------|------------|-------|
| api-gateway | account-service, transaction-processor | 2 |
| account-service | - | 0 |
| transaction-processor | notification-service | 1 |
| notification-service | - | 0 |
