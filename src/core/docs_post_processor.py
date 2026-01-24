"""
Documentation Post-Processor

Handles post-processing of generated documentation including:
- Copying docs to build directory (preserving originals)
- Fixing GitHub repository links
- Mermaid diagram rendering to PNG
- HTML site generation using mkdocs

Usage:
    from core.docs_post_processor import DocsPostProcessor

    processor = DocsPostProcessor(
        docs_dir=Path("planning/docs"),
        repo_url="https://github.com/kubernetes/kubernetes"
    )
    result = processor.process_all()
    print(f"HTML site: {result.html_output_dir}")
"""

import logging
import re
import shutil
import subprocess
import hashlib
import tempfile
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)


class DiagramTheme(Enum):
    """Available mermaid themes."""
    DEFAULT = "default"
    DARK = "dark"
    FOREST = "forest"
    NEUTRAL = "neutral"


@dataclass
class ProcessingResult:
    """Result from processing run."""
    success: bool = False

    # Paths
    source_dir: Optional[Path] = None
    build_dir: Optional[Path] = None
    html_output_dir: Optional[Path] = None

    # Statistics
    files_processed: int = 0
    diagrams_found: int = 0
    diagrams_rendered: int = 0
    diagrams_failed: int = 0
    github_links_fixed: int = 0

    # Errors
    errors: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        return (
            f"Processed {self.files_processed} files: "
            f"{self.diagrams_rendered}/{self.diagrams_found} diagrams rendered, "
            f"{self.github_links_fixed} GitHub links fixed"
        )


class DocsPostProcessor:
    """
    Post-processor for documentation files.

    Copies docs to a build directory, processes them (mermaid, links),
    and generates an HTML site.
    """

    # Regex patterns
    MERMAID_PATTERN = re.compile(
        r'```mermaid\s*\n(.*?)```',
        re.DOTALL | re.MULTILINE
    )

    # Match GitHub file links like: https://github.com/owner/repo/blob/branch/path/to/file.go
    GITHUB_LINK_PATTERN = re.compile(
        r'https://github\.com/([^/]+)/([^/]+)/(blob|tree)/([^/]+)/([^\s\)]+)'
    )

    def __init__(
        self,
        docs_dir: Path,
        repo_url: Optional[str] = None,
        build_dir: Optional[Path] = None,
        theme: DiagramTheme = DiagramTheme.DEFAULT,
        background: str = "white",
        scale: int = 2,
    ):
        """
        Initialize the post-processor.

        Args:
            docs_dir: Root directory containing source markdown files
            repo_url: GitHub repository URL (for fixing links)
            build_dir: Directory for processed files (default: docs_dir/../build)
            theme: Mermaid theme for diagram rendering
            background: Background color for diagrams
            scale: Scale factor for diagram resolution
        """
        self.docs_dir = Path(docs_dir).resolve()
        self.repo_url = repo_url
        self.theme = theme
        self.background = background
        self.scale = scale

        # Parse repo owner/name from URL
        self.repo_owner = None
        self.repo_name = None
        if repo_url:
            match = re.search(r'github\.com/([^/]+)/([^/]+)', repo_url)
            if match:
                self.repo_owner = match.group(1)
                self.repo_name = match.group(2).rstrip('.git')

        # Build directory - sibling to docs_dir
        if build_dir:
            self.build_dir = Path(build_dir).resolve()
        else:
            self.build_dir = self.docs_dir.parent / "build"

        # Markdown goes to build/docs/, HTML goes to build/site/
        # This avoids mkdocs error about site_dir being inside docs_dir
        self.build_docs_dir = self.build_dir / "docs"
        self.html_output_dir = self.build_dir / "site"

        # Check for tools
        self.mmdc_path = shutil.which("mmdc")
        self.mkdocs_path = shutil.which("mkdocs")

        if not self.mmdc_path:
            logger.warning(
                "mermaid-cli (mmdc) not found - diagrams will NOT be rendered! "
                "Install with: npm install -g @mermaid-js/mermaid-cli"
            )

        if not self.mkdocs_path:
            logger.warning(
                "mkdocs not found - HTML site will NOT be generated! "
                "Install with: pip install mkdocs mkdocs-material"
            )

    def process_all(self) -> ProcessingResult:
        """
        Run full post-processing pipeline.

        1. Copy docs to build directory
        2. Fix GitHub links
        3. Render mermaid diagrams
        4. Generate HTML site

        Returns:
            ProcessingResult with paths and statistics
        """
        result = ProcessingResult(
            source_dir=self.docs_dir,
            build_dir=self.build_dir
        )

        if not self.docs_dir.exists():
            logger.error(f"Docs directory not found: {self.docs_dir}")
            result.errors.append(f"Directory not found: {self.docs_dir}")
            return result

        try:
            # Step 1: Copy docs to build directory
            logger.info(f"Copying docs to build directory: {self.build_dir}")
            self._copy_docs()

            # Find all markdown files in build docs directory
            md_files = list(self.build_docs_dir.rglob("*.md"))
            logger.info(f"Found {len(md_files)} markdown files")

            # Step 2: Process each file
            for md_file in md_files:
                try:
                    file_result = self._process_file(md_file)
                    result.files_processed += 1
                    result.diagrams_found += file_result.get('diagrams_found', 0)
                    result.diagrams_rendered += file_result.get('diagrams_rendered', 0)
                    result.diagrams_failed += file_result.get('diagrams_failed', 0)
                    result.github_links_fixed += file_result.get('links_fixed', 0)
                except Exception as e:
                    logger.error(f"Error processing {md_file}: {e}")
                    result.errors.append(f"{md_file.name}: {e}")

            # Step 3: Generate HTML site
            if self.mkdocs_path:
                logger.info("Generating HTML site...")
                html_success = self._generate_html()
                if html_success:
                    result.html_output_dir = self.html_output_dir
                    logger.info(f"HTML site generated: {self.html_output_dir}")
                else:
                    result.errors.append("HTML generation failed")
            else:
                logger.warning("mkdocs not available, skipping HTML generation")

            result.success = len(result.errors) == 0
            logger.info(f"Processing complete: {result}")

        except Exception as e:
            logger.error(f"Processing failed: {e}")
            result.errors.append(str(e))

        return result

    def _copy_docs(self) -> None:
        """Copy source docs to build directory."""
        # Clean build directory
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)

        # Copy docs to build/docs/ (not build/ directly)
        shutil.copytree(self.docs_dir, self.build_docs_dir)
        logger.info(f"  → Copied {self.docs_dir} to {self.build_docs_dir}")

    def _process_file(self, md_file: Path) -> dict:
        """Process a single markdown file."""
        stats = {
            'diagrams_found': 0,
            'diagrams_rendered': 0,
            'diagrams_failed': 0,
            'links_fixed': 0
        }

        content = md_file.read_text(encoding='utf-8')
        original_content = content

        # Fix GitHub links
        if self.repo_owner and self.repo_name:
            content, links_fixed = self._fix_github_links(content)
            stats['links_fixed'] = links_fixed
            if links_fixed > 0:
                logger.debug(f"  Fixed {links_fixed} GitHub links in {md_file.name}")

        # Find and render mermaid diagrams
        matches = list(self.MERMAID_PATTERN.finditer(content))
        if matches:
            stats['diagrams_found'] = len(matches)
            logger.info(f"Found {len(matches)} mermaid diagrams in {md_file.name}")

            # Process in reverse to preserve positions
            for i, match in enumerate(reversed(matches)):
                diagram_code = match.group(1).strip()
                diagram_index = len(matches) - 1 - i

                # Generate unique filename
                diagram_hash = hashlib.md5(diagram_code.encode()).hexdigest()[:8]
                diagram_name = f"{md_file.stem}_diagram_{diagram_index}_{diagram_hash}"

                # Render diagram
                success, image_path = self._render_mermaid(
                    diagram_code,
                    md_file.parent,
                    diagram_name
                )

                if success and image_path:
                    title = self._extract_diagram_title(diagram_code)
                    image_md = f"![{title}]({image_path.name})"
                    content = content[:match.start()] + image_md + content[match.end():]
                    stats['diagrams_rendered'] += 1
                    logger.info(f"  ✓ Rendered: {diagram_name}.png")
                else:
                    stats['diagrams_failed'] += 1
                    logger.warning(f"  ✗ Failed: diagram {diagram_index}")

        # Write if changed
        if content != original_content:
            md_file.write_text(content, encoding='utf-8')

        return stats

    def _fix_github_links(self, content: str) -> Tuple[str, int]:
        """
        Fix GitHub links to point to the correct repository.

        Returns:
            Tuple of (fixed_content, num_links_fixed)
        """
        fixed_count = 0

        def replace_link(match):
            nonlocal fixed_count
            owner = match.group(1)
            repo = match.group(2)
            link_type = match.group(3)  # blob or tree
            branch = match.group(4)
            path = match.group(5)

            # Check if this link should be fixed
            # Fix if owner doesn't match OR repo doesn't match
            if owner != self.repo_owner or repo != self.repo_name:
                fixed_count += 1
                return f"https://github.com/{self.repo_owner}/{self.repo_name}/{link_type}/{branch}/{path}"

            return match.group(0)  # Return unchanged

        fixed_content = self.GITHUB_LINK_PATTERN.sub(replace_link, content)
        return fixed_content, fixed_count

    def _sanitize_mermaid(self, code: str) -> str:
        """Sanitize mermaid code to fix common syntax issues."""
        lines = code.split('\n')
        sanitized = []

        for line in lines:
            # Remove inline comments
            if '#' in line and not line.strip().startswith('#'):
                parts = line.split('#')
                if len(parts) > 1:
                    before = parts[0].rstrip()
                    if before.endswith(';') or '-->' in before or '-.>' in before or '==>' in before:
                        line = before

            # Fix node labels with problematic characters
            def fix_label(match):
                content = match.group(1)
                content = content.replace('(', ' - ').replace(')', '')
                content = content.replace('/', '-')
                return f'[{content}]'

            line = re.sub(r'\[([^\]]+)\]', fix_label, line)

            def fix_paren_label(match):
                prefix = match.group(1)
                content = match.group(2)
                if '(' in content or ')' in content:
                    content = content.replace('(', ' - ').replace(')', '')
                return f'{prefix}({content})'

            line = re.sub(r'(\w+)\(([^)]+)\)', fix_paren_label, line)
            sanitized.append(line)

        return '\n'.join(sanitized)

    def _render_mermaid(
        self,
        code: str,
        output_dir: Path,
        name: str
    ) -> Tuple[bool, Optional[Path]]:
        """Render mermaid code to PNG."""
        if not self.mmdc_path:
            return False, None

        code = self._sanitize_mermaid(code)
        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{name}.png"

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.mmd', delete=False, encoding='utf-8'
        ) as f:
            f.write(code)
            temp_input = Path(f.name)

        try:
            cmd = [
                self.mmdc_path,
                "-i", str(temp_input),
                "-o", str(output_path),
                "-t", self.theme.value,
                "-b", self.background,
                "-s", str(self.scale),
                "--quiet"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0 and output_path.exists():
                return True, output_path
            else:
                if result.stderr:
                    logger.debug(f"mmdc error: {result.stderr[:200]}")
                return False, None

        except Exception as e:
            logger.debug(f"mermaid error: {e}")
            return False, None
        finally:
            temp_input.unlink(missing_ok=True)

    def _extract_diagram_title(self, code: str) -> str:
        """Extract a title from mermaid code."""
        lines = code.strip().split('\n')

        for line in lines:
            if line.strip().startswith('title'):
                return line.split('title', 1)[1].strip()

        first_line = lines[0].strip().lower() if lines else ""
        type_names = {
            'graph': 'Flow Diagram',
            'flowchart': 'Flowchart',
            'sequencediagram': 'Sequence Diagram',
            'classdiagram': 'Class Diagram',
            'statediagram': 'State Diagram',
            'erdiagram': 'ER Diagram',
            'gantt': 'Gantt Chart',
            'pie': 'Pie Chart',
        }

        for key, name in type_names.items():
            if first_line.startswith(key.lower()):
                return name

        return "Diagram"

    def _generate_html(self) -> bool:
        """Generate HTML site using mkdocs."""
        if not self.mkdocs_path:
            logger.error("mkdocs not installed - cannot generate HTML site")
            return False

        # Create mkdocs config
        # docs_dir = build/docs/, site_dir = build/site/ (must not be inside docs_dir)
        config_content = f"""
site_name: Documentation
docs_dir: "{self.build_docs_dir}"
site_dir: "{self.html_output_dir}"
use_directory_urls: false

theme:
  name: material
  palette:
    scheme: default
  features:
    - navigation.instant
    - navigation.sections
    - search.highlight

plugins:
  - search

markdown_extensions:
  - toc:
      permalink: true
  - tables
  - fenced_code
"""

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yml', delete=False, encoding='utf-8'
        ) as f:
            f.write(config_content)
            config_path = Path(f.name)

        try:
            # Ensure output dir exists
            self.html_output_dir.mkdir(parents=True, exist_ok=True)

            logger.info(f"Running mkdocs build with config: {config_path}")
            logger.info(f"  docs_dir: {self.build_docs_dir}")
            logger.info(f"  site_dir: {self.html_output_dir}")

            result = subprocess.run(
                [self.mkdocs_path, "build", "-f", str(config_path), "--clean"],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(self.build_dir.parent)  # Run from parent of build dir
            )

            if result.returncode == 0:
                # Verify site was actually created
                if self.html_output_dir.exists() and any(self.html_output_dir.iterdir()):
                    logger.info(f"HTML site generated successfully: {self.html_output_dir}")
                    return True
                else:
                    logger.error(f"mkdocs completed but site dir is empty: {self.html_output_dir}")
                    return False
            else:
                logger.error(f"mkdocs build failed (exit code {result.returncode})")
                if result.stdout:
                    logger.error(f"  stdout: {result.stdout[:500]}")
                if result.stderr:
                    logger.error(f"  stderr: {result.stderr[:500]}")
                return False

        except subprocess.TimeoutExpired:
            logger.error("mkdocs build timed out after 120 seconds")
            return False
        except Exception as e:
            logger.error(f"HTML generation error: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return False
        finally:
            config_path.unlink(missing_ok=True)

    def check_dependencies(self) -> dict:
        """Check if required dependencies are available."""
        deps = {}

        if self.mmdc_path:
            try:
                result = subprocess.run(
                    [self.mmdc_path, "--version"],
                    capture_output=True, text=True, timeout=5
                )
                deps['mermaid-cli'] = result.stdout.strip() or "installed"
            except:
                deps['mermaid-cli'] = "error"
        else:
            deps['mermaid-cli'] = None

        if self.mkdocs_path:
            try:
                result = subprocess.run(
                    [self.mkdocs_path, "--version"],
                    capture_output=True, text=True, timeout=5
                )
                deps['mkdocs'] = result.stdout.strip() or "installed"
            except:
                deps['mkdocs'] = "error"
        else:
            deps['mkdocs'] = None

        return deps


def process_docs(
    docs_dir: Path,
    repo_url: Optional[str] = None,
    theme: str = "default",
    verbose: bool = False
) -> ProcessingResult:
    """
    Convenience function to process documentation.

    Args:
        docs_dir: Directory containing markdown files
        repo_url: GitHub repository URL (for fixing links)
        theme: Mermaid theme
        verbose: Enable verbose logging

    Returns:
        ProcessingResult with paths and statistics
    """
    log_level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )

    try:
        theme_enum = DiagramTheme(theme)
    except ValueError:
        theme_enum = DiagramTheme.DEFAULT

    processor = DocsPostProcessor(
        docs_dir=Path(docs_dir),
        repo_url=repo_url,
        theme=theme_enum
    )

    return processor.process_all()


# CLI interface
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Post-process documentation (mermaid, links, HTML)"
    )
    parser.add_argument(
        "docs_dir",
        type=str,
        help="Directory containing markdown files"
    )
    parser.add_argument(
        "--repo-url",
        type=str,
        help="GitHub repository URL for fixing links"
    )
    parser.add_argument(
        "--theme",
        type=str,
        default="default",
        choices=["default", "dark", "forest", "neutral"],
        help="Mermaid theme (default: default)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check dependencies only"
    )

    args = parser.parse_args()

    if args.check:
        processor = DocsPostProcessor(Path(args.docs_dir), repo_url=args.repo_url)
        deps = processor.check_dependencies()
        print("Dependencies:")
        for name, status in deps.items():
            symbol = "✓" if status else "✗"
            print(f"  {symbol} {name}: {status or 'not installed'}")
    else:
        result = process_docs(
            Path(args.docs_dir),
            repo_url=args.repo_url,
            theme=args.theme,
            verbose=args.verbose
        )

        print(f"\n{'='*60}")
        print("Processing Complete")
        print(f"{'='*60}")
        print(f"Source:             {result.source_dir}")
        print(f"Build:              {result.build_dir}")
        print(f"HTML:               {result.html_output_dir}")
        print(f"Files processed:    {result.files_processed}")
        print(f"Diagrams rendered:  {result.diagrams_rendered}/{result.diagrams_found}")
        print(f"GitHub links fixed: {result.github_links_fixed}")

        if result.errors:
            print(f"\nErrors ({len(result.errors)}):")
            for err in result.errors[:10]:
                print(f"  - {err}")

        if result.html_output_dir and result.html_output_dir.exists():
            print(f"\n{'='*60}")
            print(f"View site: cd {result.html_output_dir} && python3 -m http.server 8080")
            print(f"{'='*60}")
