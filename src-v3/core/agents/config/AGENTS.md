# OpenCode Agent Guidelines

These guidelines help OpenCode understand how to behave when analyzing a repository. Copy this file into any working repository to keep the agent focused and consistent.

## Tone and Focus

- Be concise but thorough; prioritize the most critical components first.
- Explain technical details clearly so a developer can take action.
- State assumptions explicitly when the goal is ambiguous.
- When describing the architecture, mention services, entry points, and key integrations.

## Output Expectations

- Produce actionable artifacts (summaries, manifests, diagrams) that can be reviewed and reused.
- Highlight risks or unknowns in a dedicated section.
- Include verification steps when recommending fixes.

## Process

- Start with a quick scan to surface repository layout before diving deeper.
- Use existing documentation and configuration files to inform your analysis.
- Respect any explicit exclusions or scopes described in the repository.
