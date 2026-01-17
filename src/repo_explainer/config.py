"""Configuration management for repo-explainer."""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Global settings for repo-explainer."""

    model_config = SettingsConfigDict(
        env_prefix="REPO_EXPLAINER_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Allow extra fields in .env without validation errors
    )

    # OpenCode settings
    opencode_binary: str = Field(default="opencode", description="Path to OpenCode binary")
    opencode_output_format: str = Field(default="json", description="OpenCode output format")
    opencode_model: str = Field(
        default="openrouter/google/gemini-3-flash-preview",
        description="OpenCode model identifier (provider/model)",
    )

    # Analysis settings
    analysis_depth: Literal["quick", "standard", "deep"] = Field(
        default="standard", description="Depth of analysis"
    )

    # Output settings
    output_dir: Path = Field(default=Path("docs"), description="Output directory for docs")
    diagrams_dir: Path = Field(default=Path("diagrams"), description="Output directory for diagrams")

    # Logging
    verbose: bool = Field(default=False, description="Enable verbose output")


# Global settings instance
_settings: Settings | None = None


def get_settings() -> Settings:
    """Get or create the global settings instance."""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings


def reset_settings() -> None:
    """Reset settings (useful for testing)."""
    global _settings
    _settings = None
