# Communication Patterns

## Overview

**Diagram:** [View Diagram](../diagrams/src/communication-types.mermaid)

## Statistics

| Pattern | Count | Percentage |
|---------|-------|------------|
| HTTP/REST (Sync) | 2 | 67% |
| Events (Async) | 1 | 33% |
| **Total** | **3** | **100%** |

## Synchronous Communication (HTTP/REST)

| Source | Target | Details |
|--------|--------|--------|
| api-gateway | account-service | GET /accounts |
| api-gateway | transaction-processor | POST /transactions |


## Asynchronous Communication (Events)

**Diagram:** [View Diagram](../diagrams/src/event-flow.mermaid)

### Publishers

- **transaction-processor**: transaction.completed, transaction.failed

### Subscribers

- **notification-service**: transaction.completed

