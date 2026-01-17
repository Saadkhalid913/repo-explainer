# Component Relationships

## Interaction Diagram

This diagram shows services organized by architectural layer (Presentation, Business, Integration, Infrastructure) with their dependencies.

**Diagram:** [View Diagram](../diagrams/src/layered-architecture.mermaid)

## Communication Patterns

### Synchronous (HTTP/REST)

- **front-end** → **orders**: /orders
- **orders** → **payment**: /payment

