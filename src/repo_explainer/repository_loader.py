"""Repository loader for cloning and resolving repository paths."""

import re
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Tuple

from git import Repo
from git.exc import InvalidGitRepositoryError
from rich.console import Console
from urllib.parse import urlparse

console = Console()


@dataclass
class CommitInfo:
    """Information about a git commit."""
    sha: str
    short_sha: str
    message: str
    author_name: str
    author_email: str
    date: datetime
    files: list[str]


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

    @staticmethod
    def is_git_repo(path: Path) -> bool:
        """
        Check if a path is a valid git repository.

        Args:
            path: Path to check

        Returns:
            True if it's a git repository, False otherwise
        """
        try:
            Repo(path)
            return True
        except InvalidGitRepositoryError:
            return False

    def get_recent_commits(
        self,
        repo_path: Path,
        count: int = 10,
        branch: str = "main",
        since_commit: str | None = None,
    ) -> list[CommitInfo]:
        """
        Get recent commits from a specific branch (defaults to main).

        Args:
            repo_path: Path to the git repository
            count: Number of recent commits to retrieve
            branch: Branch to get commits from (default: "main")
            since_commit: Only get commits after this SHA (exclusive)

        Returns:
            List of CommitInfo objects with commit details
        """
        try:
            repo = Repo(repo_path)
            commits = []

            # Try to get commits from the specified branch
            # First try origin/branch, then local branch
            target_ref = None
            for ref in [f"origin/{branch}", branch]:
                try:
                    target_ref = repo.commit(ref)
                    break
                except Exception:
                    continue

            if target_ref is None:
                console.print(f"[yellow]Warning: Could not find branch '{branch}'[/yellow]")
                # Fall back to current HEAD
                target_ref = repo.head.commit

            for commit in repo.iter_commits(target_ref, max_count=count):
                # Stop if we reach the since_commit
                if since_commit and commit.hexsha.startswith(since_commit):
                    break
                
                # Get list of files changed in this commit
                files = list(commit.stats.files.keys())
                
                commits.append(CommitInfo(
                    sha=commit.hexsha,
                    short_sha=commit.hexsha[:8],
                    message=commit.message.split('\n')[0].strip(),
                    author_name=commit.author.name if commit.author else "",
                    author_email=commit.author.email if commit.author else "",
                    date=commit.committed_datetime,
                    files=files,
                ))

            return commits
        except InvalidGitRepositoryError:
            console.print(f"[yellow]Warning: {repo_path} is not a git repository[/yellow]")
            return []
        except Exception as e:
            console.print(f"[yellow]Warning: Could not read git history: {e}[/yellow]")
            return []

    def get_changed_files(
        self,
        repo_path: Path,
        since_commit: str | None = None,
        count: int = 10,
        branch: str = "main",
    ) -> list[str]:
        """
        Get list of files changed in recent commits on a specific branch (defaults to main).

        Always compares against the specified branch (main by default), regardless
        of what branch you're currently on.

        Args:
            repo_path: Path to the git repository
            since_commit: If provided, get changes since this commit SHA
            count: Number of recent commits to check (if since_commit not provided)
            branch: Branch to check for changes (default: "main")

        Returns:
            Deduplicated list of changed file paths (only files that still exist)
        """
        try:
            repo = Repo(repo_path)
            changed_files = set()

            # Determine the target branch ref
            target_ref = None
            for ref in [f"origin/{branch}", branch]:
                try:
                    target_ref = ref
                    repo.commit(ref)  # Verify it exists
                    break
                except Exception:
                    continue

            if target_ref is None:
                console.print(f"[yellow]Warning: Could not find branch '{branch}', using HEAD[/yellow]")
                target_ref = "HEAD"

            if since_commit:
                # Get diff from specific commit to the target branch
                try:
                    diff = repo.git.diff('--name-only', since_commit, target_ref)
                    if diff.strip():
                        changed_files.update(diff.strip().split('\n'))
                except Exception as e:
                    console.print(f"[yellow]Warning: Could not diff from {since_commit} to {target_ref}: {e}[/yellow]")
                    return []
            else:
                # Get files from recent commits on the target branch
                try:
                    for commit in repo.iter_commits(target_ref, max_count=count):
                        changed_files.update(commit.stats.files.keys())
                except Exception as e:
                    console.print(f"[yellow]Warning: Could not iterate commits on {target_ref}: {e}[/yellow]")
                    return []

            # Filter out deleted files and non-code files
            # Check if files exist in the TARGET BRANCH, not locally
            # (user might be on a different branch)
            existing_files = []
            for f in changed_files:
                # Skip common non-code files
                if any(f.endswith(ext) for ext in ['.pyc', '.pyo', '.lock', '.log']):
                    continue
                
                # Check if file exists in the target branch using git ls-tree
                try:
                    result = repo.git.ls_tree('--name-only', target_ref, f)
                    if result.strip():  # File exists in target branch
                        existing_files.append(f)
                except Exception:
                    # If git check fails, fall back to local check
                    file_path = repo_path / f
                    if file_path.exists() and file_path.is_file():
                        existing_files.append(f)

            return sorted(existing_files)
        except InvalidGitRepositoryError:
            console.print(f"[yellow]Warning: {repo_path} is not a git repository[/yellow]")
            return []
        except Exception as e:
            console.print(f"[yellow]Warning: Could not get changed files: {e}[/yellow]")
            return []

    def get_last_doc_update_commit(
        self,
        repo_path: Path,
        docs_dir: Path,
    ) -> str | None:
        """
        Find the commit SHA when documentation was last updated.

        Looks for a marker file in the docs directory that stores the last commit.

        Args:
            repo_path: Path to the git repository
            docs_dir: Path to the documentation directory

        Returns:
            Commit SHA or None if not found
        """
        marker_file = docs_dir / ".repo-explainer" / "last_commit.txt"
        if marker_file.exists():
            return marker_file.read_text().strip()
        return None

    def save_doc_update_commit(
        self,
        repo_path: Path,
        docs_dir: Path,
        branch: str = "main",
    ) -> str | None:
        """
        Save the specified branch's latest commit as the last documentation update point.

        Args:
            repo_path: Path to the git repository
            docs_dir: Path to the documentation directory
            branch: Branch to save the commit from (default: "main")

        Returns:
            The commit SHA that was saved, or None on error
        """
        try:
            repo = Repo(repo_path)
            
            # Get the commit SHA from the target branch
            target_sha = None
            for ref in [f"origin/{branch}", branch]:
                try:
                    target_sha = repo.commit(ref).hexsha
                    break
                except Exception:
                    continue
            
            if target_sha is None:
                # Fall back to HEAD
                target_sha = repo.head.commit.hexsha
                console.print(f"[yellow]Warning: Could not find branch '{branch}', using HEAD[/yellow]")
            
            marker_dir = docs_dir / ".repo-explainer"
            marker_dir.mkdir(parents=True, exist_ok=True)
            
            marker_file = marker_dir / "last_commit.txt"
            marker_file.write_text(target_sha)

            return target_sha
        except Exception as e:
            console.print(f"[yellow]Warning: Could not save commit marker: {e}[/yellow]")
            return None

    def get_commit_diff(
        self,
        repo_path: Path,
        commit_sha: str,
        branch: str = "main",
    ) -> str:
        """
        Get the diff content for a specific commit.

        Args:
            repo_path: Path to the git repository
            commit_sha: SHA of the commit to get diff for
            branch: Branch context for the diff (default: "main")

        Returns:
            Diff content as string, or empty string on error
        """
        try:
            repo = Repo(repo_path)

            # Get the commit object
            commit = repo.commit(commit_sha)

            # If it's not a merge commit, get diff with parent
            if len(commit.parents) == 1:
                parent = commit.parents[0]
                diff = commit.diff(parent, create_patch=True)
            else:
                # For merge commits, get diff with first parent (mainline)
                diff = commit.diff(commit.parents[0], create_patch=True)

            # Convert diff objects to string
            diff_content = ""
            for d in diff:
                diff_content += f"--- a/{d.a_path}\n+++ b/{d.b_path}\n"
                if d.diff:
                    diff_content += d.diff.decode('utf-8', errors='replace')

            return diff_content

        except Exception as e:
            console.print(f"[yellow]Warning: Could not get diff for commit {commit_sha}: {e}[/yellow]")
            return ""
