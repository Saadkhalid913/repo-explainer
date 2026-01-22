
"""Orchestration logic for repository analysis and documentation generation."""

from core.agents import (
    OpenCodeWrapper,
    OpenCodeConfig,
    OpencodeProjectConfig,
    AgentType,
)
import sys
from pathlib import Path
from typing import Optional
from core.utils.clone_repo import clone_repo


def is_git_url(path_or_url: str) -> bool:
    """Check if the input is a Git URL."""
    return (
        path_or_url.startswith("http://")
        or path_or_url.startswith("https://")
        or path_or_url.startswith("git@")
    )


def analyze_repository_structure(
    repo_input: str, model: str = "openrouter/google/gemini-2.5-flash"
) -> tuple[str, Path]:
    """
    Analyze repository structure using discovery agent.

    Args:
        repo_input: GitHub URL or local path to repository
        model: Model to use for analysis

    Returns:
        Tuple of (analysis_markdown, repo_path)
    """
    print(f"[Discovery] Analyzing repository: {repo_input}")

    # Determine if it's a URL or local path
    if is_git_url(repo_input):
        repo_path = clone_repo(repo_input)
    else:
        repo_path = Path(repo_input).resolve()
        if not repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")
        if not repo_path.is_dir():
            raise ValueError(
                f"Repository path is not a directory: {repo_path}")

    # Create OpenCode wrapper with default configuration
    # This sets up the workspace with all agents and skills
    agent_config = OpenCodeConfig(
        model=model,
        verbose=True,
    )

    wrapper = OpenCodeWrapper(
        working_dir=repo_path,
        config=agent_config,
        project_config=OpencodeProjectConfig.default(),
    )

    # Execute discovery analysis using discovery agent
    prompt = """Analyze this repository and provide a comprehensive markdown summary of its structure.

Include:
- Overall architecture and organization
- Key components, modules, and their purposes
- Directory structure and file organization
- Entry points and main functionality
- Dependencies and external integrations
- Technology stack

Format the output as a detailed markdown document that can be used as context for documentation generation."""

    response = wrapper.execute(
        prompt=prompt,
        agent_type=AgentType.EXPLORATION,
    )

    if not response.success:
        raise RuntimeError(f"Discovery analysis failed: {response.error}")

    # Extract markdown from response
    # The output should contain the analysis
    analysis_markdown = response.output

    # Cleanup
    wrapper.cleanup_artifacts()

    return analysis_markdown, repo_path


def generate_documentation(
    repo_path: Path,
    analysis_context: str,
    model: str = "openrouter/google/gemini-2.5-flash",
    output_path: Optional[Path] = None,
) -> Path:
    """
    Generate documentation using the analysis context.

    Args:
        repo_path: Path to the repository
        analysis_context: Markdown analysis from discovery phase
        model: Model to use for documentation generation
        output_path: Optional path to save documentation (defaults to repo_path/docs.md)

    Returns:
        Path to the generated documentation file
    """
    print(f"[Documentation] Generating documentation for: {repo_path}")

    # Create OpenCode wrapper with default configuration
    # Note: The same wrapper can be used with different agents
    agent_config = OpenCodeConfig(
        model=model,
        verbose=True,
    )

    wrapper = OpenCodeWrapper(
        working_dir=repo_path,
        config=agent_config,
        project_config=OpencodeProjectConfig.default(),
    )

    # Execute documentation generation with analysis context using documentation agent
    prompt = """Generate comprehensive markdown documentation following the guidelines in the GENERATE_DOCUMENTATION skill.

Include:
- Overview and architecture
- Component descriptions
- Usage examples
- API references where applicable
- Diagrams if helpful

Output the complete documentation as a single, well-structured markdown document."""

    response = wrapper.execute(
        prompt=prompt,
        agent_type=AgentType.DOCUMENTATION,
        context=analysis_context,
    )

    if not response.success:
        raise RuntimeError(
            f"Documentation generation failed: {response.error}")

    # Extract documentation from response
    documentation = response.output

    # Determine output path
    if output_path is None:
        output_path = repo_path / "docs.md"
    else:
        output_path = Path(output_path)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Save documentation
    output_path.write_text(documentation, encoding="utf-8")
    print(f"[Documentation] Saved to: {output_path}")

    # Cleanup
    wrapper.cleanup_artifacts()

    return output_path


def main() -> None:
    """Main orchestration function."""
    if len(sys.argv) < 2:
        print("Usage: python -m core.main <repo_url_or_path> [output_path]")
        sys.exit(1)

    repo_input = sys.argv[1]
    output_path = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else None

    try:
        # Step 1: Analyze repository structure
        print("\n" + "=" * 60)
        print("STEP 1: Repository Structure Analysis")
        print("=" * 60)

        analysis, repo_path = analyze_repository_structure(repo_input)

        with open("./analysis.md", "w") as f:
            f.write(analysis)

        # Step 2: Generate documentation
        print("\n" + "=" * 60)
        print("STEP 2: Documentation Generation")
        print("=" * 60)
        doc_path = generate_documentation(
            repo_path=repo_path,
            analysis_context=analysis,
            output_path=output_path,
        )

        with open("./documentation.md", "w") as f:
            f.write(doc_path.read_text())

        print("\n" + "=" * 60)
        print("SUCCESS")
        print("=" * 60)
        print(f"Documentation saved to: {doc_path}")

    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
