"""HTML generation and serving for documentation."""

import http.server
import json
import socketserver
import threading
import webbrowser
from datetime import datetime
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
        self.update_history = self._load_update_history()

    def _load_update_history(self) -> list[dict]:
        """Load update history from .repo-explainer/updates.json."""
        history_file = self.docs_dir / ".repo-explainer" / "updates.json"
        if history_file.exists():
            try:
                return json.loads(history_file.read_text())
            except json.JSONDecodeError:
                return []
        return []

    def _get_update_banner_html(self, root_path: str) -> str:
        """
        Generate HTML for the update notification banner.

        Args:
            root_path: Relative path to root for navigation

        Returns:
            HTML string for the update banner, or empty string if no updates
        """
        if not self.update_history:
            return ""

        latest = self.update_history[0]
        try:
            update_time = datetime.fromisoformat(latest["timestamp"])
            now = datetime.now()
            delta = now - update_time

            # Format time ago
            if delta.days > 30:
                time_ago = f"{delta.days // 30} month{'s' if delta.days // 30 > 1 else ''} ago"
            elif delta.days > 0:
                time_ago = f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
            elif delta.seconds > 3600:
                hours = delta.seconds // 3600
                time_ago = f"{hours} hour{'s' if hours > 1 else ''} ago"
            elif delta.seconds > 60:
                minutes = delta.seconds // 60
                time_ago = f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            else:
                time_ago = "just now"

            files_count = latest.get("files_changed", 0)
            update_type = latest.get("type", "update")
            commits = latest.get("commits", [])

            # Build the banner
            banner_class = "update-banner" if delta.days < 7 else "update-banner update-banner-old"

            commits_html = ""
            if commits:
                commits_html = f'<span class="update-commits">Commits: {", ".join(commits[:3])}</span>'

            return f'''
            <div class="{banner_class}" id="update-banner">
                <div class="update-banner-content">
                    <span class="update-badge">Updated</span>
                    <span class="update-time">{time_ago}</span>
                    <span class="update-details">{files_count} file{'s' if files_count != 1 else ''} changed</span>
                    {commits_html}
                </div>
                <button class="update-banner-close" onclick="document.getElementById('update-banner').style.display='none'" aria-label="Dismiss">×</button>
            </div>
            '''
        except (KeyError, ValueError):
            return ""

    def _get_update_banner_css(self) -> str:
        """Get CSS styles for the update banner."""
        return '''
        .update-banner {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 0.75rem 1.5rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-size: 0.9rem;
            position: sticky;
            top: 0;
            z-index: 1000;
            box-shadow: 0 2px 10px rgba(102, 126, 234, 0.3);
        }

        .update-banner-old {
            background: linear-gradient(135deg, #6c757d 0%, #495057 100%);
        }

        .update-banner-content {
            display: flex;
            align-items: center;
            gap: 1rem;
            flex-wrap: wrap;
        }

        .update-badge {
            background: rgba(255,255,255,0.2);
            padding: 0.25rem 0.75rem;
            border-radius: 20px;
            font-weight: 600;
            font-size: 0.8rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }

        .update-time {
            font-weight: 500;
        }

        .update-details {
            opacity: 0.9;
        }

        .update-commits {
            opacity: 0.8;
            font-family: 'SFMono-Regular', Consolas, monospace;
            font-size: 0.85em;
        }

        .update-banner-close {
            background: rgba(255,255,255,0.2);
            border: none;
            color: white;
            width: 28px;
            height: 28px;
            border-radius: 50%;
            cursor: pointer;
            font-size: 1.2rem;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: background 0.2s;
        }

        .update-banner-close:hover {
            background: rgba(255,255,255,0.3);
        }

        @media (max-width: 768px) {
            .update-banner {
                flex-direction: column;
                gap: 0.5rem;
                text-align: center;
            }

            .update-banner-content {
                justify-content: center;
            }

            .update-commits {
                display: none;
            }
        }
        '''

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

        # Generate update history page
        self._generate_updates_page()

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

        # Get update banner (only show on index page)
        update_banner = ""
        if current_file == "index.md" and self.update_history:
            update_banner = self._get_update_banner_html(root_path)

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} - Repository Documentation</title>
    <style>
        {self._get_css()}
        {self._get_update_banner_css()}
    </style>
</head>
<body>
    {update_banner}
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
                <a href="{root_path}updates.html" class="nav-item {'active' if 'updates' in current_file else ''}">
                    📋 Update History
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

    def _generate_updates_page(self) -> None:
        """Generate the update history page with engineer-friendly information."""
        if not self.update_history:
            # Create a placeholder page
            body = """
            <h1>📋 Update History</h1>
            <p>No updates recorded yet. Run <code>repo-explain update</code> to track documentation updates.</p>
            """
        else:
            # Build update cards (more readable than tables)
            update_cards = []
            for update in self.update_history[:20]:
                try:
                    timestamp = datetime.fromisoformat(update["timestamp"])
                    date_str = timestamp.strftime("%B %d, %Y at %H:%M")
                    update_type = update.get("type", "update")
                    files_count = update.get("files_changed", 0)
                    summary = update.get("summary", f"{files_count} files changed")
                    commits = update.get("commits", [])
                    categories = update.get("categories", {})
                    files = update.get("files", [])

                    # Build commit messages HTML (the useful part!)
                    commits_html = ""
                    commit_summaries = update.get("commit_summaries", [])
                    if commits:
                        commit_items = []
                        for i, c in enumerate(commits[:5]):
                            if isinstance(c, dict):
                                sha = c.get("sha", "")
                                msg = c.get("message", "No message")
                                author = c.get("author", "Unknown")

                                # Add AI summary if available
                                summary_html = ""
                                if i < len(commit_summaries) and commit_summaries[i]:
                                    summary = commit_summaries[i]
                                    summary_text = summary.get("summary", "")
                                    category = summary.get("category", "unknown")
                                    impact = summary.get("impact_level", "unknown")

                                    if summary_text:
                                        # Add category badge
                                        category_badge = ""
                                        if category != "unknown":
                                            category_badge = f'<span class="summary-category category-{category}">{category.title()}</span>'

                                        summary_html = f'''
                                        <div class="commit-summary">
                                            <div class="summary-text">{summary_text}</div>
                                            {category_badge}
                                        </div>
                                        '''

                                commit_items.append(f'''
                                    <div class="commit-item">
                                        <code class="commit-sha">{sha}</code>
                                        <span class="commit-msg">{msg}</span>
                                        <span class="commit-author">by {author}</span>
                                        {summary_html}
                                    </div>
                                ''')
                            else:
                                # Legacy format (just SHA string)
                                commit_items.append(f'<div class="commit-item"><code>{c}</code></div>')

                        commits_html = f'''
                        <div class="commits-section">
                            <h4>📝 Commits & AI Summaries</h4>
                            {"".join(commit_items)}
                        </div>
                        '''

                    # Build categories HTML (what areas were affected)
                    categories_html = ""
                    if categories:
                        cat_badges = []
                        cat_icons = {
                            "components": "🧩",
                            "cli": "⌨️",
                            "docs": "📄",
                            "config": "⚙️",
                            "tests": "🧪",
                            "other": "📁",
                        }
                        for cat, cat_files in categories.items():
                            icon = cat_icons.get(cat, "📁")
                            cat_badges.append(f'<span class="cat-badge cat-{cat}">{icon} {cat.title()} ({len(cat_files)})</span>')
                        
                        categories_html = f'''
                        <div class="categories-section">
                            <h4>📂 Areas Affected</h4>
                            <div class="cat-badges">{"".join(cat_badges)}</div>
                        </div>
                        '''

                    # Build files list (collapsible)
                    files_html = ""
                    if files:
                        files_list = "".join(f"<li><code>{f}</code></li>" for f in files[:15])
                        if len(files) > 15:
                            files_list += f"<li><em>... and {len(files) - 15} more files</em></li>"
                        files_html = f'''
                        <details class="files-section">
                            <summary>📋 View all {len(files)} changed files</summary>
                            <ul class="files-list">{files_list}</ul>
                        </details>
                        '''

                    # Build the update card
                    badge_class = "badge-incremental" if update_type == "incremental" else "badge-full"
                    update_cards.append(f'''
                    <div class="update-card">
                        <div class="update-header">
                            <span class="update-date">{date_str}</span>
                            <span class="update-type-badge {badge_class}">{update_type}</span>
                        </div>
                        <div class="update-summary">
                            <strong>{summary}</strong>
                        </div>
                        {categories_html}
                        {commits_html}
                        {files_html}
                    </div>
                    ''')
                except (KeyError, ValueError) as e:
                    continue

            cards_html = "".join(update_cards)

            body = f"""
            <h1>📋 Update History</h1>
            <p>This page shows the history of documentation updates. Each update includes commit messages, 
            affected areas, and changed files to help you understand what changed.</p>

            <div class="updates-container">
                {cards_html}
            </div>

            <style>
                .updates-container {{
                    display: flex;
                    flex-direction: column;
                    gap: 1.5rem;
                    margin-top: 2rem;
                }}

                .update-card {{
                    background: #ffffff;
                    border: 1px solid #e1e4e8;
                    border-radius: 12px;
                    padding: 1.5rem;
                    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
                }}

                .update-header {{
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: 1rem;
                    padding-bottom: 0.75rem;
                    border-bottom: 1px solid #e1e4e8;
                }}

                .update-date {{
                    color: #586069;
                    font-size: 0.9rem;
                }}

                .update-type-badge {{
                    display: inline-block;
                    padding: 0.25rem 0.75rem;
                    border-radius: 20px;
                    font-size: 0.8rem;
                    font-weight: 600;
                    text-transform: uppercase;
                }}

                .badge-incremental {{
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }}

                .badge-full {{
                    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
                    color: white;
                }}

                .update-summary {{
                    font-size: 1.1rem;
                    margin-bottom: 1rem;
                    color: #24292e;
                }}

                .categories-section, .commits-section {{
                    margin: 1rem 0;
                }}

                .categories-section h4, .commits-section h4 {{
                    margin: 0 0 0.5rem 0;
                    font-size: 0.9rem;
                    color: #586069;
                }}

                .cat-badges {{
                    display: flex;
                    flex-wrap: wrap;
                    gap: 0.5rem;
                }}

                .cat-badge {{
                    display: inline-block;
                    padding: 0.25rem 0.75rem;
                    border-radius: 16px;
                    font-size: 0.85rem;
                    background: #f6f8fa;
                    border: 1px solid #e1e4e8;
                }}

                .cat-components {{ background: #ddf4ff; border-color: #54aeff; }}
                .cat-cli {{ background: #fff8c5; border-color: #d4a72c; }}
                .cat-docs {{ background: #dafbe1; border-color: #4ac26b; }}
                .cat-config {{ background: #ffeef0; border-color: #f97583; }}
                .cat-tests {{ background: #f1e5ff; border-color: #a371f7; }}

                .commit-item {{
                    display: flex;
                    align-items: baseline;
                    gap: 0.75rem;
                    padding: 0.5rem 0;
                    border-bottom: 1px dashed #e1e4e8;
                }}

                .commit-item:last-child {{
                    border-bottom: none;
                }}

                .commit-sha {{
                    background: #f6f8fa;
                    padding: 0.2rem 0.5rem;
                    border-radius: 4px;
                    font-size: 0.85rem;
                    color: #0366d6;
                    flex-shrink: 0;
                }}

                .commit-msg {{
                    flex: 1;
                    color: #24292e;
                }}

                .commit-author {{
                    color: #586069;
                    font-size: 0.85rem;
                    flex-shrink: 0;
                }}

                .commit-summary {{
                    margin-top: 0.5rem;
                    padding: 0.5rem;
                    background: #f8f9fa;
                    border-left: 3px solid #0366d6;
                    border-radius: 4px;
                    font-size: 0.9rem;
                }}

                .summary-text {{
                    color: #24292e;
                    line-height: 1.4;
                    margin-bottom: 0.25rem;
                }}

                .summary-category {{
                    display: inline-block;
                    padding: 0.15rem 0.5rem;
                    border-radius: 12px;
                    font-size: 0.75rem;
                    font-weight: 500;
                    text-transform: uppercase;
                    letter-spacing: 0.5px;
                }}

                .category-features {{ background: #ddf4ff; color: #0a3069; }}
                .category-fixes {{ background: #dafbe1; color: #0f5132; }}
                .category-refactoring {{ background: #fff8c5; color: #664d03; }}
                .category-documentation {{ background: #f1e5ff; color: #492c73; }}
                .category-infrastructure {{ background: #ffeef0; color: #842029; }}
                .category-dependencies {{ background: #e7f3ff; color: #055160; }}

                .files-section {{
                    margin-top: 1rem;
                    border: 1px solid #e1e4e8;
                    border-radius: 8px;
                }}

                .files-section summary {{
                    padding: 0.75rem 1rem;
                    background: #f6f8fa;
                    cursor: pointer;
                    font-weight: 500;
                    border-radius: 8px;
                }}

                .files-section[open] summary {{
                    border-radius: 8px 8px 0 0;
                    border-bottom: 1px solid #e1e4e8;
                }}

                .files-list {{
                    padding: 1rem;
                    margin: 0;
                    list-style: none;
                }}

                .files-list li {{
                    padding: 0.25rem 0;
                }}

                .files-list code {{
                    background: #f6f8fa;
                    padding: 0.2rem 0.5rem;
                    border-radius: 4px;
                    font-size: 0.85rem;
                }}
            </style>

            <h2>Usage</h2>
            <pre><code># Update docs based on commits on main branch
repo-explain update . --auto --generate-html

# Update from a specific branch
repo-explain update . --branch develop --generate-html

# Force check last N commits
repo-explain update . --commits 5 --generate-html
</code></pre>
            """

        html = self._generate_page(
            title="Update History",
            body=body,
            root_path="./",
            current_file="updates.md",
        )
        updates_html = self.output_dir / "updates.html"
        updates_html.write_text(html)
        console.print(f"[dim]    ✓ Generated updates.html[/dim]")


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
