Generate documentation section with embedded mermaid diagrams

You are responsible for creating a complete documentation section with index, content, and compiled mermaid diagrams.

## Purpose

Create a comprehensive documentation section combining multiple component docs with visual diagrams.

**IMPORTANT**: Diagrams are REQUIRED, not optional. Every section must include at least 2 visual diagrams.

## Input

- Section metadata from `planning/documentation/toc.json`
- Component documentation files listed in section
- Diagram requirements (architecture, dependencies, flows)

## Processing

1. **Create section directory**: `docs/{section_name}/`

2. **Create shared assets directory**: `docs/assets/` (if not exists)
   - **CRITICAL**: All mermaid diagrams MUST be saved to `docs/assets/`
   - This ensures diagrams are accessible from all sections

3. **Generate section index.md** with:
   - Section overview and purpose
   - Component summaries (2-3 sentences each)
   - Table of contents with navigation links
   - Embedded diagrams using relative paths: `![Title](../assets/diagram_name.png)`
   - Related sections

4. **Create mermaid diagrams in assets directory** (REQUIRED):
   - **MINIMUM 2 diagrams per section** (architecture + flow/dependency/sequence)
   - Identify diagram opportunities (architecture, flows, dependencies)
   - Write `.mmd` source files to `docs/assets/{diagram_name}.mmd`
   - Compile to PNG using `mmdc` CLI: `mmdc -i docs/assets/diagram.mmd -o docs/assets/diagram.png -t dark -b transparent`
   - If compilation fails, use ASCII art fallback (see below)
   - Reference in markdown using: `![Diagram](../assets/diagram_name.png)`

5. **Organize content hierarchy**:
   - Main section index
   - Subsections for complex topics
   - Clear navigation between pages

## Diagram Compilation

**CRITICAL**: All diagrams must be in `docs/assets/` directory.

```bash
# Create assets directory (if not exists)
mkdir -p docs/assets

# Check if mmdc is available
if command -v mmdc &> /dev/null; then
    # Compile each diagram to assets directory
    mmdc -i docs/assets/diagram1.mmd -o docs/assets/diagram1.png -t dark -b transparent
    mmdc -i docs/assets/diagram2.mmd -o docs/assets/diagram2.png -t dark -b transparent
    echo "Diagrams compiled successfully to docs/assets/"
else
    echo "Warning: mmdc not found - diagrams will remain as .mmd source files in docs/assets/"
    echo "Install with: npm install -g @mermaid-js/mermaid-cli"
fi
```

## Output Structure

**IMPORTANT**: Diagrams are stored in shared assets directory, not in section directories.

```
docs/
  assets/                  # Shared assets directory for ALL diagrams
    architecture.mmd       # Mermaid source files
    architecture.png       # Compiled diagrams (if mmdc available)
    dependencies.mmd
    dependencies.png
  {section_name}/
    index.md               # Main section page (references ../assets/diagram.png)
```

## Diagram Types

- **Architecture diagrams**: Use `flowchart TD` for system structure
- **Dependency graphs**: Use `graph LR` for component relationships
- **Sequence diagrams**: Use `sequenceDiagram` for interactions
- **Class diagrams**: Use `classDiagram` for object models

## Error Handling and ASCII Fallbacks

- If `mmdc` compilation fails, use ASCII art fallback diagrams
- Log warning but continue pipeline
- Document in section that diagrams may require manual compilation
- Don't fail the entire documentation generation

### ASCII Art Fallback Templates

When mermaid compilation fails, use ASCII art:

**Simple Architecture**:
```
    ┌─────────┐
    │ Client  │
    └────┬────┘
         │
    ┌────▼────┐
    │   API   │
    └────┬────┘
         │
    ┌────▼────┐
    │Component│
    └─────────┘
```

**Flow Diagram**:
```
Request → Validate → Process → Store → Response
```

**Component Relationships**:
```
       ┌──────────────┐
       │     Main     │
       └──┬────────┬──┘
          │        │
     ┌────▼───┐ ┌─▼────┐
     │ Module │ │Module│
     │   A    │ │  B   │
     └────────┘ └──────┘
```

## Example Section Index

```markdown
# Architecture Overview

This section describes the core architectural patterns and design decisions.

## Components

- **Core API**: REST API layer with authentication
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Auth Service**: JWT-based authentication

## Architecture Diagram

![System Architecture](../assets/architecture.png)

## Related Sections

- [API Reference](../api_reference/index.md)
- [Components](../components/index.md)
```

**Note**: All image paths use `../assets/` to reference the shared assets directory.
