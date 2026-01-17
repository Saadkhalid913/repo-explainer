"""Repository loading and Git operations."""

import re
import tempfile
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from git import GitCommandError, InvalidGitRepositoryError, Repo
from rich.console import Console

from repo_explainer.models import FileInfo, LanguageType, RepositoryInfo, SizeCategory


class RepositoryLoader:
    """Handles repository loading from local paths or Git URLs."""

    # File extensions to language mapping
    LANGUAGE_MAP: dict[str, LanguageType] = {
        ".py": LanguageType.PYTHON,
        ".pyw": LanguageType.PYTHON,
        ".js": LanguageType.JAVASCRIPT,
        ".jsx": LanguageType.JAVASCRIPT,
        ".mjs": LanguageType.JAVASCRIPT,
        ".cjs": LanguageType.JAVASCRIPT,
        ".ts": LanguageType.TYPESCRIPT,
        ".tsx": LanguageType.TYPESCRIPT,
        ".mts": LanguageType.TYPESCRIPT,
        ".cts": LanguageType.TYPESCRIPT,
    }

    # Directories to ignore during scanning
    IGNORE_DIRS = {
        ".git",
        ".svn",
        ".hg",
        "node_modules",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        "venv",
        ".venv",
        "env",
        ".env",
        "dist",
        "build",
        ".next",
        ".nuxt",
        "coverage",
        ".coverage",
        ".tox",
        "eggs",
        "*.egg-info",
    }

    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self._temp_dir: Optional[tempfile.TemporaryDirectory[str]] = None

    def load(self, repo_path: str) -> tuple[Path, RepositoryInfo]:
        """
        Load a repository from a local path or Git URL.

        Returns the resolved local path and repository info.
        """
        if self._is_git_url(repo_path):
            local_path = self._clone_repository(repo_path)
        else:
            local_path = Path(repo_path).resolve()
            if not local_path.exists():
                raise FileNotFoundError(f"Repository path does not exist: {local_path}")
            if not local_path.is_dir():
                raise ValueError(f"Repository path is not a directory: {local_path}")

        repo_info = self._analyze_repository(local_path)
        return local_path, repo_info

    def cleanup(self) -> None:
        """Clean up any temporary directories created for cloned repos."""
        if self._temp_dir:
            self._temp_dir.cleanup()
            self._temp_dir = None

    def _is_git_url(self, path: str) -> bool:
        """Check if the path is a Git URL."""
        # SSH format: git@github.com:user/repo.git
        if path.startswith("git@"):
            return True

        # HTTP(S) format
        parsed = urlparse(path)
        if parsed.scheme in ("http", "https"):
            return True

        # Git protocol
        if parsed.scheme == "git":
            return True

        return False

    def _clone_repository(self, url: str) -> Path:
        """Clone a remote repository to a temporary directory."""
        self._temp_dir = tempfile.TemporaryDirectory(prefix="repo-explainer-")
        clone_path = Path(self._temp_dir.name)

        self.console.print(f"[dim]Cloning repository from {url}...[/]")

        try:
            Repo.clone_from(url, clone_path, depth=1)  # Shallow clone for speed
        except GitCommandError as e:
            raise RuntimeError(f"Failed to clone repository: {e}") from e

        return clone_path

    def _analyze_repository(self, repo_path: Path) -> RepositoryInfo:
        """Analyze repository structure and gather metadata."""
        # Try to get Git info
        git_remote = None
        git_branch = None
        git_commit = None

        try:
            repo = Repo(repo_path)
            if repo.remotes:
                git_remote = repo.remotes.origin.url
            git_branch = repo.active_branch.name
            git_commit = repo.head.commit.hexsha[:8]
        except (InvalidGitRepositoryError, TypeError):
            pass  # Not a Git repo or detached HEAD

        # Scan files
        files = self._scan_files(repo_path)

        # Count languages
        language_counts: dict[LanguageType, int] = {}
        total_lines = 0

        for file_info in files:
            if file_info.language:
                language_counts[file_info.language] = (
                    language_counts.get(file_info.language, 0) + 1
                )
            total_lines += file_info.line_count

        # Determine primary language
        primary_language = None
        if language_counts:
            primary_language = max(language_counts, key=language_counts.get)  # type: ignore

        # Determine size category
        file_count = len(files)
        if file_count < 100:
            size_category = SizeCategory.SMALL
        elif file_count < 1000:
            size_category = SizeCategory.MEDIUM
        elif file_count < 10000:
            size_category = SizeCategory.LARGE
        else:
            size_category = SizeCategory.VERY_LARGE

        return RepositoryInfo(
            path=repo_path,
            name=repo_path.name,
            primary_language=primary_language,
            languages=list(language_counts.keys()),
            size_category=size_category,
            file_count=file_count,
            total_lines=total_lines,
            git_remote=git_remote,
            git_branch=git_branch,
            git_commit=git_commit,
        )

    def _scan_files(self, repo_path: Path) -> list[FileInfo]:
        """Scan repository for source files."""
        files: list[FileInfo] = []

        for path in repo_path.rglob("*"):
            # Skip directories
            if path.is_dir():
                continue

            # Skip ignored directories
            if any(ignored in path.parts for ignored in self.IGNORE_DIRS):
                continue

            # Skip hidden files
            if path.name.startswith("."):
                continue

            # Get file info
            suffix = path.suffix.lower()
            language = self.LANGUAGE_MAP.get(suffix)

            # Only include supported languages for now
            if language is None:
                continue

            try:
                size_bytes = path.stat().st_size
                # Count lines for text files
                line_count = 0
                if size_bytes < 1_000_000:  # Skip very large files
                    try:
                        line_count = len(path.read_text(encoding="utf-8").splitlines())
                    except (UnicodeDecodeError, PermissionError):
                        pass

                files.append(
                    FileInfo(
                        path=path.relative_to(repo_path),
                        language=language,
                        size_bytes=size_bytes,
                        line_count=line_count,
                    )
                )
            except OSError:
                pass  # Skip files we can't read

        return files

    def get_file_tree(self, repo_path: Path, max_depth: int = 3) -> str:
        """Generate a text representation of the file tree."""
        lines = [f"{repo_path.name}/"]
        self._build_tree(repo_path, "", lines, max_depth, current_depth=0)
        return "\n".join(lines)

    def _build_tree(
        self,
        path: Path,
        prefix: str,
        lines: list[str],
        max_depth: int,
        current_depth: int,
    ) -> None:
        """Recursively build the file tree."""
        if current_depth >= max_depth:
            return

        try:
            entries = sorted(path.iterdir(), key=lambda p: (p.is_file(), p.name.lower()))
        except PermissionError:
            return

        # Filter out ignored directories
        entries = [
            e for e in entries
            if not any(re.match(pattern.replace("*", ".*"), e.name) for pattern in self.IGNORE_DIRS)
            and not e.name.startswith(".")
        ]

        for i, entry in enumerate(entries):
            is_last = i == len(entries) - 1
            connector = "└── " if is_last else "├── "
            lines.append(f"{prefix}{connector}{entry.name}")

            if entry.is_dir():
                extension = "    " if is_last else "│   "
                self._build_tree(
                    entry, prefix + extension, lines, max_depth, current_depth + 1
                )
