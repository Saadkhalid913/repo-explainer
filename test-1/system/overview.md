# System Architecture Overview

**Total Services:** 4
**Analysis Date:** 2026-01-17

## Architecture Diagram

**Diagram:** [View Layered Architecture](diagrams/src/layered-architecture.mermaid)

## System Metrics

| Metric | Value |
|--------|-------|
| Services | 4 |
| Inter-Service Connections | 3 |
| HTTP/REST Calls | 2 |
| Event-Driven Flows | 1 |

## Services

### api-gateway

- **Language:** Unknown
- **Repository:** `https://example.com/api`
- **Documentation:** [View Details](../services/api-gateway/overview.md)

### account-service

- **Language:** Unknown
- **Repository:** `https://example.com/account`
- **Documentation:** [View Details](../services/account-service/overview.md)

### transaction-processor

- **Language:** Unknown
- **Repository:** `https://example.com/tx`
- **Documentation:** [View Details](../services/transaction-processor/overview.md)

### notification-service

- **Language:** Unknown
- **Repository:** `https://example.com/notify`
- **Documentation:** [View Details](../services/notification-service/overview.md)

## Quick Links

- [Component Architecture](components/overview.md)
- [Data Flow](dataflow/overview.md)
- [API Documentation](api/overview.md)
- [Dependencies](dependencies/overview.md)
- [Communication Patterns](communication/overview.md)

