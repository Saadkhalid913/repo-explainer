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
from typing import Optional, Callable, Dict, Any
import logging
import time
import re
import json

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

    def _log(self, message: str) -> None:
        """Log to both logger and TUI callback."""
        logger.info(message)
        if self.stream_callback:
            self.stream_callback(json.dumps({"type": "message", "content": message}))

    def _execute_with_retry(
        self,
        prompt: str,
        agent_type: AgentType,
        expected_files: list[Path],
        max_retries: int = 1
    ) -> Dict[str, Any]:
        """Execute agent with retry on failure. Validates expected output files exist."""
        for attempt in range(max_retries + 1):
            try:
                response = self.wrapper.execute(
                    prompt=prompt,
                    agent_type=agent_type,
                    stream_output=False,
                    stream_callback=self.stream_callback
                )

                # Log response status for debugging
                if not response.success:
                    self._log(f"  Agent returned error: {response.error}")
                    logger.warning(f"Agent error: {response.error}")

                # Check expected files exist
                missing = [f for f in expected_files if not f.exists()]
                if not missing:
                    return {"success": True, "output": str(response)[:200]}

                self._log(f"  ⚠ Attempt {attempt+1}: Missing files: {[f.name for f in missing]}")

            except Exception as e:
                self._log(f"  ⚠ Attempt {attempt+1} failed: {e}")

            if attempt < max_retries:
                self._log(f"  → Retrying in 3s...")
                time.sleep(3)

        # Return partial success if some files exist
        existing = [f for f in expected_files if f.exists()]
        return {
            "success": len(existing) > 0,
            "output": f"Partial: {len(existing)}/{len(expected_files)} files created",
            "missing": [str(f) for f in expected_files if not f.exists()]
        }

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

            # Step 2: Delegator Agent - Create manifest and allocate tasks
            logger.info("Step 2: Allocating component exploration tasks...")
            step2_result = self._step_2_delegate_tasks()
            results["steps"]["delegate"] = step2_result

            # Validate delegator output before proceeding
            manifest_path = self.planning_dir / "component_manifest.md"
            if not manifest_path.exists():
                raise RuntimeError("Delegator failed to create component_manifest.md")
            results["output_paths"]["task_allocation"] = str(
                self.planning_dir / "task_allocation.md"
            )

            # Step 2.5: Generate doc_tree.json from manifest
            logger.info("Step 2.5: Generating documentation structure...")
            step2_5_result = self._generate_doc_tree_from_manifest()
            results["steps"]["structure_plan"] = step2_5_result
            results["output_paths"]["doc_tree"] = str(self.planning_dir / "doc_tree.json")

            # Step 3: Wait for subagents with early failure detection
            logger.info("Step 3: Waiting for exploration subagents...")
            wait_result = self._wait_for_exploration_subagents()
            results["steps"]["subagent_wait"] = wait_result

            if not wait_result.get("success") and wait_result.get("reason") == "no_subagent_output":
                raise RuntimeError("Delegator did not spawn subagents - check delegator prompt")

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

**Depth Requirement**: Enumerate all major components explicitly based on what you find.
Identify the actual components in THIS repository - do not use examples from other projects.

**IMPORTANT**: You MUST write `planning/overview.md` before finishing!
Use the Write tool, not bash echo commands.
"""
        return self._execute_with_retry(
            prompt=prompt,
            agent_type=AgentType.EXPLORATION,
            expected_files=[self.planning_dir / "overview.md"],
            max_retries=1
        )

    def _step_1_5_plan_structure(self) -> dict:
        """
        Step 1.5: Generate documentation structure plan (doc_tree.json).

        This step creates a JSON file that defines:
        - All documentation files that will be created
        - Exact titles for navigation sidebar
        - Exact headings for each page
        - Navigation ordering

        This ensures all subsequent documentation agents use consistent
        titles, headings, and cross-link paths.

        Returns:
            dict: Step execution result
        """
        # First, try to generate doc_tree.json using the Structure Planner agent
        prompt = """Generate the documentation structure plan.

Your task:
1. Read `planning/overview.md` to understand the repository
2. Read `planning/component_manifest.md` to get the component list
3. Generate `planning/doc_tree.json` with the complete documentation structure

The doc_tree.json MUST include:
- Every documentation file that will be created
- Exact `title` for each file (for sidebar navigation, max 25 chars)
- Exact `heading` for each file (the H1 at top of page)
- `nav_order` for sidebar ordering

Follow the schema from your plan_doc_structure skill.

**CRITICAL**:
- Titles must be clean noun phrases (e.g., "WebSearch Tool")
- NEVER use code, paths, or sentences as titles
- Use kebab-case for directory names
- Every directory must have an index.md

Write the JSON to `planning/doc_tree.json` using the Write tool.
"""

        try:
            response = self.wrapper.execute(
                prompt=prompt,
                agent_type=AgentType.STRUCTURE_PLANNER,
                stream_output=False,
                stream_callback=self.stream_callback
            )

            # Verify doc_tree.json was created
            doc_tree_path = self.planning_dir / "doc_tree.json"
            if doc_tree_path.exists():
                logger.info("  → doc_tree.json created successfully")
                return {
                    "success": True,
                    "output": str(response)[:200],
                    "doc_tree_path": str(doc_tree_path)
                }
            else:
                # Fall back to Python-generated structure
                logger.warning("  → Agent didn't create doc_tree.json, generating from manifest")
                return self._generate_doc_tree_from_manifest()

        except Exception as e:
            logger.warning(f"  → Structure planner failed: {e}, falling back to Python generation")
            return self._generate_doc_tree_from_manifest()

    def _generate_doc_tree_from_manifest(self) -> dict:
        """
        Fallback: Generate doc_tree.json from component_manifest.md using Python.

        This provides deterministic control over the structure if the agent
        fails to generate valid JSON.

        Returns:
            dict: Step execution result
        """
        import json
        import re
        from datetime import datetime

        manifest_path = self.planning_dir / "component_manifest.md"

        # Parse component manifest
        components = []
        if manifest_path.exists():
            content = manifest_path.read_text()
            # Look for table rows: | component-id | Display Name | path |
            for line in content.split('\n'):
                if '|' in line and not line.strip().startswith('|--'):
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) >= 4 and parts[1] and parts[1] != 'Component ID':
                        components.append({
                            'id': parts[1],
                            'name': parts[2],
                            'path': parts[3] if len(parts) > 3 else f"docs/{parts[1]}/"
                        })

        # Build the doc tree structure
        repo_name = self.repo_path.name
        tree = {
            "repository": repo_name,
            "title": f"{repo_name.replace('-', ' ').replace('_', ' ').title()} Documentation",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "structure": {
                "index.md": {
                    "title": "Home",
                    "heading": f"{repo_name.replace('-', ' ').replace('_', ' ').title()} Documentation",
                    "description": "Main documentation landing page",
                    "nav_order": 1
                }
            }
        }

        # Add component entries
        for i, comp in enumerate(components, start=1):
            comp_id = comp['id']
            comp_name = comp['name']

            # Create clean title (max 25 chars)
            title = comp_name if len(comp_name) <= 25 else comp_name[:22] + "..."

            tree["structure"][f"{comp_id}/"] = {
                "index.md": {
                    "title": title,
                    "heading": comp_name,
                    "description": f"Documentation for {comp_name}",
                    "nav_order": i
                },
                "architecture.md": {
                    "title": "Architecture",
                    "heading": f"{comp_name} Architecture",
                    "nav_order": 2
                }
            }

        # Write the doc tree
        doc_tree_path = self.planning_dir / "doc_tree.json"
        doc_tree_path.write_text(json.dumps(tree, indent=2))

        logger.info(f"  → Generated doc_tree.json with {len(components)} components")

        return {
            "success": True,
            "output": f"Generated doc_tree.json from manifest ({len(components)} components)",
            "doc_tree_path": str(doc_tree_path),
            "fallback": True
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

## STEP 0: DISCOVER ACTUAL FILES (CRITICAL - DO THIS FIRST!)

Before creating any manifest, you MUST discover what files actually exist:

1. Run `ls -la` to see top-level files and directories
2. Run `ls -la src/` (if src/ exists) to see source files
3. Note the ACTUAL file names you see

**ONLY use file paths you have verified exist!**
**DO NOT invent or guess file paths!**

### MANDATORY EXCLUSIONS - DO NOT DOCUMENT THESE:

- `planning/` - This is the pipeline's output directory, NOT source code!
- `.git/` - Git metadata, never document this
- `node_modules/`, `vendor/`, `venv/`, `.venv/` - Dependencies
- `dist/`, `build/`, `out/`, `target/` - Build outputs
- Lock files: `package-lock.json`, `pnpm-lock.yaml`, `yarn.lock`, `bun.lock`, `Gemfile.lock`, `poetry.lock`, `Cargo.lock`
- `.env*` files - Environment configuration
- `.DS_Store`, `*.log`, `*.tmp` - System/temp files
- `.opencode/`, `.claude/` - Tool configuration

**If you see `planning/` in the directory listing, IGNORE IT COMPLETELY.**

## STEP 1: Create Component Manifest

After discovering actual files, create `planning/component_manifest.md` with:
- ONLY components based on files you VERIFIED exist
- Use the EXACT file paths you discovered in Step 0

Example format (use actual paths from THIS repository):
```markdown
# Component Manifest

| Component ID | Display Name | Path | Output Path |
|-------------|--------------|------|-------------|
| component-a | Component A | src/actual_file.ts | planning/docs/component-a/index.md |
```

## STEP 2: Identify Components

1. Read `planning/overview.md` for context
2. Based on the ACTUAL **SOURCE** files you discovered in Step 0:
   - Group related files into components
   - Name components based on their functionality
   - Base count on repo size: 3-5 for small repos, 5-10 for medium repos
   - **ONLY include files that ACTUALLY EXIST!**
   - **SKIP all excluded items from Step 0 (planning/, .git/, lock files, etc.)**

Focus on actual source code and meaningful configuration, NOT:
- Lock files (pnpm-lock.yaml, package-lock.json, etc.)
- Git metadata (.git/)
- Pipeline output (planning/)
- IDE/editor configs (.vscode/, .idea/)

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

    def _wait_for_exploration_subagents(self, timeout: int = 600, poll_interval: int = 10) -> dict:
        """Wait for subagents with early failure detection."""
        EARLY_FAIL_THRESHOLD = 45  # Fail fast if 0 output after 45s

        task_file = self.planning_dir / "task_allocation.md"
        expected_count = 3  # Conservative default

        if task_file.exists():
            content = task_file.read_text()
            match = re.search(r'total_tasks:\s*(\d+)', content)
            if match:
                expected_count = int(match.group(1))
            else:
                expected_count = len(re.findall(r'##\s+Task\s+\d+', content)) or 3

        self._log(f"Expecting {expected_count} component directories")

        start_time = time.time()
        last_count, last_file_count, stable_iterations = 0, 0, 0

        while time.time() - start_time < timeout:
            current_count, file_count = 0, 0
            if self.component_docs_dir.exists():
                dirs = [d for d in self.component_docs_dir.iterdir() if d.is_dir()]
                current_count = len(dirs)
                file_count = sum(1 for d in dirs for f in d.iterdir() if f.is_file())

            elapsed = int(time.time() - start_time)

            # SUCCESS: Got all expected components
            if current_count >= expected_count:
                self._log(f"✓ All {current_count} components documented ({file_count} files)")
                return {"success": True, "components": current_count, "files": file_count}

            # EARLY FAIL: No output after threshold - delegator likely didn't spawn subagents
            if elapsed > EARLY_FAIL_THRESHOLD and current_count == 0:
                self._log(f"✗ No subagent output after {elapsed}s - delegator may have failed to spawn")
                return {"success": False, "reason": "no_subagent_output", "components": 0}

            # Activity detection
            if current_count != last_count or file_count != last_file_count:
                self._log(f"[{elapsed}s] Progress: {current_count}/{expected_count} components, {file_count} files")
                last_count, last_file_count, stable_iterations = current_count, file_count, 0
            else:
                stable_iterations += 1
                if stable_iterations % 3 == 0:
                    self._log(f"[{elapsed}s] Waiting... ({current_count}/{expected_count})")

            # EARLY EXIT: No activity for 90s AND have at least 50% of expected components
            min_completion = max(1, expected_count // 2)  # At least 50% or 1
            if stable_iterations >= 9 and current_count >= min_completion:
                self._log(f"[{elapsed}s] No activity for 90s, proceeding with {current_count}/{expected_count} components ({current_count * 100 // expected_count}%)")
                return {"success": True, "components": current_count, "partial": True}

            # STUCK: No activity for 90s but less than 50% - log once and keep waiting
            if stable_iterations == 9 and current_count < min_completion:
                self._log(f"[{elapsed}s] Only {current_count}/{expected_count} components ({current_count * 100 // expected_count}%), need {min_completion}+ to proceed. Waiting...")

            time.sleep(poll_interval)

        self._log(f"Timeout after {timeout}s. Have {last_count}/{expected_count} components")
        return {"success": last_count > 0, "components": last_count, "timeout": True}

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

Example structure (use the actual repository name and components you found):
```markdown
# {Repository Name} Documentation

## Overview
{Brief description from planning/overview.md}

## Quick Start
- [Component A](docs/component-a/index.md)
- [Component B](docs/component-b/index.md)

## Documentation Index
{List ALL components from planning/docs/ with links}
```

Make the index welcoming, scannable, and easy to navigate.
All links should be relative to planning/ (e.g., docs/component/index.md).
**Use the ACTUAL component names from the docs you read, not example names.**
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
            "docs_raw_dir": str(result.docs_raw_dir) if result.docs_raw_dir else None,
            "docs_rendered_dir": str(result.docs_rendered_dir) if result.docs_rendered_dir else None,
            "html_output_dir": str(result.html_output_dir) if result.html_output_dir else None,
            "files_processed": result.files_processed,
            "diagrams_found": result.diagrams_found,
            "diagrams_rendered": result.diagrams_rendered,
            "diagrams_failed": result.diagrams_failed,
            "github_links_fixed": result.github_links_fixed,
            "markdown_issues_fixed": result.markdown_issues_fixed,
            "validation_errors": [str(e) for e in result.validation_errors],
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
