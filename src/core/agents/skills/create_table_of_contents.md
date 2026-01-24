Create comprehensive table of contents from component documentation

You are responsible for aggregating all component documentation and creating a structured table of contents for final documentation generation.

## Purpose

Analyze all component documentation files and create a hierarchical table of contents that organizes components into logical documentation sections.

## Input

- Read all markdown files in `planning/docs/*/`
- Parse component overviews, APIs, architectures
- Identify topics and themes

## Processing

1. **Scan component documentation**:
   - Read all subdirectories in `planning/docs/`
   - Extract component names, descriptions, topics
   - Identify key themes (architecture, APIs, utilities, etc.)

2. **Group related components** into documentation sections:
   - Architecture (core systems, design patterns)
   - Components (major modules, services)
   - APIs (endpoints, interfaces, contracts)
   - Utilities (helpers, tools, libraries)
   - Development (testing, deployment, configuration)

3. **Create section hierarchy**:
   - Main topics (top-level sections)
   - Subtopics (component groupings)
   - Individual components (leaf nodes)

4. **Map components to sections**:
   - Assign each component to one or more sections
   - Collect relevant files for each section
   - Generate section metadata (title, description)

## Output

Write `planning/documentation/toc.json`:

```json
{
  "repository": "Repository Name",
  "sections": [
    {
      "name": "architecture",
      "title": "Architecture Overview",
      "description": "Core architectural patterns and design decisions",
      "priority": 1,
      "components": ["core_api", "database", "auth"],
      "files": [
        "planning/docs/core_api/architecture.md",
        "planning/docs/database/schema.md",
        "planning/docs/auth/design.md"
      ]
    },
    {
      "name": "api_reference",
      "title": "API Reference",
      "description": "Complete API documentation for all endpoints",
      "priority": 2,
      "components": ["core_api", "auth"],
      "files": [
        "planning/docs/core_api/api.md",
        "planning/docs/auth/api.md"
      ]
    }
  ],
  "metadata": {
    "total_sections": 5,
    "total_components": 12,
    "generated_at": "2026-01-23"
  }
}
```

## Quality Verification

Before creating TOC, verify component docs meet minimum standards:

For each component, check:
- [ ] Has index.md file (rename if needed)
- [ ] Has minimum 100 lines of content
- [ ] Has at least 1 diagram reference
- [ ] Has at least 1 code block
- [ ] Has at least 1 table

If component docs are too shallow:
- Log warning in TOC about shallow documentation
- Still include in TOC but mark as "needs expansion"
- Document which quality criteria are missing

## Enhanced Output Format

Create `planning/documentation/toc.json` with quality metadata:

```json
{
  "repository": "Repository Name",
  "sections": [
    {
      "name": "architecture",
      "title": "Architecture Overview",
      "description": "Core architectural patterns and design decisions",
      "priority": 1,
      "components": ["api_server", "controller_manager"],
      "files": ["planning/docs/api_server/index.md", "planning/docs/controller_manager/index.md"],
      "quality": {
        "api_server": {
          "depth": "deep",
          "lines": 287,
          "diagrams": 3,
          "examples": 5,
          "tables": 2,
          "warnings": []
        },
        "controller_manager": {
          "depth": "shallow",
          "lines": 42,
          "diagrams": 0,
          "examples": 0,
          "tables": 0,
          "warnings": ["Missing controller enumeration", "No code examples", "No diagrams"]
        }
      }
    }
  ],
  "metadata": {
    "total_sections": 5,
    "total_components": 12,
    "generated_at": "2026-01-23",
    "quality_summary": {
      "deep_docs": 8,
      "shallow_docs": 4,
      "total_warnings": 12
    }
  }
}
```

## Guidelines

- **Logical grouping**: Sections should reflect user mental models (architecture, API, components)
- **No duplication**: Each file should appear in only one section
- **Priority ordering**: Higher priority sections appear first
- **Clear titles**: Section titles should be self-explanatory
- **Useful descriptions**: Section descriptions help readers navigate
- **Balanced sections**: Aim for 3-8 sections with roughly equal content
- **Quality tracking**: Include quality metrics for each component
- **Warning visibility**: Make shallow documentation visible to users
