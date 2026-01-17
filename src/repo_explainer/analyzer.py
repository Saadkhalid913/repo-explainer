"""Code analyzer with tree-sitter and AST support."""

import ast
import json
from dataclasses import asdict
from pathlib import Path
from typing import Any, Optional

from rich.console import Console

from repo_explainer.models import ComponentInfo, FileInfo, LanguageType, RepositoryInfo

# Try to import tree-sitter (optional dependency for enhanced parsing)
try:
    import tree_sitter_python as tspython
    import tree_sitter_javascript as tsjavascript
    import tree_sitter_typescript as tstypescript
    from tree_sitter import Language, Parser

    TREE_SITTER_AVAILABLE = True
except ImportError:
    TREE_SITTER_AVAILABLE = False


class CodeAnalyzer:
    """Analyzes code structure and extracts component information."""

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self._parsers: dict[LanguageType, Any] = {}

        if TREE_SITTER_AVAILABLE:
            self._init_tree_sitter()

    def _init_tree_sitter(self) -> None:
        """Initialize tree-sitter parsers for supported languages."""
        if not TREE_SITTER_AVAILABLE:
            return

        try:
            # Python parser
            py_parser = Parser(Language(tspython.language()))
            self._parsers[LanguageType.PYTHON] = py_parser

            # JavaScript parser
            js_parser = Parser(Language(tsjavascript.language()))
            self._parsers[LanguageType.JAVASCRIPT] = js_parser

            # TypeScript parser
            ts_parser = Parser(Language(tstypescript.language_typescript()))
            self._parsers[LanguageType.TYPESCRIPT] = ts_parser
        except Exception as e:
            self.console.print(f"[yellow]Warning: Failed to initialize tree-sitter: {e}[/]")

    def analyze_repository(
        self, repo_path: Path, repo_info: RepositoryInfo
    ) -> list[ComponentInfo]:
        """
        Analyze the repository and extract component information.

        This provides local enrichment data that can be sent to OpenCode
        for more comprehensive analysis.
        """
        components: list[ComponentInfo] = []

        # Analyze directory structure as top-level components
        for entry in repo_path.iterdir():
            if entry.is_dir() and not entry.name.startswith("."):
                if entry.name in ("node_modules", "__pycache__", ".git", "venv", ".venv"):
                    continue

                component = self._analyze_directory(entry, repo_path)
                if component:
                    components.append(component)

        # Build dependency graph between components
        self._analyze_dependencies(components, repo_path)

        return components

    def _analyze_dependencies(
        self, components: list[ComponentInfo], repo_path: Path
    ) -> None:
        """Analyze import statements to build dependency graph between components."""
        component_names = {c.id for c in components}
        
        for component in components:
            internal_deps: set[str] = set()
            external_deps: set[str] = set()
            
            for file_path in component.files:
                full_path = repo_path / file_path
                if not full_path.exists():
                    continue
                    
                if full_path.suffix == ".py":
                    structure = self.extract_python_structure(full_path)
                    for imp in structure.get("imports", []):
                        # Check if this import matches another component
                        top_module = imp.split(".")[0]
                        if top_module in component_names and top_module != component.id:
                            internal_deps.add(top_module)
                        elif not imp.startswith("."):
                            # External dependency (not relative import)
                            external_deps.add(top_module)
                            
                elif full_path.suffix in (".js", ".jsx", ".ts", ".tsx"):
                    # Simple regex-based import extraction for JS/TS
                    try:
                        content = full_path.read_text(encoding="utf-8")
                        import re
                        # Match import statements
                        for match in re.finditer(r"(?:import|require)\s*\(?['\"]([^'\"]+)['\"]", content):
                            imp = match.group(1)
                            if imp.startswith("."):
                                # Relative import - check if it crosses into another component
                                continue
                            top_module = imp.split("/")[0]
                            if top_module in component_names and top_module != component.id:
                                internal_deps.add(top_module)
                            elif not top_module.startswith("@"):
                                external_deps.add(top_module)
                            elif top_module.startswith("@"):
                                # Scoped package
                                external_deps.add(imp.split("/")[0] + "/" + imp.split("/")[1] if "/" in imp else top_module)
                    except (UnicodeDecodeError, OSError):
                        continue
            
            component.dependencies = list(internal_deps)
            component.external_dependencies = list(external_deps)

    def _analyze_directory(
        self, dir_path: Path, repo_root: Path
    ) -> Optional[ComponentInfo]:
        """Analyze a directory as a potential component."""
        # Count source files
        source_files: list[Path] = []
        for ext in (".py", ".js", ".jsx", ".ts", ".tsx"):
            source_files.extend(dir_path.rglob(f"*{ext}"))

        if not source_files:
            return None

        # Try to determine component type
        component_type = self._infer_component_type(dir_path, source_files)

        return ComponentInfo(
            id=dir_path.name,
            name=dir_path.name,
            component_type=component_type,
            path=dir_path.relative_to(repo_root),
            files=[f.relative_to(repo_root) for f in source_files[:20]],  # Limit for now
        )

    def _infer_component_type(
        self, dir_path: Path, source_files: list[Path]
    ) -> str:
        """Infer the component type based on naming and structure."""
        name_lower = dir_path.name.lower()

        # Check for common patterns
        if any(
            pattern in name_lower
            for pattern in ("service", "api", "server", "backend")
        ):
            return "service"
        elif any(pattern in name_lower for pattern in ("ui", "frontend", "client", "app")):
            return "module"
        elif any(pattern in name_lower for pattern in ("lib", "util", "helper", "common")):
            return "package"
        elif any(pattern in name_lower for pattern in ("test", "spec", "__test__")):
            return "tests"
        elif name_lower in ("src", "source"):
            return "source"
        else:
            return "module"

    def extract_python_structure(self, file_path: Path) -> dict[str, Any]:
        """Extract structure from a Python file using AST."""
        try:
            source = file_path.read_text(encoding="utf-8")
            tree = ast.parse(source)
        except (SyntaxError, UnicodeDecodeError):
            return {}

        structure: dict[str, Any] = {
            "classes": [],
            "functions": [],
            "imports": [],
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                class_info = {
                    "name": node.name,
                    "methods": [
                        m.name for m in node.body if isinstance(m, ast.FunctionDef)
                    ],
                    "bases": [self._get_name(b) for b in node.bases],
                    "line": node.lineno,
                }
                structure["classes"].append(class_info)

            elif isinstance(node, ast.FunctionDef) and not isinstance(
                getattr(node, "parent", None), ast.ClassDef
            ):
                # Top-level functions only
                if any(isinstance(parent, ast.ClassDef) for parent in ast.walk(tree)):
                    continue
                func_info = {
                    "name": node.name,
                    "args": [arg.arg for arg in node.args.args],
                    "line": node.lineno,
                }
                structure["functions"].append(func_info)

            elif isinstance(node, ast.Import):
                for alias in node.names:
                    structure["imports"].append(alias.name)

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    structure["imports"].append(node.module)

        return structure

    def _get_name(self, node: ast.expr) -> str:
        """Get a string name from an AST node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_name(node.value)}.{node.attr}"
        else:
            return "<unknown>"

    def prepare_analysis_context(
        self,
        repo_path: Path,
        repo_info: RepositoryInfo,
        components: list[ComponentInfo],
        file_tree: str,
    ) -> str:
        """
        Prepare context for OpenCode/LLM analysis.

        Returns a formatted string with repository structure and metadata
        suitable for inclusion in prompts.
        """
        context_parts = [
            f"# Repository: {repo_info.name}",
            "",
            "## Overview",
            f"- Primary Language: {repo_info.primary_language.value if repo_info.primary_language else 'Unknown'}",
            f"- Languages: {', '.join(l.value for l in repo_info.languages)}",
            f"- Size: {repo_info.size_category.value} ({repo_info.file_count} files, {repo_info.total_lines} lines)",
        ]

        if repo_info.git_remote:
            context_parts.append(f"- Git Remote: {repo_info.git_remote}")
        if repo_info.git_branch:
            context_parts.append(f"- Branch: {repo_info.git_branch}")

        context_parts.extend([
            "",
            "## Directory Structure",
            "```",
            file_tree,
            "```",
            "",
            "## Components",
        ])

        for component in components:
            context_parts.extend([
                f"### {component.name}",
                f"- Type: {component.component_type}",
                f"- Path: {component.path}",
                f"- Files: {len(component.files)}",
            ])

        return "\n".join(context_parts)

    def export_for_opencode(
        self,
        repo_info: RepositoryInfo,
        components: list[ComponentInfo],
    ) -> str:
        """Export analysis data as JSON for OpenCode commands."""
        data = {
            "repository": {
                "name": repo_info.name,
                "path": str(repo_info.path),
                "primary_language": (
                    repo_info.primary_language.value if repo_info.primary_language else None
                ),
                "languages": [l.value for l in repo_info.languages],
                "size_category": repo_info.size_category.value,
                "file_count": repo_info.file_count,
                "total_lines": repo_info.total_lines,
                "git_remote": repo_info.git_remote,
                "git_branch": repo_info.git_branch,
                "git_commit": repo_info.git_commit,
            },
            "components": [
                {
                    "id": c.id,
                    "name": c.name,
                    "type": c.component_type,
                    "path": str(c.path),
                    "files": [str(f) for f in c.files],
                }
                for c in components
            ],
        }
        return json.dumps(data, indent=2)
