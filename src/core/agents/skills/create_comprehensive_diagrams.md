Comprehensive diagram generation for all documentation types

## Diagram Types Required

### 1. Architecture Diagrams (Mermaid flowchart)

Show component in system context:
```mermaid
flowchart TB
    Client-->API[API Server]
    API-->Component[Your Component]
    Component-->DB[etcd]
```

### 2. Flow Diagrams (Mermaid flowchart)

Show request/response flow:
```mermaid
flowchart LR
    Request-->Validate
    Validate-->Process
    Process-->Store
    Store-->Response
```

### 3. Sequence Diagrams (Mermaid sequenceDiagram)

Show interactions over time:
```mermaid
sequenceDiagram
    Client->>Server: Request
    Server->>Service: Process
    Service->>Database: Query
    Database-->>Client: Response
```

### 4. Component Diagrams (Mermaid graph)

Show internal structure:
```mermaid
graph TD
    Main[Main Controller]-->A[Sub-controller A]
    Main-->B[Sub-controller B]
    A-->Cache
    B-->Cache
```

## Placement

- Save to: `docs/assets/{component}_{type}.mmd`
- Reference in markdown: `![Architecture](../assets/component_architecture.png)`
- Generate both .mmd source and .png compiled version

## ASCII Fallbacks

For simple relationships, use ASCII art:
```
    ┌─────────┐
    │ Client  │
    └────┬────┘
         │
    ┌────▼────┐
    │   API   │
    └────┬────┘
         │
    ┌────▼────┐
    │Component│
    └─────────┘
```

## Error Handling

- If mmdc compilation fails, keep .mmd source files
- Log warning but continue documentation
- Don't fail the entire pipeline over diagram compilation
- Document in section that diagrams may require manual compilation
