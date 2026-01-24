Generate main documentation index aggregating all sections

You are responsible for creating the main entry point for documentation (`docs/index.md`) that links to all sections and provides navigation.

## Purpose

Create the main documentation index that ties everything together and provides a clear entry point for readers.

## Input

- All section index files: `docs/*/index.md`
- Section metadata from `planning/documentation/toc.json`
- Repository overview from `planning/overview.md`

## Processing

1. **Read all section titles and descriptions**:
   - Parse section index files
   - Extract titles, descriptions, key topics
   - Identify most important sections

2. **Create hierarchical navigation structure**:
   - Group sections by category
   - Order by priority/importance
   - Create clear hierarchy (main sections → subsections)

3. **Generate quick start guide**:
   - Link to most important sections
   - Provide common entry points
   - Add "Getting Started" recommendations

4. **Add search/navigation helpers**:
   - Table of contents with anchors
   - Cross-references between sections
   - External links (repo, issues, etc.)

5. **Include repository overview summary**:
   - Brief description of the repository
   - Key features and capabilities
   - Technology stack summary

## Output

Generate `docs/index.md`:

```markdown
# {Repository Name} Documentation

## Overview

{Brief 2-3 paragraph description of the repository, its purpose, and key capabilities}

**Key Features:**
- Feature 1
- Feature 2
- Feature 3

**Tech Stack:** Python, FastAPI, PostgreSQL, Redis

## Quick Start

New to this project? Start here:

1. [Architecture Overview](architecture/index.md) - Understand the system design
2. [Getting Started Guide](getting_started/index.md) - Set up your development environment
3. [API Reference](api_reference/index.md) - Explore available endpoints

## Documentation Structure

### Core Documentation

#### [Architecture](architecture/index.md)
Core architectural patterns, design decisions, and system structure.

#### [Components](components/index.md)
Detailed documentation for all major components and modules.

#### [API Reference](api_reference/index.md)
Complete API documentation including endpoints, request/response formats, and authentication.

### Developer Guides

#### [Development Setup](development/index.md)
Environment setup, build instructions, and development workflows.

#### [Testing](testing/index.md)
Testing strategy, running tests, and writing new tests.

#### [Deployment](deployment/index.md)
Deployment procedures, configuration, and operations.

### Additional Resources

#### [Troubleshooting](troubleshooting/index.md)
Common issues and solutions.

#### [FAQ](faq/index.md)
Frequently asked questions.

## Contributing

See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines on contributing to this project.

## License

See [LICENSE](../LICENSE) for license information.

## Support

- **Issues**: [GitHub Issues](https://github.com/org/repo/issues)
- **Discussions**: [GitHub Discussions](https://github.com/org/repo/discussions)
- **Documentation**: This site

---

*Documentation generated on {date}*
```

## Guidelines

- **Clear structure**: Logical organization that matches user mental models
- **Scannable**: Use headings, lists, and formatting for easy scanning
- **Action-oriented**: Guide users to what they need ("Start here", "See X for Y")
- **Comprehensive**: Link to ALL sections, no orphaned documentation
- **Contextual**: Brief descriptions help users decide what to read
- **Navigation**: Make it easy to find specific information
- **Welcoming**: Friendly tone that invites exploration
- **Up-to-date**: Include generation date and maintenance notes
