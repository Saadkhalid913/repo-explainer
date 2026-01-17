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
        "large_system_analysis": "Comprehensive analysis for large monorepos like Kubernetes, Linux, etc.",
        "extra_deep_analysis": "Exhaustive documentation with per-component, per-interaction, and per-API pages",
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


def get_large_system_prompt() -> str:
    """Get the large system analysis prompt for complex monorepos."""
    return load_prompt("large_system_analysis")


def get_extra_deep_prompt() -> str:
    """Get the extra deep analysis prompt for exhaustive documentation."""
    return load_prompt("extra_deep_analysis")
