# Repo Explainer V3 - Agent Wrapper Architecture

**Status:** In Development
**Architecture:** Wrapper-based agent system with skill management

---

## Overview

V3 is a redesign focusing on clean agent wrappers for OpenCode and Claude Code CLI tools, with a skill-based system for managing agent capabilities.

### Key Features

- **Unified Agent Interface**: Both OpenCode and Claude Code wrappers share the same API
- **Skill Management**: Load, add, remove skills dynamically
- **Context Management**: Maintain working directory and execution context
- **Event Streaming**: Parse and handle real-time events from agents
- **Artifact Handling**: Automatic extraction and management of generated artifacts

---

## Architecture

```
src-v3/
├── core/
│   ├── models/
│   │   └── skill.py            # Skill model and SkillName registry
│   ├── agents/
│   │   ├── config/
│   │   │   ├── AGENTS.md
│   │   │   └── .claude.md
│   │   ├── skills/
│   │   │   ├── analyze_components.md
│   │   │   └── generate_documentation.md
│   │   ├── opencode_wrapper.py      # OpenCode CLI wrapper
│   │   └── claude_code_wrapper.py   # Claude Code CLI wrapper
│   └── utils/
│       └── clone_repo.py       # Repository cloning utilities
```

---

## Core Components

### 1. Skill System

Skills are self-contained prompts/capabilities that agents can use. Each skill follows this format:

```markdown
Brief description of what the skill does (first line)

Detailed instructions for the agent...

## Objectives
...

## Output Format
...
```

**Skill Model** (`models/skill.py`):
```python
@dataclass
class Skill:
    name: str
    content: str
    args: Optional[str]
    metadata: Dict[str, Any]

    @property
    def description(self) -> str:
        """First line of the content describes the skill."""

    @property
    def implementation(self) -> str:
        """Everything after the first line is the skill implementation."""


class SkillName(Enum):
    # Exploration agent skills
    ANALYZE_COMPONENTS = "analyze_components.md"
    DISCOVER_ARCHITECTURE = "discover_architecture.md"
    DEPENDENCY_ANALYSIS = "dependency_analysis.md"

    # Documentation agent skills
    GENERATE_DOCUMENTATION = "generate_documentation.md"
    DOCUMENT_API = "document_api.md"
```

`SkillName` files live in `src-v3/core/agents/skills` and are copied into
`.opencode/skills/<skill>/SKILL.md`. Agent files live in
`src-v3/core/agents/config` and are copied into `.opencode/agents/` (for example,
`exploration.md` and `documentation.md`). The wrappers also copy `AGENTS.md`
to the repository root so global guidance is always available.

### Project Configuration

`OpencodeProjectConfig` seeds each repository with the files that outline the
agent's behavior. It copies `AGENTS.md`, the selected agent files from
`src-v3/core/agents/config`, ALL `SkillName` prompts into `.opencode/skills/<skill>/SKILL.md`,
and any bash command definitions from `src-v3/core/agents/commands` into
`.opencode/commands/`.

The system now uses two main agents:

- **Exploration Agent** – Maps repository structure and identifies components using:
  - `analyze_components` - Identify and categorize code components
  - `discover_architecture` - Map overall system architecture
  - `dependency_analysis` - Analyze component dependencies

- **Documentation Agent** – Generates comprehensive documentation using:
  - `generate_documentation` - Create overview docs for components
  - `document_api` - Document public APIs and interfaces

You select the agent at execution time by passing `agent_type` to the `execute()` method.
Wrappers accept a `project_config` argument so you can provide custom overrides,
including restricting `enabled_agents`.

### 2. OpenCode Wrapper

High-level wrapper for OpenCode CLI.

```python
from pathlib import Path
from core.agents import create_opencode_wrapper
from core.models import SkillName

# Create wrapper
wrapper = create_opencode_wrapper(
    working_dir=Path("./my-repo"),
    model="claude-sonnet-4-5-20250929",
    skill_names=[SkillName.ANALYZE_COMPONENTS],
    verbose=True
)

# Execute a prompt
response = wrapper.execute(
    prompt="Analyze this repository and identify all components",
    context="Focus on Python modules",
    progress_callback=lambda event: print(event)
)

if response.success:
    print(f"Generated {len(response.artifacts)} artifacts")
    for name, content in response.artifacts.items():
        print(f"- {name}")
```

### 3. Claude Code Wrapper

Identical API to OpenCode wrapper, but uses Claude Code CLI.

```python
from core.agents import create_claude_code_wrapper, OpencodeProjectConfig

# Drop-in replacement for OpenCode
wrapper = create_claude_code_wrapper(
    working_dir=Path("./my-repo"),
    model="claude-sonnet-4-5-20250929",
    project_config=OpencodeProjectConfig.default(),
)

# Same API as OpenCode
response = wrapper.execute(prompt="...")
```

---

## Usage Examples

### Example 1: Basic Usage

```python
from pathlib import Path
from core.agents import create_opencode_wrapper, OpencodeProjectConfig

# Initialize the workspace with all agents and skills
wrapper = create_opencode_wrapper(
    working_dir=Path("."),
    project_config=OpencodeProjectConfig.default(),
    verbose=True
)

# Execute with the exploration agent
from core.agents import AgentType
response = wrapper.execute(
    prompt="List all Python files in this repository",
    agent_type=AgentType.EXPLORATION
)

if response.success:
    print(response.output)
else:
    print(f"Error: {response.error}")
```

### Example 2: Using Skills

```python
from pathlib import Path
from core.agents import OpenCodeWrapper, OpenCodeConfig
from core.models import SkillName

wrapper = OpenCodeWrapper(
    working_dir=Path("./my-repo"),
    config=OpenCodeConfig(verbose=True),
    skill_names=[SkillName.ANALYZE_COMPONENTS],
)

# Execute the registered skill
response = wrapper.execute_skill("analyze_components")

# Or include the skill in the prompt
response = wrapper.execute(
    prompt="Document the API layer",
    skills_to_use=["analyze_components"]
)
```

### Example 3: Selecting Skill Subsets

```python
from pathlib import Path
from core.agents import create_opencode_wrapper, OpencodeProjectConfig

wrapper = create_opencode_wrapper(
    working_dir=Path("./my-repo"),
    project_config=OpencodeProjectConfig.default(),
)

response = wrapper.execute(
    prompt="Generate documentation only for the service layer",
    agent_type=AgentType.DOCUMENTATION,
)
```

### Example 4: Progress Tracking

```python
from pathlib import Path
from core.agents import create_opencode_wrapper

def on_progress(event: dict):
    """Handle progress events."""
    event_type = event.get("type")
    if event_type == "tool_use":
        tool = event.get("tool", {}).get("name")
        print(f"🔧 Using tool: {tool}")
    elif event_type == "text":
        text = event.get("text", "")
        print(f"💬 Agent: {text[:50]}...")

wrapper = create_opencode_wrapper(working_dir=Path("."))

response = wrapper.execute(
    prompt="Analyze repository structure",
    progress_callback=on_progress
)
```

### Example 5: Artifact Management

```python
from pathlib import Path
from core.agents import create_opencode_wrapper

wrapper = create_opencode_wrapper(working_dir=Path("./my-repo"))

response = wrapper.execute(
    prompt="Create architecture documentation with diagrams"
)

if response.success:
    # Access all artifacts
    for artifact_name, content in response.artifacts.items():
        print(f"\n{'='*60}")
        print(f"Artifact: {artifact_name}")
        print(f"{'='*60}")
        print(content[:200] + "...")

    # Get specific artifact
    components = wrapper.get_artifact("components.json")
    if components:
        import json
        data = json.loads(components)
        print(f"Found {len(data['components'])} components")

    # Cleanup
    # wrapper.cleanup_artifacts()
```

### Example 6: Switching Between OpenCode and Claude Code

```python
from pathlib import Path
from core.agents import create_opencode_wrapper, create_claude_code_wrapper

# Use OpenCode
opencode = create_opencode_wrapper(working_dir=Path("."))
response1 = opencode.execute("Analyze this repo")

# Switch to Claude Code (same API!)
claude_code = create_claude_code_wrapper(working_dir=Path("."))
response2 = claude_code.execute("Analyze this repo")

# Both have identical interfaces
assert type(response1).__name__ in ["OpenCodeResponse", "ClaudeCodeResponse"]
assert hasattr(response1, 'success')
assert hasattr(response1, 'artifacts')
```

---

## Configuration

### OpenCodeConfig

```python
from core.agents import OpenCodeConfig, OutputFormat

config = OpenCodeConfig(
    binary_path="opencode",  # Path to binary
    model="claude-sonnet-4-5-20250929",
    output_format=OutputFormat.JSON,
    timeout=600,  # seconds
    verbose=False,
    max_tokens=None,
    temperature=None,
)
```

### ClaudeCodeConfig

```python
from core.agents import ClaudeCodeConfig

config = ClaudeCodeConfig(
    binary_path="claude",  # Path to Claude Code binary
    model="claude-sonnet-4-5-20250929",
    # ... same as OpenCodeConfig
)
```

---

## Skill Format

Skills must follow this format:

```markdown
Brief one-line description of what the skill does

## Detailed Instructions

Provide detailed instructions for the agent...

## Objectives

1. Objective 1
2. Objective 2

## Output Format

Describe expected output...

## Guidelines

- Guideline 1
- Guideline 2
```

**Key Requirements:**
- First line MUST be the skill description
- Rest is the skill implementation/prompt
- Can include examples, guidelines, output formats

**Example Skill File** (`skills/analyze_code.md`):

```markdown
Analyze code quality and identify issues

Review the codebase and identify:
- Code smells
- Performance issues
- Security vulnerabilities
- Best practice violations

## Output

Create a JSON file with findings:
```json
{
  "issues": [
    {
      "file": "path/to/file.py",
      "line": 42,
      "severity": "high|medium|low",
      "category": "security|performance|quality",
      "description": "Issue description"
    }
  ]
}
```
```

---

## API Reference

### OpenCodeWrapper

```python
class OpenCodeWrapper:
    def __init__(
        self,
        working_dir: Path,
        config: Optional[OpenCodeConfig] = None,
        project_config: Optional[OpencodeProjectConfig] = None,
    )

    def execute(
        self,
        prompt: str,
        agent_type: AgentType,
        context: Optional[str] = None,
        progress_callback: Optional[Callable[[Dict], None]] = None,
    ) -> OpenCodeResponse

    def get_artifact(self, artifact_name: str) -> Optional[str]
    def cleanup_artifacts(self) -> None
```

Skills are copied into `.opencode/skills/<name>/SKILL.md` when the wrapper initializes using the registered `SkillName` values,
and all agent files are copied to `.opencode/agents/` alongside `AGENTS.md`. Supply a custom `OpencodeProjectConfig` to
swap in different guidance files, agent subsets, or skill catalogs.

### ClaudeCodeWrapper

- Identical API to `OpenCodeWrapper` (same optional `project_config` parameter), just replace class names:
- `ClaudeCodeWrapper` instead of `OpenCodeWrapper`
- `ClaudeCodeConfig` instead of `OpenCodeConfig`
- `ClaudeCodeResponse` instead of `OpenCodeResponse`

---

## Differences from V2

| Aspect | V2 | V3 |
|--------|----|----|
| **Architecture** | Integrated agents in TUI | Standalone wrappers |
| **Interface** | Interactive TUI | Programmatic API |
| **Skills** | Hard-coded prompts | Dynamic skill loading |
| **CLI Tools** | OpenCode only | OpenCode + Claude Code |
| **Context** | Per-screen state | Per-wrapper instance |
| **Reusability** | TUI-specific | Library-first |

---

## Next Steps

1. **Implement Discovery Agent** using wrappers
2. **Implement Documentation Agent** using wrappers
3. **Build CLI interface** on top of wrappers
4. **Add more built-in skills**
5. **Create skill composition system**
6. **Add tool support** (not just skills)

---

## Testing

```python
# Test OpenCode wrapper
from pathlib import Path
from core.agents import create_opencode_wrapper

wrapper = create_opencode_wrapper(
    working_dir=Path("."),
    verbose=True
)

response = wrapper.execute("List all Python files")
assert response.success
print(response.output)
```

---

## License

See LICENSE file in repository root.

---

**Status:** ✅ Wrappers Complete, Ready for Agent Implementation
