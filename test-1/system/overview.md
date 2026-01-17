# System Architecture Overview

**Total Services:** 3
**Analysis Date:** 2026-01-17

## Architecture Diagram

This diagram shows all services organized by architectural layer with their dependencies.

**Diagram:** [View Layered Architecture](diagrams/src/layered-architecture.mermaid)

## System Metrics

| Metric | Value |
|--------|-------|
| Services | 3 |
| Inter-Service Connections | 2 |
| HTTP/REST Calls | 2 |
| Event-Driven Flows | 0 |

## Services

### front-end

- **Language:** Unknown
- **Repository:** `https://example.com/fe`
- **Documentation:** [View Details](../services/front-end/overview.md)

### orders

- **Language:** Unknown
- **Repository:** `https://example.com/orders`
- **Documentation:** [View Details](../services/orders/overview.md)

### payment

- **Language:** Unknown
- **Repository:** `https://example.com/payment`
- **Documentation:** [View Details](../services/payment/overview.md)

## Quick Links

- [Component Architecture](components/overview.md) - Services as system components
- [Data Flow](dataflow/overview.md) - How data moves through the system
- [API Documentation](api/overview.md) - API endpoints and flows
- [Dependencies](dependencies/overview.md) - Service dependency graph
- [Communication Patterns](communication/overview.md) - Sync vs async patterns

