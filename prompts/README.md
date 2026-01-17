# Repository Explainer Prompts

This directory contains prompt templates and schemas for AI-powered repository analysis using OpenCode/Claude.

## Overview

The prompts system provides:
- **Rich, context-aware prompts** with explicit file-to-component mappings
- **Orchestrator-ready metadata** for Stage 2+ multi-agent coordination
- **Progressive analysis levels** (quick, standard, deep)
- **Validation schemas** for consistent output formats

## Directory Structure

```
prompts/
├── README.md                    # This file
├── schemas/
│   └── orchestrator_context.json  # JSON schema for orchestrator context
├── templates/
│   ├── quick_scan_v2.md          # Lightweight inventory with file mappings
│   ├── architecture_deep_dive.md  # Comprehensive architectural analysis
│   ├── pattern_detection.md       # Architectural & design pattern detection
│   └── dependency_mapping.md      # Internal & external dependency graphs
└── examples/
    └── (example outputs to be added)
```

## Prompt Templates

### 1. Quick Scan V2 (`quick_scan_v2.md`)

**Purpose**: Rapid repository inventory for baseline context

**Outputs**:
- `repository-summary.json` - Repository metadata
- `module-index.md` - File/module table of contents
- `components-quick.json` - Basic component registry with file paths
- `tech-stack.txt` - Technology inventory

**Use Cases**:
- Initial repository assessment
- Pre-analysis for determining analysis strategy
- Fast onboarding overview

**Estimated Duration**: 2-5 minutes for medium repositories

**Example**:
```bash
opencode run "$(cat prompts/templates/quick_scan_v2.md)" --format json
```

### 2. Architecture Deep Dive (`architecture_deep_dive.md`)

**Purpose**: Comprehensive architectural analysis with function-level details

**Outputs**:
- `architecture.md` - Detailed architecture documentation
- `components.mermaid` - Component relationship diagram
- `dataflow.mermaid` - Data flow sequence diagram
- `components.json` - Full component registry with function mappings
- `tech-stack.txt` - Detailed technology stack

**Key Features**:
- ✅ File-to-component mappings for ALL components
- ✅ Function-level details with line ranges
- ✅ Internal and external dependency tracking
- ✅ Interface documentation (REST, GraphQL, function exports)
- ✅ Entry point identification

**Use Cases**:
- Standard analysis mode
- Deep code understanding for onboarding
- Architecture documentation generation

**Estimated Duration**: 5-15 minutes for medium repositories

**Example**:
```bash
repo-explainer analyze ./my-repo --depth standard
# Uses this prompt internally
```

### 3. Pattern Detection (`pattern_detection.md`)

**Purpose**: Identify architectural and design patterns with evidence

**Inputs Required**:
- `components.json` from prior architecture analysis
- Repository directory structure

**Outputs**:
- `patterns/identified-patterns.md` - Pattern report
- `patterns/patterns.json` - Structured pattern metadata with evidence

**Detected Patterns**:

**Architectural**:
- MVC (Model-View-Controller)
- Microservices
- Layered Architecture
- Event-Driven
- CQRS
- Hexagonal/Ports & Adapters

**Design**:
- Singleton
- Factory
- Observer
- Strategy
- Decorator
- Adapter
- Repository

**Key Features**:
- ✅ Confidence scoring (0.0-1.0)
- ✅ Evidence with file paths and line ranges
- ✅ No false positives from naming alone
- ✅ Multiple instances tracked per pattern

**Use Cases**:
- Pattern-based documentation
- Code quality assessment
- Architecture validation

**Estimated Duration**: 3-8 minutes for medium repositories

**Example**:
```python
from repo_explainer.opencode_service import OpenCodeService

service = OpenCodeService(repo_path)
result = service.detect_patterns()
```

### 4. Dependency Mapping (`dependency_mapping.md`)

**Purpose**: Build comprehensive dependency graphs (internal + external)

**Inputs Required**:
- `components.json` from prior architecture analysis
- Package manager files (package.json, requirements.txt, go.mod, etc.)

**Outputs**:
- `dependencies/overview.md` - Dependency analysis report
- `dependencies/dependency-graph.json` - Structured dependency data
- `dependencies/dependency-graph.mermaid` - Visual dependency diagram

**Key Features**:
- ✅ External package catalog with versions
- ✅ Package-to-component usage mapping
- ✅ Internal component dependencies with evidence
- ✅ Dependency layer calculation (topological sort)
- ✅ Circular dependency detection

**Use Cases**:
- Dependency impact analysis
- Upgrade planning
- Architecture validation
- Security vulnerability assessment

**Estimated Duration**: 4-10 minutes for medium repositories

**Example**:
```python
from repo_explainer.opencode_service import OpenCodeService

service = OpenCodeService(repo_path)
result = service.map_dependencies()
```

## Orchestrator Context Contract

### Schema: `schemas/orchestrator_context.json`

This JSON schema defines the data structure that Stage 2+ orchestrators expect from analysis prompts. It ensures consistency across all prompt outputs and enables multi-agent coordination.

**Key Sections**:

1. **Repository** - Metadata and summary
2. **Analysis** - Session metadata and token tracking
3. **Components** - Component registry with file mappings
4. **Dependencies** - Internal and external dependency graphs
5. **Patterns** - Detected architectural/design patterns
6. **Diagrams** - Generated diagram metadata
7. **Artifacts** - File paths to all generated artifacts

**Usage**:
```json
{
  "repository": {
    "name": "my-app",
    "path": "/path/to/repo",
    "primary_language": "Python",
    "languages": ["Python", "JavaScript"],
    "entry_points": ["src/main.py"]
  },
  "components": [
    {
      "component_id": "auth-service",
      "name": "Authentication Service",
      "type": "service",
      "file_path": "src/services/auth.py",
      "line_range": {"start": 1, "end": 250},
      "key_functions": [
        {
          "name": "verify_token",
          "file_path": "src/services/auth.py",
          "line_range": {"start": 45, "end": 68},
          "signature": "def verify_token(token: str) -> User"
        }
      ],
      "dependencies": {
        "internal": ["database-client"],
        "external": ["pyjwt", "cryptography"]
      }
    }
  ]
}
```

## Prompt Design Principles

### 1. File-to-Component Mapping

**Every** component, function, and relationship MUST include:
- `file_path`: Relative path from repository root
- `line_range`: Start and end line numbers (when applicable)

**Good Example**:
```json
{
  "component_id": "user-service",
  "file_path": "src/services/user.py",
  "line_range": {"start": 1, "end": 180}
}
```

**Bad Example**:
```json
{
  "component_id": "user-service",
  "description": "Handles user operations"
  // ❌ Missing file_path!
}
```

### 2. Evidence-Based Analysis

All assertions must be backed by concrete evidence:
- File references
- Line numbers
- Code snippets (when helpful)

### 3. Token Efficiency

Prompts guide the AI to:
- Read files strategically (manifests first, then entry points)
- Use glob/grep before reading full files
- Read only relevant sections using line ranges
- Cache information to avoid re-analysis

### 4. Validation Requirements

Each prompt includes a validation checklist:
- [ ] All file paths are relative to repo root
- [ ] Line ranges are accurate
- [ ] JSON output is valid
- [ ] No placeholders or TODO items in output

## Usage in Code

### Python API

```python
from pathlib import Path
from repo_explainer.opencode_service import OpenCodeService

# Initialize service
repo_path = Path("./my-repository")
service = OpenCodeService(repo_path)

# Quick scan
quick_result = service.quick_scan()

# Full architecture analysis
arch_result = service.analyze_architecture()

# Pattern detection (requires components.json)
pattern_result = service.detect_patterns()

# Dependency mapping (requires components.json)
dep_result = service.map_dependencies()
```

### CLI

```bash
# Quick scan
repo-explainer analyze ./my-repo --depth quick

# Standard analysis (uses architecture_deep_dive)
repo-explainer analyze ./my-repo --depth standard

# Deep analysis (uses all prompts)
repo-explainer analyze ./my-repo --depth deep

# Verbose mode to see prompt execution
repo-explainer analyze ./my-repo --depth standard --verbose
```

### Direct OpenCode

```bash
# Run specific prompt directly
cd /path/to/repo
opencode run "$(cat /path/to/prompts/templates/quick_scan_v2.md)" \
  --format json \
  --model openrouter/google/gemini-3-flash-preview
```

## Prompt Development Guidelines

When creating or modifying prompts:

### 1. Start with Requirements
- Define expected outputs (formats, files)
- Specify required inputs (context files, manifests)
- List success criteria

### 2. Provide Clear Instructions
- Step-by-step workflow
- Example output formats
- Validation checklists

### 3. Include Constraints
- Token efficiency guidelines
- Time/cost limits
- Quality requirements

### 4. Test with Real Repositories
- Small (< 100 files)
- Medium (100-1000 files)
- Large (> 1000 files)

### 5. Validate Outputs
- Check JSON schema compliance
- Verify file paths exist
- Confirm line ranges are accurate

## Prompt Evolution

### Stage 1 (Current)
- ✅ Quick scan v2
- ✅ Architecture deep dive
- ✅ Pattern detection
- ✅ Dependency mapping

### Stage 2 (Planned)
- [ ] Sequence diagram generation
- [ ] Entity-relationship diagram extraction
- [ ] API documentation generation
- [ ] Test coverage analysis

### Stage 3 (Future)
- [ ] Security vulnerability detection
- [ ] Performance optimization suggestions
- [ ] Refactoring recommendations
- [ ] Multi-repository analysis

## Contributing

When adding new prompts:

1. **Create template** in `templates/<name>.md`
2. **Define schema** if introducing new output format
3. **Add loader function** in `src/repo_explainer/prompts.py`
4. **Add service method** in `src/repo_explainer/opencode_service.py`
5. **Document** in this README
6. **Test** with diverse repositories
7. **Add examples** in `examples/`

## References

- [REQUIREMENTS.md](../REQUIREMENTS.md) - Functional requirements
- [improve_prompts.md](../improve_prompts.md) - Improvement plan
- [stages/stage_2.md](../stages/stage_2.md) - Stage 2 orchestrator requirements
- [OpenCode Documentation](https://docs.opencode.ai)

---

**Last Updated**: 2026-01-17
**Version**: 1.0
