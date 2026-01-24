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
from typing import Optional, Callable
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

    def __init__(
        self,
        repo_path: Path,
        model: Optional[str] = None,
        verbose: bool = False,
        stream_callback: Optional[Callable[[str], None]] = None,
        repo_url: Optional[str] = None
    ):
        """
        Initialize the documentation pipeline.

        Args:
            repo_path: Path to the repository to document
            model: AI model to use for agents
            verbose: Enable verbose logging
            stream_callback: Optional callback for streaming agent output events
            repo_url: GitHub repository URL (for fixing links in docs)
        """
        self.repo_path = Path(repo_path)
        self.model = model
        self.verbose = verbose
        self.stream_callback = stream_callback
        self.repo_url = repo_url
        self.wrapper: Optional[OpenCodeWrapper] = None

        # Directory structure - everything in planning/
        self.planning_dir = self.repo_path / "planning"
        self.component_docs_dir = self.planning_dir / "docs"
        self.assets_dir = self.planning_dir / "assets"

    def setup(self) -> None:
        """Setup the pipeline by creating necessary directories."""
        self.planning_dir.mkdir(exist_ok=True)
        self.component_docs_dir.mkdir(exist_ok=True)
        self.assets_dir.mkdir(exist_ok=True)  # For diagrams

        # Create wrapper with all agents enabled
        self.wrapper = create_opencode_wrapper(
            self.repo_path,
            model=self.model,
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
            logger.info(
                "Step 3: Component exploration (parallel subagents)...")
            logger.info("  → Subagents spawned by delegator agent")

            # CRITICAL: Wait for subagents to complete
            # The delegator spawns async subagents - we must wait for them
            logger.info("  → Waiting for exploration subagents to complete...")
            self._wait_for_exploration_subagents()

            # Step 4: Generate component docs index (title page)
            logger.info("Step 4: Generating component documentation index...")
            step4_result = self._step_4_generate_docs_index()
            results["steps"]["docs_index"] = step4_result
            results["output_paths"]["component_docs"] = str(self.component_docs_dir)

            # Step 5: Overview Writer Agent - Generate main index
            logger.info("Step 5: Generating main documentation index...")
            step5_result = self._step_5_generate_overview()
            results["steps"]["generate_overview"] = step5_result
            results["output_paths"]["main_index"] = str(
                self.planning_dir / "index.md"
            )

            # Step 6: Post-process documentation
            # - Copy docs to build/ (preserving originals)
            # - Fix GitHub links
            # - Render mermaid diagrams to PNG
            # - Generate HTML site
            logger.info("Step 6: Post-processing and rendering documentation...")
            step6_result = self._step_6_post_process()
            results["steps"]["post_process"] = step6_result

            # Record output paths from post-processing
            if step6_result.get("html_output_dir"):
                results["output_paths"]["html_site"] = step6_result["html_output_dir"]
            if step6_result.get("build_dir"):
                results["output_paths"]["build"] = step6_result["build_dir"]

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

## CRITICAL: Safe Exploration for Large Repos

**DO NOT use broad glob patterns!** They will overflow the context.

**Step 1 - Safe Directory Discovery**:
- Use `ls -la` to list top-level directories
- Or use glob pattern `*/` (NOT `*`) to get only directories
- NEVER use `*` alone - it returns all files recursively!

**Step 2 - Targeted Exploration**:
- Look at `cmd/*/` for main executables
- Look at `pkg/*/` for packages
- Read key files like README.md, go.mod for context

**Step 3 - Write the Overview**:
Write your findings to `planning/overview.md` using the Write tool:
- Repository purpose and description
- Technology stack
- Directory structure overview
- Major components identified (8-15 for large projects)
- Architectural patterns observed

**Depth Requirement**: Enumerate all major components explicitly.
For Kubernetes: apiserver, scheduler, controller-manager, kubelet, kube-proxy,
client-go, kubectl, etc.

**IMPORTANT**: You MUST write `planning/overview.md` before finishing!
Use the Write tool, not bash echo commands.
"""

        response = self.wrapper.execute(
            prompt=prompt,
            agent_type=AgentType.EXPLORATION,
            stream_output=False,
            stream_callback=self.stream_callback
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
        - Identify 8-15 major components (MORE for large projects!)
        - Create task allocation plan in planning/task_allocation.md
        - Spawn parallel explorer subagents for each component

        Returns:
            dict: Step execution result
        """
        prompt = """Read the repository overview and allocate component exploration tasks.

Your task:

## STEP 1: Create Component Manifest (DO THIS FIRST!)

Create `planning/component_manifest.md` with a table of ALL components you will document.
This prevents dead links when components reference each other.

Example:
```markdown
# Component Manifest

| Component ID | Display Name | Output Path |
|-------------|--------------|-------------|
| api-server | API Server | docs/api-server/ |
| scheduler | Scheduler | docs/scheduler/ |
| controller-manager | Controller Manager | docs/controller-manager/ |
```

## STEP 2: Identify Components

1. Read `planning/overview.md` to understand the repository structure
2. Identify **8-15 major components** that should be explored in detail
   - For large projects like Kubernetes, identify ALL major subsystems:
     - Control plane: apiserver, scheduler, controller-manager, etcd integration
     - Node components: kubelet, kube-proxy
     - Client libraries: client-go, kubectl, API machinery
     - Storage: volume plugins, CSI drivers
     - Networking: CNI, services, ingress
     - Security: auth, admission controllers
   - **DO NOT under-identify components!**

## STEP 3: Create Task Allocation

Create `planning/task_allocation.md` with:
- YAML frontmatter with task count (should be 8-15)
- Task descriptions for each component
- Component paths, focus areas, and output locations

## STEP 4: Spawn Subagents (CRITICAL!)

Spawn parallel exploration subagents using the Task tool:
- Use the Task tool with subagent_type="exploration" for EACH component
- One subagent per component (8-15 subagents total!)
- **IMPORTANT**: Each outputs to `planning/docs/{component_name}/index.md`
- Tell each subagent to read `planning/component_manifest.md` for cross-linking

Example prompt for subagent:
```
Explore the {component_name} component in {paths}.

**FIRST**: Read `planning/component_manifest.md` to see all components being documented.
Use this for cross-linking - only link to components in the manifest!

Create comprehensive documentation in planning/docs/{component_name}/

Files to create:
- index.md (main overview, 100+ lines)
- architecture.md (with mermaid diagrams)
- api_reference.md (if applicable)
- configuration.md (if applicable)

Cross-link format: [Component Name](../{component-id}/index.md)

Include in each file:
- Enumerate ALL sub-components by name
- Code examples (minimum 3 per file)
- Mermaid diagrams using ```mermaid blocks
- Reference tables where applicable
- Links to source files

Focus on: {focus_areas}
```

**File Naming Standard**: All component docs must use `index.md` as the main file.

**IMPORTANT**: You MUST spawn 8-15 subagents for a large project. Don't just create the
task allocation file - actually spawn the Task tool calls to create the subagents.
"""

        response = self.wrapper.execute(
            prompt=prompt,
            agent_type=AgentType.DELEGATOR,
            stream_output=False,
            stream_callback=self.stream_callback
        )

        return {
            "success": response.success if hasattr(response, 'success') else True,
            "output": str(response)[:200]
        }

    def _step_4_create_toc(self) -> dict:
        """
        Step 4: Use Documentation agent to create table of contents AND spawn section writers.

        The documentation agent will:
        - Read all component docs from planning/docs/*/
        - Group components into logical documentation sections
        - Create planning/documentation/toc.json
        - SPAWN section writer agents for each section

        Returns:
            dict: Step execution result
        """
        prompt = """Create a table of contents from component documentation and spawn section writers.

## Task 1: Create TOC

1. Read all component documentation from `planning/docs/*/`
2. Analyze the content and identify common themes/topics
3. Group components into 4-8 logical documentation sections:
   - control-plane (API server, scheduler, controller-manager)
   - node-components (kubelet, kube-proxy)
   - client-libraries (client-go, kubectl)
   - storage (volume plugins, CSI)
   - networking (CNI, services)
   - etc.
4. Create `planning/documentation/toc.json` with:
   - Section names, titles, descriptions
   - Component assignments to sections
   - File paths for each section
   - Priority ordering

## Task 2: SPAWN Section Writers (CRITICAL!)

After creating the TOC, you MUST spawn section writer agents using the Task tool:

For EACH section in your TOC, spawn a section_writer agent:

```
Task tool call:
  subagent_type: "section_writer"
  description: "Write {section_name} documentation"
  prompt: "Create final documentation for the {section_name} section.

  Read these component docs: {list of planning/docs/component paths}

  Create: docs/{section_name}/index.md

  Requirements:
  1. Create section directory: docs/{section_name}/
  2. Write mermaid diagrams to: docs/assets/{section_name}_*.mmd
  3. Compile diagrams: mmdc -i docs/assets/{name}.mmd -o docs/assets/{name}.png -t dark -b transparent
  4. Reference diagrams as: ![Title](../assets/{name}.png)
  5. Create comprehensive index.md (200+ lines)
  6. Include links between sections
  "
```

**YOU MUST SPAWN SECTION WRITERS - DO NOT SKIP THIS STEP!**

The section writers will:
- Read component docs from planning/docs/
- Compile mermaid diagrams to PNG
- Create final docs in docs/{section}/index.md
"""

        response = self.wrapper.execute(
            prompt=prompt,
            agent_type=AgentType.DOCUMENTATION,
            stream_output=False,
            stream_callback=self.stream_callback
        )

        return {
            "success": response.success if hasattr(response, 'success') else True,
            "output": str(response)[:200]
        }

    def _wait_for_exploration_subagents(self, timeout: int = 600, poll_interval: int = 10) -> None:
        """
        Wait for exploration subagents to complete by monitoring planning/docs/.

        This is necessary because when the delegator spawns subagents, they run
        asynchronously. The delegator returns immediately, but subagents continue
        running in the background.

        Strategy:
        1. Read task_allocation.md to get expected component count
        2. Poll planning/docs/ until we have that many directories
        3. Also check that files are being written (activity detection)
        """
        import time
        import re

        task_file = self.planning_dir / "task_allocation.md"
        expected_count = 8  # Default minimum

        # Try to read expected count from task_allocation.md
        if task_file.exists():
            content = task_file.read_text()
            # Look for YAML frontmatter with total_tasks
            match = re.search(r'total_tasks:\s*(\d+)', content)
            if match:
                expected_count = int(match.group(1))
            else:
                # Count task headers like "## Task N:"
                task_matches = re.findall(r'##\s+Task\s+\d+', content)
                if task_matches:
                    expected_count = len(task_matches)

        logger.info(f"  → Expecting {expected_count} component directories")

        start_time = time.time()
        last_count = 0
        last_file_count = 0
        stable_iterations = 0

        while time.time() - start_time < timeout:
            # Count directories and files in planning/docs/
            if self.component_docs_dir.exists():
                dirs = [d for d in self.component_docs_dir.iterdir() if d.is_dir()]
                current_count = len(dirs)
                # Count total files for activity detection
                file_count = sum(1 for d in dirs for f in d.iterdir() if f.is_file())
            else:
                current_count = 0
                file_count = 0

            # Check if we have enough and count is stable
            if current_count >= expected_count:
                logger.info(f"  → All {current_count} components documented ({file_count} files)")
                return

            # Detect activity - if count or files changed, reset stability counter
            if current_count != last_count or file_count != last_file_count:
                elapsed = int(time.time() - start_time)
                dir_names = [d.name for d in dirs] if dirs else []
                logger.info(f"  → [{elapsed}s] Progress: {current_count}/{expected_count} components, {file_count} files")
                if dir_names:
                    logger.info(f"  → Components: {', '.join(sorted(dir_names)[:5])}{'...' if len(dir_names) > 5 else ''}")
                last_count = current_count
                last_file_count = file_count
                stable_iterations = 0
            else:
                stable_iterations += 1

            # If stable for 6 iterations (60 seconds) and we have some docs, proceed
            # (some subagents may have failed or be stuck)
            if stable_iterations >= 6 and current_count >= 3:
                elapsed = int(time.time() - start_time)
                logger.info(f"  → [{elapsed}s] No new activity for 60s, proceeding with {current_count} components")
                return

            time.sleep(poll_interval)

        logger.warning(f"  → Timeout after {timeout}s. Have {last_count}/{expected_count} components")

    def _step_4_generate_docs_index(self) -> dict:
        """
        Step 4: Generate planning/docs/index.md as a title page for components.

        This creates a README-like index that:
        - Lists all component documentation
        - Extracts descriptions from each component's index.md
        - Provides navigation to all subcomponents

        Returns:
            dict: Step execution result
        """
        import re

        if not self.component_docs_dir.exists():
            return {"success": False, "error": "No component docs directory"}

        # Get all component directories
        components = sorted([
            d for d in self.component_docs_dir.iterdir()
            if d.is_dir() and not d.name.startswith('.')
        ])

        if not components:
            return {"success": False, "error": "No components found"}

        # Build the index content
        lines = [
            "# Component Documentation",
            "",
            "This directory contains detailed documentation for each major component.",
            "",
            "## Components",
            "",
        ]

        for component_dir in components:
            component_name = component_dir.name
            # Convert kebab-case to Title Case
            display_name = ' '.join(
                word.capitalize() for word in component_name.replace('-', ' ').replace('_', ' ').split()
            )

            # Try to extract description from component's index.md
            index_file = component_dir / "index.md"
            description = ""
            if index_file.exists():
                content = index_file.read_text()
                # Look for first paragraph after the title
                lines_content = content.split('\n')
                for i, line in enumerate(lines_content):
                    # Skip title and empty lines
                    if line.startswith('#') or not line.strip():
                        continue
                    # Found first content line - use as description
                    description = line.strip()
                    # Truncate if too long
                    if len(description) > 150:
                        description = description[:147] + "..."
                    break

            # List files in the component
            md_files = sorted([f.stem for f in component_dir.glob("*.md")])
            file_list = ", ".join(md_files[:4])
            if len(md_files) > 4:
                file_list += f", +{len(md_files) - 4} more"

            lines.append(f"### [{display_name}]({component_name}/index.md)")
            if description:
                lines.append(f"")
                lines.append(f"{description}")
            lines.append(f"")
            lines.append(f"**Files:** {file_list}")
            lines.append(f"")

        # Add summary
        lines.extend([
            "---",
            "",
            f"*{len(components)} components documented*",
        ])

        # Write the index file
        index_path = self.component_docs_dir / "index.md"
        index_path.write_text('\n'.join(lines))

        logger.info(f"  → Created docs index with {len(components)} components")

        return {
            "success": True,
            "components": len(components),
            "path": str(index_path)
        }

    def _step_5_generate_overview(self) -> dict:
        """
        Step 5: Use Overview Writer agent to generate main documentation index.

        The overview writer will:
        - Read component docs from planning/docs/*/
        - Read repository overview from planning/overview.md
        - Create planning/index.md with comprehensive navigation

        Returns:
            dict: Step execution result
        """
        prompt = """Generate the main documentation index at planning/index.md.

Your task:
1. Read component docs from `planning/docs/*/index.md`
2. Read repository overview from `planning/overview.md`
3. **CREATE `planning/index.md`** with:
   - Repository overview (2-3 paragraphs from planning/overview.md)
   - Key features and tech stack
   - Quick Start guide (links to 3-5 most important docs)
   - Complete documentation structure with links to ALL component docs

**CRITICAL**: You MUST create the file `planning/index.md` using the Write tool.
This is the main entry point for all documentation.

Example structure:
```markdown
# Kubernetes Documentation

## Overview
Kubernetes is a container orchestration platform...

## Quick Start
- [API Server](docs/api-server/index.md)
- [Kubelet](docs/kubelet/index.md)
- [Client-Go](docs/client-go/index.md)

## Documentation Index

### Control Plane
- [API Server](docs/api-server/index.md) - REST API
- [Scheduler](docs/scheduler/index.md) - Pod scheduling
- [Controller Manager](docs/controller-manager/index.md) - Controllers

### Node Components
- [Kubelet](docs/kubelet/index.md) - Node agent
- [Kube-proxy](docs/kube-proxy/index.md) - Network proxy
```

Make the index welcoming, scannable, and easy to navigate.
All links should be relative to planning/ (e.g., docs/component/index.md).
"""

        response = self.wrapper.execute(
            prompt=prompt,
            agent_type=AgentType.OVERVIEW_WRITER,
            stream_output=False,
            stream_callback=self.stream_callback
        )

        return {
            "success": response.success if hasattr(response, 'success') else True,
            "output": str(response)[:200]
        }

    def _step_6_post_process(self) -> dict:
        """
        Step 6: Post-process documentation.

        - Copies docs to build/ directory (preserving originals)
        - Fixes GitHub links to point to correct repository
        - Renders mermaid diagrams to PNG
        - Generates HTML site using mkdocs

        Returns:
            dict: Step execution result with paths and statistics
        """
        from .docs_post_processor import DocsPostProcessor, DiagramTheme

        processor = DocsPostProcessor(
            docs_dir=self.planning_dir,  # Process all of planning/, not just docs/
            repo_url=self.repo_url,
            theme=DiagramTheme.DEFAULT,
            background="white"
        )

        # Run full post-processing pipeline
        result = processor.process_all()

        # Store result for later use (e.g., printing HTML path)
        self._post_process_result = result

        # Log summary
        if result.github_links_fixed > 0:
            logger.info(f"  → Fixed {result.github_links_fixed} GitHub links")
        logger.info(f"  → Rendered {result.diagrams_rendered}/{result.diagrams_found} diagrams")
        if result.html_output_dir:
            logger.info(f"  → HTML site: {result.html_output_dir}")

        return {
            "success": result.success,
            "source_dir": str(result.source_dir) if result.source_dir else None,
            "build_dir": str(result.build_dir) if result.build_dir else None,
            "html_output_dir": str(result.html_output_dir) if result.html_output_dir else None,
            "files_processed": result.files_processed,
            "diagrams_found": result.diagrams_found,
            "diagrams_rendered": result.diagrams_rendered,
            "diagrams_failed": result.diagrams_failed,
            "github_links_fixed": result.github_links_fixed,
            "errors": result.errors
        }

def run_documentation_pipeline(
    repo_path: Path,
    model: Optional[str] = None,
    verbose: bool = False,
    stream_callback: Optional[Callable[[str], None]] = None,
    repo_url: Optional[str] = None
) -> dict:
    """
    Execute the full multi-agent documentation pipeline.

    This is a convenience function that creates a pipeline, sets it up,
    and runs all steps.

    Args:
        repo_path: Path to the repository to document
        model: AI model to use for agents
        verbose: Enable verbose logging
        stream_callback: Optional callback for streaming agent output events
        repo_url: GitHub repository URL (for fixing links in docs)

    Returns:
        dict: Pipeline execution results

    Example:
        >>> from pathlib import Path
        >>> result = run_documentation_pipeline(Path("./my_repo"))
        >>> print(f"Success: {result['success']}")
        >>> print(f"Main index: {result['output_paths']['main_index']}")
    """
    pipeline = DocumentationPipeline(
        repo_path,
        model=model,
        verbose=verbose,
        stream_callback=stream_callback,
        repo_url=repo_url
    )
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
