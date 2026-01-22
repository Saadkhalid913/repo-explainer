"""OpenCode configuration schema and loader."""

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .project_config import AgentType

CONFIG_FILE = Path(__file__).resolve().parent / "config" / "opencode.json"


@dataclass
class AgentConfig:
    """Configuration for a single agent."""

    name: str
    description: str
    model: Optional[str] = None
    tools: Dict[str, bool] = field(default_factory=dict)
    skills: List[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict) -> "AgentConfig":
        """Create AgentConfig from dictionary."""
        return cls(
            name=data["name"],
            description=data["description"],
            model=data.get("model"),
            tools=data.get("tools", {}),
            skills=data.get("skills", []),
        )


@dataclass
class OpencodeConfig:
    """
    Complete OpenCode configuration defining all agents and their skills.

    This represents the opencode.json configuration file that maps
    agent types to their associated skills and tool permissions.
    """

    agents: Dict[str, AgentConfig] = field(default_factory=dict)

    @classmethod
    def load(cls, config_path: Path = CONFIG_FILE) -> "OpencodeConfig":
        """
        Load OpenCode configuration from JSON file.

        Args:
            config_path: Path to opencode.json (defaults to bundled config)

        Returns:
            Loaded OpencodeConfig instance
        """
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")

        with open(config_path, "r") as f:
            data = json.load(f)

        agents_data = data.get("agents", {})
        agents = {
            name: AgentConfig.from_dict(config)
            for name, config in agents_data.items()
        }

        return cls(agents=agents)

    @classmethod
    def default(cls) -> "OpencodeConfig":
        """Load the default bundled configuration."""
        return cls.load()

    def get_agent(self, agent_type: "AgentType") -> AgentConfig:
        """
        Get configuration for a specific agent type.

        Args:
            agent_type: The agent type to retrieve

        Returns:
            AgentConfig for the specified type

        Raises:
            KeyError: If agent type not found in configuration
        """
        # Handle both enum and string
        agent_name = agent_type.value if hasattr(
            agent_type, "value") else str(agent_type)
        if agent_name not in self.agents:
            raise KeyError(f"Agent '{agent_name}' not found in configuration")
        return self.agents[agent_name]

    def get_all_skills(self) -> List[str]:
        """
        Get a deduplicated list of all skills used by any agent.

        Returns:
            List of all unique skill names
        """
        all_skills = set()
        for agent_config in self.agents.values():
            all_skills.update(agent_config.skills)
        return sorted(list(all_skills))

    def save(self, config_path: Path) -> None:
        """
        Save configuration to JSON file.

        Args:
            config_path: Path where to save the configuration
        """
        data = {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "OpenCode Agent Configuration",
            "description": "Defines agents and their associated skills for OpenCode 2026",
            "type": "object",
            "agents": {
                name: {
                    "name": agent.name,
                    "description": agent.description,
                    **({"model": agent.model} if agent.model else {}),
                    **({"tools": agent.tools} if agent.tools else {}),
                    **({"skills": agent.skills} if agent.skills else {}),
                }
                for name, agent in self.agents.items()
            },
        }

        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            json.dump(data, f, indent=2)
