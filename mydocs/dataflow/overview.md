# Data Flow

This page visualizes how data flows through the system.

## Data Flow Diagram

![Data Flow Diagram](../diagrams/dataflow.svg)

<details>
<summary>View Mermaid Source</summary>

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant RL as Repository Loader
    participant ORC as Orchestrator
    participant OCS as OpenCode Service
    participant OM as Output Manager
    participant DC as Doc Composer
    participant HG as HTML Generator

    rect rgb(240, 240, 240)
    Note over User, HG: Full Analysis Flow
    User->>CLI: repo-explain analyze [repo]
    CLI->>ORC: run()
    ORC->>RL: load(repo)
    RL-->>ORC: repo_path
    ORC->>OCS: analyze_architecture()
    OCS-->>ORC: OpenCodeResult
    ORC->>OM: write_analysis_result()
    OM->>DC: compose()
    DC-->>OM: composed_files
    OM-->>ORC: output_files
    ORC-->>CLI: AnalysisResult
    CLI->>HG: generate() (if --generate-html)
    HG-->>CLI: html_dir
    end

    rect rgb(230, 240, 255)
    Note over User, HG: Incremental Update Flow
    User->>CLI: repo-explain update [repo]
    CLI->>RL: get_changed_files()
    RL-->>CLI: changed_files
    CLI->>OCS: analyze_changes(changed_files)
    OCS-->>CLI: OpenCodeResult
    CLI->>OM: write_analysis_result()
    OM-->>CLI: output_files
    CLI->>HG: generate() (if --generate-html)
    HG->>HG: _get_update_banner_html()
    HG-->>CLI: html_dir
    end

    CLI->>User: Display output paths & Start server

```
</details>

## Description

1. **Input**: User provides a repository path or URL to the `cli`.
2. **Loading**: `RepositoryLoader` resolves the path or clones the repo.
3. **Orchestration**: `Orchestrator` (or `cli` directly for simple commands) manages the pipeline.
4. **Analysis**: `OpenCodeService` or `OpenCodeRunner` executes AI analysis (full or incremental).
5. **Processing**: `OutputManager` captures raw output and artifacts.
6. **Composition**: `DocComposer` builds structured Markdown docs and diagrams.
7. **Conversion**: `HTMLGenerator` optionally converts the results to HTML for viewing.
