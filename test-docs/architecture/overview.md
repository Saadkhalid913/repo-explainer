# Architecture Overview

## repo-explainer

This repository is a small-sized project primarily written in python.

## System Architecture

### Components

```mermaid
graph TD
    %% Core Components
    CLI[CLI (Typer)] --> Orch[Orchestrator]
    
    subgraph Core Logic
        Orch --> Config[Config Manager]
        Orch --> Models[Data Models]
    end

    subgraph Pipeline Stages
        Orch --> Loader[Repository Loader]
        Orch --> Analyzer[Code Analyzer]
        Orch --> AI[AI Runners / LLM Service]
        Orch --> DocGen[Documentation Generator]
        Orch --> DiagGen[Diagram Generator]
    end

    subgraph Output
        DocGen --> Output[Output Manager]
        DiagGen --> Output
    end

    %% External Dependencies
    Loader --> Git[GitPython]
    Analyzer --> Tree[Tree-sitter]
    AI --> OpenCode[OpenCode Agent]
    AI --> API[LLM APIs]

    %% Relationships
    Loader -- Source Files --> Analyzer
    Analyzer -- Component Graph --> AI
    AI -- Insights/Mermaid --> DocGen
    AI -- Insights/Mermaid --> DiagGen

```

## Key Components

### src
- **Type**: source
- **Path**: `src`
- **Files**: 12 source files

## Data Flow

```mermaid
flowchart TD
    Start([User Input]) --> CLI[CLI Arguments Parsing]
    CLI --> Init[Initialize Orchestrator]
    
    Init --> Load[Load Repository]
    Load --> Source[Source Code Files]
    
    Source --> Analyze[Static Analysis (Tree-sitter)]
    Analyze --> Context[Analysis Context / Component Graph]
    
    Context --> AI{AI Provider?}
    
    AI -- OpenCode --> Agent[Run OpenCode Agent]
    AI -- Claude --> Claude[Run Claude Agent]
    AI -- LLM --> API[Direct LLM API]
    
    Agent --> Insights[Architectural Insights & Diagrams]
    Claude --> Insights
    API --> Insights
    
    Context --> Merge[Merge Structural & AI Data]
    Insights --> Merge
    
    Merge --> GenDocs[Generate Markdown]
    Merge --> GenDiag[Generate Diagrams]
    
    GenDocs --> Write[Write to Output Dir]
    GenDiag --> Write
    
    Write --> End([Final Documentation])

```

