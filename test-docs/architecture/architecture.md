# Architecture Overview

The `repo-explainer` is a Python-based CLI tool designed to automate the documentation of software repositories. It utilizes a **Pipeline Architecture** to process repositories through distinct stages of loading, analysis, AI augmentation, and generation.

## High-Level Architecture

The system is orchestrated by a central controller that manages the flow of data between specialized components.

1.  **Input Layer**: Accepts user commands via CLI to target local or remote repositories.
2.  **Ingestion Layer**: Handles repository cloning and file system traversal.
3.  **Analysis Layer**: Performs static analysis using Tree-sitter to build a semantic understanding of the code (components, dependencies).
4.  **Intelligence Layer**: Integrates with LLMs (via OpenCode, Claude, or direct APIs) to generate human-like insights and architectural reasoning.
5.  **Generation Layer**: Synthesizes the structural data and AI insights into diagrams (Mermaid) and Markdown documentation.
6.  **Output Layer**: Persists the generated artifacts to the filesystem.

## Design Patterns

-   **Orchestrator Pattern**: Central `Orchestrator` class manages the lifecycle and dependencies of the analysis process.
-   **Adapter Pattern**: `OpenCodeRunner`, `ClaudeRunner`, and `LLMService` provide a unified interface for different AI backends.
-   **Strategy Pattern**: Analysis depth and output formats are handled via configurable strategies.
-   **Repository Pattern**: `RepositoryLoader` abstracts the details of acquiring code (git vs local).

## Key Subsystems

-   **Core**: Configuration, Models, and CLI entry points.
-   **Analysis Engine**: Static code analysis powered by Tree-sitter.
-   **AI Integration**: Abstractions for communicating with LLMs.
-   **Generators**: Modules for creating specific output formats (Diagrams, Docs).
