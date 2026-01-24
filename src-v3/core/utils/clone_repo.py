import re
import shutil
from pathlib import Path
from typing import Callable, Optional, Tuple, NamedTuple
from git import Repo, RemoteProgress


class CloneProgress(RemoteProgress):
    """Progress handler for git clone operations."""

    def __init__(self, callback: Optional[Callable[[str], None]] = None):
        super().__init__()
        self.callback = callback
        self._last_message = ""

    def update(self, op_code, cur_count, max_count=None, message=""):
        """Called for each progress update."""
        if self.callback:
            # Build progress message
            op_names = {
                self.COUNTING: "Counting objects",
                self.COMPRESSING: "Compressing objects",
                self.WRITING: "Writing objects",
                self.RECEIVING: "Receiving objects",
                self.RESOLVING: "Resolving deltas",
                self.FINDING_SOURCES: "Finding sources",
                self.CHECKING_OUT: "Checking out files",
            }

            # Get operation name
            op_name = "Cloning"
            for code, name in op_names.items():
                if op_code & code:
                    op_name = name
                    break

            # Build message
            if max_count:
                pct = int(100 * cur_count / max_count)
                msg = f"{op_name}: {pct}%"
            else:
                msg = f"{op_name}..."

            if message:
                msg += f" {message}"

            # Only callback if message changed
            if msg != self._last_message:
                self._last_message = msg
                self.callback(msg)


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


def clone_repo(
    url: str,
    base_tmp_dir: str = "./tmp",
    force: bool = False,
    progress_callback: Optional[Callable[[str], None]] = None,
) -> Path:
    """
    Clone a GitHub repository and save it to {base_tmp_dir}/{author}/{reponame}.

    Args:
        url: The GitHub URL (HTTPS or SSH).
        base_tmp_dir: The base directory for clones (default: ./tmp).
        force: If True, remove existing directory and re-clone.
        progress_callback: Optional callback for progress updates.

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
            if progress_callback:
                progress_callback("Removing existing clone...")
            shutil.rmtree(target_path)
        else:
            if progress_callback:
                progress_callback("Using existing clone")
            return CloneResult(path=target_path, author=author, reponame=reponame).path

    # Ensure parent directory exists
    target_path.parent.mkdir(parents=True, exist_ok=True)

    if progress_callback:
        progress_callback(f"Cloning {author}/{reponame}...")

    try:
        # Clone with depth=1 for efficiency
        progress = CloneProgress(progress_callback) if progress_callback else None
        Repo.clone_from(url, str(target_path), depth=1, progress=progress)
        if progress_callback:
            progress_callback("Clone complete")
    except Exception as e:
        raise RuntimeError(
            f"Failed to clone repository from {url} to {target_path}: {e}"
        )

    return CloneResult(path=target_path, author=author, reponame=reponame).path
