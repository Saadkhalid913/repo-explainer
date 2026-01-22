"""Orchestration logic for repository analysis and documentation generation."""

from core.models.skill import SkillName
from core.agents import (
    OpenCodeWrapper,
    OpenCodeConfig,
    OpencodeProjectConfig,
)
import sys
from pathlib import Path
from typing import Optional

# Add src-v3 to path to allow imports
sys.path.insert(0, str(Path(__file__).parent / "src-v3"))


def analyze_repository_structure(
    repo_path: Path,
    model: str = "google/gemini-3-flash-preview",
) -> str:
    """
    Analyze repository structure using discovery agent.

    Args:
        repo_path: Path to the repository to analyze
        model: Model to use for analysis

    Returns:
        Markdown text describing the repository structure
    """
    print(f"[Discovery] Analyzing repository: {repo_path}")

    # Create discovery agent configuration
    discovery_config = OpencodeProjectConfig.discovery_agent()

    # Create OpenCode wrapper with discovery agent config
    agent_config = OpenCodeConfig(
        model=model,
        verbose=True,
    )

    wrapper = OpenCodeWrapper(
        working_dir=repo_path,
        config=agent_config,
        project_config=discovery_config,
    )

    # Execute discovery analysis
    prompt = """Analyze this repository and provide a comprehensive markdown summary of its structure.

Include:
- Overall architecture and organization
- Key components, modules, and their purposes
- Directory structure and file organization
- Entry points and main functionality
- Dependencies and external integrations
- Technology stack

Format the output as a detailed markdown document that can be used as context for documentation generation."""

    response = wrapper.execute(prompt=prompt)

    if not response.success:
        raise RuntimeError(f"Discovery analysis failed: {response.error}")

    # Extract markdown from response
    # The output should contain the analysis
    analysis_markdown = response.output

    # Cleanup
    wrapper.cleanup_artifacts()

    return analysis_markdown


def generate_documentation(
    repo_path: Path,
    analysis_context: str,
    model: str = "google/gemini-3-flash-preview",
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

    # Create documentation agent configuration with GENERATE_DOCUMENTATION skill
    doc_config = OpencodeProjectConfig.documentation_agent(
        skill_names=[SkillName.GENERATE_DOCUMENTATION]
    )

    # Create OpenCode wrapper with documentation agent config
    agent_config = OpenCodeConfig(
        model=model,
        verbose=True,
    )

    wrapper = OpenCodeWrapper(
        working_dir=repo_path,
        config=agent_config,
        project_config=doc_config,
    )

    # Execute documentation generation with analysis context
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
        print("Usage: python main.py <repo_path> [output_path]")
        sys.exit(1)

    repo_path = Path(sys.argv[1]).resolve()
    output_path = Path(sys.argv[2]).resolve() if len(sys.argv) > 2 else None

    if not repo_path.exists():
        raise SystemExit(f"Repository path does not exist: {repo_path}")

    if not repo_path.is_dir():
        raise SystemExit(f"Repository path is not a directory: {repo_path}")

    try:
        # Step 1: Analyze repository structure
        print("\n" + "=" * 60)
        print("STEP 1: Repository Structure Analysis")
        print("=" * 60)
        analysis = analyze_repository_structure(repo_path)

        # Step 2: Generate documentation
        print("\n" + "=" * 60)
        print("STEP 2: Documentation Generation")
        print("=" * 60)
        doc_path = generate_documentation(
            repo_path=repo_path,
            analysis_context=analysis,
            output_path=output_path,
        )

        print("\n" + "=" * 60)
        print("SUCCESS")
        print("=" * 60)
        print(f"Documentation saved to: {doc_path}")

    except Exception as e:
        print(f"\nERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
