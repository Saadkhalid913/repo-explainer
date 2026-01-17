# HTML Documentation Generation - User Guide

## Quick Start

After analyzing a repository with `repo-explain analyze`, convert the markdown documentation to beautiful HTML:

```bash
repo-explain generate-html
```

## Expected Output

When you run `repo-explain generate-html`, you'll see:

```
╭──────────────────────────────╮
│ HTML Documentation Generator │
│ Source: docs                 │
╰──────────────────────────────╯

🌐 Generating HTML documentation...
  Found 13 markdown file(s)
    ✓ index.md → index.html
    ✓ dataflow/overview.md → dataflow/overview.html
    ✓ dependencies/upstream.md → dependencies/upstream.html
    ✓ dependencies/overview.md → dependencies/overview.html
    ✓ dependencies/downstream.md → dependencies/downstream.html
    ✓ dependencies/external.md → dependencies/external.html
    ✓ components/overview.md → components/overview.html
    ✓ components/opencode-core.md → components/opencode-core.html
    ✓ components/opencode-api.md → components/opencode-api.html
    ✓ components/opencode-cli.md → components/opencode-cli.html
    ✓ tech-stack/overview.md → tech-stack/overview.html
    ✓ src/ANALYSIS_SUMMARY.md → src/ANALYSIS_SUMMARY.html
    ✓ src/raw/architecture.md → src/raw/architecture.html
  Copied diagrams to HTML output
✓ Generated HTML documentation at docs/html

✓ Docs server started on http://localhost:8080/index.html

Serving documentation for: opencode
Press Ctrl+C to stop the server
```

Then your browser automatically opens to: **http://localhost:8080/index.html**

## What You'll See in the Browser

### Beautiful Documentation Interface

The HTML documentation features:

1. **Sidebar Navigation (Left)**
   - 📚 Documentation (Home)
   - 📦 Components
   - 🔄 Data Flow  
   - 🔗 Dependencies
   - 🌐 API
   - 🛠️ Tech Stack

2. **Main Content Area (Right)**
   - Clean, readable typography
   - Syntax-highlighted code blocks
   - Embedded SVG diagrams
   - Responsive tables
   - Styled blockquotes
   - Collapsible details sections

3. **Design**
   - GitHub-inspired color scheme
   - Modern, professional look
   - Responsive (works on mobile)
   - Smooth transitions
   - Clean spacing and hierarchy

## Command Options

### Basic Usage
```bash
# Generate HTML and start server (recommended)
repo-explain generate-html

# The command auto-detects docs in these locations:
# 1. ./opencode/docs
# 2. ./docs
# 3. Current directory (if it has index.md)
```

### Specify Custom Path
```bash
# Specify exact docs location
repo-explain generate-html ./my-docs

# Analyze a specific repository's docs
repo-explain generate-html ./tmp/torvalds/linux/docs
```

### Custom Port
```bash
# Use port 3000 instead of 8080
repo-explain generate-html --port 3000

# The server will try ports 8080-8089 if the specified port is busy
```

### Generate Without Server
```bash
# Just create HTML files, don't start server
repo-explain generate-html --no-serve

# Then manually open in browser:
open docs/html/index.html
```

### Server Without Auto-Browser
```bash
# Start server but don't auto-open browser
repo-explain generate-html --no-browser

# Useful for:
# - Running on remote servers
# - CI/CD pipelines
# - When you want to open manually later
```

### Custom Output Directory
```bash
# Save HTML to a different location
repo-explain generate-html --output ./public

# Useful for deploying to web servers
```

## Complete Workflow Example

```bash
# Step 1: Analyze a repository
repo-explain analyze https://github.com/user/repo

# Step 2: Generate HTML documentation
repo-explain generate-html

# Step 3: Browser opens automatically to localhost:8080
# View your beautiful documentation!

# Step 4: Stop server when done
# Press Ctrl+C in the terminal
```

## Use Cases

### 1. Local Development Preview
```bash
# Quick way to preview docs while writing them
repo-explain generate-html
# Edit markdown files -> refresh browser to see changes
```

### 2. Team Presentations
```bash
# Start server before a meeting
repo-explain generate-html --port 8080

# Share link with team:
# "Check out the docs at localhost:8080"
```

### 3. Documentation Review
```bash
# Generate HTML for easier navigation
repo-explain generate-html --no-browser

# Open specific pages to review
open docs/html/components/overview.html
```

### 4. Static Site Deployment
```bash
# Generate HTML for web server
repo-explain generate-html --output ./public --no-serve

# Deploy public/ directory to:
# - GitHub Pages
# - Netlify
# - Vercel
# - Any static host
```

## Troubleshooting

### "Could not find documentation directory"
```bash
# Specify the path explicitly:
repo-explain generate-html ./docs

# Or make sure you're in the project root:
cd /path/to/project
repo-explain generate-html
```

### Port Already in Use
```bash
# The tool automatically tries ports 8080-8089
# Or specify a different port:
repo-explain generate-html --port 9000
```

### Want to Regenerate HTML
```bash
# Just run the command again - it overwrites existing HTML
repo-explain generate-html
```

## Tips

1. **Keep Server Running**: Leave the server running while you work on docs
2. **Refresh to See Changes**: If you edit markdown, regenerate HTML and refresh browser
3. **Use for Demos**: Great for showing documentation during presentations
4. **Deploy Static HTML**: The generated HTML works perfectly on any static host
5. **Mobile Friendly**: The responsive design works great on phones/tablets

## What Gets Generated

```
docs/html/
├── index.html              # Main landing page
├── components/             # Component documentation
│   ├── overview.html
│   └── [components].html
├── dataflow/              # Data flow documentation
│   └── overview.html
├── dependencies/          # Dependencies documentation
│   ├── overview.html
│   ├── upstream.html
│   ├── downstream.html
│   └── external.html
├── api/                   # API documentation
│   └── overview.html
├── tech-stack/           # Technology stack
│   └── overview.html
└── diagrams/             # SVG diagrams
    ├── components.svg
    └── dataflow.svg
```

## Server Details

- **Protocol**: HTTP
- **Default Port**: 8080 (with fallback to 8081-8089)
- **Threading**: Runs in background thread
- **Logging**: Silent (no request logs cluttering output)
- **Shutdown**: Graceful on Ctrl+C
- **Auto-start**: Enabled by default
- **Auto-browser**: Opens browser automatically (disable with --no-browser)

## Next Steps

1. ✅ Generate markdown docs: `repo-explain analyze`
2. ✅ Convert to HTML: `repo-explain generate-html`  
3. ✅ View in browser at `localhost:8080`
4. 🎉 Share your beautiful documentation!

---

**For more information**, see:
- `README.md` - Project overview
- `docs.md` - Complete API reference
- `repo-explain generate-html --help` - Command help
