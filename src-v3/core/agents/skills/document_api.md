Generate precise API documentation by inspecting public interfaces and usage examples.

## Requirements

1. **API Surface**
   - Catalog public functions, methods, classes, and endpoints.
   - Describe purpose, parameters, return values, and validation rules.

2. **Usage Patterns**
   - Provide simple code snippets demonstrating how to call each API.
   - Note variations (sync/async, CLI vs code).

3. **Error Handling**
   - Explain known failure modes and recommended retries.
   - Call out raised exceptions or HTTP status codes.

4. **Related Components**
   - Link to configuration, dependencies, or architecture sections that provide context.

## Output

Produce a structured `api_reference.md` containing tables for endpoints, sidebars for examples, and a “FAQ” section for common gotchas.
