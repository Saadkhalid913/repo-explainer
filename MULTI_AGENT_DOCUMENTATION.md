# Multi-Agent Documentation System

## Overview

A hierarchical multi-agent system for automated repository documentation generation. The system orchestrates multiple specialized agents working in sequence to produce comprehensive, structured documentation with diagrams.

## Implementation Status

✅ **COMPLETE** - All components implemented and tested.

## Architecture

### Agent Types (5 total)

1. **EXPLORATION** - Repository exploration and analysis
2. **DOCUMENTATION** - Documentation aggregation and TOC creation
3. **DELEGATOR** - Task allocation across parallel agents (NEW)
4. **SECTION_WRITER** - Section generation with mermaid diagrams (NEW)
5. **OVERVIEW_WRITER** - Main documentation index creation (NEW)

### Skills (10 total)

**Exploration Skills:**
- `analyze_components` - Component identification and analysis
- `discover_architecture` - Architecture pattern discovery
- `dependency_analysis` - Dependency mapping

**Documentation Skills:**
- `generate_documentation` - Documentation generation
- `document_api` - API documentation
- `create_table_of_contents` - TOC creation (NEW)

**Delegator Skills:**
- `allocate_exploration_tasks` - Dynamic task allocation (NEW)

**Section Writer Skills:**
- `generate_section_with_diagrams` - Section generation with diagrams (NEW)
- `create_mermaid_diagrams` - Mermaid diagram creation (NEW)

**Overview Writer Skills:**
- `generate_overview_index` - Main index generation (NEW)

## Pipeline Workflow

```
1. Explorer Agent
   └─> Creates planning/overview.md

2. Delegator Agent
   ├─> Reads overview
   ├─> Creates planning/task_allocation.md
   └─> Spawns parallel Explorer Subagents
       └─> Each outputs to planning/docs/{component}/

3. Documentation Agent
   ├─> Reads all component docs
   ├─> Creates planning/documentation/toc.json
   └─> Spawns parallel Section Writer Subagents
       └─> Each outputs to docs/{section}/

4. Overview Writer Agent
   ├─> Reads all section indices
   └─> Creates docs/index.md
```

## File-Based Communication

```
{working_dir}/
  planning/
    overview.md              # Explorer output
    task_allocation.md       # Delegator output
    docs/
      component_1/          # Component exploration outputs
        overview.md
        api.md
        architecture.md
      component_2/...
    documentation/
      toc.json              # Documentation agent output
  docs/
    index.md                # Overview writer output (main entry point)
    section_1/              # Section writer outputs
      index.md
      diagram1.mmd
      diagram1.png
    section_2/...
```

## Usage

### Python API

```python
from pathlib import Path
from core.documentation_pipeline import run_documentation_pipeline

# Run full pipeline
result = run_documentation_pipeline(
    repo_path=Path("./my_repository"),
    verbose=True
)

# Check results
if result['success']:
    print(f"Documentation generated at: {result['output_paths']['main_index']}")
else:
    print(f"Errors: {result['errors']}")
```

### Command Line

```bash
# Run pipeline on a repository
python src-v3/core/documentation_pipeline.py /path/to/repository

# Example output:
# 2026-01-23 - INFO - Step 1: Creating repository overview...
# 2026-01-23 - INFO - Step 2: Allocating component exploration tasks...
# 2026-01-23 - INFO - Step 3: Component exploration (parallel subagents)...
# 2026-01-23 - INFO - Step 4: Creating table of contents...
# 2026-01-23 - INFO - Step 5: Generating documentation sections...
# 2026-01-23 - INFO - Step 6: Generating main documentation index...
# 2026-01-23 - INFO - Pipeline completed successfully!
```

### Programmatic API

```python
from pathlib import Path
from core.documentation_pipeline import DocumentationPipeline

# Create pipeline
pipeline = DocumentationPipeline(
    repo_path=Path("./my_repository"),
    verbose=True
)

# Setup (creates directories, initializes wrapper)
pipeline.setup()

# Run full pipeline
result = pipeline.run()

# Or run individual steps
pipeline._step_1_explore_repository()
pipeline._step_2_delegate_tasks()
pipeline._step_4_create_toc()
pipeline._step_6_generate_overview()
```

## Testing

```bash
# Run all tests
python -m pytest src-v3/core/documentation_pipeline_test.py -v

# Run specific test class
python -m pytest src-v3/core/documentation_pipeline_test.py::TestAgentTypesAndSkills -v

# Expected output:
# 15 passed in 1.30s
```

## Test Coverage

- ✅ Agent type definitions and configs
- ✅ Skill definitions and validation
- ✅ OpencodeProjectConfig applies all agents/skills
- ✅ Pipeline initialization and setup
- ✅ Directory structure creation
- ✅ File-based communication protocol
- ✅ Mock pipeline execution

## Dependencies

### Required
- Python 3.8+
- opencode CLI (for multi-agent execution)
- File system write permissions

### Optional
- **mermaid-cli (`mmdc`)** - For diagram compilation
  ```bash
  npm install -g @mermaid-js/mermaid-cli
  ```
  - Used by section_writer agent for PNG generation
  - Pipeline continues if not available (diagrams remain as .mmd files)

## Files Created/Modified

### New Agent Configs (3 files)
- `src-v3/core/agents/config/delegator.md`
- `src-v3/core/agents/config/section_writer.md`
- `src-v3/core/agents/config/overview_writer.md`

### New Skills (5 files)
- `src-v3/core/agents/skills/allocate_exploration_tasks.md`
- `src-v3/core/agents/skills/create_table_of_contents.md`
- `src-v3/core/agents/skills/generate_section_with_diagrams.md`
- `src-v3/core/agents/skills/create_mermaid_diagrams.md`
- `src-v3/core/agents/skills/generate_overview_index.md`

### Modified Files (3 files)
- `src-v3/core/models/skill.py` - Added 5 new SkillName entries
- `src-v3/core/agents/project_config.py` - Added 3 new AgentType entries
- `src-v3/core/agents/config/documentation.md` - Added create_table_of_contents skill

### New Implementation (2 files)
- `src-v3/core/documentation_pipeline.py` - Pipeline orchestration
- `src-v3/core/documentation_pipeline_test.py` - Comprehensive tests

## Design Decisions

### 1. File-Based Communication
Agents communicate via files in structured directories rather than in-memory state. This provides:
- Clear audit trail of agent outputs
- Easy debugging and inspection
- Resumable pipelines
- Parallel execution support

### 2. Dynamic Task Allocation
The delegator agent dynamically determines component split (3-10 components) based on:
- Repository structure and size
- Architectural boundaries
- Code complexity
- Dependency relationships

### 3. Mermaid Diagram Support
Section writers can generate and compile mermaid diagrams:
- Source files (.mmd) always created
- PNG compilation attempted if mmdc available
- Graceful degradation if compilation fails
- Pipeline continues without failing

### 4. Hierarchical Agent System
Six-step pipeline with subagent spawning:
- Main pipeline agents: Explorer, Delegator, Documentation, Overview Writer
- Subagents: Component explorers (spawned by delegator), Section writers (spawned by documentation agent)
- Enables parallel execution for exploration and section generation

## Error Handling

- **Missing mmdc**: Logs warning, keeps .mmd files, continues pipeline
- **Component exploration failure**: Logs error, continues with other components
- **Critical failures** (Explorer, Delegator): Abort pipeline
- **Non-critical failures** (individual section writer): Skip that section, continue

## Future Enhancements

Potential improvements not yet implemented:
- Retry logic for failed subagents
- Progress tracking and status updates
- Incremental documentation updates (only changed components)
- Custom section templates
- Diagram validation and auto-correction
- Multi-language support (currently optimized for Python/JS)

## References

- Original plan: See plan mode transcript
- Workflow diagram: Based on multi-agent documentation workflow
- OpenCode documentation: For agent wrapper usage
- Mermaid documentation: For diagram syntax

---

*Implementation completed: 2026-01-23*
*Total test coverage: 15 tests, 100% passing*
