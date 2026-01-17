# Work Visualizations

## Master Project Timeline

```mermaid
gantt
    title Repository Explainer Development - 8 Week Timeline
    dateFormat  YYYY-MM-DD
    axisFormat  %b %d

    section Developer A (Core Infrastructure)
    Phase 1 Foundation          :crit, deva1, 2026-01-17, 14d
    Phase 2 Intelligence        :deva2, after deva1, 14d
    Phase 3 Scaling             :deva3, after deva2, 14d
    Phase 4 Integrations        :deva4, after deva3, 14d

    section Developer B (Analysis Engine)
    Phase 1 Foundation          :crit, devb1, 2026-01-17, 14d
    Phase 2 Intelligence        :devb2, after devb1, 14d
    Phase 3 Scaling             :devb3, after devb2, 14d
    Phase 4 Integrations        :devb4, after devb3, 14d

    section Milestones
    Foundation Complete         :milestone, m1, 2026-01-31, 0d
    Intelligence Complete       :milestone, m2, 2026-02-14, 0d
    Scaling Complete            :milestone, m3, 2026-02-28, 0d
    Integrations Complete       :milestone, m4, 2026-03-14, 0d
```

## Developer A Task Flow

```mermaid
flowchart LR
    subgraph Phase1["Phase 1: Foundation (Week 1-2)"]
        A1[A1.1: Setup & Structure<br/>4h]
        A2[A1.2: CLI Scaffolding<br/>6h]
        A3[A1.3: Config Mgmt<br/>8h]
        A4[A1.4: Repo Loader<br/>12h]
        A5[A1.5: Rich UI<br/>4h]
        A6[A1.6: Logging<br/>4h]
    end

    subgraph Sync1["Week 2 Sync Point"]
        S1[Foundation Complete<br/>File System Ready]
    end

    subgraph Phase2["Phase 2: Intelligence (Week 3-4)"]
        B1[A2.1: OpenRouter<br/>8h]
        B2[A2.2: Prompt Templates<br/>8h]
        B3[A2.3: Context Mgmt<br/>6h]
        B4[A2.4: Retry Logic<br/>4h]
        B5[A2.5: Cost Tracking<br/>6h]
        B6[A2.6: Progress Reporting<br/>6h]
    end

    subgraph Sync2["Week 4 Sync Point"]
        S2[Intelligence Complete<br/>End-to-End Analysis]
    end

    subgraph Phase3["Phase 3: Scaling (Week 5-6)"]
        C1[A3.1: Incremental Engine<br/>10h]
        C2[A3.2: Caching Layer<br/>8h]
        C3[A3.3: Cost Monitor<br/>4h]
        C4[A3.4: Retry Handler<br/>4h]
        C5[A3.5: Multi-repo Loader<br/>8h]
        C6[A3.6: Service Registry<br/>6h]
    end

    subgraph Sync3["Week 6 Sync Point"]
        S3[Scaling Complete<br/>Incremental Updates]
    end

    subgraph Phase4["Phase 4: Integrations (Week 7-8)"]
        D1[A4.1: Provider Registry<br/>8h]
        D2[A4.2: LLM Adapters<br/>6h]
        D3[A4.3: Static Export<br/>8h]
        D4[A4.4: Diagram Export<br/>4h]
        D5[A4.5: Telemetry<br/>6h]
        D6[A4.6: Integration Testing<br/>10h]
    end

    A1 --> A2 --> A3 --> A4
    A2 --> A5
    A3 --> A6
    A6 --> S1 --> B1 --> B3 --> B4
    B1 --> B2 --> B5 --> B6
    B6 --> S2 --> C1 --> C2 --> C3 --> C4
    C1 --> C5 --> C6
    C6 --> S3 --> D1 --> D2 --> D3 --> D4
    D3 --> D5 --> D6

    style Phase1 fill:#e3f2fd
    style Phase2 fill:#fff3e0
    style Phase3 fill:#e8f5e9
    style Phase4 fill:#f3e5f5
    style S1 fill:#fff59d
    style S2 fill:#fff59d
    style S3 fill:#fff59d
```

## Developer B Task Flow

```mermaid
flowchart LR
    subgraph Phase1["Phase 1: Foundation (Week 1-2)"]
        A1[B1.1: Tree-sitter Python<br/>10h]
        A2[B1.2: Tree-sitter JS/TS<br/>10h]
        A3[B1.3: File Scanner<br/>6h]
        A4[B1.4: Component ID<br/>10h]
        A5[B1.5: Arch Diagram<br/>10h]
        A6[B1.6: Markdown Writer<br/>8h]
    end

    subgraph Sync1["Week 2 Sync Point"]
        S1[Foundation Complete<br/>Parsing Ready]
    end

    subgraph Phase2["Phase 2: Intelligence (Week 3-4)"]
        B1[B2.1: Arch Patterns<br/>10h]
        B2[B2.2: Design Patterns<br/>10h]
        B3[B2.3: Dep Mapper<br/>8h]
        B4[B2.4: Dep Graph<br/>8h]
        B5[B2.5: Seq Diagram<br/>8h]
        B6[B2.6: ER Diagram<br/>6h]
        B7[B2.7: Call Graph<br/>8h]
    end

    subgraph Sync2["Week 4 Sync Point"]
        S2[Intelligence Complete<br/>All Diagrams Ready]
    end

    subgraph Phase3["Phase 3: Scaling (Week 5-6)"]
        C1[B3.1: Parallel Executor<br/>10h]
        C2[B3.2: Context Opt<br/>8h]
        C3[B3.3: Progressive Stream<br/>6h]
        C4[B3.4: Hierarchical<br/>8h]
        C5[B3.5: Cross-Service<br/>10h]
        C6[B3.6: System Diagram<br/>8h]
        C7[B3.7: Unified Builder<br/>10h]
    end

    subgraph Sync3["Week 6 Sync Point"]
        S3[Scaling Complete<br/>Performance Optimized]
    end

    subgraph Phase4["Phase 4: Integrations (Week 7-8)"]
        D1[B4.1: HTML Renderer<br/>10h]
        D2[B4.2: SSG Integration<br/>10h]
        D3[B4.3: VS Code Hooks<br/>8h]
        D4[B4.4: Diagram Export<br/>8h]
        D5[B4.5: ASCII Fallback<br/>6h]
        D6[B4.6: Cross-repo Links<br/>6h]
        D7[B4.7: Performance Opt<br/>10h]
    end

    A1 --> A2 --> A3 --> A4 --> A5 --> A6
    A6 --> S1 --> B1 --> B5
    B1 --> B2 --> B6
    B1 --> B3 --> B4
    B1 --> B7
    B7 --> S2 --> C1 --> C2 --> C3 --> C4
    B4 --> C5 --> C6 --> C7
    C7 --> S3 --> D1 --> D2 --> D3 --> D4 --> D5 --> D6 --> D7

    style Phase1 fill:#e3f2fd
    style Phase2 fill:#fff3e0
    style Phase3 fill:#e8f5e9
    style Phase4 fill:#f3e5f5
    style S1 fill:#fff59d
    style S2 fill:#fff59d
    style S3 fill:#fff59d
```

## Cross-Developer Dependency Graph

```mermaid
flowchart LR
    subgraph DevA["Developer A"]
        A1[A1.3: Config Management]
        A2[A1.4: Repository Loader]
        A3[A2.2: Prompt Templates]
        A4[A2.5: Cost Tracking]
        A5[A3.6: Service Registry]
        A6[A4.3: Static Export]
    end

    subgraph DevB["Developer B"]
        B1[B1.4: Component ID]
        B2[B2.1: Pattern Detection]
        B3[B3.1: Parallel Executor]
        B4[B3.6: System Diagram]
        B5[B3.7: Unified Builder]
        B6[B4.1: HTML Renderer]
    end

    A1 -.->|Needed for| B6[Markdown Writer]
    B1 -.->|Informs| A3
    A2 -.->|Required by| B7[Tree-sitter Python]
    A2 -.->|Required by| B8[Tree-sitter JS/TS]
    A3 -.->|Consumed by| B2
    A4 -.->|Monitored by| B3
    A5 -.->|Used by| B9[Cross-Service Mapper]
    A6 -.->|Consumes| B5
    B5 -.->|Extended by| A7[Diagram Export]

    style DevA fill:#bbdefb
    style DevB fill:#ffe0b2
    style A1 stroke:#1565c0,stroke-width:2px
    style A2 stroke:#1565c0,stroke-width:2px
    style A4 stroke:#1565c0,stroke-width:2px
```

## Critical Path Analysis

```mermaid
graph TD
    START([Project Start])

    subgraph P1["Phase 1: Foundation"]
        F1[Setup & Structure<br/>Shared]
        F2A[CLI & Config<br/>Dev A]
        F2B[Parsing & Components<br/>Dev B]
        F3A[Repo Loader<br/>Dev A]
        F3B[Tree-sitter Integration<br/>Dev B]
        MS1[Milestone 1<br/>Foundation]
    end

    subgraph P2["Phase 2: Intelligence"]
        I1A[OpenRouter Integration<br/>Dev A]
        I1B[Pattern Detection<br/>Dev B]
        I2A[Prompt Templates<br/>Dev A]
        I2B[Diagram Generators<br/>Dev B]
        MS2[Milestone 2<br/>Intelligence]
    end

    subgraph P3["Phase 3: Scaling"]
        S1A[Incremental Engine<br/>Dev A]
        S1B[Parallel Executor<br/>Dev B]
        S2A[Caching System<br/>Dev A]
        S2B[Progressive Streaming<br/>Dev B]
        MS3[Milestone 3<br/>Scaling]
    end

    subgraph P4["Phase 4: Integrations"]
        L1A[Multi-repo Support<br/>Dev A]
        L1B[Cross-Service Mapper<br/>Dev B]
        L2A[Provider Registry<br/>Dev A]
        L2B[HTML Export<br/>Dev B]
        MS4[Milestone 4<br/>Complete]
    end

    END([Project Complete])

    START --> F1
    F1 --> F2A & F2B
    F2A --> F3A
    F2B --> F3B
    F3A & F3B --> MS1 --> I1A & I1B
    I1A --> I2A
    I1B --> I2B
    I2A & I2B --> MS2 --> S1A & S1B
    S1A --> S2A
    S1B --> S2B
    S2A & S2B --> MS3 --> L1A & L1B
    L1A --> L2A
    L1B --> L2B
    L2A & L2B --> MS4 --> END

    style F1 fill:#c8e6c9
    style F2A fill:#e3f2fd
    style F2B fill:#fff9c4
    style I1A fill:#e3f2fd
    style I1B fill:#fff9c4
    style S1A fill:#e3f2fd
    style S1B fill:#fff9c4
    style L1A fill:#e3f2fd
    style L1B fill:#fff9c4
    style MS1 fill:#fff59d,stroke:#f57f17,stroke-width:2px
    style MS2 fill:#fff59d,stroke:#f57f17,stroke-width:2px
    style MS3 fill:#fff59d,stroke:#f57f17,stroke-width:2px
    style MS4 fill:#81c784,stroke:#2e7d32,stroke-width:2px
```

## Risk Matrix

```mermaid
graph LR
    subgraph HIGH_RISK["High Risk Dependencies"]
        H1[A1.4: Repo Loader<br/>→ B1.1, B1.2]
        H2[A2.2: Prompt Templates<br/>→ B2.1, B2.2]
        H3[B1.4: Component ID<br/>→ A2.2]
    end

    subgraph MEDIUM_RISK["Medium Risk Dependencies"]
        M1[A2.5: Cost Tracking<br/>→ B3.1]
        M2[A3.6: Service Registry<br/>→ B3.5]
        M3[B2.4: Dep Graph<br/>→ B3.1]
    end

    subgraph LOW_RISK["Low Risk"]
        L1[A1.5: Rich UI]
        L2[B2.7: Call Graph]
        L3[A4.5: Telemetry]
    end

    style HIGH_RISK fill:#ffcdd2
    style MEDIUM_RISK fill:#ffe0b2
    style LOW_RISK fill:#c8e6c9
    style H1 stroke:#c62828,stroke-width:2px
    style H2 stroke:#c62828,stroke-width:2px
    style H3 stroke:#c62828,stroke-width:2px
```

## Work Distribution Summary

```mermaid
pie title Effort Distribution by Developer
    "Developer A (Core Infrastructure)" : 158
    "Developer B (Analysis Engine)" : 228
```

```mermaid
pie title Effort Distribution by Phase
    "Phase 1: Foundation" : 90
    "Phase 2: Intelligence" : 96
    "Phase 3: Scaling" : 100
    "Phase 4: Integrations" : 100
```

## Weekly Velocity Targets

```mermaid
gantt
    title Weekly Velocity Targets (Hours per Developer)
    dateFormat  YYYY-MM-DD
    axisFormat  Week %W

    section Developer A
    Week 1: Development     :a1, 2026-01-17, 8h
    Week 2: Development     :a2, after a1, 8h
    Week 3: Development     :a3, after a2, 8h
    Week 4: Development     :a4, after a3, 8h
    Week 5: Development     :a5, after a4, 8h
    Week 6: Development     :a6, after a5, 8h
    Week 7: Development     :a7, after a6, 8h
    Week 8: Development     :a8, after a7, 8h

    section Developer B
    Week 1: Development     :b1, 2026-01-17, 8h
    Week 2: Development     :b2, after b1, 8h
    Week 3: Development     :b3, after b2, 8h
    Week 4: Development     :b4, after b3, 8h
    Week 5: Development     :b5, after b4, 8h
    Week 6: Development     :b6, after b5, 8h
    Week 7: Development     :b7, after b6, 8h
    Week 8: Development     :b8, after b7, 8h
```

## Integration Test Schedule

```mermaid
sequenceDiagram
    participant A as Developer A
    participant B as Developer B
    participant Test as Integration Tests

    Note over A,B: Week 1-2: Foundation Phase
    A->>B: Deliver Config Manager & Repo Loader
    B->>A: Delivers Component ID & Markdown Writer
    A->>Test: Integration Test 1 (Week 2)
    Test-->>A,B: Feedback & Fixes

    Note over A,B: Week 3-4: Intelligence Phase
    A->>B: Delivers OpenRouter & Prompt Templates
    B->>A: Delivers Pattern Detection & Diagrams
    B->>Test: Integration Test 2 (Week 4)
    Test-->>A,B: Feedback & Fixes

    Note over A,B: Week 5-6: Scaling Phase
    A->>B: Delivers Incremental Engine & Service Registry
    B->>A: Delivers Parallel Executor & System Diagrams
    A->>Test: Integration Test 3 (Week 6)
    Test-->>A,B: Feedback & Fixes

    Note over A,B: Week 7-8: Polish Phase
    A->>B: Delivers Provider Registry & Static Export
    B->>A: Delivers HTML Renderer & Diagram Export
    A->>B: Integration Test 4 (Week 8)
    B->>A: Full Feature Test Suite
    Test-->>A,B: Final Approval