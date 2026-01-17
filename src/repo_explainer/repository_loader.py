"""Repository loader for cloning and resolving repository paths."""

import re
import shutil
from pathlib import Path
from typing import Tuple
from urllib.parse import urlparse

from git import Repo
from rich.console import Console

console = Console()


class RepositoryLoader:
    """Loads repositories from local paths or Git URLs."""

    def __init__(self, tmp_dir: Path = Path("./tmp")):
        """
        Initialize the repository loader.

        Args:
            tmp_dir: Directory to store cloned repositories (default: ./tmp)
        """
        self.tmp_dir = tmp_dir

    @staticmethod
    def is_git_url(path_or_url: str) -> bool:
        """
        Check if the input is a Git URL.

        Args:
            path_or_url: String that might be a Git URL or local path

        Returns:
            True if it's a Git URL, False otherwise

        Examples:
            >>> RepositoryLoader.is_git_url("https://github.com/user/repo")
            True
            >>> RepositoryLoader.is_git_url("git@github.com:user/repo.git")
            True
            >>> RepositoryLoader.is_git_url("./local/path")
            False
        """
        # Check for common Git URL patterns
        git_url_patterns = [
            r"^https?://",  # HTTP(S) URLs
            r"^git@",  # SSH URLs
            r"^ssh://",  # SSH protocol
            r"^git://",  # Git protocol
        ]

        return any(re.match(pattern, path_or_url) for pattern in git_url_patterns)

    @staticmethod
    def parse_git_url(git_url: str) -> Tuple[str, str]:
        """
        Parse a Git URL to extract owner and repository name.

        Args:
            git_url: Git URL to parse

        Returns:
            Tuple of (owner, repo_name)

        Examples:
            >>> RepositoryLoader.parse_git_url("https://github.com/torvalds/linux")
            ('torvalds', 'linux')
            >>> RepositoryLoader.parse_git_url("git@github.com:user/repo.git")
            ('user', 'repo')
        """
        # Handle SSH URLs like git@github.com:user/repo.git
        if git_url.startswith("git@"):
            # Extract the path part after the colon
            match = re.match(r"git@[^:]+:(.+)", git_url)
            if match:
                path = match.group(1)
            else:
                raise ValueError(f"Invalid SSH Git URL format: {git_url}")
        else:
            # Parse as regular URL
            parsed = urlparse(git_url)
            path = parsed.path

        # Remove leading slash and .git suffix
        path = path.lstrip("/").removesuffix(".git")

        # Split into owner and repo
        parts = path.split("/")
        if len(parts) < 2:
            raise ValueError(
                f"Cannot extract owner/repo from Git URL: {git_url}. "
                f"Expected format: owner/repo, got: {path}"
            )

        owner = parts[-2]
        repo = parts[-1]

        return owner, repo

    def get_clone_path(self, git_url: str) -> Path:
        """
        Get the local path where a Git URL should be cloned.

        Args:
            git_url: Git URL

        Returns:
            Path where the repository will be cloned (./tmp/owner/repo)

        Examples:
            >>> loader = RepositoryLoader()
            >>> loader.get_clone_path("https://github.com/torvalds/linux")
            Path('./tmp/torvalds/linux')
        """
        owner, repo = self.parse_git_url(git_url)
        return self.tmp_dir / owner / repo

    def clone_repository(self, git_url: str, force: bool = False) -> Path:
        """
        Clone a Git repository to the tmp directory.

        Args:
            git_url: Git URL to clone
            force: If True, remove existing directory and re-clone

        Returns:
            Path to the cloned repository

        Raises:
            ValueError: If the URL is invalid
            GitCommandError: If cloning fails
        """
        clone_path = self.get_clone_path(git_url)

        # Check if already cloned
        if clone_path.exists():
            if force:
                console.print(f"[yellow]Removing existing clone:[/yellow] {clone_path}")
                shutil.rmtree(clone_path)
            else:
                console.print(f"[dim]Using existing clone:[/dim] {clone_path}")
                return clone_path

        # Create parent directory
        clone_path.parent.mkdir(parents=True, exist_ok=True)

        # Clone the repository
        console.print(f"[cyan]Cloning repository:[/cyan] {git_url}")
        console.print(f"[dim]Destination:[/dim] {clone_path}")

        try:
            Repo.clone_from(git_url, str(clone_path), depth=1)
            console.print(f"[green]Clone successful![/green]")
            return clone_path
        except Exception as e:
            # Clean up failed clone
            if clone_path.exists():
                shutil.rmtree(clone_path)
            raise ValueError(f"Failed to clone repository: {str(e)}") from e

    def load(self, path_or_url: str, force_clone: bool = False) -> Path:
        """
        Load a repository from a local path or Git URL.

        If a Git URL is provided, the repository will be cloned to ./tmp/owner/repo.
        If a local path is provided, it will be returned as-is.

        Args:
            path_or_url: Local path or Git URL
            force_clone: If True, remove and re-clone existing repositories

        Returns:
            Path to the repository (either the input path or cloned path)

        Examples:
            >>> loader = RepositoryLoader()
            >>> loader.load("./my-project")
            Path('./my-project')
            >>> loader.load("https://github.com/user/repo")
            Path('./tmp/user/repo')
        """
        if self.is_git_url(path_or_url):
            return self.clone_repository(path_or_url, force=force_clone)
        else:
            # Return local path as-is
            return Path(path_or_url).resolve()

    def cleanup(self, owner: str | None = None, repo: str | None = None) -> None:
        """
        Clean up cloned repositories.

        Args:
            owner: If provided, only clean this owner's repos
            repo: If provided (with owner), only clean this specific repo
        """
        if owner and repo:
            # Clean specific repo
            path = self.tmp_dir / owner / repo
            if path.exists():
                console.print(f"[yellow]Removing:[/yellow] {path}")
                shutil.rmtree(path)
        elif owner:
            # Clean all repos for owner
            path = self.tmp_dir / owner
            if path.exists():
                console.print(f"[yellow]Removing:[/yellow] {path}")
                shutil.rmtree(path)
        else:
            # Clean entire tmp directory
            if self.tmp_dir.exists():
                console.print(f"[yellow]Removing:[/yellow] {self.tmp_dir}")
                shutil.rmtree(self.tmp_dir)
