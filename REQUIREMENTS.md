# Repository Explainer - Functional Requirements Document

## 1. Executive Summary

**Project Name**: Repository Explainer

**Purpose**: An AI-powered CLI tool that analyzes software repositories and generates comprehensive documentation, architectural diagrams, and knowledge bases to accelerate developer onboarding and understanding of complex codebases.

**Primary Use Case**: Onboarding new developers by providing automated, comprehensive documentation of repository structure, architecture, and design patterns.

---

## 2. Project Goals

### 2.1 Core Objectives
- Decompose repositories into structured markdown documentation
- Generate visual diagrams representing architecture and component relationships
- Identify and document both explicit and implicit design patterns
- Support analysis of single repositories, monorepos, and multi-repository systems
- Create portable, LLM-compatible, and human-readable output

### 2.2 Success Criteria
- New developers can understand a codebase 70% faster using generated documentation
- Generated documentation accurately represents repository structure and relationships
- Tool successfully analyzes repositories ranging from small projects to large monorepos
- Output is compatible with standard markdown viewers and LLM consumption

---

## 3. Functional Requirements

### 3.1 Repository Access & Ingestion

#### FR-1.1: Multi-Source Repository Support
- **Priority**: P0 (Critical)
- **Description**: Support analysis of both local and remote repositories
- **Acceptance Criteria**:
  - Accept local filesystem paths to git repositories
  - Accept GitHub repository URLs (https/ssh)
  - Automatically clone remote repositories to temporary workspace
  - Handle private repositories with authentication (SSH keys, PAT tokens)

#### FR-1.2: Repository Size Handling
- **Priority**: P0 (Critical)
- **Description**: Handle repositories of variable sizes efficiently
- **Acceptance Criteria**:
  - Support small repositories (< 100 files)
  - Support medium repositories (100-1000 files)
  - Support large repositories (1000-10000 files)
  - Support very large repositories (> 10000 files) with performance optimizations
  - Implement rate limiting and cost controls for LLM API calls

#### FR-1.3: Incremental Update Support
- **Priority**: P1 (High)
- **Description**: Track repository changes and perform incremental analysis
- **Acceptance Criteria**:
  - Detect changes since last analysis (using git diff)
  - Re-analyze only modified components and their dependencies
  - Update affected documentation sections
  - Maintain version history of generated documentation
  - Provide full re-analysis option when needed

### 3.2 Code Analysis & Understanding

#### FR-2.1: Progressive Analysis Strategy
- **Priority**: P0 (Critical)
- **Description**: Implement multi-level analysis from high-level overview to detailed examination
- **Acceptance Criteria**:
  - **Level 1 - Overview**: Repository structure, primary languages, key directories
  - **Level 2 - Architecture**: Component identification, service boundaries, data flow
  - **Level 3 - Detailed**: Function-level analysis, design patterns, implementation details
  - Allow users to specify analysis depth via CLI flags
  - Support targeted deep-dive analysis of specific components

#### FR-2.2: Multi-Language Support
- **Priority**: P0 (Critical)
- **Description**: Analyze repositories containing multiple programming languages
- **Acceptance Criteria**:
  - Detect and identify all programming languages in repository
  - Parse and understand common languages: JavaScript/TypeScript, Python, Java, Go, Rust, C#, Ruby, PHP
  - Extract structure from configuration files: JSON, YAML, TOML, XML
  - Identify framework-specific patterns (React, Django, Spring, Express, etc.)

#### FR-2.3: Architectural Pattern Detection
- **Priority**: P1 (High)
- **Description**: Identify and document architectural and design patterns
- **Acceptance Criteria**:
  - Detect architectural patterns: Microservices, MVC, Layered, Event-driven, CQRS, Hexagonal
  - Identify design patterns: Singleton, Factory, Observer, Strategy, etc.
  - Document API patterns: REST, GraphQL, gRPC
  - Recognize infrastructure patterns: Containerization, CI/CD, IaC

#### FR-2.4: Dependency Analysis
- **Priority**: P0 (Critical)
- **Description**: Map all internal and external dependencies
- **Acceptance Criteria**:
  - Extract dependencies from package managers (npm, pip, maven, cargo, go.mod, etc.)
  - Identify internal module dependencies
  - Map service-to-service dependencies (for microservices)
  - Document external library usage and versions
  - Detect upstream and downstream dependencies

### 3.3 Documentation Generation

#### FR-3.1: Markdown Documentation Output
- **Priority**: P0 (Critical)
- **Description**: Generate structured markdown documentation
- **Acceptance Criteria**:
  - Create hierarchical markdown file structure
  - Include table of contents and cross-references
  - Document each component/module with: purpose, responsibilities, dependencies, key functions/classes
  - Generate index/overview documents
  - Include code snippets and examples where relevant
  - Support markdown extensions (GitHub Flavored Markdown)

#### FR-3.2: Auto-Detected Documentation Structure
- **Priority**: P1 (High)
- **Description**: Automatically determine optimal documentation organization
- **Acceptance Criteria**:
  - Analyze repository to determine structure (component-based, layer-based, or hybrid)
  - Adapt to monorepo structures with multiple sub-projects
  - Create logical groupings for related functionality
  - Generate navigation aids and cross-references
  - Allow manual override of detected structure via configuration

#### FR-3.3: Multi-Repository Support (Future)
- **Priority**: P2 (Future)
- **Description**: Analyze and document relationships across multiple repositories
- **Acceptance Criteria**:
  - Accept list of related repositories (e.g., microservices)
  - Map inter-service communication patterns
  - Document shared dependencies and libraries
  - Generate system-wide architectural views
  - Track versioning and compatibility across services

### 3.4 Diagram Generation

#### FR-4.1: Architecture Diagrams
- **Priority**: P0 (Critical)
- **Description**: Generate high-level system architecture diagrams
- **Acceptance Criteria**:
  - Create component diagrams showing major system parts
  - Show service boundaries and interfaces
  - Illustrate data flow between components
  - Output as Mermaid diagram format
  - Include both visual and ASCII representations

#### FR-4.2: Sequence Diagrams
- **Priority**: P1 (High)
- **Description**: Document interaction flows and API call patterns
- **Acceptance Criteria**:
  - Generate sequence diagrams for key user flows
  - Document API request/response patterns
  - Show authentication and authorization flows
  - Illustrate error handling paths
  - Output as Mermaid sequence diagrams

#### FR-4.3: Entity Relationship Diagrams
- **Priority**: P1 (High)
- **Description**: Visualize data models and database schemas
- **Acceptance Criteria**:
  - Extract database schemas from ORM models
  - Document entity relationships (one-to-one, one-to-many, many-to-many)
  - Include key fields and data types
  - Show foreign key relationships
  - Output as Mermaid ER diagrams

#### FR-4.4: Call Graphs & Dependency Diagrams
- **Priority**: P1 (High)
- **Description**: Visualize code dependencies and call hierarchies
- **Acceptance Criteria**:
  - Generate function call graphs for critical paths
  - Create module dependency diagrams
  - Visualize service dependency graphs
  - Map external library dependencies
  - Support filtering and depth control to manage complexity

#### FR-4.5: Portable Diagram Formats
- **Priority**: P0 (Critical)
- **Description**: Ensure diagrams are portable and LLM-compatible
- **Acceptance Criteria**:
  - Primary format: Mermaid.js (renders in GitHub, VS Code, etc.)
  - Include ASCII art versions for terminal viewing
  - Support export to SVG/PNG via Mermaid CLI (optional)
  - Ensure diagrams are readable by LLMs for future analysis

### 3.5 CLI Interface

#### FR-5.1: Command Structure
- **Priority**: P0 (Critical)
- **Description**: Provide intuitive CLI commands
- **Acceptance Criteria**:
  ```bash
  # Basic usage
  repo-explainer analyze <repo-path-or-url>

  # With options
  repo-explainer analyze <repo> --depth <quick|standard|deep>
  repo-explainer analyze <repo> --output <dir> --format <markdown|html|json>
  repo-explainer analyze <repo> --incremental

  # Multi-repo analysis (future)
  repo-explainer analyze-multi <config-file>

  # Update existing analysis
  repo-explainer update <analysis-dir>
  ```

#### FR-5.2: Configuration Management
- **Priority**: P1 (High)
- **Description**: Support configuration via files and environment variables
- **Acceptance Criteria**:
  - Support `.repo-explainer.yaml` configuration file
  - Environment variables for sensitive data (API keys)
  - Configuration options: LLM provider, analysis depth, output format, ignored paths
  - Ability to save analysis settings for reuse

#### FR-5.3: Progress Reporting
- **Priority**: P1 (High)
- **Description**: Provide feedback during analysis
- **Acceptance Criteria**:
  - Display progress bars for long-running operations
  - Show current analysis phase (scanning, analyzing, generating)
  - Estimate time remaining based on repository size
  - Display token usage and API costs
  - Support verbose mode for detailed logging

### 3.6 LLM Integration

#### FR-6.1: OpenRouter Integration
- **Priority**: P0 (Critical)
- **Description**: Integrate with OpenRouter API for LLM access
- **Acceptance Criteria**:
  - Support OpenRouter API authentication
  - Initial model: Gemini 2.5 Flash
  - Configurable model selection
  - Handle rate limiting and retries
  - Track and report API costs

#### FR-6.2: Prompt Engineering
- **Priority**: P0 (Critical)
- **Description**: Design effective prompts for code understanding
- **Acceptance Criteria**:
  - Specialized prompts for different analysis tasks (architecture, patterns, documentation)
  - Context-aware prompts that include relevant code snippets
  - Prompts optimized for token efficiency
  - Few-shot examples for consistent output formatting
  - Validation of LLM responses for accuracy

#### FR-6.3: Context Management
- **Priority**: P1 (High)
- **Description**: Manage context window effectively for large repositories
- **Acceptance Criteria**:
  - Chunk large files intelligently (by function/class boundaries)
  - Prioritize important files for detailed analysis
  - Use hierarchical summarization for large codebases
  - Implement context caching where supported by provider
  - Track token usage per analysis

---

## 4. Non-Functional Requirements

### 4.1 Performance

#### NFR-1.1: Analysis Speed
- **Priority**: P1 (High)
- Small repos (< 100 files): Complete analysis in < 2 minutes
- Medium repos (100-1000 files): Complete analysis in < 10 minutes
- Large repos (> 1000 files): Provide progressive results, full analysis < 1 hour

#### NFR-1.2: Resource Efficiency
- **Priority**: P1 (High)
- Memory usage: < 2GB for medium repositories
- Disk usage: Output should be < 10% of repository size
- Concurrent processing: Support parallel analysis where safe

### 4.2 Reliability

#### NFR-2.1: Error Handling
- **Priority**: P0 (Critical)
- Gracefully handle network failures (API, git clone)
- Retry failed LLM requests with exponential backoff
- Continue analysis even if individual files fail
- Provide clear error messages and recovery suggestions

#### NFR-2.2: Data Quality
- **Priority**: P0 (Critical)
- Generated documentation must be factually accurate
- Diagrams must correctly represent code relationships
- Validation mechanisms to detect hallucinations

### 4.3 Usability

#### NFR-3.1: Output Quality
- **Priority**: P0 (Critical)
- Documentation must be readable by technical and non-technical users
- Diagrams must be clear and not overly complex
- Consistent formatting and structure across all generated docs
- Include glossary for domain-specific terms

#### NFR-3.2: Compatibility
- **Priority**: P0 (Critical)
- Output compatible with popular markdown viewers (GitHub, GitLab, VS Code)
- Mermaid diagrams render correctly in standard tools
- Works on macOS, Linux, and Windows
- Python 3.9+ support

### 4.4 Security

#### NFR-4.1: Credential Management
- **Priority**: P0 (Critical)
- Never log or store API keys in plain text
- Support secure credential storage (environment variables, keychain)
- Respect .gitignore and exclude sensitive files from analysis

#### NFR-4.2: Data Privacy
- **Priority**: P0 (Critical)
- Provide option to analyze offline (local models future)
- Clear disclosure of what code is sent to LLM APIs
- Option to exclude sensitive files/directories
- No telemetry without explicit user consent

### 4.5 Maintainability

#### NFR-5.1: Code Quality
- **Priority**: P1 (High)
- Well-documented Python codebase
- Modular architecture for easy extension
- Comprehensive test coverage (>80%)
- Type hints throughout

#### NFR-5.2: Extensibility
- **Priority**: P1 (High)
- Plugin architecture for custom analyzers
- Support for additional LLM providers
- Configurable output formatters
- Custom diagram generators

---

## 5. System Architecture (High-Level)

### 5.1 Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI Interface                         │
│                    (Argument parsing, Config)                │
└────────────────────────────┬────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────┐
│                   Orchestration Layer                        │
│          (Analysis pipeline, Progress tracking)              │
└────────┬─────────────┬─────────────┬────────────┬───────────┘
         │             │             │            │
         ▼             ▼             ▼            ▼
┌─────────────┐ ┌──────────┐ ┌───────────┐ ┌──────────────┐
│   Repository │ │   Code   │ │    LLM    │ │ Documentation│
│   Loader     │ │ Analyzer │ │  Service  │ │  Generator   │
└─────────────┘ └──────────┘ └───────────┘ └──────────────┘
         │             │             │            │
         │             │             │            │
         ▼             ▼             ▼            ▼
┌─────────────────────────────────────────────────────────────┐
│                      Output Layer                            │
│         (Markdown writer, Diagram generator)                 │
└─────────────────────────────────────────────────────────────┘
```

### 5.2 Component Descriptions

**CLI Interface**: Handles user commands, argument parsing, and configuration loading

**Orchestration Layer**: Coordinates the analysis pipeline, manages state, and tracks progress

**Repository Loader**: Clones or accesses repositories, handles authentication, manages file system operations

**Code Analyzer**: Parses code, builds ASTs, detects patterns, extracts structure

**LLM Service**: Manages OpenRouter API calls, prompt construction, response parsing, context management

**Documentation Generator**: Creates markdown files, generates diagrams, organizes output

**Output Layer**: Writes files to disk, manages output directory structure, handles formatting

---

## 6. Data Model

### 6.1 Core Entities

#### Repository
```python
{
  "path": str,              # Local path or URL
  "name": str,              # Repository name
  "primary_language": str,  # Detected primary language
  "languages": [str],       # All languages detected
  "size_category": str,     # small|medium|large
  "last_analyzed": datetime,
  "analysis_version": str
}
```

#### Component
```python
{
  "id": str,
  "name": str,
  "type": str,              # service|module|package|class
  "path": str,              # Relative path in repo
  "description": str,       # LLM-generated description
  "responsibilities": [str],
  "dependencies": [str],    # Component IDs
  "external_dependencies": [str],
  "files": [str],
  "interfaces": [Interface]
}
```

#### Diagram
```python
{
  "type": str,              # architecture|sequence|er|call-graph
  "title": str,
  "mermaid_code": str,
  "ascii_art": str,
  "related_components": [str]
}
```

### 6.2 Output Structure

```
<output-dir>/
├── index.md                     # Main overview
├── architecture/
│   ├── overview.md
│   ├── system-architecture.md
│   └── diagrams/
│       ├── high-level.mmd
│       └── component-diagram.mmd
├── components/
│   ├── component-a/
│   │   ├── overview.md
│   │   ├── api.md
│   │   └── diagrams/
│   └── component-b/
├── data-models/
│   ├── entities.md
│   └── diagrams/
│       └── er-diagram.mmd
├── dependencies/
│   ├── internal.md
│   ├── external.md
│   └── diagrams/
│       └── dependency-graph.mmd
├── patterns/
│   └── identified-patterns.md
└── metadata/
    ├── analysis-log.json
    └── config.yaml
```

---

## 7. Phases & Milestones

### Phase 1: MVP (Minimum Viable Product)
**Timeline**: 4-6 weeks
**Goal**: Basic single-repository analysis with markdown output

- [ ] CLI scaffolding and configuration
- [ ] Repository cloning and local access
- [ ] Basic code scanning and structure detection
- [ ] OpenRouter + Gemini 2.5 Flash integration
- [ ] Simple markdown documentation generation
- [ ] Basic architecture diagram generation (Mermaid)
- [ ] Python, JavaScript/TypeScript support

### Phase 2: Enhanced Analysis
**Timeline**: 4-6 weeks
**Goal**: Comprehensive analysis with all diagram types

- [ ] Sequence diagram generation
- [ ] Entity relationship diagrams
- [ ] Call graph generation
- [ ] Dependency mapping (internal + external)
- [ ] Design pattern detection
- [ ] Multi-language support expansion
- [ ] Progressive analysis implementation

### Phase 3: Scale & Performance
**Timeline**: 3-4 weeks
**Goal**: Handle large repositories efficiently

- [ ] Incremental update support
- [ ] Context management optimization
- [ ] Smart sampling for large codebases
- [ ] Parallel processing
- [ ] Cost optimization and caching

### Phase 4: Multi-Repository Support
**Timeline**: 4-6 weeks
**Goal**: Analyze microservices and monorepos

- [ ] Multi-repo configuration
- [ ] Inter-service relationship mapping
- [ ] System-wide architectural views
- [ ] Service dependency tracking
- [ ] Unified documentation generation

### Phase 5: Enhancements & Polish
**Timeline**: Ongoing
**Goal**: Improve usability and extend functionality

- [ ] Interactive HTML output
- [ ] VS Code extension integration
- [ ] Custom analyzer plugins
- [ ] Additional LLM provider support
- [ ] Local model support (privacy mode)
- [ ] Web-based visualization (future consideration)

---

## 8. Success Metrics

### 8.1 Quality Metrics
- **Accuracy**: >90% accuracy in component identification (validated by manual review)
- **Completeness**: >95% of repository components documented
- **Diagram Correctness**: >85% of relationships correctly represented

### 8.2 Performance Metrics
- **Analysis Speed**: Meets NFR-1.1 targets
- **Cost Efficiency**: <$1 API cost per 1000 files analyzed
- **Token Efficiency**: <50% of theoretical maximum tokens used

### 8.3 User Satisfaction
- **Onboarding Time**: 50-70% reduction in time to understand new codebase
- **Documentation Quality**: User rating >4/5 on clarity and usefulness
- **Adoption**: Successful analysis of 10+ diverse repositories

---

## 9. Risks & Mitigations

### 9.1 Technical Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| LLM hallucinations produce inaccurate docs | High | Medium | Implement validation, cross-reference with static analysis, allow manual review |
| Large repos exceed context limits | High | High | Implement chunking, progressive analysis, smart sampling |
| API costs become prohibitive | Medium | Medium | Implement caching, rate limiting, cost tracking, optimize prompts |
| Parsing complex languages fails | Medium | Low | Start with popular languages, add language support incrementally |
| Generated diagrams become unreadable | Medium | Medium | Implement complexity limits, allow filtering, hierarchical views |

### 9.2 Project Risks

| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Scope creep | High | High | Stick to phased approach, prioritize ruthlessly |
| Gemini API changes | Medium | Low | Abstract LLM provider interface, support multiple models |
| User needs differ from assumptions | Medium | Medium | Early user testing, iterative feedback |

---

## 10. Open Questions

### 10.1 For Immediate Clarification
1. **Test Coverage**: What level of test coverage is acceptable for MVP vs later phases?
2. **Private Repos**: What authentication methods should be prioritized (PAT, SSH, OAuth)?
3. **Cost Limits**: Should we implement hard cost limits per analysis run?
4. **Output Versioning**: How should we version the output format for backward compatibility?

### 10.2 For Future Discussion
1. **Collaboration**: Should multiple users be able to contribute to/edit generated docs?
2. **CI/CD Integration**: Should this run automatically in pipelines to keep docs updated?
3. **Hosted Service**: Is there interest in a hosted web service version?
4. **Custom Models**: Should we support fine-tuned models for specific domains/frameworks?

---

## 11. Appendix

### 11.1 Technology Stack (Proposed)

**Core Language**: Python 3.9+

**Key Libraries**:
- `click` or `typer` - CLI framework
- `GitPython` - Git operations
- `tree-sitter` - Code parsing
- `openrouter` / `requests` - LLM API calls
- `pydantic` - Data validation
- `pyyaml` - Configuration
- `rich` - Terminal UI/progress
- `pytest` - Testing

**Optional**:
- `ast` / `astroid` - Python AST analysis
- `jedi` - Python code intelligence
- `ts-morph` (via subprocess) - TypeScript analysis

### 11.2 Competitor Analysis

**Similar Tools**:
- GitHub Copilot Workspace (proprietary, GitHub-only)
- Sourcegraph Cody (requires infrastructure)
- Mintlify (docs generation, not architectural analysis)
- Swimm (continuous documentation, requires manual input)

**Differentiators**:
- Fully automated, no manual intervention required
- Comprehensive architectural analysis
- Multi-repository support
- Portable, LLM-compatible output
- Open-source and CLI-first
- Optimized for onboarding use case

### 11.3 References
- [Mermaid.js Documentation](https://mermaid.js.org/)
- [OpenRouter API Documentation](https://openrouter.ai/docs)
- [Tree-sitter Documentation](https://tree-sitter.github.io/tree-sitter/)
- [Google Gemini Documentation](https://ai.google.dev/gemini-api/docs)

---

**Document Version**: 1.0
**Last Updated**: 2026-01-16
**Status**: Draft - Pending Review
