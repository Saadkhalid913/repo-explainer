#!/usr/bin/env python3
"""
Extract mermaid diagrams from markdown files and render them.
"""
import re
import os
import subprocess
from pathlib import Path

def extract_diagrams(filepath):
    """Extract mermaid code blocks from a file."""
    with open(filepath, 'r') as f:
        content = f.read()
    
    pattern = r'```mermaid\n(.*?)```'
    matches = re.findall(pattern, content, re.DOTALL)
    return matches

def get_diagram_title(diagram):
    """Extract title from diagram if present."""
    lines = diagram.strip().split('\n')
    for line in lines:
        if line.strip().startswith('title'):
            return line.split('title')[1].strip()
    return None

def render_diagram(input_path, output_path):
    """Render a mermaid diagram using mmdc."""
    if not os.path.exists(input_path):
        print(f"Input file not found: {input_path}")
        return False
    
    try:
        # Render as PNG
        result_png = subprocess.run(
            ['mmdc', '-i', input_path, '-o', output_path + '.png', '-t', 'default', '-b', 'transparent'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Render as SVG
        result_svg = subprocess.run(
            ['mmdc', '-i', input_path, '-o', output_path + '.svg', '-t', 'default', '-b', 'transparent'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result_png.returncode == 0 and result_svg.returncode == 0:
            return True
        else:
            print(f"Error rendering {input_path}")
            print(f"PNG error: {result_png.stderr}")
            print(f"SVG error: {result_svg.stderr}")
            return False
    except subprocess.TimeoutExpired:
        print(f"Timeout rendering {input_path}")
        return False
    except Exception as e:
        print(f"Exception rendering {input_path}: {e}")
        return False

def main():
    base_dir = Path('/Users/saadkhalid/Projects/repo-explainer/work')
    rendered_dir = base_dir / 'rendered'
    rendered_dir.mkdir(exist_ok=True)
    
    files_to_process = [
        'dependency-graph.md',
        'visualizations.md'
    ]
    
    total_diagrams = 0
    success_count = 0
    
    for filename in files_to_process:
        filepath = base_dir / filename
        
        if not filepath.exists():
            print(f"Skipping {filename}: not found")
            continue
        
        print(f"\nProcessing {filename}...")
        diagrams = extract_diagrams(filepath)
        print(f"  Found {len(diagrams)} diagrams")
        
        for i, diagram in enumerate(diagrams):
            total_diagrams += 1
            title = get_diagram_title(diagram) or f'diagram{i+1}'
            
            # Sanitize title for filename
            safe_title = re.sub(r'[^\w\s-]', '', title).strip().replace(' ', '-').lower()[:50]
            safe_title = re.sub(r'-+', '-', safe_title)
            
            # Create output filename
            output_base = rendered_dir / f'{filename.replace(".md", "")}-{i+1:02d}-{safe_title}'
            
            # Write temporary .mmd file
            temp_mmd = rendered_dir / f'{output_base.name}.mmd'
            with open(temp_mmd, 'w') as f:
                f.write(diagram.strip())
                f.write('\n')
            
            # Render
            
            print(f"  Rendering {i+1}/{len(diagrams)}: {title}")
            if render_diagram(temp_mmd, str(output_base)):
                success_count += 1
                print(f"    ✓ Saved as {output_base.name}.png/.svg")
                # Remove temp file
                temp_mmd.unlink()
            else:
                print(f"    ✗ Failed to render")
                # Keep temp file for debugging
                print(f"    Saved raw diagram to: {temp_mmd}")
    
    print(f"\n{'='*60}")
    print(f"Rendered {success_count}/{total_diagrams} diagrams successfully")
    print(f"Output directory: {rendered_dir}")
    print(f"{'='*60}")

if __name__ == '__main__':
    main()