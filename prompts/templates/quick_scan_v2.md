# Quick Scan V2 - Repository Inventory

## Objective
Perform a rapid inventory of this repository to establish baseline context for deeper analysis. Generate a structured module/file table of contents with minimal token usage.

## Required Outputs

### 1. Repository Summary (repository-summary.json)
Create a JSON file with:
```json
{
  "name": "<repo-name>",
  "primary_language": "<language>",
  "languages": ["<lang1>", "<lang2>"],
  "size_category": "<small|medium|large>",
  "entry_points": [
    {
      "file_path": "<relative-path>",
      "purpose": "<brief-description>"
    }
  ],
  "structure_type": "<monorepo|single-project|library>",
  "framework": "<detected-framework-if-any>"
}
```

### 2. Module Index (module-index.md)
Generate a markdown table of contents:
```markdown
# Module Index

## Core Modules
- `<module-name>` (`<file-path>`) - <one-line-purpose>
- ...

## Utilities/Libraries
- `<module-name>` (`<file-path>`) - <one-line-purpose>

## Configuration
- `<config-file>` - <purpose>

## Tests
- `<test-directory>/` - <coverage-note>
```

### 3. File-to-Component Mapping (components-quick.json)
```json
{
  "components": [
    {
      "component_id": "<unique-id>",
      "name": "<component-name>",
      "type": "<module|package|service>",
      "file_path": "<relative-path>",
      "description": "<one-sentence-purpose>",
      "exports": ["<key-exports>"]
    }
  ]
}
```

### 4. Technology Stack (tech-stack.txt)
List detected technologies:
```
Languages: Python 3.x, JavaScript
Frameworks: React, FastAPI
Package Managers: npm, pip
Build Tools: webpack, setuptools
Testing: pytest, jest
CI/CD: GitHub Actions
Containerization: Docker
```

## Analysis Instructions

1. **Scan project structure**
   - Identify all package/manifest files (package.json, pyproject.toml, go.mod, Cargo.toml, pom.xml)
   - List main entry points (main.py, index.js, cmd/main.go, etc.)
   - Detect framework indicators (e.g., React in package.json, Django in requirements.txt)

2. **Catalog modules/components**
   - For each significant directory/file, create a component entry
   - Include file path, type, and one-sentence description
   - For modules with __init__.py or index.js, treat as package

3. **Extract key exports**
   - For each component, list 2-3 most important exported functions/classes
   - Don't include full signatures, just names

4. **Classify size**
   - small: < 50 files
   - medium: 50-500 files
   - large: > 500 files

5. **Identify structure type**
   - monorepo: Contains multiple packages/ or apps/ directories
   - single-project: One cohesive application
   - library: Primarily exports reusable code

## Constraints
- Maximum 5 minutes of analysis time
- Focus on top-level structure, not deep implementation
- Include file paths for ALL component references
- Output MUST be valid JSON/Markdown as specified

## Success Criteria
- Every component has a file_path
- At least 80% of significant code modules are cataloged
- Tech stack accurately reflects major dependencies
- Entry points correctly identified

## Example Context Request
If you need to read files to determine structure, prefer:
- Package/manifest files first
- README files
- Entry point files (main.*, index.*, app.*)
- Top-level __init__.py or index.js files

Avoid reading:
- Test files (unless needed for framework detection)
- Build output directories
- node_modules, venv, vendor directories
