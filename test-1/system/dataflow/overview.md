# Data Flow Overview

## System Data Flow

This diagram shows how data flows through the system layers.

**Diagram:** [View Diagram](../diagrams/src/data-flow.mermaid)

## Data Flow Patterns

### From api-gateway

- **→ account-service** (http): GET /accounts
- **→ transaction-processor** (http): POST /transactions

### From transaction-processor

- **→ notification-service** (event): transaction.completed

