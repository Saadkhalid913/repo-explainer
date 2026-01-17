# One-Command HTML Generation Feature

## Overview

You can now generate HTML documentation immediately after repository analysis in a single command!

## Usage

### The Simple Way
```bash
repo-explain analyze . --generate-html
```

This single command will:
1. ✅ Analyze your repository with OpenCode
2. ✅ Generate markdown documentation
3. ✅ Convert markdown to HTML
4. ✅ Start HTTP server at `localhost:8080`
5. ✅ Open browser automatically
6. ⏸️ Keep server running (press Ctrl+C to stop)

### With Options
```bash
# Use custom port
repo-explain analyze . --generate-html --html-port 3000

# Don't auto-open browser
repo-explain analyze . --generate-html --no-browser

# Analyze remote repository with HTML generation
repo-explain analyze https://github.com/user/repo --generate-html

# Complete example with all options
repo-explain analyze https://github.com/user/repo \
  --depth quick \
  --generate-html \
  --html-port 9000 \
  --no-browser \
  --verbose
```

## Available Flags

When using `--generate-html` with the `analyze` command:

| Flag | Description | Default |
|------|-------------|---------|
| `--generate-html` | Generate HTML after analysis | `false` |
| `--html-port PORT` | Server port | `8080` |
| `--no-browser` | Don't auto-open browser | `false` (opens browser) |

## Example Output

```bash
$ repo-explain analyze . --generate-html
```

```
╭────────────────────────────────╮
│ Repository Explainer v0.1.0    │
│ Analyzing: repo-explainer      │
╰────────────────────────────────╯

Checking OpenCode availability... ✓

Running standard analysis...

Analysis complete!

Output saved to: docs/

📚 Coherent Documentation:
  - index.md (Start here!)
  - components/overview.md
  - dataflow/overview.md
  - dependencies/overview.md
  - tech-stack/overview.md

💡 Tip: Open `docs/index.md` to start exploring

============================================================

╭────────────────────╮
│ HTML Generation    │
│ Converting markdown│
╰────────────────────╯

🌐 Generating HTML documentation...
  Found 13 markdown file(s)
    ✓ index.md → index.html
    ✓ components/overview.md → components/overview.html
    ✓ dataflow/overview.md → dataflow/overview.html
    ✓ dependencies/overview.md → dependencies/overview.html
    ✓ dependencies/upstream.md → dependencies/upstream.html
    ✓ dependencies/downstream.md → dependencies/downstream.html
    ✓ dependencies/external.md → dependencies/external.html
    ✓ tech-stack/overview.md → tech-stack/overview.html
    ...
  Copied diagrams to HTML output
✓ Generated HTML documentation at docs/html

✓ Docs server started on http://localhost:8080/index.html

Serving documentation for: repo-explainer
Press Ctrl+C to stop the server

[Browser opens automatically to http://localhost:8080/index.html]
```

## Benefits

### Before (Two-Step Process)
```bash
# Step 1: Analyze
repo-explain analyze .
# Wait for completion...

# Step 2: Generate HTML
repo-explain generate-html
# Wait again...
```

### After (One Command)
```bash
# Single command does everything
repo-explain analyze . --generate-html
```

**Advantages:**
- ⚡ Faster workflow
- 🎯 One command to remember
- 🚀 Instant preview in browser
- ✨ Perfect for demos and presentations
- 🔄 Seamless end-to-end pipeline

## When to Use Each Approach

### Use `analyze --generate-html` when:
- ✅ Starting fresh with a new repository
- ✅ Want immediate HTML preview
- ✅ Giving presentations or demos
- ✅ Want the complete workflow in one command

### Use `generate-html` separately when:
- ✅ Already have markdown documentation
- ✅ Want to regenerate HTML without re-analysis
- ✅ Testing HTML changes
- ✅ Serving existing docs with custom options

## Technical Details

### What Happens Internally

When you run `repo-explain analyze --generate-html`:

1. **Analysis Phase** (same as before)
   - Loads repository
   - Runs OpenCode analysis
   - Generates markdown files
   - Creates diagrams

2. **HTML Generation Phase** (automatically triggered)
   - Imports `HTMLGenerator` and `DocsServer`
   - Converts all markdown to HTML
   - Copies diagrams and assets
   - Starts HTTP server
   - Opens browser (unless `--no-browser`)
   - Keeps server running

3. **Server Lifecycle**
   - Server runs in background thread
   - Listens on specified port (default 8080)
   - Serves static HTML files
   - Handles Ctrl+C gracefully

### Error Handling

If HTML generation fails:
- ✅ Analysis results are still saved
- ✅ Markdown documentation is available
- ⚠️ Error message is displayed
- ℹ️ You can still run `generate-html` separately

## Complete Workflow Examples

### Example 1: Quick Local Analysis with HTML
```bash
repo-explain analyze . --depth quick --generate-html
```

### Example 2: Deep Remote Analysis with HTML
```bash
repo-explain analyze https://github.com/torvalds/linux \
  --depth deep \
  --generate-html \
  --html-port 9000
```

### Example 3: Verbose Analysis with HTML (No Browser)
```bash
repo-explain analyze . \
  --verbose \
  --generate-html \
  --no-browser
```

Then manually open: `http://localhost:8080/index.html`

### Example 4: Force Clone with HTML
```bash
repo-explain analyze https://github.com/facebook/react \
  --force-clone \
  --generate-html
```

## Help

View all options:
```bash
repo-explain analyze --help
```

```
Options:
  --depth, -d [quick|standard|deep]  Analysis depth (default: standard)
  --output, -o PATH                  Output directory (default: docs/)
  --force-clone                      Force re-clone for Git URLs
  --generate-html                    Generate HTML and start server after analysis
  --html-port PORT                   Port for HTML server (default: 8080)
  --no-browser                       Don't open browser automatically
  --verbose, -V                      Show real-time analysis activity
  --help                            Show help message
```

## Summary

The `--generate-html` flag provides a seamless, one-command workflow for:
1. Analyzing repositories
2. Generating documentation
3. Viewing beautiful HTML in your browser

**Quick Start:**
```bash
repo-explain analyze . --generate-html
```

That's it! Your documentation is analyzed, generated, and served at `localhost:8080` 🎉
