# Data Flow Overview

## System Data Flow

This diagram shows how data flows from user input through the presentation layer, business processing, and backend services.

**Diagram:** [View Diagram](../diagrams/src/data-flow.mermaid)

## Data Flow Patterns

### From front-end

- **→ orders** (http): /orders

### From orders

- **→ payment** (http): /payment

