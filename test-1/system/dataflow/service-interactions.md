# Service Interactions

## Interaction Sequence

This diagram shows the sequence of interactions between services.

**Diagram:** [View Diagram](../diagrams/src/service-interaction.mermaid)

## Interaction Details

| Source | Target | Type | Details |
|--------|--------|------|--------|
| api-gateway | account-service | http | GET /accounts |
| api-gateway | transaction-processor | http | POST /transactions |
| transaction-processor | notification-service | event | transaction.completed |
