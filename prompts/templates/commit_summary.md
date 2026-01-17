# Commit Summary Analysis

## Context
You are analyzing a Git commit to provide a human-readable summary of what changed, similar to a GitHub PR description.

## Commit Information
- **SHA**: {commit_sha}
- **Message**: {commit_message}
- **Author**: {author_name} <{author_email}>
- **Date**: {date}

## Changed Files
{file_list}

## Git Diff Summary
```
{diff_content}
```

## Instructions

### 1. Analyze the Changes
- Read through the commit message and diff
- Identify what functionality was added, modified, or removed
- Note any new features, bug fixes, or architectural changes

### 2. Categorize the Impact
- **Features**: New functionality or capabilities
- **Fixes**: Bug fixes or corrections
- **Refactoring**: Code structure improvements without functional changes
- **Documentation**: Changes to docs, comments, or READMEs
- **Infrastructure**: Build, deployment, or CI/CD changes
- **Dependencies**: New or updated dependencies

### 3. Write a Clear Summary
Provide a concise but informative summary that answers:
- What was the main purpose of this commit?
- What specific changes were made?
- Are there any breaking changes or important notes?

### 4. Output Format
Return a JSON object with:
```json
{
  "summary": "Brief 1-2 sentence overview",
  "category": "features|fixes|refactoring|documentation|infrastructure|dependencies",
  "impact_level": "low|medium|high",
  "breaking_changes": false,
  "details": "More detailed explanation if needed"
}
```

## Constraints
- Focus on the actual code/description changes, not the diff format
- Keep summaries actionable and informative for developers
- Be specific but concise
- If the commit is a merge, focus on the net effect of the merged changes