#!/usr/bin/env python3
"""Validation script for coherent documentation structure."""

import re
import sys
from pathlib import Path
from typing import List, Tuple


class CoherenceValidator:
    """Validates the coherent documentation structure."""

    def __init__(self, docs_dir: Path):
        """
        Initialize the validator.

        Args:
            docs_dir: Path to the documentation directory
        """
        self.docs_dir = docs_dir
        self.errors: List[str] = []
        self.warnings: List[str] = []

    def validate(self) -> bool:
        """
        Run all validation checks.

        Returns:
            True if validation passes, False otherwise
        """
        print(f"Validating coherent documentation in: {self.docs_dir}\n")

        # Check 1: index.md exists
        if not self._validate_index_exists():
            return False

        # Check 2: Required subpages exist
        self._validate_subpages_exist()

        # Check 3: Validate links in index.md
        self._validate_index_links()

        # Check 4: Validate embedded diagrams
        self._validate_diagrams()

        # Check 5: Validate subpage structure
        self._validate_subpage_structure()

        # Check 6: Validate manifest
        self._validate_manifest()

        # Report results
        self._report_results()

        return len(self.errors) == 0

    def _validate_index_exists(self) -> bool:
        """Check that index.md exists."""
        index_path = self.docs_dir / "index.md"
        if not index_path.exists():
            self.errors.append("❌ index.md not found")
            return False
        print("✓ index.md exists")
        return True

    def _validate_subpages_exist(self) -> None:
        """Check that expected subpages exist."""
        expected_subpages = ["components.md", "dataflow.md", "tech-stack.md"]

        for subpage in expected_subpages:
            subpage_path = self.docs_dir / subpage
            if subpage_path.exists():
                print(f"✓ {subpage} exists")
            else:
                self.warnings.append(f"⚠ {subpage} not found (optional)")

    def _validate_index_links(self) -> None:
        """Validate that all links in index.md resolve to existing files."""
        index_path = self.docs_dir / "index.md"
        content = index_path.read_text()

        # Extract markdown links: [text](path)
        link_pattern = r"\[([^\]]+)\]\(([^\)]+)\)"
        links = re.findall(link_pattern, content)

        for link_text, link_path in links:
            # Skip external links and anchors
            if link_path.startswith(("http://", "https://", "#")):
                continue

            # Resolve relative path
            target_path = self.docs_dir / link_path

            if target_path.exists():
                print(f"✓ Link valid: [{link_text}]({link_path})")
            else:
                self.errors.append(f"❌ Broken link in index.md: [{link_text}]({link_path})")

    def _validate_diagrams(self) -> None:
        """Validate that diagram files exist."""
        diagrams_dir = self.docs_dir / "diagrams"

        if not diagrams_dir.exists():
            self.warnings.append("⚠ diagrams/ directory not found")
            return

        # Check for SVG files
        svg_files = list(diagrams_dir.glob("*.svg"))
        if svg_files:
            print(f"✓ Found {len(svg_files)} rendered diagram(s)")
            for svg_file in svg_files:
                print(f"  - {svg_file.name}")
        else:
            self.warnings.append("⚠ No rendered SVG diagrams found")

        # Verify Mermaid sources exist
        mermaid_files = list(self.docs_dir.glob("*.mermaid"))
        if mermaid_files:
            print(f"✓ Found {len(mermaid_files)} Mermaid source(s)")
            for mermaid_file in mermaid_files:
                print(f"  - {mermaid_file.name}")

    def _validate_subpage_structure(self) -> None:
        """Validate that subpages have proper structure."""
        subpages = ["components.md", "dataflow.md", "tech-stack.md"]

        for subpage_name in subpages:
            subpage_path = self.docs_dir / subpage_name
            if not subpage_path.exists():
                continue

            content = subpage_path.read_text()

            # Check for title (# heading)
            if not re.match(r"^#\s+", content):
                self.errors.append(f"❌ {subpage_name} missing title (# heading)")
            else:
                print(f"✓ {subpage_name} has proper title")

            # Check for content (at least 3 lines)
            if len(content.strip().split("\n")) < 3:
                self.warnings.append(f"⚠ {subpage_name} seems too short")

            # Check for diagram embeds or Mermaid blocks
            has_diagram = "![" in content or "```mermaid" in content
            if has_diagram:
                print(f"✓ {subpage_name} includes diagram/visualization")

    def _validate_manifest(self) -> None:
        """Validate that coherence manifest exists."""
        manifest_path = self.docs_dir / ".repo-explainer" / "coherence.json"

        if manifest_path.exists():
            print("✓ coherence.json manifest exists")

            try:
                import json

                manifest = json.loads(manifest_path.read_text())

                # Validate manifest structure
                if "timestamp" in manifest:
                    print(f"  - Timestamp: {manifest['timestamp']}")
                if "files" in manifest:
                    print(f"  - Files tracked: {len(manifest['files'])}")
                if "version" in manifest:
                    print(f"  - Version: {manifest['version']}")

            except json.JSONDecodeError:
                self.errors.append("❌ coherence.json is not valid JSON")
        else:
            self.warnings.append("⚠ coherence.json manifest not found")

    def _report_results(self) -> None:
        """Print validation results summary."""
        print("\n" + "=" * 60)
        print("VALIDATION SUMMARY")
        print("=" * 60)

        if self.errors:
            print(f"\n❌ Errors ({len(self.errors)}):")
            for error in self.errors:
                print(f"  {error}")

        if self.warnings:
            print(f"\n⚠ Warnings ({len(self.warnings)}):")
            for warning in self.warnings:
                print(f"  {warning}")

        if not self.errors and not self.warnings:
            print("\n✅ All validation checks passed!")
        elif not self.errors:
            print("\n✅ Validation passed with warnings")
        else:
            print("\n❌ Validation failed")


def main() -> int:
    """Run validation."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Validate coherent documentation structure"
    )
    parser.add_argument(
        "docs_dir",
        type=Path,
        nargs="?",
        default=Path("docs"),
        help="Path to documentation directory (default: ./docs)",
    )

    args = parser.parse_args()

    if not args.docs_dir.exists():
        print(f"Error: Documentation directory not found: {args.docs_dir}")
        return 1

    validator = CoherenceValidator(args.docs_dir)
    success = validator.validate()

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
