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

## Guidelines

- **Logical grouping**: Sections should reflect user mental models (architecture, API, components)
- **No duplication**: Each file should appear in only one section
- **Priority ordering**: Higher priority sections appear first
- **Clear titles**: Section titles should be self-explanatory
- **Useful descriptions**: Section descriptions help readers navigate
- **Balanced sections**: Aim for 3-8 sections with roughly equal content
