Document the system architecture, focusing on services, data flow, and key integrations.

## Objectives

1. **Map Services & Boundaries**
   - Identify microservices, daemons, CLI entry points, and APIs.
   - Capture ownership or module-level boundaries (folders/packages).
   - Note runtime constraints (language, framework, runtime flags).

2. **Trace Data Flow**
   - Highlight how information moves between services, queues, and storage.
   - Identify protocols (HTTP, gRPC, events) and serialization formats.
   - Flag shared data models or message contracts.

3. **Surface Integration Points**
   - External dependencies (cloud services, third-party APIs).
   - Internal integration points (libraries, shared tooling, config).
   - Deployment artifacts or infra requirements (k8s, serverless, cron).

## Output

Create an `architecture_summary.md` that covers each layer, includes diagrams (Mermaid or ASCII), and lists assumptions for unknown boundaries.
