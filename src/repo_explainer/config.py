"""Configuration management using Pydantic settings."""

from enum import Enum
from pathlib import Path
from typing import Optional

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class AnalysisDepth(str, Enum):
    """Analysis depth levels mapped to OpenCode commands."""

    QUICK = "quick"
    STANDARD = "standard"
    DEEP = "deep"


class OutputFormat(str, Enum):
    """Output format options."""

    MARKDOWN = "markdown"
    JSON = "json"


class Settings(BaseSettings):
    """Global configuration for repo-explainer."""

    model_config = SettingsConfigDict(
        env_prefix="REPO_EXPLAINER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # OpenRouter / LLM settings
    openrouter_api_key: Optional[str] = Field(default=None, description="OpenRouter API key")
    llm_model: str = Field(
        default="google/gemini-2.5-flash-preview",
        description="LLM model to use via OpenRouter",
    )
    llm_base_url: str = Field(
        default="https://openrouter.ai/api/v1",
        description="OpenRouter API base URL",
    )

    # OpenCode settings
    opencode_binary: str = Field(default="opencode", description="Path to OpenCode binary")
    opencode_server_url: Optional[str] = Field(
        default=None, description="OpenCode server URL if using remote mode"
    )

    # Analysis settings
    default_depth: AnalysisDepth = Field(
        default=AnalysisDepth.STANDARD,
        description="Default analysis depth",
    )
    output_format: OutputFormat = Field(
        default=OutputFormat.MARKDOWN,
        description="Default output format",
    )

    # Paths
    output_dir: Path = Field(default=Path("./repo-docs"), description="Default output directory")
    cache_dir: Path = Field(default=Path("./.repo-explainer-cache"), description="Cache directory")

    # Behavior
    verbose: bool = Field(default=False, description="Enable verbose output")
    use_claude_fallback: bool = Field(
        default=False, description="Fall back to Claude CLI if OpenCode unavailable"
    )
    claude_binary: str = Field(default="claude", description="Path to Claude CLI binary")

    # Limits
    max_files: int = Field(default=10000, description="Maximum files to analyze")
    max_tokens_per_request: int = Field(
        default=100000, description="Max tokens per LLM request"
    )


# Singleton instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def load_config_file(config_path: Path) -> Settings:
    """Load settings from a YAML config file and merge with env/defaults."""
    global _settings

    if config_path.exists():
        with open(config_path) as f:
            config_data = yaml.safe_load(f) or {}
        _settings = Settings(**config_data)
    else:
        _settings = Settings()

    return _settings


def reset_settings() -> None:
    """Reset settings to None (useful for testing)."""
    global _settings
    _settings = None
