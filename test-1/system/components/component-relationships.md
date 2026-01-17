# Component Relationships

## Interaction Diagram

This diagram shows services organized by architectural layer with their dependencies.

**Diagram:** [View Diagram](../diagrams/src/layered-architecture.mermaid)

## Communication Patterns

### Synchronous (HTTP/REST)

- **api-gateway** → **account-service**: GET /accounts
- **api-gateway** → **transaction-processor**: POST /transactions

### Asynchronous (Events/Messages)

- **transaction-processor** → **notification-service**: transaction.completed

