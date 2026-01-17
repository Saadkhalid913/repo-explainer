# System Components

## Architecture Overview

This diagram shows all services within the system boundary, their technologies, and how they communicate.

**Diagram:** [View Diagram](../diagrams/src/c4-context.mermaid)

## Components by Layer

### Presentation Layer

- **api-gateway** (Unknown)

### Business Logic Layer

- **account-service** (Unknown)
- **transaction-processor** (Unknown)

### Integration Layer

- **notification-service** (Unknown)


## Component Interaction Matrix

| Component | Depends On | Used By | Layer |
|-----------|------------|---------|-------|
| api-gateway | account-service, transaction-processor | - | Presentation |
| account-service | - | api-gateway | Business |
| transaction-processor | notification-service | api-gateway | Business |
| notification-service | - | transaction-processor | Integration |
