Generate a complete documentation structure as a JSON file for consistent navigation and cross-linking.

# Documentation Structure Planning

This skill generates `planning/doc_tree.json` which defines the complete documentation structure before any documentation is written.

## Purpose

The doc tree ensures:
1. All documentation files have consistent, pre-defined titles and headings
2. Cross-links between components are valid (paths are known upfront)
3. Navigation sidebar shows clean titles (not code snippets or descriptions)
4. All documentation agents receive the same structural context

## Output Schema

Write to `planning/doc_tree.json`:

```json
{
  "repository": "repo-name",
  "title": "Repository Name Documentation",
  "generated_at": "2024-01-15T10:30:00Z",
  "structure": {
    "index.md": {
      "title": "Home",
      "heading": "Repository Name Documentation",
      "description": "Main documentation landing page",
      "nav_order": 1
    },
    "components/": {
      "index.md": {
        "title": "Components",
        "heading": "Component Overview",
        "description": "Overview of all system components",
        "nav_order": 1
      },
      "component-name/": {
        "index.md": {
          "title": "Component Name",
          "heading": "Component Name",
          "description": "Brief description of what this component does",
          "nav_order": 1
        },
        "architecture.md": {
          "title": "Architecture",
          "heading": "Component Name Architecture",
          "description": "Internal architecture and design patterns",
          "nav_order": 2
        },
        "api_reference.md": {
          "title": "API Reference",
          "heading": "Component Name API Reference",
          "description": "API endpoints and interfaces",
          "nav_order": 3
        }
      }
    }
  }
}
```

## Field Definitions

### Required Fields for Every File

| Field | Type | Description |
|-------|------|-------------|
| `title` | string | Short name for navigation sidebar (max 25 chars) |
| `heading` | string | Full H1 heading for the page (what appears at top) |
| `nav_order` | integer | Position in navigation (1-based) |

### Optional Fields

| Field | Type | Description |
|-------|------|-------------|
| `description` | string | Brief description (for index pages, tooltips) |
| `cross_links` | array | List of related file paths for cross-referencing |

## Rules

1. **Title vs Heading**
   - `title`: Concise sidebar label (e.g., "WebSearch Tool")
   - `heading`: Page H1 header (e.g., "WebSearch Tool" or "WebSearch Tool Documentation")
   - Never use code, paths, or sentences as titles

2. **Path Conventions**
   - Component directories: kebab-case (e.g., `websearch-tool/`, `api-gateway/`)
   - Standard files: `index.md`, `architecture.md`, `api_reference.md`, `configuration.md`
   - Each directory must have `index.md` as entry point

3. **Navigation Order**
   - `nav_order: 1` = first in list
   - Group related items with consecutive numbers
   - Index pages should be `nav_order: 1` in their directory

4. **Naming Guidelines**
   - NO code snippets as titles (bad: "Assuming you have custom config...")
   - NO file paths as titles (bad: "src/api/handlers")
   - NO descriptions as titles (bad: "This component handles...")
   - YES clear noun phrases (good: "API Gateway", "Authentication", "Configuration")

## Process

1. Read `planning/overview.md` to understand repository structure
2. Read `planning/component_manifest.md` to get component list
3. Generate logical navigation structure based on component relationships
4. Assign clear, consistent titles/headings to all files
5. Write `planning/doc_tree.json`

## Example Structure Generation

For a repository with components: api-gateway, auth-service, database

```json
{
  "repository": "my-service",
  "title": "My Service Documentation",
  "structure": {
    "index.md": {
      "title": "Home",
      "heading": "My Service Documentation",
      "nav_order": 1
    },
    "components/": {
      "index.md": {
        "title": "Components",
        "heading": "System Components",
        "nav_order": 1
      },
      "api-gateway/": {
        "index.md": {
          "title": "API Gateway",
          "heading": "API Gateway",
          "nav_order": 1
        },
        "architecture.md": {
          "title": "Architecture",
          "heading": "API Gateway Architecture",
          "nav_order": 2
        }
      },
      "auth-service/": {
        "index.md": {
          "title": "Authentication",
          "heading": "Authentication Service",
          "nav_order": 2
        }
      },
      "database/": {
        "index.md": {
          "title": "Database",
          "heading": "Database Layer",
          "nav_order": 3
        }
      }
    }
  }
}
```

## Validation

The generated doc_tree.json should:
- Have valid JSON syntax
- Have a `title` and `heading` for every `.md` file
- Have `nav_order` as positive integers
- Use kebab-case for all directory names
- Have `index.md` in every directory that contains other files
