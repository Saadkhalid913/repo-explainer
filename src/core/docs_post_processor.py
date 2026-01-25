"""
Documentation Post-Processor

Handles post-processing of generated documentation including:
- Copying docs to build directory (preserving originals)
- Creating docs_raw/ (original) and docs/ (rendered) copies
- Fixing GitHub repository links
- Mermaid diagram rendering to PNG (with validation and retry)
- HTML site generation using mkdocs
- Validation to ensure all diagrams are rendered

Usage:
    from core.docs_post_processor import DocsPostProcessor

    processor = DocsPostProcessor(
        docs_dir=Path("planning/docs"),
        repo_url="https://github.com/owner/repo"
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
from typing import List, Optional, Tuple, Callable
from enum import Enum

logger = logging.getLogger(__name__)


class DiagramTheme(Enum):
    """Available mermaid themes."""
    DEFAULT = "default"
    DARK = "dark"
    FOREST = "forest"
    NEUTRAL = "neutral"


@dataclass
class ValidationError:
    """A validation error found in processed docs."""
    file_path: Path
    error_type: str
    message: str
    line_number: Optional[int] = None


@dataclass
class ProcessingResult:
    """Result from processing run."""
    success: bool = False

    # Paths
    source_dir: Optional[Path] = None
    build_dir: Optional[Path] = None
    docs_raw_dir: Optional[Path] = None  # Unrendered copy
    docs_rendered_dir: Optional[Path] = None  # Rendered copy (for mkdocs)
    html_output_dir: Optional[Path] = None

    # Statistics
    files_processed: int = 0
    diagrams_found: int = 0
    diagrams_rendered: int = 0
    diagrams_failed: int = 0
    github_links_fixed: int = 0
    internal_links_fixed: int = 0  # Broken internal links converted to plain text
    markdown_issues_fixed: int = 0
    doc_tree_errors: int = 0  # Validation errors against doc_tree.json

    # Validation
    validation_errors: List[ValidationError] = field(default_factory=list)

    # Errors
    errors: List[str] = field(default_factory=list)

    def __str__(self) -> str:
        return (
            f"Processed {self.files_processed} files: "
            f"{self.diagrams_rendered}/{self.diagrams_found} diagrams rendered, "
            f"{self.github_links_fixed} GitHub links fixed, "
            f"{self.internal_links_fixed} broken internal links fixed"
        )


class DocsPostProcessor:
    """
    Post-processor for documentation files.

    Copies docs to a build directory, processes them (mermaid, links),
    and generates an HTML site.

    Output structure:
        build/
        ├── docs_raw/     # Original markdown (unrendered mermaid)
        ├── docs/         # Rendered markdown (mermaid → PNG)
        └── site/         # HTML site from mkdocs
    """

    # Regex patterns - multiple patterns to catch edge cases
    MERMAID_PATTERNS = [
        # Standard fenced code block
        re.compile(r'```mermaid\s*\n(.*?)\n```', re.DOTALL),
        # With extra whitespace
        re.compile(r'```\s*mermaid\s*\n(.*?)\n\s*```', re.DOTALL),
        # Indented code blocks
        re.compile(r'^\s*```mermaid\s*\n(.*?)\n\s*```', re.DOTALL | re.MULTILINE),
    ]

    # Pattern to detect unrendered mermaid in final output
    UNRENDERED_MERMAID_PATTERN = re.compile(r'```mermaid', re.IGNORECASE)

    # Match GitHub file links
    GITHUB_LINK_PATTERN = re.compile(
        r'https://github\.com/([^/]+)/([^/]+)/(blob|tree)/([^/]+)/([^\s\)]+)'
    )

    # Pattern for stray/orphan backticks at end of sections
    STRAY_BACKTICKS_PATTERN = re.compile(r'\n```\s*$')

    def __init__(
        self,
        docs_dir: Path,
        repo_url: Optional[str] = None,
        build_dir: Optional[Path] = None,
        theme: DiagramTheme = DiagramTheme.DEFAULT,
        background: str = "white",
        scale: int = 2,
        log_callback: Optional[Callable[[str], None]] = None,
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
            log_callback: Optional callback for logging messages to TUI
        """
        self.docs_dir = Path(docs_dir).resolve()
        self.repo_url = repo_url
        self.theme = theme
        self.background = background
        self.scale = scale
        self.log_callback = log_callback

        # Parse repo owner/name from URL
        self.repo_owner = None
        self.repo_name = None
        if repo_url:
            match = re.search(r'github\.com/([^/]+)/([^/]+)', repo_url)
            if match:
                self.repo_owner = match.group(1)
                self.repo_name = match.group(2).rstrip('.git')

        # Build directory structure
        if build_dir:
            self.build_dir = Path(build_dir).resolve()
        else:
            self.build_dir = self.docs_dir.parent / "build"

        # Output directories
        self.docs_raw_dir = self.build_dir / "docs_raw"  # Unrendered copy
        self.docs_rendered_dir = self.build_dir / "docs"  # Rendered copy for mkdocs
        self.html_output_dir = self.build_dir / "site"  # HTML output

        # Check for tools
        self.mmdc_path = shutil.which("mmdc")
        self.mkdocs_path = shutil.which("mkdocs")

        if not self.mmdc_path:
            self._log("WARNING: mermaid-cli (mmdc) not found - diagrams will NOT be rendered!")

        if not self.mkdocs_path:
            self._log("WARNING: mkdocs not found - HTML site will NOT be generated!")

    def _log(self, message: str) -> None:
        """Log a message, optionally to callback."""
        logger.info(message)
        if self.log_callback:
            self.log_callback(message)

    def process_all(self) -> ProcessingResult:
        """
        Run full post-processing pipeline.

        1. Copy docs to docs_raw/ (preserve original)
        2. Copy docs to docs/ (for rendering)
        3. Fix markdown issues (stray backticks, etc.)
        4. Fix GitHub links
        5. Render mermaid diagrams to PNG
        6. Validate all diagrams rendered
        7. Create index.md if missing
        8. Generate HTML site

        Returns:
            ProcessingResult with paths and statistics
        """
        result = ProcessingResult(
            source_dir=self.docs_dir,
            build_dir=self.build_dir
        )

        if not self.docs_dir.exists():
            self._log(f"ERROR: Docs directory not found: {self.docs_dir}")
            result.errors.append(f"Directory not found: {self.docs_dir}")
            return result

        try:
            # Step 1: Copy docs to both raw and rendered directories
            self._log("Copying docs to build directories...")
            self._copy_docs()
            result.docs_raw_dir = self.docs_raw_dir
            result.docs_rendered_dir = self.docs_rendered_dir

            # Find all markdown files in rendered docs directory
            md_files = list(self.docs_rendered_dir.rglob("*.md"))
            self._log(f"Found {len(md_files)} markdown files")

            # Step 2: Process each file
            for md_file in md_files:
                try:
                    file_result = self._process_file(md_file)
                    result.files_processed += 1
                    result.diagrams_found += file_result.get('diagrams_found', 0)
                    result.diagrams_rendered += file_result.get('diagrams_rendered', 0)
                    result.diagrams_failed += file_result.get('diagrams_failed', 0)
                    result.github_links_fixed += file_result.get('links_fixed', 0)
                    result.internal_links_fixed += file_result.get('internal_links_fixed', 0)
                    result.markdown_issues_fixed += file_result.get('markdown_fixed', 0)
                except Exception as e:
                    logger.error(f"Error processing {md_file}: {e}")
                    result.errors.append(f"{md_file.name}: {e}")

            # Step 3: Validate all mermaid diagrams were rendered
            self._log("Validating mermaid rendering...")
            validation_errors = self._validate_no_unrendered_mermaid()
            result.validation_errors.extend(validation_errors)

            if validation_errors:
                self._log(f"WARNING: {len(validation_errors)} unrendered mermaid blocks found")
                # Try to fix remaining blocks
                for error in validation_errors:
                    self._attempt_mermaid_recovery(error.file_path)

            # Step 3.5: Validate against doc_tree.json
            self._log("Validating against doc_tree.json...")
            doc_tree_errors = self._validate_against_doc_tree()
            result.validation_errors.extend(doc_tree_errors)
            result.doc_tree_errors = len(doc_tree_errors)

            if doc_tree_errors:
                self._log(f"WARNING: {len(doc_tree_errors)} doc tree validation errors")
                for error in doc_tree_errors[:5]:  # Show first 5
                    self._log(f"  - {error.error_type}: {error.message[:80]}")

            # Step 4: Ensure top-level index.md exists
            self._ensure_index_exists()

            # Step 5: Generate HTML site
            if self.mkdocs_path:
                self._log("Generating HTML site...")
                html_success = self._generate_html()
                if html_success:
                    result.html_output_dir = self.html_output_dir
                    self._log(f"HTML site generated: {self.html_output_dir}")
                else:
                    result.errors.append("HTML generation failed")
            else:
                self._log("mkdocs not available, skipping HTML generation")

            result.success = len(result.errors) == 0 and result.diagrams_failed == 0
            self._log(f"Processing complete: {result}")

        except Exception as e:
            logger.error(f"Processing failed: {e}")
            result.errors.append(str(e))

        return result

    # Files that are internal planning artifacts and should NOT appear in final docs
    EXCLUDED_FILES = {
        'component_manifest.md',  # Internal metadata for cross-linking
        'task_allocation.md',     # Internal pipeline task tracking
    }

    def _copy_docs(self) -> None:
        """Copy source docs to both raw and rendered directories with restructuring.

        The source structure is:
            planning/
            ├── overview.md
            ├── component_manifest.md  (EXCLUDED - internal)
            ├── task_allocation.md     (EXCLUDED - internal)
            ├── docs/
            │   └── component_name/
            │       ├── index.md
            │       └── *.md
            └── assets/

        The output structure will be:
            build/docs/
            ├── index.md (from overview.md)
            ├── components/
            │   └── component_name/
            │       ├── index.md
            │       └── *.md
            └── assets/
        """
        # Clean build directory
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)

        # Copy to docs_raw/ (unmodified backup - keep original structure)
        shutil.copytree(self.docs_dir, self.docs_raw_dir)
        self._log(f"  → Copied to docs_raw/")

        # Create docs/ with restructured layout
        self.docs_rendered_dir.mkdir(parents=True, exist_ok=True)

        # Copy and restructure, excluding internal planning files
        for item in self.docs_dir.iterdir():
            # Skip excluded planning files
            if item.name in self.EXCLUDED_FILES:
                self._log(f"  → Excluded internal file: {item.name}")
                continue

            dest = self.docs_rendered_dir / item.name

            if item.name == "docs":
                # Rename docs/ to components/ to avoid confusion
                dest = self.docs_rendered_dir / "components"
                if item.is_dir():
                    shutil.copytree(item, dest)
            elif item.name == "overview.md":
                # Copy overview.md as index.md (main landing page)
                shutil.copy2(item, self.docs_rendered_dir / "index.md")
                # Don't keep duplicate overview.md
            elif item.is_dir():
                shutil.copytree(item, dest)
            else:
                shutil.copy2(item, dest)

        self._log(f"  → Restructured to docs/")

    def _process_file(self, md_file: Path) -> dict:
        """Process a single markdown file."""
        stats = {
            'diagrams_found': 0,
            'diagrams_rendered': 0,
            'diagrams_failed': 0,
            'links_fixed': 0,
            'internal_links_fixed': 0,
            'markdown_fixed': 0
        }

        content = md_file.read_text(encoding='utf-8')
        original_content = content

        # Step 1: Fix markdown issues (stray backticks, etc.)
        content, markdown_fixes = self._fix_markdown_issues(content)
        stats['markdown_fixed'] = markdown_fixes

        # Step 2: Fix GitHub links
        if self.repo_owner and self.repo_name:
            content, links_fixed = self._fix_github_links(content)
            stats['links_fixed'] = links_fixed
            if links_fixed > 0:
                logger.debug(f"  Fixed {links_fixed} GitHub links in {md_file.name}")

        # Step 3: Fix broken internal links (links to components that weren't documented)
        content, internal_fixed = self._fix_broken_internal_links(content, md_file)
        stats['internal_links_fixed'] = internal_fixed
        if internal_fixed > 0:
            logger.debug(f"  Fixed {internal_fixed} broken internal links in {md_file.name}")

        # Step 4: Find and render ALL mermaid diagrams
        all_matches = []
        for pattern in self.MERMAID_PATTERNS:
            matches = list(pattern.finditer(content))
            for match in matches:
                # Check if this match overlaps with existing ones
                overlaps = False
                for existing in all_matches:
                    if (match.start() < existing[1] and match.end() > existing[0]):
                        overlaps = True
                        break
                if not overlaps:
                    all_matches.append((match.start(), match.end(), match))

        # Sort by position
        all_matches.sort(key=lambda x: x[0])
        unique_matches = [m[2] for m in all_matches]

        if unique_matches:
            stats['diagrams_found'] = len(unique_matches)
            self._log(f"Found {len(unique_matches)} mermaid diagrams in {md_file.name}")

            # Process in reverse to preserve positions
            for i, match in enumerate(reversed(unique_matches)):
                diagram_code = match.group(1).strip()
                diagram_index = len(unique_matches) - 1 - i

                # Generate unique filename
                diagram_hash = hashlib.md5(diagram_code.encode()).hexdigest()[:8]
                diagram_name = f"{md_file.stem}_diagram_{diagram_index}_{diagram_hash}"

                # Render diagram with retries
                success, image_path = self._render_mermaid_with_retry(
                    diagram_code,
                    md_file.parent,
                    diagram_name,
                    max_retries=2
                )

                if success and image_path:
                    title = self._extract_diagram_title(diagram_code)
                    image_md = f"![{title}]({image_path.name})"
                    content = content[:match.start()] + image_md + content[match.end():]
                    stats['diagrams_rendered'] += 1
                    self._log(f"  ✓ Rendered: {diagram_name}.png")
                else:
                    stats['diagrams_failed'] += 1
                    # Leave a comment about the failed diagram
                    fallback = f"<!-- MERMAID RENDER FAILED: {diagram_name} -->\n{match.group(0)}"
                    content = content[:match.start()] + fallback + content[match.end():]
                    self._log(f"  ✗ Failed: diagram {diagram_index} in {md_file.name}")

        # Write if changed
        if content != original_content:
            md_file.write_text(content, encoding='utf-8')

        return stats

    def _fix_markdown_issues(self, content: str) -> Tuple[str, int]:
        """Fix common markdown issues like stray backticks."""
        fixes = 0

        # Fix stray backticks at end of file/sections
        if self.STRAY_BACKTICKS_PATTERN.search(content):
            content = self.STRAY_BACKTICKS_PATTERN.sub('\n', content)
            fixes += 1

        # Fix unclosed code blocks (orphan ```)
        lines = content.split('\n')
        in_code_block = False
        code_block_lang = None
        fixed_lines = []

        for i, line in enumerate(lines):
            stripped = line.strip()

            if stripped.startswith('```'):
                if in_code_block:
                    # This closes the current block
                    in_code_block = False
                    code_block_lang = None
                else:
                    # This opens a new block
                    in_code_block = True
                    # Extract language if present
                    lang_match = re.match(r'```(\w+)?', stripped)
                    code_block_lang = lang_match.group(1) if lang_match else None

            fixed_lines.append(line)

        # If we ended in an unclosed code block, close it
        if in_code_block:
            fixed_lines.append('```')
            fixes += 1

        return '\n'.join(fixed_lines), fixes

    def _fix_github_links(self, content: str) -> Tuple[str, int]:
        """Fix GitHub links to point to the correct repository."""
        fixed_count = 0

        def replace_link(match):
            nonlocal fixed_count
            owner = match.group(1)
            repo = match.group(2)
            link_type = match.group(3)
            branch = match.group(4)
            path = match.group(5)

            if owner != self.repo_owner or repo != self.repo_name:
                fixed_count += 1
                return f"https://github.com/{self.repo_owner}/{self.repo_name}/{link_type}/{branch}/{path}"

            return match.group(0)

        fixed_content = self.GITHUB_LINK_PATTERN.sub(replace_link, content)
        return fixed_content, fixed_count

    def _fix_broken_internal_links(self, content: str, file_path: Path) -> Tuple[str, int]:
        """
        Find internal markdown links and convert broken ones to plain text.

        [Link Text](../component/file.md) → Link Text (if target doesn't exist)

        This handles the case where documentation was generated with cross-links
        to components that were never successfully documented.

        Args:
            content: The markdown content to process
            file_path: Path to the current file (for resolving relative links)

        Returns:
            Tuple of (fixed content, number of links fixed)
        """
        # Match markdown links: [text](path)
        # Exclude external links (http/https) and anchors (#)
        INTERNAL_LINK_PATTERN = re.compile(
            r'\[([^\]]+)\]\((?!https?://|#)([^)]+\.md(?:#[^)]*)?)\)'
        )

        fixed_count = 0

        def check_and_fix(match):
            nonlocal fixed_count
            link_text = match.group(1)
            link_path = match.group(2)

            # Remove anchor from path for file existence check
            path_without_anchor = link_path.split('#')[0]

            # Resolve relative path from current file's directory
            target = (file_path.parent / path_without_anchor).resolve()

            if not target.exists():
                fixed_count += 1
                # Convert to plain text - just the link text
                return link_text

            return match.group(0)  # Keep original if target exists

        fixed_content = INTERNAL_LINK_PATTERN.sub(check_and_fix, content)
        return fixed_content, fixed_count

    def _sanitize_mermaid(self, code: str) -> str:
        """Sanitize mermaid code to fix common syntax issues."""
        lines = code.split('\n')
        sanitized = []

        for line in lines:
            # Skip empty lines at start
            if not sanitized and not line.strip():
                continue

            # Remove inline comments that might break parsing
            if '#' in line and not line.strip().startswith('#'):
                parts = line.split('#')
                if len(parts) > 1:
                    before = parts[0].rstrip()
                    # Only remove if it looks like a comment, not a color
                    if before.endswith(';') or '-->' in before or '-.>' in before or '==>' in before:
                        line = before

            # Fix subgraph names with parentheses - mermaid doesn't allow them
            # e.g., "subgraph Name (src/file.ts)" → "subgraph Name"
            if line.strip().startswith('subgraph '):
                # Remove parentheses and their contents from subgraph names
                line = re.sub(r'\([^)]*\)', '', line)
                # Clean any remaining special characters except basic ones
                parts = line.split('subgraph ', 1)
                if len(parts) > 1:
                    name = parts[1].strip()
                    # Keep only alphanumeric, spaces, underscores, hyphens
                    cleaned_name = re.sub(r'[^a-zA-Z0-9\s_-]', '', name).strip()
                    if cleaned_name:
                        line = f'    subgraph {cleaned_name}'

            # Fix node labels with problematic characters
            def fix_label(match):
                content = match.group(1)
                # Replace parentheses in labels
                content = content.replace('(', ' - ').replace(')', '')
                content = content.replace('/', '-')
                return f'[{content}]'

            line = re.sub(r'\[([^\]]+)\]', fix_label, line)

            # Fix parentheses in node definitions
            def fix_paren_label(match):
                prefix = match.group(1)
                content = match.group(2)
                if '(' in content or ')' in content:
                    content = content.replace('(', ' - ').replace(')', '')
                return f'{prefix}({content})'

            line = re.sub(r'(\w+)\(([^)]+)\)', fix_paren_label, line)

            sanitized.append(line)

        # Also remove style references to subgraphs with spaces (invalid)
        result = '\n'.join(sanitized)
        result = re.sub(r'^\s*style\s+\w+\s+\w+\s+fill:[^\n]*$', '', result, flags=re.MULTILINE)

        return result

    def _render_mermaid_with_retry(
        self,
        code: str,
        output_dir: Path,
        name: str,
        max_retries: int = 2
    ) -> Tuple[bool, Optional[Path]]:
        """Render mermaid code with retries and sanitization."""
        if not self.mmdc_path:
            return False, None

        # First attempt with original code
        success, path = self._render_mermaid(code, output_dir, name)
        if success:
            return True, path

        # Retry with sanitized code
        for attempt in range(max_retries):
            sanitized = self._sanitize_mermaid(code)
            if sanitized != code:
                success, path = self._render_mermaid(sanitized, output_dir, f"{name}_sanitized")
                if success:
                    # Rename to original name
                    final_path = output_dir / f"{name}.png"
                    if path and path.exists():
                        shutil.move(str(path), str(final_path))
                    return True, final_path

            # Try with simplified theme
            if attempt == max_retries - 1:
                success, path = self._render_mermaid(
                    sanitized, output_dir, name,
                    theme_override="neutral"
                )
                if success:
                    return True, path

        return False, None

    def _render_mermaid(
        self,
        code: str,
        output_dir: Path,
        name: str,
        theme_override: Optional[str] = None
    ) -> Tuple[bool, Optional[Path]]:
        """Render mermaid code to PNG."""
        if not self.mmdc_path:
            return False, None

        output_dir.mkdir(parents=True, exist_ok=True)
        output_path = output_dir / f"{name}.png"

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.mmd', delete=False, encoding='utf-8'
        ) as f:
            f.write(code)
            temp_input = Path(f.name)

        try:
            theme = theme_override or self.theme.value
            cmd = [
                self.mmdc_path,
                "-i", str(temp_input),
                "-o", str(output_path),
                "-t", theme,
                "-b", self.background,
                "-s", str(self.scale),
                "--quiet"
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0 and output_path.exists():
                return True, output_path
            else:
                if result.stderr:
                    logger.debug(f"mmdc error: {result.stderr[:300]}")
                return False, None

        except subprocess.TimeoutExpired:
            logger.debug(f"mmdc timeout for {name}")
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
            'sequence': 'Sequence Diagram',
            'classdiagram': 'Class Diagram',
            'class': 'Class Diagram',
            'statediagram': 'State Diagram',
            'state': 'State Diagram',
            'erdiagram': 'ER Diagram',
            'gantt': 'Gantt Chart',
            'pie': 'Pie Chart',
            'mindmap': 'Mind Map',
            'timeline': 'Timeline',
            'journey': 'User Journey',
            'gitgraph': 'Git Graph',
            'c4context': 'C4 Context Diagram',
        }

        for key, name in type_names.items():
            if first_line.startswith(key):
                return name

        return "Diagram"

    def _validate_against_doc_tree(self) -> List[ValidationError]:
        """
        Validate generated docs match the planned structure in doc_tree.json.

        Checks:
        1. All files in doc_tree.json exist
        2. Each file uses the correct heading from doc_tree.json
        3. Headings are clean (no code snippets, paths, or descriptions)

        Returns:
            List of validation errors found
        """
        import json

        errors = []

        # Look for doc_tree.json in both source and build directories
        doc_tree_path = self.docs_dir / "doc_tree.json"
        if not doc_tree_path.exists():
            doc_tree_path = self.docs_raw_dir / "doc_tree.json" if self.docs_raw_dir else None

        if not doc_tree_path or not doc_tree_path.exists():
            return errors  # No tree to validate against

        try:
            tree = json.loads(doc_tree_path.read_text())
        except json.JSONDecodeError as e:
            errors.append(ValidationError(
                file_path=doc_tree_path,
                error_type="invalid_json",
                message=f"doc_tree.json has invalid JSON: {e}"
            ))
            return errors

        # Flatten the tree structure to get all file paths and metadata
        def flatten_tree(structure: dict, prefix: str = "") -> list:
            """Recursively flatten the tree structure."""
            items = []
            for key, value in structure.items():
                if key.endswith('.md'):
                    # This is a file
                    path = prefix + key
                    items.append((path, value))
                elif key.endswith('/'):
                    # This is a directory - recurse
                    items.extend(flatten_tree(value, prefix + key))
            return items

        if "structure" not in tree:
            return errors

        file_entries = flatten_tree(tree["structure"])

        # Map source paths to rendered paths
        # Source: planning/docs/{component}/ -> Rendered: build/docs/components/{component}/
        def map_to_rendered_path(source_path: str) -> Path:
            """Map doc_tree path to actual rendered path."""
            # The doc_tree uses paths relative to planning/docs/
            # But we restructure: docs/ -> components/
            if source_path.startswith("docs/"):
                return self.docs_rendered_dir / "components" / source_path[5:]
            return self.docs_rendered_dir / source_path

        # Validate each file
        for rel_path, metadata in file_entries:
            full_path = map_to_rendered_path(rel_path)

            # Check file exists
            if not full_path.exists():
                # Also check without the restructuring
                alt_path = self.docs_rendered_dir / rel_path
                if not alt_path.exists():
                    errors.append(ValidationError(
                        file_path=full_path,
                        error_type="missing_file",
                        message=f"File from doc_tree.json not found: {rel_path}"
                    ))
                    continue
                else:
                    full_path = alt_path

            # Check heading matches
            expected_heading = metadata.get("heading")
            if expected_heading:
                try:
                    content = full_path.read_text(encoding='utf-8')

                    # Look for the H1 heading
                    h1_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                    if h1_match:
                        actual_heading = h1_match.group(1).strip()

                        # Check for bad heading patterns
                        bad_patterns = [
                            (r'^Assuming\s+', "Heading starts with 'Assuming'"),
                            (r'^func\s+\w+\(', "Heading is a function signature"),
                            (r'^class\s+\w+', "Heading is a class definition"),
                            (r'^src/', "Heading is a file path"),
                            (r'^pkg/', "Heading is a file path"),
                            (r'^cmd/', "Heading is a file path"),
                            (r'\.go$', "Heading ends with .go"),
                            (r'\.py$', "Heading ends with .py"),
                            (r'\.ts$', "Heading ends with .ts"),
                            (r'This\s+(service|component|module)\s+', "Heading is a description"),
                        ]

                        for pattern, description in bad_patterns:
                            if re.search(pattern, actual_heading, re.IGNORECASE):
                                errors.append(ValidationError(
                                    file_path=full_path,
                                    error_type="bad_heading",
                                    message=f"{description}: '{actual_heading[:50]}...'"
                                ))
                                break

                        # Check if heading matches expected (case-insensitive comparison)
                        if actual_heading.lower() != expected_heading.lower():
                            # Only warn if significantly different
                            if not (actual_heading.lower().startswith(expected_heading.lower()) or
                                    expected_heading.lower().startswith(actual_heading.lower())):
                                errors.append(ValidationError(
                                    file_path=full_path,
                                    error_type="heading_mismatch",
                                    message=f"Expected heading '{expected_heading}', got '{actual_heading[:50]}'"
                                ))
                    else:
                        errors.append(ValidationError(
                            file_path=full_path,
                            error_type="missing_heading",
                            message=f"No H1 heading found, expected '{expected_heading}'"
                        ))
                except Exception as e:
                    logger.debug(f"Error reading {full_path}: {e}")

        return errors

    def _validate_no_unrendered_mermaid(self) -> List[ValidationError]:
        """Check that no mermaid code blocks remain unrendered."""
        errors = []

        for md_file in self.docs_rendered_dir.rglob("*.md"):
            content = md_file.read_text(encoding='utf-8')

            # Find any remaining mermaid blocks
            for match in self.UNRENDERED_MERMAID_PATTERN.finditer(content):
                # Find line number
                line_num = content[:match.start()].count('\n') + 1
                errors.append(ValidationError(
                    file_path=md_file,
                    error_type="unrendered_mermaid",
                    message=f"Unrendered mermaid block at line {line_num}",
                    line_number=line_num
                ))

        return errors

    def _attempt_mermaid_recovery(self, md_file: Path) -> None:
        """Attempt to recover/re-render failed mermaid diagrams."""
        content = md_file.read_text(encoding='utf-8')

        # Try each pattern again
        for pattern in self.MERMAID_PATTERNS:
            matches = list(pattern.finditer(content))
            if not matches:
                continue

            for i, match in enumerate(reversed(matches)):
                diagram_code = match.group(1).strip()
                diagram_hash = hashlib.md5(diagram_code.encode()).hexdigest()[:8]
                diagram_name = f"{md_file.stem}_recovery_{i}_{diagram_hash}"

                # Try aggressive sanitization
                sanitized = self._aggressive_sanitize(diagram_code)

                success, image_path = self._render_mermaid(
                    sanitized,
                    md_file.parent,
                    diagram_name,
                    theme_override="neutral"
                )

                if success and image_path:
                    title = self._extract_diagram_title(diagram_code)
                    image_md = f"![{title}]({image_path.name})"
                    content = content[:match.start()] + image_md + content[match.end():]
                    self._log(f"  ✓ Recovery succeeded: {diagram_name}")

        md_file.write_text(content, encoding='utf-8')

    def _aggressive_sanitize(self, code: str) -> str:
        """More aggressive sanitization for problematic diagrams."""
        code = self._sanitize_mermaid(code)

        # Remove style definitions that might cause issues
        code = re.sub(r'style\s+\w+\s+fill:[^,\n]+', '', code)
        code = re.sub(r'style\s+\w+\s+stroke:[^,\n]+', '', code)

        # Fix subgraph names - remove all special characters including parentheses
        # Pattern: subgraph Name (with stuff) → subgraph Name with stuff
        def fix_subgraph(match):
            name = match.group(1)
            # Remove parentheses and their content, or just the parens
            name = re.sub(r'\([^)]*\)', '', name)  # Remove (content)
            name = re.sub(r'[^a-zA-Z0-9\s_-]', '', name)  # Remove special chars
            name = name.strip()
            return f'subgraph {name}'

        code = re.sub(r'subgraph\s+([^\n\[]+?)(?=\n|\[)', fix_subgraph, code)

        # Also handle style references to subgraphs - they need to match the cleaned name
        # Remove style lines that reference complex subgraph names
        code = re.sub(r'^\s*style\s+[^a-zA-Z0-9_\s][^\n]*$', '', code, flags=re.MULTILINE)

        # Simplify edge labels
        code = re.sub(r'--\s*"[^"]+"\s*-->', '-->', code)
        code = re.sub(r'--\s*"[^"]+"\s*-.->', '-.->', code)

        return code

    def _ensure_index_exists(self) -> None:
        """Ensure a top-level index.md exists in the docs directory."""
        index_path = self.docs_rendered_dir / "index.md"

        if index_path.exists():
            # Enhance existing index if it's just an overview
            self._enhance_index_with_navigation(index_path)
            return

        # Look for existing index files
        possible_indices = [
            self.docs_rendered_dir / "overview.md",
            self.docs_rendered_dir / "README.md",
            self.docs_rendered_dir / "components" / "index.md",
        ]

        for candidate in possible_indices:
            if candidate.exists():
                # Copy as index.md
                shutil.copy(str(candidate), str(index_path))
                self._log(f"  → Created index.md from {candidate.name}")
                self._enhance_index_with_navigation(index_path)
                return

        # Create a basic index that links to all content
        self._log("  → Creating basic index.md")
        self._create_basic_index(index_path)

    def _enhance_index_with_navigation(self, index_path: Path) -> None:
        """Add navigation section to existing index if missing."""
        content = index_path.read_text(encoding='utf-8')

        # Check if it already has a components/navigation section
        if '## Components' in content or '## Documentation' in content:
            return

        # Find components
        components_dir = self.docs_rendered_dir / "components"
        if not components_dir.exists():
            return

        # Build navigation section
        nav_section = ["\n\n---\n\n## Component Documentation\n\n"]

        for component_dir in sorted(components_dir.iterdir()):
            if not component_dir.is_dir():
                continue

            index_file = component_dir / "index.md"
            if index_file.exists():
                # Extract title from component index
                try:
                    comp_content = index_file.read_text(encoding='utf-8')
                    title_match = re.search(r'^#\s+(.+)$', comp_content, re.MULTILINE)
                    title = title_match.group(1) if title_match else component_dir.name.replace('_', ' ').title()
                except:
                    title = component_dir.name.replace('_', ' ').title()

                rel_path = index_file.relative_to(self.docs_rendered_dir)
                nav_section.append(f"- [{title}](components/{component_dir.name}/index.md)\n")

        if len(nav_section) > 1:
            content += ''.join(nav_section)
            index_path.write_text(content, encoding='utf-8')
            self._log(f"  → Enhanced index.md with navigation")

    def _create_basic_index(self, index_path: Path) -> None:
        """Create a comprehensive index.md with links to all documentation."""
        content = ["# Documentation\n\n"]

        # Add overview section if overview.md exists
        overview_path = self.docs_rendered_dir / "overview.md"
        if overview_path.exists():
            try:
                overview_content = overview_path.read_text(encoding='utf-8')
                # Extract first paragraph after title
                lines = overview_content.split('\n')
                intro_lines = []
                in_intro = False
                for line in lines:
                    if line.startswith('#'):
                        in_intro = True
                        continue
                    if in_intro:
                        if line.strip() == '' and intro_lines:
                            break
                        if line.strip():
                            intro_lines.append(line)
                if intro_lines:
                    content.append('\n'.join(intro_lines[:5]) + '\n\n')
            except:
                pass

        # Add components section
        components_dir = self.docs_rendered_dir / "components"
        if components_dir.exists():
            content.append("## Components\n\n")

            for component_dir in sorted(components_dir.iterdir()):
                if not component_dir.is_dir():
                    continue

                index_file = component_dir / "index.md"
                if index_file.exists():
                    try:
                        comp_content = index_file.read_text(encoding='utf-8')
                        title_match = re.search(r'^#\s+(.+)$', comp_content, re.MULTILINE)
                        title = title_match.group(1) if title_match else component_dir.name.replace('_', ' ').title()

                        # Try to get description (first paragraph)
                        desc_match = re.search(r'^#[^\n]+\n+([^\n#]+)', comp_content)
                        desc = desc_match.group(1).strip()[:100] if desc_match else ""
                    except:
                        title = component_dir.name.replace('_', ' ').title()
                        desc = ""

                    content.append(f"### [{title}](components/{component_dir.name}/index.md)\n\n")
                    if desc:
                        content.append(f"{desc}\n\n")

        # Add other files section
        other_files = []
        for md_file in sorted(self.docs_rendered_dir.glob("*.md")):
            if md_file.name in ('index.md', 'overview.md'):
                continue
            try:
                file_content = md_file.read_text(encoding='utf-8')
                title_match = re.search(r'^#\s+(.+)$', file_content, re.MULTILINE)
                title = title_match.group(1) if title_match else md_file.stem.replace('_', ' ').title()
            except:
                title = md_file.stem.replace('_', ' ').title()
            other_files.append(f"- [{title}]({md_file.name})\n")

        if other_files:
            content.append("\n## Additional Resources\n\n")
            content.extend(other_files)

        index_path.write_text(''.join(content), encoding='utf-8')

    def _build_navigation(self) -> list:
        """Build navigation structure for mkdocs."""
        nav = []

        # Home/Index
        if (self.docs_rendered_dir / "index.md").exists():
            nav.append({"Home": "index.md"})

        # Components section
        components_dir = self.docs_rendered_dir / "components"
        if components_dir.exists():
            components_nav = []
            for component_dir in sorted(components_dir.iterdir()):
                if not component_dir.is_dir():
                    continue

                # Get component title from index.md
                index_file = component_dir / "index.md"
                if index_file.exists():
                    try:
                        content = index_file.read_text(encoding='utf-8')
                        title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                        title = title_match.group(1) if title_match else component_dir.name.replace('_', ' ').title()
                        # Sanitize title - remove escaped newlines and special chars
                        title = title.replace('\\n', ' ').replace('\n', ' ').replace('\\', '')
                        title = ' '.join(title.split()).strip()
                    except:
                        title = component_dir.name.replace('_', ' ').title()
                else:
                    title = component_dir.name.replace('_', ' ').title()

                # Build component nav with sub-pages in LOGICAL ORDER
                component_nav = []

                # Define preferred order for component pages
                preferred_order = ['index.md', 'architecture.md', 'api_reference.md', 'configuration.md']
                preferred_titles = {
                    'index.md': 'Overview',
                    'architecture.md': 'Architecture',
                    'api_reference.md': 'API Reference',
                    'configuration.md': 'Configuration'
                }

                # Add files in preferred order first
                md_files = list(component_dir.glob("*.md"))
                added_files = set()

                for preferred_file in preferred_order:
                    file_path = component_dir / preferred_file
                    if file_path.exists():
                        nav_title = preferred_titles.get(preferred_file, preferred_file.replace('_', ' ').replace('.md', '').title())
                        component_nav.append({nav_title: f"components/{component_dir.name}/{preferred_file}"})
                        added_files.add(preferred_file)

                # Add any remaining files alphabetically
                for md_file in sorted(md_files):
                    if md_file.name in added_files:
                        continue
                    try:
                        file_content = md_file.read_text(encoding='utf-8')
                        file_title_match = re.search(r'^#\s+(.+)$', file_content, re.MULTILINE)
                        file_title = file_title_match.group(1) if file_title_match else md_file.stem.replace('_', ' ').title()
                    except:
                        file_title = md_file.stem.replace('_', ' ').title()
                    component_nav.append({file_title: f"components/{component_dir.name}/{md_file.name}"})

                if component_nav:
                    components_nav.append({title: component_nav})

            if components_nav:
                nav.append({"Components": components_nav})

        # Other top-level files (excluding internal planning files)
        excluded_from_nav = {'index.md', 'overview.md'} | self.EXCLUDED_FILES
        other_files = []
        for md_file in sorted(self.docs_rendered_dir.glob("*.md")):
            if md_file.name in excluded_from_nav:
                continue
            try:
                content = md_file.read_text(encoding='utf-8')
                title_match = re.search(r'^#\s+(.+)$', content, re.MULTILINE)
                title = title_match.group(1) if title_match else md_file.stem.replace('_', ' ').title()
            except:
                title = md_file.stem.replace('_', ' ').title()
            other_files.append({title: md_file.name})

        if other_files:
            nav.append({"Resources": other_files})

        return nav

    def _format_nav_yaml(self, nav_items: list) -> str:
        """Format navigation items as YAML for mkdocs config."""
        if not nav_items:
            return ""

        def sanitize_title(title: str) -> str:
            """Sanitize a title for use in YAML nav."""
            # Remove literal \n sequences and actual newlines
            title = title.replace('\\n', ' ').replace('\n', ' ')
            # Remove backslashes
            title = title.replace('\\', '')
            # Collapse multiple spaces
            title = ' '.join(title.split())
            # Remove quotes that could break YAML
            title = title.replace('"', "'")
            return title.strip()

        def format_item(item, indent=0):
            lines = []
            prefix = "  " * indent
            if isinstance(item, dict):
                for key, value in item.items():
                    safe_key = sanitize_title(key)
                    if isinstance(value, str):
                        lines.append(f'{prefix}- "{safe_key}": {value}')
                    elif isinstance(value, list):
                        lines.append(f'{prefix}- "{safe_key}":')
                        for sub_item in value:
                            lines.extend(format_item(sub_item, indent + 1))
            return lines

        yaml_lines = ["nav:"]
        for item in nav_items:
            yaml_lines.extend(format_item(item, 1))

        return '\n'.join(yaml_lines)

    def _generate_html(self) -> bool:
        """Generate HTML site using mkdocs."""
        if not self.mkdocs_path:
            logger.error("mkdocs not installed - cannot generate HTML site")
            return False

        # Build navigation structure
        nav_items = self._build_navigation()
        nav_yaml = self._format_nav_yaml(nav_items)

        # Create mkdocs config
        config_content = f"""
site_name: Documentation
docs_dir: "{self.docs_rendered_dir}"
site_dir: "{self.html_output_dir}"
use_directory_urls: false

theme:
  name: material
  palette:
    scheme: default
  features:
    - navigation.instant
    - navigation.sections
    - navigation.expand
    - search.highlight
    - toc.integrate

plugins:
  - search

markdown_extensions:
  - toc:
      permalink: true
  - tables
  - fenced_code
  - attr_list
  - admonition
  - pymdownx.details
  - pymdownx.superfences

{nav_yaml}
"""

        with tempfile.NamedTemporaryFile(
            mode='w', suffix='.yml', delete=False, encoding='utf-8'
        ) as f:
            f.write(config_content)
            config_path = Path(f.name)

        try:
            self.html_output_dir.mkdir(parents=True, exist_ok=True)

            self._log(f"Running mkdocs build...")
            logger.debug(f"  docs_dir: {self.docs_rendered_dir}")
            logger.debug(f"  site_dir: {self.html_output_dir}")

            result = subprocess.run(
                [self.mkdocs_path, "build", "-f", str(config_path), "--clean"],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(self.build_dir.parent)
            )

            if result.returncode == 0:
                if self.html_output_dir.exists() and any(self.html_output_dir.iterdir()):
                    self._log(f"HTML site generated successfully")
                    return True
                else:
                    self._log(f"ERROR: mkdocs completed but site dir is empty")
                    return False
            else:
                self._log(f"ERROR: mkdocs build failed")
                if result.stderr:
                    logger.error(f"  stderr: {result.stderr[:500]}")
                return False

        except subprocess.TimeoutExpired:
            self._log("ERROR: mkdocs build timed out")
            return False
        except Exception as e:
            self._log(f"ERROR: HTML generation failed: {e}")
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
        print(f"Docs (raw):         {result.docs_raw_dir}")
        print(f"Docs (rendered):    {result.docs_rendered_dir}")
        print(f"HTML:               {result.html_output_dir}")
        print(f"Files processed:    {result.files_processed}")
        print(f"Diagrams rendered:  {result.diagrams_rendered}/{result.diagrams_found}")
        print(f"GitHub links fixed: {result.github_links_fixed}")
        print(f"Internal links fixed: {result.internal_links_fixed}")
        print(f"Markdown fixes:     {result.markdown_issues_fixed}")

        if result.validation_errors:
            print(f"\nValidation Errors ({len(result.validation_errors)}):")
            for err in result.validation_errors[:10]:
                print(f"  - {err.file_path.name}: {err.message}")

        if result.errors:
            print(f"\nErrors ({len(result.errors)}):")
            for err in result.errors[:10]:
                print(f"  - {err}")

        if result.html_output_dir and result.html_output_dir.exists():
            print(f"\n{'='*60}")
            print(f"View site: cd {result.html_output_dir} && python3 -m http.server 8080")
            print(f"{'='*60}")
