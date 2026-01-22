import re
import shutil
from pathlib import Path
from typing import Tuple, NamedTuple
from git import Repo


def parse_github_url(url: str) -> Tuple[str, str]:
    """
    Parse a GitHub URL to extract author (owner) and repository name.

    Supports:
    - https://github.com/author/repo
    - https://github.com/author/repo.git
    - git@github.com:author/repo.git
    """
    # Handle SSH
    if url.startswith("git@"):
        match = re.search(r"github\.com:([^/]+)/([^/\.]+)", url)
        if match:
            return match.group(1), match.group(2).removesuffix(".git")

    # Handle HTTPS
    match = re.search(r"github\.com/([^/]+)/([^/\.]+)", url)
    if match:
        return match.group(1), match.group(2).removesuffix(".git")

    raise ValueError(f"Could not parse GitHub URL: {url}")


class CloneResult(NamedTuple):
    path: Path
    author: str
    reponame: str


def is_github_url(url: str) -> bool:
    """Check if the string is a valid GitHub URL."""
    return (
        url.startswith("https://github.com/")
        or url.startswith("http://github.com/")
        or url.startswith("git@github.com:")
    )


def clone_repo(url: str, base_tmp_dir: str = "./tmp", force: bool = False) -> Path:
    """
    Clone a GitHub repository and save it to {base_tmp_dir}/{author}/{reponame}.

    Args:
        url: The GitHub URL (HTTPS or SSH).
        base_tmp_dir: The base directory for clones (default: ./tmp).
        force: If True, remove existing directory and re-clone.

    Returns:
        Path to the cloned repository.
    """
    # Validate URL format
    if not is_github_url(url):
        raise ValueError(
            f"Invalid GitHub URL: {url}. "
            "Expected format: https://github.com/owner/repo or git@github.com:owner/repo"
        )

    try:
        repo_info = parse_github_url(url)
    except ValueError as e:
        raise ValueError(f"Could not parse GitHub URL '{url}': {e}")

    author, reponame = repo_info
    target_path = Path(base_tmp_dir) / author / reponame

    if target_path.exists():
        if force:
            shutil.rmtree(target_path)
        else:
            return CloneResult(path=target_path, author=author, reponame=reponame).path

    # Ensure parent directory exists
    target_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        # Clone with depth=1 for efficiency
        Repo.clone_from(url, str(target_path), depth=1)
    except Exception as e:
        raise RuntimeError(
            f"Failed to clone repository from {url} to {target_path}: {e}"
        )

    return CloneResult(path=target_path, author=author, reponame=reponame).path
