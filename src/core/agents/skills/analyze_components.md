Analyze and identify all significant components in a repository

You are tasked with analyzing a codebase and identifying its key components, modules, and subsystems.

## Objectives

1. **Identify Components**
   - Services, modules, libraries, subsystems
   - Entry points (main files, CLI commands, API endpoints)
   - Core functionality areas
   - Utilities and helpers

2. **Extract Metadata**
   - Component name and type
   - Location (path and key files)
   - Brief description
   - Entry points and public APIs
   - Dependencies

3. **Map Relationships**
   - Dependencies between components
   - Data flow
   - Integration points

## Output

Create a file `components_discovered.json` with this structure:

```json
{
  "components": [
    {
      "id": "unique_component_id",
      "name": "Component Name",
      "type": "service|module|library|subsystem|api",
      "path": "relative/path/to/component",
      "files": ["file1.py", "file2.py"],
      "description": "Brief description",
      "entry_points": ["main", "run"],
      "public_api": ["exported_function1", "ExportedClass"],
      "dependencies": ["other_component_id"]
    }
  ],
  "metadata": {
    "total_components": 10,
    "primary_language": "Python",
    "architectural_pattern": "microservice|monolith|library"
  }
}
```

## Guidelines

- Focus on significant components (not every utility file)
- Use clear, descriptive names
- Map dependencies accurately
- Group related files into logical components
