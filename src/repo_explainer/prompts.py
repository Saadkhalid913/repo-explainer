"""Prompt templates for OpenCode analysis."""

from pathlib import Path
from typing import Dict

# Get the prompts directory
PROMPTS_DIR = Path(__file__).parent.parent.parent / "prompts" / "templates"


def load_prompt(template_name: str) -> str:
    """
    Load a prompt template from the prompts directory.

    Args:
        template_name: Name of the template file (without .md extension)

    Returns:
        Prompt template content as string

    Raises:
        FileNotFoundError: If template file doesn't exist
    """
    template_path = PROMPTS_DIR / f"{template_name}.md"

    if not template_path.exists():
        raise FileNotFoundError(
            f"Prompt template not found: {template_path}\n"
            f"Available templates: {list_available_prompts()}"
        )

    return template_path.read_text()


def list_available_prompts() -> list[str]:
    """
    List all available prompt templates.

    Returns:
        List of template names (without .md extension)
    """
    if not PROMPTS_DIR.exists():
        return []

    return [p.stem for p in PROMPTS_DIR.glob("*.md")]


def get_prompt_metadata() -> Dict[str, str]:
    """
    Get metadata about available prompts.

    Returns:
        Dictionary mapping prompt names to their descriptions
    """
    return {
        "quick_scan_v2": "Lightweight repository inventory with file mappings and module index",
        "architecture_deep_dive": "Comprehensive architectural analysis with function-level details",
        "pattern_detection": "Identify architectural and design patterns with evidence",
        "dependency_mapping": "Build internal and external dependency graphs",
    }


# Inline prompt templates as fallback (for when prompt files aren't available)
# These match the legacy prompts but with improved structure

QUICK_SCAN_LEGACY = """Perform a quick scan of this repository and generate:

## Required Outputs

1. **repository-summary.json**: Repository metadata
   ```json
   {
     "name": "<repo-name>",
     "primary_language": "<language>",
     "languages": ["<lang1>", "<lang2>"],
     "entry_points": ["<file1>", "<file2>"],
     "framework": "<framework-if-detected>"
   }
   ```

2. **module-index.md**: Table of contents listing all major modules with file paths

3. **tech-stack.txt**: Detected technologies and frameworks

## Instructions
- Scan project structure and identify all package/manifest files
- List main entry points with file paths
- Detect framework indicators
- Catalog major modules/components with file paths
- Extract technology stack from package managers

**Critical**: Every component/module reference must include its file path.
"""

ARCHITECTURE_LEGACY = """Analyze this repository and generate:

## Required Outputs

1. **architecture.md**: High-level architecture overview
   - System components with file paths
   - Component responsibilities and key functions
   - Data flow description
   - Entry points and integrations

2. **components.mermaid**: Component diagram showing:
   - All major components with file references in labels
   - Dependencies as directed edges
   - External systems

3. **dataflow.mermaid**: Data flow sequence diagram showing:
   - Typical request flow
   - Components involved with file references
   - Data transformations

4. **components.json**: Structured component data
   ```json
   {
     "components": [
       {
         "component_id": "<id>",
         "name": "<name>",
         "type": "<module|service|package>",
         "file_path": "<relative-path>",
         "key_functions": [
           {
             "name": "<function-name>",
             "file_path": "<file>",
             "line_range": {"start": 0, "end": 0},
             "purpose": "<description>"
           }
         ],
         "dependencies": {
           "internal": ["<component-id>"],
           "external": ["<package-name>"]
         }
       }
     ]
   }
   ```

5. **tech-stack.txt**: Technology stack summary with versions

## Instructions
Focus on:
- Main entry points and their responsibilities
- Core modules/packages and their relationships
- External dependencies and integrations
- Data flow between components

**Critical Requirements**:
- Every component MUST have a file_path
- Key functions MUST include file paths and line ranges
- Component diagrams MUST include file references in node labels
- All dependencies must reference component IDs or package names

## Analysis Workflow
1. Read package/manifest files first
2. Identify entry points and major components
3. For each component:
   - Record file path and line ranges
   - Extract 3-5 key functions with signatures and line numbers
   - Map dependencies to other components
4. Generate architecture.md with all collected data
5. Create Mermaid diagrams from component relationships
6. Validate all file paths are correct
"""


def get_quick_scan_prompt() -> str:
    """Get the quick scan prompt (v2 if available, legacy otherwise)."""
    try:
        return load_prompt("quick_scan_v2")
    except FileNotFoundError:
        return QUICK_SCAN_LEGACY


def get_architecture_prompt() -> str:
    """Get the architecture analysis prompt (deep dive if available, legacy otherwise)."""
    try:
        return load_prompt("architecture_deep_dive")
    except FileNotFoundError:
        return ARCHITECTURE_LEGACY


def get_pattern_detection_prompt() -> str:
    """Get the pattern detection prompt."""
    return load_prompt("pattern_detection")


def get_dependency_mapping_prompt() -> str:
    """Get the dependency mapping prompt."""
    return load_prompt("dependency_mapping")


# Incremental update prompt template
INCREMENTAL_UPDATE_TEMPLATE = """Analyze changes in this repository and update the existing documentation.

## Changed Files
The following files have been modified in recent commits:
{changed_files_list}

## Instructions

### 1. Analyze Each Changed File
For each file listed above:
- Read the file and understand what functionality it provides
- Identify which component it belongs to (or if it's a new component)
- Note new/modified/removed functions with line numbers
- Check for new dependencies introduced

### 2. Update architecture.md
Update the architecture documentation:
- Update relevant component descriptions for modified files
- Add new sections if new modules/components were added
- Update data flow descriptions if affected
- Remove references to deleted functionality

### 3. Update components.json
Update the component registry:
- Update existing component entries for modified files
- Add new component entries for new files
- Update key_functions with current line ranges
- Update dependency lists if imports changed

### 4. Update Mermaid Diagrams
If component relationships or data flow changed:
- Regenerate components.mermaid with updated structure
- Regenerate dataflow.mermaid if data flow was affected

### 5. Create CHANGELOG.md
Create a changelog entry summarizing:
- Which components were affected
- What functionality was added/modified/removed
- Any breaking changes or new dependencies

## Output Files
Create/update these files in the repository root:
- architecture.md (updated)
- components.json (updated)
- components.mermaid (if relationships changed)
- dataflow.mermaid (if data flow changed)
- CHANGELOG.md (new entry)

## Constraints
- Focus ONLY on the changed files listed above
- Preserve existing documentation structure and formatting
- Include file paths and line numbers for all references
- Don't re-analyze unchanged files
"""


def get_incremental_update_prompt(
    changed_files: list[str],
    existing_components_path: str | None = None,
) -> str:
    """
    Get the incremental update prompt with changed files.

    Args:
        changed_files: List of changed file paths
        existing_components_path: Path to existing components.json (for context)

    Returns:
        Formatted prompt string
    """
    files_list = "\n".join(f"- `{f}`" for f in changed_files)

    prompt = INCREMENTAL_UPDATE_TEMPLATE.format(
        changed_files_list=files_list,
    )

    if existing_components_path:
        prompt += f"\n\n**Note:** Read the existing `{existing_components_path}` for context on current component structure.\n"

    return prompt
