Allocate component exploration tasks based on repository overview

You are responsible for analyzing the repository overview and intelligently allocating component exploration tasks across parallel agents.

## Purpose

Analyze the repository overview and dynamically determine how to split exploration into parallel component analysis tasks.

## Input

- Read `planning/overview.md` for repository structure
- Identify major components, services, or architectural layers

## Processing

1. **Identify 3-10 major components** based on:
   - Directory structure and code organization
   - Code volume (lines of code, file count)
   - Architectural boundaries (services, layers, modules)
   - Dependency centrality (how many components depend on it)

2. **Prioritize components** by:
   - Dependency centrality (core vs peripheral)
   - Complexity (code size, cyclomatic complexity)
   - User-specified focus areas

3. **Create task allocation plan** with:
   - Component name and description
   - Files/directories to explore
   - Specific focus areas (API, architecture, dependencies)
   - Priority level (high, medium, low)
   - Output location

## Output

Write `planning/task_allocation.md` with YAML frontmatter and task descriptions:

```yaml
---
total_tasks: 5
parallel_execution: true
max_parallel: 10
---

# Task Allocation Plan

## Task 1: Explore Core API Layer
- **Component**: Core API
- **Paths**: `src/core/api/`, `src/core/routes/`
- **Priority**: High
- **Focus**: REST endpoints, authentication, data contracts
- **Output**: `planning/docs/core_api/index.md`
- **Description**: Analyze the main API layer including all REST endpoints, authentication mechanisms, and data validation

## Task 2: Explore Database Layer
- **Component**: Database Layer
- **Paths**: `src/database/`, `src/models/`
- **Priority**: High
- **Focus**: Schema design, migrations, ORM usage
- **Output**: `planning/docs/database/index.md`
- **Description**: Document database schema, migrations, and data access patterns
```

## Subagent Spawning

**CRITICAL**: After creating the task allocation file, you MUST spawn parallel exploration subagents:

1. Use the Task tool with `subagent_type="exploration"` for each component (lowercase!)
2. Pass component-specific prompts including:
   - Component name and paths
   - Focus areas
   - **IMPORTANT**: Output location as `planning/docs/{component_name}/index.md`
   - Depth requirements (200+ lines, 3+ examples, 2+ diagrams, 1+ table)
3. Aim for 3-10 parallel tasks based on:
   - Repository complexity
   - Component count
   - Resource limits (max 10 parallel agents)

**Example subagent prompt**:
```
Explore the {component_name} component located in {paths}.

Create comprehensive documentation in planning/docs/{component_name}/index.md

Requirements:
- Enumerate ALL sub-components by name (don't generalize)
- Include minimum 3 code examples
- Include minimum 2 diagrams
- Include minimum 1 reference table
- Create multi-file structure if component is complex (10+ files)

Focus areas:
- {focus_area_1}
- {focus_area_2}
- {focus_area_3}
```

**File Naming Convention**: All component documentation must use `index.md` as the main file name, not `README.md` or `overview.md`. This ensures consistent navigation across all documentation.

**IMPORTANT**: Don't just create the task allocation file and stop. You must ACTUALLY SPAWN the subagents using the Task tool. The task allocation file is just documentation - the real work happens when you spawn the subagents.

## Guidelines

- Don't over-segment: Group related code into cohesive components
- Balance task load: Aim for roughly equal complexity per task
- Respect dependencies: Note which components should be explored first
- Focus on major components: Skip trivial utilities or test helpers
- Clear boundaries: Each component should have distinct responsibilities
