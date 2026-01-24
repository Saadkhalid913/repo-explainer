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
- **Output**: `planning/docs/core_api/`
- **Description**: Analyze the main API layer including all REST endpoints, authentication mechanisms, and data validation

## Task 2: Explore Database Layer
- **Component**: Database Layer
- **Paths**: `src/database/`, `src/models/`
- **Priority**: High
- **Focus**: Schema design, migrations, ORM usage
- **Output**: `planning/docs/database/`
- **Description**: Document database schema, migrations, and data access patterns
```

## Subagent Spawning

After creating the task allocation file, spawn parallel exploration subagents:

1. Use the Task tool with `subagent_type="Explore"` for each component
2. Pass component-specific prompts including:
   - Component name and paths
   - Focus areas
   - Output location
3. Aim for 3-10 parallel tasks based on:
   - Repository complexity
   - Component count
   - Resource limits (max 10 parallel agents)

## Guidelines

- Don't over-segment: Group related code into cohesive components
- Balance task load: Aim for roughly equal complexity per task
- Respect dependencies: Note which components should be explored first
- Focus on major components: Skip trivial utilities or test helpers
- Clear boundaries: Each component should have distinct responsibilities
