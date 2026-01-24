"""Project configuration helpers for agent wrappers."""

import shutil
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Set

from ..models.skill import Skill, SkillName

CONFIG_SOURCE_DIR = Path(__file__).resolve().parent / "config"
COMMANDS_SOURCE_DIR = Path(__file__).resolve().parent / "commands"


class AgentType(Enum):
    """Available agent types."""

    EXPLORATION = "exploration"
    DOCUMENTATION = "documentation"
    DELEGATOR = "delegator"
    SECTION_WRITER = "section_writer"
    OVERVIEW_WRITER = "overview_writer"

    @property
    def filename(self) -> str:
        """Agent markdown filename (e.g., 'exploration.md')."""
        return f"{self.value}.md"

    @property
    def source_path(self) -> Path:
        """Path to the source config file."""
        return CONFIG_SOURCE_DIR / self.filename

    def load_content(self) -> str:
        """Read the agent config content."""
        if not self.source_path.exists():
            raise FileNotFoundError(
                f"Agent config not found: {self.source_path}")
        return self.source_path.read_text()


@dataclass
class OpencodeProjectConfig:
    """
    Project configuration for OpenCode workspaces.

    By default, ALL agents and ALL skills are configured.
    Use `enabled_agents` to limit which agents are written to the workspace.

    Example:
        # Default: all agents, all skills
        config = OpencodeProjectConfig()

        # Only exploration agent
        config = OpencodeProjectConfig(enabled_agents={AgentType.EXPLORATION})

        # Apply to workspace
        config.apply(Path("/path/to/repo"))
    """

    enabled_agents: Set[AgentType] = field(
        default_factory=lambda: {*AgentType})
    """Which agents to write to the workspace. Defaults to ALL agents."""

    # Internal caches (populated on init)
    _agent_contents: Dict[AgentType, str] = field(init=False, repr=False)
    _skills: Dict[str, Skill] = field(init=False, repr=False)

    # Output paths
    AGENTS_DIR = Path(".opencode/agents")
    SKILLS_DIR = Path(".opencode/skills")
    COMMANDS_DIR = Path(".opencode/commands")
    GLOBAL_AGENTS_FILE = "AGENTS.md"

    def __post_init__(self) -> None:
        self._agent_contents = {}
        self._skills = {}
        self._load_all()

    def _load_all(self) -> None:
        """Load all agents and skills from source."""
        # Load ALL agent configs (filtering happens at write time)
        for agent_type in AgentType:
            try:
                self._agent_contents[agent_type] = agent_type.load_content()
            except FileNotFoundError:
                pass  # Skip missing agent configs

        # Load ALL skills (agents decide what they use)
        for skill_name in SkillName:
            skill = Skill.from_enum(skill_name)
            self._skills[skill.name] = skill

    def apply(self, working_dir: Path) -> None:
        """
        Write configuration to workspace.

        Creates:
        - AGENTS.md (global context)
        - .opencode/agents/ (enabled agent files copied directly)
        - .opencode/skills/ (all skills)
        - .opencode/commands/ (bash commands, if configured)
        """

        # ensure working dir exists
        working_dir.mkdir(parents=True, exist_ok=True)

        self._write_global_agents_md(working_dir)
        self._write_agent_files(working_dir)
        self._write_skills(working_dir)
        self._write_commands(working_dir)

    def _write_global_agents_md(self, working_dir: Path) -> None:
        """Write the global AGENTS.md file."""
        source = CONFIG_SOURCE_DIR / self.GLOBAL_AGENTS_FILE
        if source.exists():
            target = working_dir / self.GLOBAL_AGENTS_FILE
            target.write_text(source.read_text())

    def _write_agent_files(self, working_dir: Path) -> None:
        """Write enabled agent files to .opencode/agents/."""
        agents_dir = working_dir / self.AGENTS_DIR
        agents_dir.mkdir(parents=True, exist_ok=True)

        for agent_type in self.enabled_agents:
            source_path = agent_type.source_path
            if not source_path.exists():
                continue

            target_path = agents_dir / source_path.name
            shutil.copy2(source_path, target_path)

    def _write_skills(self, working_dir: Path) -> None:
        """Write all skills to .opencode/skills/."""
        skills_dir = working_dir / self.SKILLS_DIR
        if skills_dir.exists():
            shutil.rmtree(skills_dir)

        for skill in self._skills.values():
            skill.save(skills_dir / skill.name / "SKILL.md")

    def _write_commands(self, working_dir: Path) -> None:
        """Copy configured bash commands to .opencode/commands/."""
        commands_dir = working_dir / self.COMMANDS_DIR
        if commands_dir.exists():
            shutil.rmtree(commands_dir)

        if not COMMANDS_SOURCE_DIR.exists():
            return

        shutil.copytree(COMMANDS_SOURCE_DIR, commands_dir)

    def cleanup(self, working_dir: Path) -> None:
        """Remove all files created by this configuration."""
        # Remove skills directory
        skills_dir = working_dir / self.SKILLS_DIR
        if skills_dir.exists():
            shutil.rmtree(skills_dir)

        # Remove commands directory
        commands_dir = working_dir / self.COMMANDS_DIR
        if commands_dir.exists():
            shutil.rmtree(commands_dir)

        # Remove agents directory
        agents_dir = working_dir / self.AGENTS_DIR
        if agents_dir.exists():
            shutil.rmtree(agents_dir)

        # Remove global AGENTS.md
        agents_file = working_dir / self.GLOBAL_AGENTS_FILE
        if agents_file.exists():
            agents_file.unlink()

    def get_skill(self, name: str) -> Optional[Skill]:
        """Get a skill by name."""
        return self._skills.get(name)

    @property
    def all_skills(self) -> Dict[str, Skill]:
        """All loaded skills."""
        return self._skills.copy()

    @property
    def all_agents(self) -> Dict[AgentType, str]:
        """All loaded agent contents."""
        return self._agent_contents.copy()

    # Convenience constructors

    @classmethod
    def default(cls) -> "OpencodeProjectConfig":
        """All agents, all skills."""
        return cls()

    @classmethod
    def exploration_only(cls) -> "OpencodeProjectConfig":
        """Only the exploration agent."""
        return cls(enabled_agents={AgentType.EXPLORATION})

    @classmethod
    def documentation_only(cls) -> "OpencodeProjectConfig":
        """Only the documentation agent."""
        return cls(enabled_agents={AgentType.DOCUMENTATION})
