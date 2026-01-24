#!/usr/bin/env python3
"""
Repository Documentation TUI

A terminal user interface for documenting GitHub repositories using the multi-agent
documentation system powered by OpenCode.

Usage:
    python src/document_repo.py
    python src/document_repo.py https://github.com/owner/repo
    python src/document_repo.py https://github.com/owner/repo --model sonnet
"""

import argparse
import shutil
import sys
from datetime import datetime
from pathlib import Path

from rich.console import Console

from core.agents import AgentType
from core.documentation_pipeline import DocumentationPipeline
from core.tui import RichTUI, print_completion_summary, prompt_for_url
from core.utils.clone_repo import clone_repo, is_github_url


def copy_output_to_dist(
    repo_name: str,
    build_docs_dir: Path,
    html_site_dir: Path,
    tui: RichTUI,
) -> Path:
    """
    Copy final documentation to dist/ folder in current working directory.

    Args:
        repo_name: Name of the repository (used for folder naming)
        build_docs_dir: Path to processed markdown docs (build/docs/)
        html_site_dir: Path to HTML site (build/site/)
        tui: TUI instance for logging progress

    Returns:
        Path to the dist folder
    """
    # Create dist folder in current working directory
    dist_dir = Path.cwd() / "dist" / repo_name
    dist_docs = dist_dir / "markdown"
    dist_site = dist_dir / "site"

    tui.log_message("DIST", f"Copying output to {dist_dir}", "cyan", "bold cyan")

    # Clean existing dist for this repo
    if dist_dir.exists():
        shutil.rmtree(dist_dir)

    dist_dir.mkdir(parents=True, exist_ok=True)

    # Copy markdown docs
    if build_docs_dir and build_docs_dir.exists():
        shutil.copytree(build_docs_dir, dist_docs)
        tui.log_message("DIST", f"Markdown docs: {dist_docs}", "green", "bold green")

    # Copy HTML site
    if html_site_dir and html_site_dir.exists():
        shutil.copytree(html_site_dir, dist_site)
        tui.log_message("DIST", f"HTML site: {dist_site}", "green", "bold green")

    return dist_dir


def main():
    """Main entry point for repository documentation TUI."""
    console = Console()

    # Parse arguments
    parser = argparse.ArgumentParser(
        description="Document a GitHub repository using multi-agent system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/document_repo.py
  python src/document_repo.py https://github.com/owner/repo
  python src/document_repo.py https://github.com/owner/repo --model sonnet
  python src/document_repo.py https://github.com/owner/repo --verbose
        """,
    )

    parser.add_argument(
        "url",
        type=str,
        nargs="?",
        default=None,
        help="GitHub URL to document (https://github.com/owner/repo). If not provided, will prompt.",
    )

    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model to use (sonnet, opus, haiku, or full model ID)",
    )

    parser.add_argument(
        "--agent",
        type=str,
        default="exploration",
        choices=["exploration", "documentation", "delegator", "section_writer", "overview_writer"],
        help="Starting agent type (default: exploration)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging (shows all events)",
    )

    args = parser.parse_args()

    # Get GitHub URL
    repo_url = args.url
    if not repo_url:
        # Show interactive prompt
        repo_url = prompt_for_url(console)

    if not repo_url:
        console.print("[red]No URL provided. Exiting.[/red]")
        sys.exit(1)

    # Validate URL
    if not is_github_url(repo_url):
        console.print(f"[red]Invalid GitHub URL: {repo_url}[/red]")
        console.print("[dim]Expected format: https://github.com/owner/repo[/dim]")
        sys.exit(1)

    # Map model shortcuts
    model_map = {
        "sonnet": "anthropic/claude-sonnet-4-5",
        "opus": "anthropic/claude-opus-4-5",
        "haiku": "anthropic/claude-haiku-4-5",
    }
    model = model_map.get(args.model, args.model)

    # Map agent type
    agent_type_map = {
        "exploration": AgentType.EXPLORATION,
        "documentation": AgentType.DOCUMENTATION,
        "delegator": AgentType.DELEGATOR,
        "section_writer": AgentType.SECTION_WRITER,
        "overview_writer": AgentType.OVERVIEW_WRITER,
    }
    agent_type = agent_type_map[args.agent]

    # Setup log file (use repo name from URL)
    # Extract repo name from URL for log file
    url_parts = repo_url.rstrip("/").split("/")
    repo_name = url_parts[-1] if url_parts else "unknown"
    log_file_path = Path(f"{repo_name}.log.txt")
    log_file = open(log_file_path, "w")

    # Initialize TUI immediately with URL
    tui = RichTUI(
        repo_url=repo_url,
        log_file=log_file,
        verbose=args.verbose,
    )

    repo_path = None
    result = None

    try:
        # Start the TUI
        tui.start()
        tui.log_message("START", "Repository Documentation System", "cyan", "bold cyan")
        tui.log_message("URL", repo_url, "cyan", "bold white")

        # Clone repository with progress
        tui.log_message("CLONE", "Starting clone...", "white", "bold white")

        # Get project root for tmp directory
        script_dir = Path(__file__).parent  # src-v3/
        project_root = script_dir.parent  # repo-explainer/
        tmp_dir = project_root / "tmp"

        def clone_progress(msg: str):
            tui.log_message("CLONE", msg, "white", "bold white")

        repo_path = clone_repo(
            repo_url,
            base_tmp_dir=str(tmp_dir),
            force=False,
            progress_callback=clone_progress,
        )
        repo_path = repo_path.resolve()

        # Update TUI with repo path and start docs watcher
        tui.repo_path = repo_path
        tui.start_docs_watcher()
        tui.log_message("CLONE", f"Repository ready: {repo_path.name}", "green", "bold green")

        # Create stream callback
        def stream_callback(line: str) -> None:
            tui.handle_event(line)

        # Initialize pipeline
        tui.log_message("INIT", "Initializing documentation pipeline...", "white", "bold white")
        pipeline = DocumentationPipeline(
            repo_path=repo_path,
            model=model,
            verbose=args.verbose,
            stream_callback=stream_callback,
            repo_url=repo_url,
        )

        # Setup and run pipeline
        tui.log_message("INIT", "Configuration applied", "green", "bold green")
        pipeline.setup()

        tui.log_message("RUN", "Starting documentation...", "cyan", "bold cyan")
        result = pipeline.run()

        # Show post-processing results and copy to dist/
        dist_dir = None
        if result and "steps" in result:
            post_process = result["steps"].get("post_process")
            if post_process:
                tui.log_post_process(post_process)

                # Copy output to dist/ folder in current working directory
                build_docs = post_process.get("build_dir")
                html_site = post_process.get("html_output_dir")
                if build_docs or html_site:
                    dist_dir = copy_output_to_dist(
                        repo_name=repo_name,
                        build_docs_dir=Path(build_docs) / "docs" if build_docs else None,
                        html_site_dir=Path(html_site) if html_site else None,
                        tui=tui,
                    )
                    result["output_paths"]["dist"] = str(dist_dir)

        # Show completion in TUI
        tui.show_completion(result)

    except KeyboardInterrupt:
        tui.log_message("ABORT", "Interrupted by user", "yellow", "bold yellow")
    except Exception as e:
        tui.log_message("ERROR", str(e)[:60], "red", "bold red")
        raise
    finally:
        # Stop TUI (exits full-screen mode)
        tui.stop()
        log_file.close()

        # Print completion summary after TUI exits
        if result is not None and repo_path is not None:
            print_completion_summary(
                repo_path=repo_path,
                repo_url=repo_url,
                log_file_path=log_file_path,
                stats=tui.stats,
                pipeline_result=result,
            )
        else:
            # Interrupted or error
            console.print()
            console.print("[yellow]Documentation interrupted or failed[/yellow]")
            console.print(f"Log file: {log_file_path}")
            if repo_path:
                console.print(f"Repository clone: {repo_path}")
            console.print()


if __name__ == "__main__":
    main()
