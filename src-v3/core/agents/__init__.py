"""Agents for repo-explainer v3."""

from .opencode_wrapper import (
    OpenCodeWrapper,
    OpenCodeConfig,
    OpenCodeResponse,
    create_opencode_wrapper,
)
from .claude_code_wrapper import (
    ClaudeCodeWrapper,
    ClaudeCodeConfig,
    ClaudeCodeResponse,
    create_claude_code_wrapper,
)
from .project_config import (
    AgentType,
    OpencodeProjectConfig,
)

__all__ = [
    # OpenCode
    "OpenCodeWrapper",
    "OpenCodeConfig",
    "OpenCodeResponse",
    "create_opencode_wrapper",
    # Claude Code
    "ClaudeCodeWrapper",
    "ClaudeCodeConfig",
    "ClaudeCodeResponse",
    "create_claude_code_wrapper",
    # Config
    "AgentType",
    "OpencodeProjectConfig",
]
