# Core Agents Module Architecture

## Overview

The `core/agents` module provides a unified abstraction layer for managing agent-based code analysis tools. It supports both OpenCode and Claude Code CLI with identical APIs for seamless interoperability.

## Module Responsibilities

1. **CLI Wrapper Abstraction** - Encapsulate complexity of subprocess management, command building, and output parsing
2. **Configuration Management** - Handle agent configuration, project setup, and skill management
3. **Artifact Extraction** - Automatically manage and extract generated files from standard locations
4. **Drop-in Compatibility** - Ensure OpenCode and Claude Code can be used interchangeably

## Key Components

### Wrapper Classes

#### OpenCodeWrapper (`opencode_wrapper.py`)
Manages OpenCode CLI interactions with full streaming support.

**Public Methods:**
- `execute(prompt, agent_type, context, stream_output, stream_callback, progress_callback)` - Execute prompt with specified agent
- `get_artifact(artifact_name)` - Retrieve specific generated artifact
- `cleanup_artifacts()` - Clean up temporary files

**Internal Methods:**
- `_build_prompt(prompt, context)` - Combine context and task prompt
- `_build_command(prompt, agent_type)` - Construct OpenCode command with arguments
- `_parse_output(output, progress_callback)` - Route to format-specific parser
- `_parse_json_output(output, progress_callback)` - Parse newline-delimited JSON events
- `_extract_artifacts()` - Extract files from `repo_explainer_artifacts/` directory
- `_check_availability()` - Verify OpenCode binary is available

**Configuration:**
```python
OpenCodeConfig(
    binary_path: str = "opencode",
    model: str = "openrouter/anthropic/claude-sonnet-4-5-20250929",
    output_format: OutputFormat = OutputFormat.JSON,
    timeout: int = 600,
    verbose: bool = False,
    max_tokens: Optional[int] = None,
)
```

#### ClaudeCodeWrapper (`claude_code_wrapper.py`)
Manages Claude Code CLI with API-compatible interface to OpenCodeWrapper.

**Differences from OpenCodeWrapper:**
- Prompt passed via stdin instead of command-line argument
- Uses `--output-format` flag instead of `--format`
- Supports `temperature` parameter
- No `agent_type` parameter in execute() - Claude Code selects agent implicitly
- Simpler output parsing (less streaming complexity)

**Configuration:**
```python
ClaudeCodeConfig(
    binary_path: str = "claude",
    model: str = "claude-sonnet-4-5-20250929",
    output_format: OutputFormat = OutputFormat.JSON,
    timeout: int = 600,
    verbose: bool = False,
    max_tokens: Optional[int] = None,
    temperature: Optional[float] = None,
)
```

### Configuration Classes

#### AgentType Enum (`project_config.py`)
Defines available agents and maps to configuration files.

```python
class AgentType(Enum):
    EXPLORATION = "exploration"       # exploration.md
    DOCUMENTATION = "documentation"   # documentation.md
```

**Properties:**
- `filename` - Returns agent markdown filename (e.g., `exploration.md`)
- `source_path` - Returns Path to config file
- `load_content()` - Read agent config as string

#### OpencodeProjectConfig (`project_config.py`)
Manages workspace setup with agents and skills.

**Methods:**
- `apply(working_dir)` - Write config files to workspace
- `cleanup(working_dir)` - Remove all config files
- `get_skill(name)` - Retrieve Skill by name
- `all_skills` - Dictionary of all loaded Skill objects
- `all_agents` - Dictionary of all loaded agent contents

**Convenience Constructors:**
- `.default()` - All agents, all skills
- `.exploration_only()` - Exploration agent only
- `.documentation_only()` - Documentation agent only

### Response Objects

#### OpenCodeResponse / ClaudeCodeResponse
```python
@dataclass
class Response:
    success: bool                          # Execution succeeded
    output: str                            # Raw tool output
    events: List[Dict[str, Any]] = []      # Parsed JSON events (if applicable)
    error: Optional[str] = None            # Error message if failed
    artifacts: Dict[str, str] = {}         # Generated files (path -> content)
    metadata: Dict[str, Any] = {}          # Additional metadata
```

## Directory Structure

```
core/agents/
├── __init__.py                    # Public API exports
├── opencode_wrapper.py            # OpenCode CLI wrapper (~455 lines)
├── claude_code_wrapper.py         # Claude Code CLI wrapper (~381 lines)
├── opencode_config.py             # Configuration schema (~137 lines)
├── project_config.py              # Project setup (~202 lines)
│
├── config/                        # Configuration and guideline files
│   ├── AGENTS.md                  # Global guidelines for all agents
│   ├── exploration.md             # Exploration agent guidelines
│   ├── documentation.md           # Documentation agent guidelines
│   ├── .claude.md                 # Claude-specific guidelines
│   └── opencode.json              # Agent-to-skill mapping schema
│
└── skills/                        # Agent skill definitions
    ├── analyze_components.md       # Identify code components
    ├── discover_architecture.md    # Map system architecture
    ├── dependency_analysis.md      # Analyze dependencies
    ├── generate_documentation.md   # Generate component docs
    └── document_api.md             # Generate API reference
```

## Workflow

### Initialization

```python
from pathlib import Path
from core.agents import create_opencode_wrapper, AgentType, OpencodeProjectConfig

# Create wrapper with optional custom config
wrapper = create_opencode_wrapper(
    working_dir=Path("/repo"),
    model="openrouter/anthropic/claude-sonnet-4-5-20250929",
    project_config=OpencodeProjectConfig.default(),
    verbose=True
)
```

### Execution

```python
# Execute with exploration agent
response = wrapper.execute(
    prompt="Analyze repository structure",
    agent_type=AgentType.EXPLORATION,
    context="Previous analysis results...",
)

# Check results
if response.success:
    print(response.output)
    for artifact_name, content in response.artifacts.items():
        print(f"Generated: {artifact_name}")
```

### Artifact Handling

The tool automatically extracts generated files from `repo_explainer_artifacts/` directory:

```python
# Access specific artifact
content = wrapper.get_artifact("architecture_summary.md")

# All artifacts available in response
for name, content in response.artifacts.items():
    # Process artifact
    pass

# Clean up when done
wrapper.cleanup_artifacts()
```

## Configuration Files

### AGENTS.md
Global guidelines applicable to all agents. Covers:
- Expected tone and communication style
- Output format expectations
- Common processes and approaches

### exploration.md
Exploration agent configuration:
- Focus: Mapping services, entry points, data contracts
- Skills: Component analysis, architecture discovery, dependency analysis
- Tools: Code reading, file system traversal, documentation generation

### documentation.md
Documentation agent configuration:
- Focus: Creating clear, comprehensive documentation
- Skills: Documentation generation, API reference creation
- Tools: Code reading, documentation writing, examples

### .claude.md
Claude-specific guidelines (optional, supplements AGENTS.md):
- More descriptive guidance
- Code paths and API references
- Paired recommendations with rationale

### opencode.json
Schema defining agent-to-skill mappings for OpenCode agents.

## Skill System

Skills are modular capabilities that agents can use. Defined in `core/models/skill.py`:

```python
@dataclass
class Skill:
    name: str                      # e.g., "analyze_components"
    content: str                   # Full prompt/definition
    args: Optional[str] = None     # Optional parameters
    metadata: Dict[str, Any] = {}  # Additional metadata
```

### Available Skills

**Exploration Agent:**
1. `analyze_components` - Identify services, modules, libraries, entry points
2. `discover_architecture` - Map system boundaries, data flow, integration points
3. `dependency_analysis` - List dependencies, identify vulnerabilities, map coupling

**Documentation Agent:**
1. `generate_documentation` - Create component overviews, architecture, examples
2. `document_api` - Catalog functions, methods, endpoints with usage patterns

## API Examples

### Basic Usage

```python
from pathlib import Path
from core.agents import create_opencode_wrapper, AgentType

wrapper = create_opencode_wrapper(Path("/my-repo"))
response = wrapper.execute("Analyze the codebase", agent_type=AgentType.EXPLORATION)

if response.success:
    print(response.output)
```

### With Context Chaining

```python
# Phase 1: Exploration
exploration = wrapper.execute(
    prompt="Identify all services and entry points",
    agent_type=AgentType.EXPLORATION
)

# Phase 2: Documentation (using exploration results as context)
if exploration.success:
    documentation = wrapper.execute(
        prompt="Create comprehensive documentation",
        agent_type=AgentType.DOCUMENTATION,
        context=exploration.output
    )
```

### With Progress Tracking

```python
def on_progress(event: Dict[str, Any]) -> None:
    if event.get("type") == "file_created":
        print(f"Created: {event.get('path')}")

response = wrapper.execute(
    prompt="Analyze repository",
    agent_type=AgentType.EXPLORATION,
    progress_callback=on_progress
)
```

### Custom Configuration

```python
from core.agents import (
    create_opencode_wrapper,
    OpencodeProjectConfig,
    AgentType
)

# Use only exploration agent
config = OpencodeProjectConfig.exploration_only()
wrapper = create_opencode_wrapper(Path("/repo"), project_config=config)
```

## Design Patterns

1. **Wrapper Pattern** - Hides CLI complexity behind clean interface
2. **Configuration Pattern** - Separates concerns (agent, project, tool configs)
3. **Skill-Based System** - Modular, loadable capabilities
4. **Artifact Pattern** - Automatic file extraction and tracking
5. **Callback Pattern** - Real-time progress tracking via callbacks
6. **Drop-in Compatibility** - OpenCode and Claude Code share identical API

## Error Handling

All wrappers follow consistent error patterns:

```python
response = wrapper.execute(...)

if not response.success:
    print(f"Error: {response.error}")
    # response.output may contain partial results
```

Common error conditions:
- Binary not found (installation issue)
- Invalid working directory
- Timeout during execution
- Command execution failure
- JSON parsing errors (for JSON format)

## Integration Points

- **Models** (`core/models/`) - Skill definitions and management
- **Utils** (`core/utils/`) - Repository cloning and setup
- **Main** (`core/main.py`) - Orchestrates discovery and documentation phases
