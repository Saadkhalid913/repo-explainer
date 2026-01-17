# System Components

## Architecture Overview

This diagram shows all services within the system boundary, their technologies, and how they communicate.

**Diagram:** [View Diagram](../diagrams/src/c4-context.mermaid)

## Components by Layer

### Presentation Layer

- **front-end** (Unknown) - Customer-facing interface

### Business Logic Layer

- **orders** (Unknown) - Core business operations

### Integration Layer

- **payment** (Unknown) - External integrations


## Component Interaction Matrix

| Component | Depends On | Used By | Layer |
|-----------|------------|---------|-------|
| front-end | orders | - | Presentation |
| orders | payment | front-end | Business |
| payment | - | orders | Integration |
