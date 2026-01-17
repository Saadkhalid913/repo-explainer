# Stage 1 Validation Guide

**Status**: ✅ Complete and Tested
**Date**: 2025-01-17
**Latest Update**: Git URL Support Added

## Quick Start

### Installation
```bash
pip install -e .
```

### Test the CLI

**Local repositories:**
```bash
# Basic tests
repo-explain --version
repo-explain --help
repo-explain analyze --help

# Run quick analysis on current directory
repo-explain analyze . --depth quick

# Run with verbose output
repo-explain analyze . --depth quick --verbose
```

**Remote repositories (Git URLs):**
```bash
# Analyze a remote GitHub repository
repo-explain analyze https://github.com/octocat/Hello-World --depth quick

# Check clone location
ls -la tmp/octocat/Hello-World/

# Analyze again (reuses existing clone)
repo-explain analyze https://github.com/octocat/Hello-World --depth quick

# Force fresh clone
repo-explain analyze https://github.com/octocat/Hello-World --force-clone --depth quick
```

## Comprehensive Test Suite

Run all validation tests:
```bash
bash test_cli.sh
```

**Expected Output:**
```
==========================================
repo-explainer CLI Validation Tests
==========================================

Test 1: repo-explain --version... PASS
Test 2: repo-explain --help... PASS
Test 3: repo-explain analyze --help... PASS
Test 4: repo-explain update --help... PASS
Test 5: repo-explain analyze /nonexistent (should fail)... PASS
Test 6: OpenCode quick analysis (may take 30-60s)... PASS
Test 7: Custom output directory... PASS
Test 8: Git URL cloning (may take 30-60s)... PASS
Test 9: Clone reuse... PASS
Test 10: Force re-clone... PASS

==========================================
Test Summary
==========================================
Total Tests: 10
Passed: 10
Failed: 0

All tests passed!
```

## What Was Built

### Core Components

1. **CLI Module** (`src/repo_explainer/cli.py`)
   - Typer-based command-line interface
   - `analyze` command with depth modes (quick/standard/deep)
   - **Git URL support** - accepts both local paths and Git URLs
   - `--force-clone` flag for re-cloning repositories
   - `update` command (placeholder for Stage 3)
   - Rich terminal UI with progress spinners and panels
   - Version and help command support

2. **Repository Loader** (`src/repo_explainer/repository_loader.py`) **NEW**
   - Git URL detection (HTTPS, SSH, Git protocol)
   - URL parsing to extract owner/repo from any Git host
   - Automatic cloning to `./tmp/owner/repo`
   - Clone reuse - existing clones are reused automatically
   - Force re-clone support with `--force-clone`
   - GitPython integration with shallow clones (depth=1)
   - Cleanup utilities for managing cloned repositories

3. **Configuration** (`src/repo_explainer/config.py`)
   - Pydantic-settings for configuration management
   - Environment variable support (REPO_EXPLAINER_*)
   - Customizable output directories
   - Global settings singleton pattern

4. **OpenCode Service** (`src/repo_explainer/opencode_service.py`)
   - Subprocess wrapper for OpenCode CLI
   - Correct command syntax: `opencode run <prompt> --format json`
   - JSON output parsing
   - Session ID and artifact extraction
   - Availability checking
   - Error handling with timeout support

### Documentation

1. **API Documentation** (`docs.md`)
   - Complete CLI command reference
   - Configuration environment variables
   - Service class documentation with examples
   - Testing and troubleshooting guide
   - Common issues and solutions

2. **Development Guidelines** (`.claude.md`)
   - Commitment to API documentation
   - Documentation update requirements
   - Development process guidelines
   - Testing guidelines
   - Change tracking

3. **Test Suite** (`test_cli.sh`)
   - 10 comprehensive validation tests
   - Tests 1-7: Core CLI functionality
   - Test 8: Git URL cloning
   - Test 9: Clone reuse verification
   - Test 10: Force re-clone functionality
   - Version and help verification
   - Command parsing validation
   - OpenCode integration test
   - Custom output directory test
   - Error handling tests

### Project Files

- `pyproject.toml` - Package configuration with all dependencies
- `README.md` - Quick start guide
- `.gitignore` - Standard Python project ignores
- `test_cli.sh` - Automated CLI validation

## Validation Results

### ✅ Tests Passing

1. **CLI Help System**
   - Version display works correctly
   - All commands have help text
   - Options display properly

2. **Command Structure**
   - `repo-explain analyze` accepts both local paths and Git URLs
   - `--depth` option accepts quick/standard/deep
   - `--output` option accepts custom paths
   - `--force-clone` flag works correctly
   - `--verbose` flag enables detailed output

3. **Git URL Support** ⭐ NEW
   - Git URLs are detected correctly (HTTPS, SSH, Git protocol)
   - Repositories are cloned to `./tmp/owner/repo` structure
   - Existing clones are reused automatically
   - Force re-clone removes and re-clones successfully
   - Works with GitHub, GitLab, and other Git hosts

4. **OpenCode Integration**
   - CLI successfully invokes OpenCode
   - JSON output is parsed correctly
   - Session IDs are extracted
   - Error handling works gracefully

5. **Configuration**
   - Environment variables are respected
   - Custom output directories are created
   - Verbose mode shows detailed information

6. **Error Handling**
   - Invalid repository paths are rejected
   - Invalid Git URLs are caught with helpful messages
   - Missing OpenCode is reported clearly
   - Clone failures show descriptive errors

## Usage Examples

### Example 1: Quick Project Scan (Local)
```bash
repo-explain analyze ./my-project --depth quick
```

### Example 2: Full Analysis with Verbose Output (Local)
```bash
repo-explain analyze ./my-project --depth standard --verbose
```

### Example 3: Custom Output Directory (Local)
```bash
repo-explain analyze ./my-project --output ./project-docs
```

### Example 4: Remote Repository Analysis (Git URL)
```bash
# Clone and analyze a GitHub repository
repo-explain analyze https://github.com/octocat/Hello-World --depth quick

# Output shows:
# Cloning repository: https://github.com/octocat/Hello-World
# Destination: tmp/octocat/Hello-World
# Clone successful!
# ...
# Analysis complete!
```

### Example 5: Clone Reuse (Git URL)
```bash
# First run clones the repository
repo-explain analyze https://github.com/facebook/react --depth quick

# Second run reuses existing clone
repo-explain analyze https://github.com/facebook/react --depth quick
# Output: "Using existing clone: tmp/facebook/react"
```

### Example 6: Force Re-clone (Git URL)
```bash
# Force re-clone to get latest changes
repo-explain analyze https://github.com/torvalds/linux \
  --force-clone \
  --depth standard \
  --verbose

# Output shows:
# Removing existing clone: tmp/torvalds/linux
# Cloning repository: https://github.com/torvalds/linux
# ...
```

### Example 7: Private Repository with SSH (Git URL)
```bash
# Analyze private repository (requires SSH keys)
repo-explain analyze git@github.com:myorg/private-repo.git --depth standard
```

### Example 8: Environment Configuration
```bash
export REPO_EXPLAINER_VERBOSE=true
export REPO_EXPLAINER_OUTPUT_DIR=./generated-docs
repo-explain analyze https://github.com/user/repo
```

## Next Steps

From the Stage 1 checklist, the following items are still pending:

### High Priority
- [ ] Logging configuration
- [x] **Repository loader with Git clone** ✅ COMPLETE
- [ ] Analyzer with prompt preparation
- [ ] Documentation generator for markdown output
- [ ] Diagram generator integration

### Medium Priority
- [ ] Tree-sitter/AST integration
- [ ] Python and JavaScript/TypeScript language support
- [ ] Custom OpenCode command support (`.opencode/commands/*.md`)
- [ ] Claude Code fallback integration

### Recently Completed
- [x] Git URL support (HTTPS, SSH, Git protocol)
- [x] Automatic cloning to `./tmp/owner/repo`
- [x] Clone reuse mechanism
- [x] Force re-clone with `--force-clone` flag
- [x] RepositoryLoader service with full API

### See Also
- Check `stages/stage_1.md` for complete implementation checklist
- Review `docs.md` for API documentation
- See `.claude.md` for development guidelines

## Troubleshooting

### OpenCode Not Found
```bash
export REPO_EXPLAINER_OPENCODE_BINARY=/path/to/opencode
repo-explain analyze .
```

### Git Clone Failures

**Invalid Git URL:**
```
Error loading repository: Cannot extract owner/repo from Git URL
```
Solution: Verify URL format (https://, git@, ssh://, git://)

**Authentication Required (Private Repos):**
```bash
# Use SSH with configured keys
repo-explain analyze git@github.com:myorg/private-repo.git

# Or configure Git credentials
git config --global credential.helper store
```

**Network Issues:**
- Check internet connection
- Verify firewall allows Git protocol
- Try manual clone: `git clone <url>`

**Clean Up Failed Clones:**
```bash
# Remove specific repo
rm -rf tmp/owner/repo

# Remove all clones
rm -rf tmp/
```

### Debug Mode
```bash
# Local repository
repo-explain analyze . --verbose

# Remote repository with verbose output
repo-explain analyze https://github.com/user/repo --verbose
```

### Check Installation
```bash
pip show repo-explainer

# Verify OpenCode is installed
opencode --version

# Verify Git is installed
git --version
```

## Files Modified/Created

```
.
├── .claude.md                         # New: Development guidelines + Git URL changelog
├── .gitignore                         # Updated: Added tmp/ directory
├── README.md                          # Updated: Comprehensive with Git URL examples
├── docs.md                            # Updated: Complete API docs + RepositoryLoader
├── pyproject.toml                     # New: Package config
├── test_cli.sh                        # Updated: 10 tests (added Git URL tests)
├── VALIDATION.md                      # Updated: This file with Git URL testing
├── src/repo_explainer/
│   ├── __init__.py                    # New: Package init
│   ├── cli.py                         # Updated: Git URL support integration
│   ├── config.py                      # New: Configuration
│   ├── opencode_service.py            # New: OpenCode integration
│   └── repository_loader.py           # New: Git clone and URL handling ⭐
└── stages/
    └── stage_1.md                     # Updated: Repository Loader checklist complete
```

### Key Additions

**repository_loader.py** - New service with:
- Git URL detection and parsing
- Automatic cloning to `./tmp/owner/repo`
- Clone reuse mechanism
- Force re-clone support
- Cleanup utilities

---

**For more information, see `docs.md` and `.claude.md`**
