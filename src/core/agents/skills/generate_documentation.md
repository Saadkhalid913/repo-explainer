Generate comprehensive markdown documentation for specified components

Create detailed markdown documentation for the given components, including architecture diagrams, API references, and usage examples.

## Requirements

1. **Component Documentation**
   - Overview and purpose
   - Architecture and design
   - Key functions and classes
   - Dependencies and relationships

2. **Code Examples**
   - Basic usage patterns
   - Common scenarios
   - Advanced patterns
   - Error handling

3. **API Reference**
   - Function signatures
   - Parameter descriptions
   - Return values
   - Examples

4. **Diagrams**
   - Architecture diagrams (Mermaid)
   - Data flow diagrams
   - Sequence diagrams (if applicable)

## Output Structure

```
repo_explainer_artifacts/
├── manifest.json
├── documentation/
│   ├── [component-name].md
│   └── overview.md
├── diagrams/
│   ├── architecture.mermaid
│   └── dataflow.mermaid
└── examples/
    ├── basic-usage.md
    └── advanced-patterns.md
```

## Manifest Format

```json
{
  "artifacts": [
    {
      "id": "unique-id",
      "name": "Human readable name",
      "type": "markdown|mermaid|code",
      "file_path": "relative/path/to/file.md",
      "component_ids": ["comp1", "comp2"]
    }
  ],
  "metadata": {
    "generated_at": "2026-01-21T10:00:00",
    "components_documented": 5
  }
}
```

## Guidelines

- Be comprehensive and accurate
- Use real code examples from the repository
- Cross-reference related components
- Follow markdown best practices
- Create valid Mermaid syntax
