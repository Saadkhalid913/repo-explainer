# Mermaid Diagram Rendering Guide

This directory contains Mermaid diagrams for the Repository Explainer project. Each diagram can be rendered using any Mermaid-compatible tool.

## Quick Rendering Options

### Option 1: Use Online Mermaid Editor
1. Visit the Mermaid Live Editor: https://mermaid.live/
2. Copy the `.mmd` file content
3. Paste into the editor to view/render

### Option 2: Use VS Code Extension
1. Install the "Mermaid Preview" extension (`bierner.markdown-mermaid`)
2. Open any `.md` or `.mmd` file
3. Press `Cmd+Shift+V` (Mac) or `Ctrl+Shift+V` (Windows/Linux) to preview

### Option 3: Command Line (requires node.js)
```bash
# Install mermaid-cli
npm install -g @mermaid-js/mermaid-cli

# Render a specific diagram
mmdc -i backend.mmd -o backend.png
mmdc -i tui.mmd -o tui.svg

# Render all diagrams
for f in **/*.mmd; do
  mmdc -i "$f" -o "${f%.mmd}.png"
done
```

### Option 4: Docker (Optional)
```bash
# Using mermaid-cli in docker
docker run -v $(pwd):/data minlag/mermaid-cli -i /data/backend.mmd -o /data/backend.png
```

## Diagram Files

### Architecture Diagrams
- `stage_1/backend.mmd` - Phase 1 backend architecture (MVP)
- `stage_2/backend.mmd` - Phase 2 backend architecture (Enhanced)
- `stage_3/backend.mmd` - Phase 3 backend architecture (Scaling)
- `stage_4/backend.mmd` - Phase 4 backend architecture (Multi-repo)
- `stage_5/backend.mmd` - Phase 5 backend architecture (Polish)

### UI/Interaction Diagrams
- `stage_1/tui.mmd` - Phase 1 terminal UI flow
- `stage_2/tui.mmd` - Phase 2 TUI with progress tracking
- `stage_3/tui.mmd` - Phase 3 TUI with incremental updates
- `stage_4/tui.mmd` - Phase 4 TUI with multi-repo support
- `stage_5/tui.mmd` - Phase 5 TUI with full features

## Work Planning Diagrams

Work planning visualizations are available in `../work/`:
- `dependency-graph.md` - Detailed dependency graphs
- `task-breakdown.md` - Task lists and timelines
- `visualizations.md` - Comprehensive visualizations

## Automated Rendering Script

```bash
#!/bin/bash
# render-diagrams.sh - Render all .mmd files as PNG and SVG

echo "Rendering Mermaid diagrams..."

# Check if mmdc is installed
if ! command -v mmdc &> /dev/null; then
    echo "mmdc not found. Install with: npm install -g @mermaid-js/mermaid-cli"
    exit 1
fi

# Render to PNG
for stage in stage_1 stage_2 stage_3 stage_4 stage_5; do
  for diagram in backend tui; do
    input="$stage/$diagram.mmd"
    output_png="rendered/$stage/$diagram.png"
    output_svg="rendered/$stage/$diagram.svg"

    mkdir -p "rendered/$stage"

    echo "Rendering $input → $output_png"
    mmdc -i "$input" -o "$output_png" -t light -b transparent
    mmdc -i "$input" -o "$output_svg" -t light -b transparent
  done
done

echo "Done! Rendered diagrams available in 'rendered/' directory"
```

To use:
```bash
chmod +x render-diagrams.sh
./render-diagrams.sh
```

## Notes
- All diagrams use MermaidJS syntax
- Light theme recommended for documentation
- SVG format recommended for embedding in documents
- PNG format recommended for presentations/screenshots