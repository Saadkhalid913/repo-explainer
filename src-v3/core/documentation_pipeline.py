"""Multi-agent documentation pipeline orchestration.

This module implements a hierarchical multi-agent system for repository
documentation generation. The pipeline consists of:

1. Explorer Agent: Creates high-level repository overview
2. Delegator Agent: Allocates component exploration tasks
3. Multiple Explorer Subagents: Analyze individual components in parallel
4. Documentation Agent: Creates table of contents from component docs
5. Multiple Section Writer Agents: Generate documentation sections with diagrams
6. Overview Writer Agent: Creates main documentation index

The agents communicate via file-based protocol using structured directories.
"""

from pathlib import Path
from typing import Optional
import logging

from .agents import (
    OpenCodeWrapper,
    OpencodeProjectConfig,
    AgentType,
    create_opencode_wrapper
)

logger = logging.getLogger(__name__)


class DocumentationPipeline:
    """Multi-agent documentation pipeline."""

    def __init__(self, repo_path: Path, verbose: bool = False):
        """
        Initialize the documentation pipeline.

        Args:
            repo_path: Path to the repository to document
            verbose: Enable verbose logging
        """
        self.repo_path = Path(repo_path)
        self.verbose = verbose
        self.wrapper: Optional[OpenCodeWrapper] = None

        # Directory structure for file-based communication
        self.planning_dir = self.repo_path / "planning"
        self.docs_dir = self.repo_path / "docs"
        self.assets_dir = self.docs_dir / "assets"
        self.component_docs_dir = self.planning_dir / "docs"
        self.documentation_dir = self.planning_dir / "documentation"

    def setup(self) -> None:
        """Setup the pipeline by creating necessary directories."""
        self.planning_dir.mkdir(exist_ok=True)
        self.docs_dir.mkdir(exist_ok=True)
        self.assets_dir.mkdir(exist_ok=True)  # Shared assets for diagrams
        self.component_docs_dir.mkdir(exist_ok=True)
        self.documentation_dir.mkdir(exist_ok=True)

        # Create wrapper with all agents enabled
        self.wrapper = create_opencode_wrapper(
            self.repo_path,
            verbose=self.verbose
        )

        logger.info(f"Pipeline initialized for repository: {self.repo_path}")

    def run(self) -> dict:
        """
        Execute the full documentation pipeline.

        Returns:
            dict: Pipeline execution results with status and paths
        """
        if not self.wrapper:
            raise RuntimeError("Pipeline not setup. Call setup() first.")

        results = {
            "success": False,
            "steps": {},
            "output_paths": {},
            "errors": []
        }

        try:
            # Step 1: Explorer Agent - Create repository overview
            logger.info("Step 1: Creating repository overview...")
            step1_result = self._step_1_explore_repository()
            results["steps"]["explore"] = step1_result
            results["output_paths"]["overview"] = str(
                self.planning_dir / "overview.md"
            )

            # Step 2: Delegator Agent - Allocate component exploration tasks
            logger.info("Step 2: Allocating component exploration tasks...")
            step2_result = self._step_2_delegate_tasks()
            results["steps"]["delegate"] = step2_result
            results["output_paths"]["task_allocation"] = str(
                self.planning_dir / "task_allocation.md"
            )

            # Step 3: Multiple Explorer Subagents (spawned by delegator)
            # These run automatically via subagent calls within step 2
            logger.info("Step 3: Component exploration (parallel subagents)...")
            logger.info("  → Subagents spawned by delegator agent")

            # Step 4: Documentation Agent - Create table of contents
            logger.info("Step 4: Creating table of contents...")
            step4_result = self._step_4_create_toc()
            results["steps"]["create_toc"] = step4_result
            results["output_paths"]["toc"] = str(
                self.documentation_dir / "toc.json"
            )

            # Step 5: Section Writer Agents (spawned by documentation agent)
            # These run automatically via subagent calls within documentation agent
            logger.info("Step 5: Generating documentation sections...")
            logger.info("  → Section writers spawned by documentation agent")

            # Step 6: Overview Writer Agent - Generate main index
            logger.info("Step 6: Generating main documentation index...")
            step6_result = self._step_6_generate_overview()
            results["steps"]["generate_overview"] = step6_result
            results["output_paths"]["main_index"] = str(
                self.docs_dir / "index.md"
            )

            results["success"] = True
            logger.info("Pipeline completed successfully!")

        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            results["errors"].append(str(e))
            results["success"] = False

        return results

    def _step_1_explore_repository(self) -> dict:
        """
        Step 1: Use Explorer agent to create repository overview.

        Returns:
            dict: Step execution result
        """
        prompt = """Analyze the repository structure and create a comprehensive overview.

Your task:
1. Explore the repository to understand its structure, purpose, and organization
2. Identify major directories, components, and architectural patterns
3. Create `planning/overview.md` with:
   - Repository purpose and description
   - Technology stack
   - Directory structure overview
   - Major components identified
   - Architectural patterns observed

This overview will be used by the delegator agent to allocate component
exploration tasks.
"""

        response = self.wrapper.execute(
            prompt=prompt,
            agent_type=AgentType.EXPLORATION
        )

        return {
            "success": response.success if hasattr(response, 'success') else True,
            "output": str(response)[:200]  # First 200 chars
        }

    def _step_2_delegate_tasks(self) -> dict:
        """
        Step 2: Use Delegator agent to allocate component exploration tasks.

        The delegator will:
        - Read planning/overview.md
        - Identify 3-10 major components
        - Create task allocation plan in planning/task_allocation.md
        - Spawn parallel explorer subagents for each component

        Returns:
            dict: Step execution result
        """
        prompt = """Read the repository overview and allocate component exploration tasks.

Your task:
1. Read `planning/overview.md` to understand the repository structure
2. Identify 3-10 major components that should be explored in detail
3. Create `planning/task_allocation.md` with:
   - YAML frontmatter with task count and parallel execution flag
   - Task descriptions for each component
   - Component paths, focus areas, and output locations
4. Spawn parallel exploration subagents using the Task tool:
   - One subagent per component
   - Each outputs to `planning/docs/{component_name}/`

Focus on creating balanced, comprehensive exploration tasks that cover all
significant code without over-segmenting.
"""

        response = self.wrapper.execute(
            prompt=prompt,
            agent_type=AgentType.DELEGATOR
        )

        return {
            "success": response.success if hasattr(response, 'success') else True,
            "output": str(response)[:200]
        }

    def _step_4_create_toc(self) -> dict:
        """
        Step 4: Use Documentation agent to create table of contents.

        The documentation agent will:
        - Read all component docs from planning/docs/*/
        - Group components into logical documentation sections
        - Create planning/documentation/toc.json

        Returns:
            dict: Step execution result
        """
        prompt = """Create a comprehensive table of contents from component documentation.

Your task:
1. Read all component documentation from `planning/docs/*/`
2. Analyze the content and identify common themes/topics
3. Group components into 3-8 logical documentation sections:
   - Architecture (core systems, design patterns)
   - Components (major modules, services)
   - APIs (endpoints, interfaces)
   - Development (testing, deployment)
   - etc.
4. Create `planning/documentation/toc.json` with:
   - Section names, titles, descriptions
   - Component assignments to sections
   - File paths for each section
   - Priority ordering

This TOC will be used by section writer agents to generate the final
documentation structure.
"""

        response = self.wrapper.execute(
            prompt=prompt,
            agent_type=AgentType.DOCUMENTATION
        )

        return {
            "success": response.success if hasattr(response, 'success') else True,
            "output": str(response)[:200]
        }

    def _step_6_generate_overview(self) -> dict:
        """
        Step 6: Use Overview Writer agent to generate main documentation index.

        The overview writer will:
        - Read all section index files from docs/*/index.md
        - Read section metadata from planning/documentation/toc.json
        - Create docs/index.md with comprehensive navigation

        Returns:
            dict: Step execution result
        """
        prompt = """Generate the main documentation index.

Your task:
1. Read all section index files from `docs/*/index.md`
2. Read section metadata from `planning/documentation/toc.json`
3. Read repository overview from `planning/overview.md`
4. Create `docs/index.md` with:
   - Repository overview (2-3 paragraphs)
   - Key features and tech stack
   - Quick Start guide (links to 3-5 most important sections)
   - Complete documentation structure with descriptions
   - Navigation helpers and external links

Make the index welcoming, scannable, and easy to navigate. This is the first
page users will see, so guide them to the most relevant content.
"""

        response = self.wrapper.execute(
            prompt=prompt,
            agent_type=AgentType.OVERVIEW_WRITER
        )

        return {
            "success": response.success if hasattr(response, 'success') else True,
            "output": str(response)[:200]
        }


def run_documentation_pipeline(
    repo_path: Path,
    verbose: bool = False
) -> dict:
    """
    Execute the full multi-agent documentation pipeline.

    This is a convenience function that creates a pipeline, sets it up,
    and runs all steps.

    Args:
        repo_path: Path to the repository to document
        verbose: Enable verbose logging

    Returns:
        dict: Pipeline execution results

    Example:
        >>> from pathlib import Path
        >>> result = run_documentation_pipeline(Path("./my_repo"))
        >>> print(f"Success: {result['success']}")
        >>> print(f"Main index: {result['output_paths']['main_index']}")
    """
    pipeline = DocumentationPipeline(repo_path, verbose=verbose)
    pipeline.setup()
    return pipeline.run()


# Example usage
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python documentation_pipeline.py <repo_path>")
        sys.exit(1)

    repo_path = Path(sys.argv[1])
    if not repo_path.exists():
        print(f"Error: Repository path does not exist: {repo_path}")
        sys.exit(1)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Run pipeline
    result = run_documentation_pipeline(repo_path, verbose=True)

    # Print results
    print("\n" + "=" * 60)
    print("PIPELINE RESULTS")
    print("=" * 60)
    print(f"Success: {result['success']}")
    print(f"\nOutput Paths:")
    for name, path in result.get('output_paths', {}).items():
        print(f"  {name}: {path}")

    if result.get('errors'):
        print(f"\nErrors:")
        for error in result['errors']:
            print(f"  - {error}")

    sys.exit(0 if result['success'] else 1)
