# HTML Documentation Example

This file demonstrates the output of the `generate-html` command.

## Running the Command

```bash
repo-explain generate-html
```

## Expected Output

```
╭──────────────────────────────╮
│ HTML Documentation Generator │
│ Source: docs                 │
╰──────────────────────────────╯

🌐 Generating HTML documentation...
  Found 13 markdown file(s)
    ✓ index.md → index.html
    ✓ components/overview.md → components/overview.html
    ✓ dataflow/overview.md → dataflow/overview.html
    ✓ dependencies/overview.md → dependencies/overview.html
    ✓ tech-stack/overview.md → tech-stack/overview.html
    ...
  Copied diagrams to HTML output
✓ Generated HTML documentation at docs/html

✓ Docs server started on http://localhost:8080/index.html

Serving documentation for: opencode
Press Ctrl+C to stop the server
```

## What You Get

### Beautiful HTML UI
- **Modern Design**: Clean, GitHub-inspired interface
- **Sidebar Navigation**: Easy access to all sections
- **Responsive Layout**: Works on desktop and mobile
- **Syntax Highlighting**: Code blocks with proper highlighting
- **Embedded Diagrams**: SVG diagrams displayed inline

### Generated Files
```
docs/html/
├── index.html                      # Main landing page
├── components/
│   ├── overview.html
│   ├── opencode-api.html
│   ├── opencode-cli.html
│   └── opencode-core.html
├── dataflow/
│   └── overview.html
├── dependencies/
│   ├── overview.html
│   ├── upstream.html
│   ├── downstream.html
│   └── external.html
├── api/
│   └── overview.html
├── tech-stack/
│   └── overview.html
└── diagrams/
    ├── components.svg
    └── dataflow.svg
```

### Server Features
- **Auto-start**: Server starts automatically by default
- **Auto-open**: Opens browser to documentation
- **Port Selection**: Uses 8080-8089 (finds available port)
- **Graceful Shutdown**: Ctrl+C to stop cleanly

## Command Options

### Basic Usage
```bash
# Generate HTML and start server
repo-explain generate-html

# Specify docs directory
repo-explain generate-html ./opencode/docs

# Use custom port
repo-explain generate-html --port 3000

# Generate without serving
repo-explain generate-html --no-serve

# Don't auto-open browser
repo-explain generate-html --no-browser
```

## Live Demo

After running `repo-explain generate-html`, navigate to:

**http://localhost:8080/index.html**

You'll see:
1. **Sidebar** with navigation links (Home, Components, Data Flow, etc.)
2. **Main content area** with your documentation
3. **Embedded diagrams** from the SVG files
4. **Clean styling** with proper typography and code highlighting

## Use Cases

1. **Local Preview**: View docs in browser with proper styling
2. **Team Demos**: Share localhost link during meetings
3. **Review Process**: Navigate documentation easily
4. **Static Export**: Deploy HTML to any web server

## Technical Details

### Markdown Processing
- Uses Python `markdown` library with extensions
- Converts `.md` links to `.html` automatically
- Preserves code blocks with syntax highlighting
- Handles tables, lists, blockquotes, etc.

### CSS Framework
- GitHub-inspired design system
- Responsive breakpoints for mobile
- Custom syntax highlighting
- Sticky sidebar navigation

### Server Implementation
- Built on Python's `http.server`
- Runs in background thread
- Silent request logging
- Automatic port fallback (8080-8089)
