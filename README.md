# Repository Explainer

AI-powered repository documentation generator using OpenCode. Analyze **any** repository - local or remote - and generate comprehensive architecture documentation, diagrams, and technology stack summaries.

## Features

📚 **Coherent Documentation** - Generates navigable, structured documentation with `index.md` as the entry point, organized subpages, and embedded diagrams.

✨ **Analyze Remote Repositories** - No need to clone manually! Pass a Git URL and we'll handle it.

🚀 **Multi-Depth Analysis** - Choose from quick, standard, or deep analysis modes.

📊 **Rich Diagrams** - Generates and renders Mermaid architecture and data flow diagrams as SVG.

🔄 **Smart Caching** - Cloned repositories are reused on subsequent runs.

🎨 **Beautiful CLI** - Rich terminal UI with progress indicators and colored output.

## Quick Start

### Installation

```bash
# Clone this repository
git clone https://github.com/yourusername/repo-explainer.git
cd repo-explainer

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Or install from requirements.txt
pip install -r requirements.txt
```

**Prerequisites:**
- Python 3.9+
- [OpenCode CLI](https://docs.opencode.ai) installed and in PATH
- [Mermaid CLI](https://github.com/mermaid-js/mermaid-cli) (optional, for diagram rendering): `npm install -g @mermaid-js/mermaid-cli`

**Note**: Always activate the virtual environment before running commands:
```bash
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
repo-explain analyze ./my-project
```

### Basic Usage

```bash
# Analyze a local repository
repo-explain analyze ./my-project

# Analyze a remote GitHub repository
repo-explain analyze https://github.com/torvalds/linux --depth quick

# Analyze with SSH URL (private repos)
repo-explain analyze git@github.com:myorg/private-repo.git

# Force re-clone to get latest changes
repo-explain analyze https://github.com/facebook/react --force-clone
```

**Where are results saved?**

Analysis results are saved to `./docs/` with a clean, organized structure:
```
docs/
├── index.md                     # 🎯 Start here! Main entry point
├── components/
│   └── overview.md              # Component architecture
├── dataflow/
│   └── overview.md              # Data flow visualization
├── tech-stack/
│   └── overview.md              # Technology stack
├── diagrams/
│   ├── components.svg           # Rendered component diagram
│   └── dataflow.svg             # Rendered data flow diagram
└── src/
    ├── raw/                     # OpenCode artifacts
    │   ├── architecture.md
    │   ├── components.mermaid
    │   ├── dataflow.mermaid
    │   └── tech-stack.txt
    ├── analysis_*.json
    ├── ANALYSIS_SUMMARY.md
    └── logs/
        ├── analysis_*.txt       # Raw OpenCode output
        └── metadata_*.json      # Session metadata
```

**Professional structure:**
- **Top level:** Only folders + index.md (clean, navigable)
- **Subdirectories:** Organized human-readable docs
- **src/:** All source files and technical artifacts

**Start exploring:** Open `docs/index.md` for quick navigation to all documentation sections.

You can specify a custom output directory:
```bash
repo-explain analyze ./my-project --output ./my-analysis
```

## Usage Examples

### Local Repositories

```bash
# Current directory with standard depth
repo-explain analyze .

# Specific path with quick scan
repo-explain analyze /path/to/repo --depth quick

# Deep analysis with verbose output
repo-explain analyze ./my-project --depth deep --verbose
```

### Remote Repositories (Git URLs)

```bash
# HTTPS URL
repo-explain analyze https://github.com/octocat/Hello-World

# SSH URL (requires SSH key setup)
repo-explain analyze git@github.com:user/repo.git

# With custom output directory
repo-explain analyze https://github.com/facebook/react \
  --output ./react-docs \
  --depth standard
```

**Where are remote repos cloned?**

Remote repositories are automatically cloned to `./tmp/owner/repo`:
- `https://github.com/torvalds/linux` → `./tmp/torvalds/linux`
- `git@github.com:user/repo.git` → `./tmp/user/repo`

Subsequent runs reuse the existing clone unless `--force-clone` is specified.

### Analysis Depth Options

| Depth | Speed | Description |
|-------|-------|-------------|
| `quick` | ⚡ Fast | Basic project structure, languages, and dependencies |
| `standard` | ⚙️ Moderate | Full architecture analysis with diagrams (default) |
| `deep` | 🔍 Thorough | Comprehensive analysis including patterns and optimizations |

### Command Options

```bash
repo-explain analyze [REPO_PATH_OR_URL] [OPTIONS]

Options:
  --depth, -d [quick|standard|deep]  Analysis depth (default: standard)
  --output, -o PATH                  Output directory (default: docs/)
  --force-clone                      Force re-clone for Git URLs
  --verbose, -V                      Show real-time analysis activity
  --help                            Show help message
```

**Verbose Mode** - See what's happening in real-time:
```bash
repo-explain analyze ./my-project --verbose
```

Output shows:
- 📄 Files being read
- ⚙️  Commands being executed
- ✏️  Files being written
- 🔍 Search patterns

## Configuration

Set environment variables to customize behavior:

```bash
# OpenCode binary path (if not in PATH)
export REPO_EXPLAINER_OPENCODE_BINARY=/usr/local/bin/opencode

# Default output directory
export REPO_EXPLAINER_OUTPUT_DIR=./generated-docs

# Enable verbose output by default
export REPO_EXPLAINER_VERBOSE=true

# Default analysis depth
export REPO_EXPLAINER_ANALYSIS_DEPTH=standard

# Default OpenCode model (provider/model)
export REPO_EXPLAINER_OPENCODE_MODEL=openrouter/google/gemini-3-flash-preview
```

Or create a `.env` file in your project root:

```env
REPO_EXPLAINER_OPENCODE_BINARY=opencode
REPO_EXPLAINER_OUTPUT_DIR=./docs
REPO_EXPLAINER_VERBOSE=false
```

## Testing

Run the test suite to validate installation:

```bash
bash test_cli.sh
```

Expected output:
```
==========================================
repo-explainer CLI Validation Tests
==========================================

Test 1: repo-explain --version... PASS
Test 2: repo-explain --help... PASS
...
Test 10: Force re-clone... PASS

All tests passed!
```

### Validating Coherent Documentation

After running analysis, you can validate the generated documentation structure:

```bash
python validate_coherence.py docs
```

This checks:
- ✓ `index.md` exists and has valid links
- ✓ Subpages (components.md, dataflow.md, tech-stack.md) exist
- ✓ Diagrams are rendered (SVG files in `diagrams/` directory)
- ✓ Mermaid source files are present
- ✓ Manifest file exists

## Documentation

- **[docs.md](docs.md)** - Complete API reference with examples
- **[VALIDATION.md](VALIDATION.md)** - Testing and validation guide
- **[stages/](stages/)** - Development roadmap and stage specifications

## Troubleshooting

### OpenCode Not Found

```bash
# Install OpenCode or specify path
export REPO_EXPLAINER_OPENCODE_BINARY=/path/to/opencode
repo-explain analyze .
```

### Git Clone Failures

**Private repositories:** Ensure SSH keys are set up or use authenticated HTTPS URLs.

**Network issues:** Check internet connection and firewall settings.

**Clean up clones:**
```bash
# Remove specific repo
rm -rf tmp/owner/repo

# Remove all clones
rm -rf tmp/
```

### Mermaid CLI Not Found

Diagram rendering requires the Mermaid CLI. If you see warnings about `mmdc` not being found:

```bash
# Install Mermaid CLI globally
npm install -g @mermaid-js/mermaid-cli

# Verify installation
mmdc --version
```

**Note:** Documentation will still be generated without Mermaid CLI, but diagrams won't be rendered to SVG. You can manually render them later or view the `.mermaid` source files.

### Mermaid Syntax Errors

The tool automatically attempts to fix Mermaid syntax errors using OpenCode:

```bash
📚 Composing coherent documentation...
  Rendering 2 diagram(s)...
    ⚠ Syntax error in dataflow.mermaid, attempting auto-fix (attempt 1/2)...
    ✓ Fixed syntax in dataflow.mermaid
    ✓ Rendered: dataflow.mermaid → dataflow.svg (after 1 fix(es))
  ✓ 2 diagram(s) rendered successfully
```

**Auto-Fix Feature:**
- Detects Mermaid rendering failures automatically
- Uses OpenCode to analyze and fix syntax errors
- Retries rendering up to 2 times
- Shows progress: "attempting auto-fix (attempt X/2)"
- Continues gracefully if auto-fix fails

**If auto-fix fails:**
- Documentation is still fully generated
- Failed diagrams show helpful notes in subpages
- Source files available in `docs/src/raw/*.mermaid`
- Can manually fix: `mmdc -i docs/src/raw/diagram.mermaid -o docs/diagrams/diagram.svg`

## Project Structure

```
repo-explainer/
├── src/repo_explainer/
│   ├── cli.py                 # CLI entry point
│   ├── config.py              # Configuration management
│   ├── opencode_service.py    # OpenCode integration
│   └── repository_loader.py   # Git clone handling
├── stages/                    # Development stages
├── docs.md                    # API documentation
├── VALIDATION.md             # Testing guide
├── test_cli.sh               # Test suite
└── README.md                 # This file
```

## Roadmap

- **Stage 1** (Current): MVP with CLI, OpenCode integration, and Git URL support ✅
- **Stage 2**: Pattern detection, dependency mapping, richer diagrams
- **Stage 3**: Incremental analysis, caching, parallel execution
- **Stage 4**: Multi-repository analysis
- **Stage 5**: Interactive HTML output, IDE integrations

See [stages/](stages/) for detailed specifications.

## Contributing

See [.claude.md](.claude.md) for development guidelines.

When making changes:
1. Update `docs.md` immediately for API changes
2. Update relevant checklist in `stages/stage_*.md`
3. Run `bash test_cli.sh` to validate
4. Commit with clear description

## License

MIT
