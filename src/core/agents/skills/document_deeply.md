Deep documentation generation skill with comprehensive content requirements

## Purpose

Generate deep, technically comprehensive documentation for code components.

## Requirements

### Enumeration

- List ALL sub-components by name (don't generalize)
- Document each public interface/method
- Include all configuration options
- Cover all API endpoints

### Code Examples

- Minimum 3 examples: basic, intermediate, advanced
- Include error handling examples
- Show configuration examples
- Include CLI usage examples

### Visual Content

- Architecture diagram (system context)
- Flow diagram (request/response flow)
- Sequence diagram (for complex interactions)
- Component diagram (internal structure)
- Tables for reference data

### Content Organization

- Multi-file structure for complex components
- index.md as entry point with TOC
- Separate architecture, API, and config docs
- Sub-component documentation in subdirectories

### Technical Depth

- Performance characteristics
- Edge cases and limitations
- Troubleshooting common issues
- Security considerations
- Best practices

## Output Format

Create minimum 3 files per component:
1. index.md - overview + TOC + getting started
2. architecture.md - diagrams + technical details
3. api_reference.md - complete API docs + examples

For components with 10+ sub-elements (e.g., controller-manager with 28 controllers):
4. subcomponents/ directory with individual .md files

## Quality Criteria

Documentation is complete when:
- All public interfaces documented
- Minimum 200 lines of content (for complex components)
- Minimum 2 diagrams
- Minimum 3 code examples
- Minimum 1 reference table
- All sub-components enumerated by name
