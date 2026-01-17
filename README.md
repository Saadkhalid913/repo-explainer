# Repository Explainer

AI-powered CLI tool that analyzes software repositories and generates comprehensive documentation, architectural diagrams, and knowledge bases.

## Features

- 🔍 **Automated Analysis**: Analyze Python and JavaScript/TypeScript repositories
- 📊 **Mermaid Diagrams**: Generate architecture, component, and dataflow diagrams
- 📝 **Markdown Documentation**: Produce structured, navigable documentation
- 🤖 **AI-Powered**: Uses OpenCode, Claude CLI, or direct LLM calls for intelligent analysis
- 🌳 **Tree-sitter Parsing**: Accurate code structure extraction
- ⚡ **Multiple Depths**: Quick, standard, and deep analysis modes

## Installation

```bash
# Clone the repository
git clone https://github.com/your-org/repo-explainer.git
cd repo-explainer

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"
```

## Quick Start

```bash
# Analyze a local repository
repo-explainer analyze /path/to/your/repo

# Analyze with specific depth
repo-explainer analyze /path/to/repo --depth deep

# Analyze a remote repository
repo-explainer analyze https://github.com/user/repo

# Specify output directory
repo-explainer analyze /path/to/repo --output ./my-docs

# Update existing documentation
repo-explainer update ./my-docs
```

## Configuration

Create a `.repo-explainer.yaml` file in your working directory:

```yaml
# Analysis settings
default_depth: standard  # quick, standard, or deep
output_format: markdown  # markdown or json
output_dir: ./repo-docs

# LLM settings
llm_model: google/gemini-2.5-flash-preview

# OpenCode settings
opencode_binary: opencode
use_claude_fallback: true
```

Or set environment variables:

```bash
export REPO_EXPLAINER_OPENROUTER_API_KEY=your-api-key
export REPO_EXPLAINER_LLM_MODEL=google/gemini-2.5-flash-preview
```

## CLI Commands

### analyze

Analyze a repository and generate documentation:

```bash
repo-explainer analyze <repo-path-or-url> [OPTIONS]

Options:
  -o, --output PATH      Output directory for documentation
  -d, --depth TEXT       Analysis depth: quick, standard, deep
  -f, --format TEXT      Output format: markdown, json
  --opencode/--no-opencode  Use OpenCode for analysis
  -v, --verbose          Enable verbose output
```

### update

Update existing documentation for a previously analyzed repository:

```bash
repo-explainer update <analysis-dir> [OPTIONS]

Options:
  --incremental/--full   Only update changed components
```

### init

Initialize a configuration file:

```bash
repo-explainer init [OPTIONS]

Options:
  -o, --output PATH      Directory to create config file in
```

## Output Structure

```
repo-docs/
├── index.md                     # Main overview with TOC
├── architecture/
│   ├── overview.md              # Architecture overview
│   ├── system-architecture.md   # Detailed architecture
│   └── diagrams/
│       ├── high-level.mmd       # High-level architecture
│       ├── component-diagram.mmd
│       └── dataflow.mmd
├── components/
│   ├── component-a/
│   │   └── overview.md
│   └── component-b/
│       └── overview.md
├── dependencies/
│   └── internal.md
├── patterns/
│   └── identified-patterns.md
├── tech-stack.txt
└── metadata/
    ├── analysis-log.json
    └── config.yaml
```

## OpenCode Integration

This tool integrates with [OpenCode](https://opencode.dev) for AI-powered analysis. Custom commands are stored in `.opencode/commands/`:

- `analyze-architecture.md` - Standard architecture analysis
- `quick-scan.md` - Fast overview generation
- `standard-scan.md` - Balanced analysis
- `deep-scan.md` - Comprehensive deep dive

If OpenCode is unavailable, the tool falls back to Claude CLI or direct OpenRouter API calls.

## Supported Languages

Currently supported:
- Python (.py)
- JavaScript (.js, .jsx, .mjs, .cjs)
- TypeScript (.ts, .tsx, .mts, .cts)

## Development

```bash
# Install dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type checking
mypy src/repo_explainer

# Linting
ruff check src/repo_explainer
```

## License

MIT License - see LICENSE file for details.
