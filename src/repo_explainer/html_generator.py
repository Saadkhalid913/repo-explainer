"""HTML generation and serving for documentation."""

import http.server
import socketserver
import threading
import webbrowser
from pathlib import Path
from typing import Optional
import markdown
from rich.console import Console

console = Console()


class HTMLGenerator:
    """Generates HTML from markdown documentation."""

    def __init__(self, docs_dir: Path, output_dir: Optional[Path] = None):
        """
        Initialize the HTML generator.

        Args:
            docs_dir: Directory containing markdown documentation
            output_dir: Directory to output HTML files (defaults to docs_dir/html)
        """
        self.docs_dir = docs_dir
        self.output_dir = output_dir or (docs_dir / "html")
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def generate(self) -> Path:
        """
        Convert all markdown files to HTML with navigation and styling.

        Returns:
            Path to the HTML output directory
        """
        console.print("\n[bold cyan]🌐 Generating HTML documentation...[/bold cyan]")

        # Find all markdown files
        md_files = list(self.docs_dir.rglob("*.md"))
        
        if not md_files:
            console.print("[yellow]No markdown files found to convert[/yellow]")
            return self.output_dir

        console.print(f"[dim]  Found {len(md_files)} markdown file(s)[/dim]")

        # Configure markdown extensions
        md = markdown.Markdown(
            extensions=[
                'extra',          # Tables, fenced code, etc.
                'codehilite',     # Syntax highlighting
                'toc',            # Table of contents
                'sane_lists',     # Better list handling
                'nl2br',          # Newline to <br>
            ],
            extension_configs={
                'codehilite': {
                    'css_class': 'highlight',
                    'linenums': False,
                }
            }
        )

        # Generate HTML for each markdown file
        for md_file in md_files:
            self._convert_file(md_file, md)

        # Copy static assets (diagrams, etc.)
        self._copy_assets()

        # Generate navigation index
        self._generate_navigation()

        console.print(f"[green]✓[/green] Generated HTML documentation at [cyan]{self.output_dir}[/cyan]")
        return self.output_dir

    def _convert_file(self, md_file: Path, md: markdown.Markdown) -> None:
        """Convert a single markdown file to HTML."""
        try:
            # Read markdown content
            md_content = md_file.read_text()

            # Convert to HTML
            html_body = md.convert(md_content)
            md.reset()  # Reset for next file

            # Get relative path from docs_dir
            rel_path = md_file.relative_to(self.docs_dir)
            html_file = self.output_dir / rel_path.with_suffix('.html')
            html_file.parent.mkdir(parents=True, exist_ok=True)

            # Calculate relative path to root for navigation
            depth = len(rel_path.parts) - 1
            root_path = "../" * depth if depth > 0 else "./"

            # Generate full HTML page
            html_page = self._generate_page(
                title=self._get_title(md_content, md_file.stem),
                body=html_body,
                root_path=root_path,
                current_file=str(rel_path),
            )

            html_file.write_text(html_page)
            console.print(f"[dim]    ✓ {rel_path} → {rel_path.with_suffix('.html')}[/dim]")

        except Exception as e:
            console.print(f"[yellow]    ⚠ Failed to convert {md_file.name}: {e}[/yellow]")

    def _get_title(self, content: str, fallback: str) -> str:
        """Extract title from markdown content or use fallback."""
        lines = content.split('\n')
        for line in lines:
            if line.startswith('# '):
                return line[2:].strip()
        return fallback.replace('-', ' ').title()

    def _generate_page(self, title: str, body: str, root_path: str, current_file: str) -> str:
        """Generate a complete HTML page with styling and navigation."""
        # Fix relative links in body (convert .md to .html)
        import re
        body = re.sub(r'href="([^"]+)\.md"', r'href="\1.html"', body)
        body = re.sub(r'\]\(([^)]+)\.md\)', r'](\1.html)', body)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Repository Documentation</title>
    <style>
        {self._get_css()}
    </style>
</head>
<body>
    <div class="container">
        <nav class="sidebar">
            <div class="nav-header">
                <a href="{root_path}index.html" class="logo">📚 Documentation</a>
            </div>
            <div class="nav-links">
                <a href="{root_path}index.html" class="nav-item {'active' if current_file == 'index.md' else ''}">
                    🏠 Home
                </a>
                <a href="{root_path}components/overview.html" class="nav-item {'active' if 'components' in current_file else ''}">
                    📦 Components
                </a>
                <a href="{root_path}dataflow/overview.html" class="nav-item {'active' if 'dataflow' in current_file else ''}">
                    🔄 Data Flow
                </a>
                <a href="{root_path}dependencies/overview.html" class="nav-item {'active' if 'dependencies' in current_file else ''}">
                    🔗 Dependencies
                </a>
                <a href="{root_path}api/overview.html" class="nav-item {'active' if 'api' in current_file else ''}">
                    🌐 API
                </a>
                <a href="{root_path}tech-stack/overview.html" class="nav-item {'active' if 'tech-stack' in current_file else ''}">
                    🛠️ Tech Stack
                </a>
            </div>
            <div class="nav-footer">
                <small>Generated by repo-explainer</small>
            </div>
        </nav>
        <main class="content">
            <article class="markdown-body">
                {body}
            </article>
        </main>
    </div>
</body>
</html>"""

    def _get_css(self) -> str:
        """Return CSS styling for the HTML pages."""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
            line-height: 1.6;
            color: #24292e;
            background: #f6f8fa;
        }

        .container {
            display: flex;
            min-height: 100vh;
        }

        .sidebar {
            width: 280px;
            background: #ffffff;
            border-right: 1px solid #e1e4e8;
            padding: 2rem 0;
            position: sticky;
            top: 0;
            height: 100vh;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
        }

        .nav-header {
            padding: 0 1.5rem 1.5rem;
            border-bottom: 1px solid #e1e4e8;
            margin-bottom: 1rem;
        }

        .logo {
            font-size: 1.5rem;
            font-weight: 700;
            color: #0366d6;
            text-decoration: none;
            display: block;
        }

        .logo:hover {
            color: #0256bd;
        }

        .nav-links {
            flex: 1;
            padding: 0 1rem;
        }

        .nav-item {
            display: block;
            padding: 0.75rem 1rem;
            color: #586069;
            text-decoration: none;
            border-radius: 6px;
            margin-bottom: 0.25rem;
            transition: all 0.2s;
        }

        .nav-item:hover {
            background: #f6f8fa;
            color: #0366d6;
        }

        .nav-item.active {
            background: #0366d6;
            color: white;
        }

        .nav-footer {
            padding: 1rem 1.5rem;
            border-top: 1px solid #e1e4e8;
            margin-top: 1rem;
            color: #586069;
            text-align: center;
        }

        .content {
            flex: 1;
            padding: 3rem;
            max-width: 1200px;
            margin: 0 auto;
        }

        .markdown-body {
            background: white;
            padding: 3rem;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        .markdown-body h1 {
            font-size: 2.5rem;
            margin-bottom: 1rem;
            padding-bottom: 0.5rem;
            border-bottom: 2px solid #e1e4e8;
            color: #24292e;
        }

        .markdown-body h2 {
            font-size: 2rem;
            margin-top: 2rem;
            margin-bottom: 1rem;
            padding-bottom: 0.3rem;
            border-bottom: 1px solid #e1e4e8;
            color: #24292e;
        }

        .markdown-body h3 {
            font-size: 1.5rem;
            margin-top: 1.5rem;
            margin-bottom: 0.75rem;
            color: #24292e;
        }

        .markdown-body p {
            margin-bottom: 1rem;
            line-height: 1.8;
        }

        .markdown-body a {
            color: #0366d6;
            text-decoration: none;
        }

        .markdown-body a:hover {
            text-decoration: underline;
        }

        .markdown-body code {
            background: #f6f8fa;
            padding: 0.2rem 0.4rem;
            border-radius: 3px;
            font-family: 'SFMono-Regular', Consolas, 'Liberation Mono', Menlo, monospace;
            font-size: 0.9em;
        }

        .markdown-body pre {
            background: #f6f8fa;
            padding: 1rem;
            border-radius: 6px;
            overflow-x: auto;
            margin: 1rem 0;
            border: 1px solid #e1e4e8;
        }

        .markdown-body pre code {
            background: none;
            padding: 0;
            font-size: 0.85em;
            line-height: 1.5;
        }

        .markdown-body ul, .markdown-body ol {
            margin-left: 2rem;
            margin-bottom: 1rem;
        }

        .markdown-body li {
            margin-bottom: 0.5rem;
        }

        .markdown-body blockquote {
            border-left: 4px solid #dfe2e5;
            padding-left: 1rem;
            margin: 1rem 0;
            color: #6a737d;
        }

        .markdown-body table {
            border-collapse: collapse;
            width: 100%;
            margin: 1rem 0;
        }

        .markdown-body th, .markdown-body td {
            border: 1px solid #e1e4e8;
            padding: 0.75rem;
            text-align: left;
        }

        .markdown-body th {
            background: #f6f8fa;
            font-weight: 600;
        }

        .markdown-body img {
            max-width: 100%;
            height: auto;
            border-radius: 6px;
            margin: 1rem 0;
        }

        .markdown-body hr {
            border: none;
            border-top: 2px solid #e1e4e8;
            margin: 2rem 0;
        }

        .markdown-body details {
            margin: 1rem 0;
            padding: 1rem;
            border: 1px solid #e1e4e8;
            border-radius: 6px;
        }

        .markdown-body summary {
            cursor: pointer;
            font-weight: 600;
            margin: -1rem;
            padding: 1rem;
            background: #f6f8fa;
            border-radius: 6px 6px 0 0;
        }

        .markdown-body summary:hover {
            background: #e1e4e8;
        }

        @media (max-width: 768px) {
            .sidebar {
                width: 100%;
                height: auto;
                position: relative;
            }

            .container {
                flex-direction: column;
            }

            .content {
                padding: 1.5rem;
            }

            .markdown-body {
                padding: 1.5rem;
            }
        }
        """

    def _copy_assets(self) -> None:
        """Copy diagrams and other assets to HTML output directory."""
        import shutil

        # Copy diagrams directory if it exists
        diagrams_src = self.docs_dir / "diagrams"
        if diagrams_src.exists():
            diagrams_dest = self.output_dir / "diagrams"
            if diagrams_dest.exists():
                shutil.rmtree(diagrams_dest)
            shutil.copytree(diagrams_src, diagrams_dest)
            console.print(f"[dim]  Copied diagrams to HTML output[/dim]")

        # Copy any other image files
        for ext in ['*.png', '*.jpg', '*.jpeg', '*.gif', '*.svg']:
            for img_file in self.docs_dir.rglob(ext):
                rel_path = img_file.relative_to(self.docs_dir)
                dest_file = self.output_dir / rel_path
                dest_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(img_file, dest_file)

    def _generate_navigation(self) -> None:
        """Generate a navigation index page if index.html doesn't exist."""
        index_html = self.output_dir / "index.html"
        if index_html.exists():
            return  # Already generated from index.md

        # Create a basic index
        html = self._generate_page(
            title="Documentation Home",
            body="<h1>Documentation</h1><p>Welcome to the documentation. Use the navigation menu to explore.</p>",
            root_path="./",
            current_file="index.md",
        )
        index_html.write_text(html)


class DocsServer:
    """Simple HTTP server for serving documentation."""

    def __init__(self, docs_dir: Path, port: int = 8080):
        """
        Initialize the documentation server.

        Args:
            docs_dir: Directory containing HTML documentation
            port: Port to serve on (default: 8080)
        """
        self.docs_dir = docs_dir
        self.port = port
        self.httpd: Optional[socketserver.TCPServer] = None
        self.thread: Optional[threading.Thread] = None

    def start(self, open_browser: bool = True) -> str:
        """
        Start the HTTP server in a background thread.

        Args:
            open_browser: Whether to open the browser automatically

        Returns:
            URL where the server is running
        """
        # Capture docs_dir in closure for CustomHandler
        docs_dir = self.docs_dir
        handler = http.server.SimpleHTTPRequestHandler

        class CustomHandler(handler):
            def __init__(self, *args, **kwargs):
                # Use docs_dir from outer scope
                super().__init__(*args, directory=str(docs_dir), **kwargs)

            def log_message(self, format, *args):
                # Suppress logs
                pass

        # Try to start server, with fallback ports
        for attempt_port in range(self.port, self.port + 10):
            try:
                self.httpd = socketserver.TCPServer(("", attempt_port), CustomHandler)
                self.port = attempt_port
                break
            except OSError:
                continue
        
        if not self.httpd:
            raise RuntimeError(f"Could not start server on ports {self.port}-{self.port+9}")

        # Start server in background thread
        self.thread = threading.Thread(target=self.httpd.serve_forever, daemon=True)
        self.thread.start()

        url = f"http://localhost:{self.port}/index.html"
        
        console.print(f"\n[bold green]✓ Docs server started on {url}[/bold green]\n")
        console.print(f"[dim]Press Ctrl+C to stop the server[/dim]\n")

        if open_browser:
            try:
                webbrowser.open(url)
                console.print("[dim]Opening browser...[/dim]\n")
            except Exception:
                pass

        return url

    def stop(self) -> None:
        """Stop the HTTP server."""
        if self.httpd:
            self.httpd.shutdown()
            self.httpd.server_close()
        if self.thread:
            self.thread.join(timeout=1)
        console.print("\n[yellow]Server stopped[/yellow]")
