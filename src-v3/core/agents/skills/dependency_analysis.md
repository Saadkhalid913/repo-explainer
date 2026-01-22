Analyze the repository’s dependency graph to identify risks, shared modules, and upgrade paths.

## Objectives

1. **Dependency Inventory**
   - List all direct dependencies (libraries, services).
   - Identify duplicated or overlapping functionality.

2. **Upgrade Gaps**
   - Highlight outdated major versions or known-security vulnerabilities.
   - Recommend drift from upstream (custom forks, patches).

3. **Coupling & Ownership**
   - Map which services or modules consume each dependency.
   - Note shared libraries that cross-team boundaries.

4. **Opportunity Signals**
   - Suggest dependency consolidation, replacements, or deprecations.
   - Call out opportunities for sandboxing or isolation (containers, virtualenvs).

## Output

Deliver `dependency_matrix.md` with tables, risk flags, and a visual “dependency spider” summary (ASCII/Markdown). Map vulnerable dependencies to their owning teams/sources.
