"""Skill model for agent capabilities."""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Dict, Any, Optional

SKILLS_SOURCE_DIR = Path(__file__).resolve().parents[1] / "agents" / "skills"


class SkillName(Enum):
    """Canonical skill registry."""

    # Exploration agent skills
    ANALYZE_COMPONENTS = "analyze_components.md"
    DISCOVER_ARCHITECTURE = "discover_architecture.md"
    DEPENDENCY_ANALYSIS = "dependency_analysis.md"

    # Documentation agent skills
    GENERATE_DOCUMENTATION = "generate_documentation.md"
    DOCUMENT_API = "document_api.md"

    # Delegator agent skills
    ALLOCATE_EXPLORATION_TASKS = "allocate_exploration_tasks.md"

    # Documentation agent enhancements
    CREATE_TABLE_OF_CONTENTS = "create_table_of_contents.md"

    # Section writer agent skills
    GENERATE_SECTION_WITH_DIAGRAMS = "generate_section_with_diagrams.md"
    CREATE_MERMAID_DIAGRAMS = "create_mermaid_diagrams.md"

    # Overview writer agent skills
    GENERATE_OVERVIEW_INDEX = "generate_overview_index.md"

    @property
    def source_path(self) -> Path:
        """Path to the skill definition file."""
        return SKILLS_SOURCE_DIR / self.value

    @property
    def default_name(self) -> str:
        """Default skill identifier (file stem)."""
        return Path(self.value).stem

    def load_content(self) -> str:
        """Read the skill prompt content."""
        path = self.source_path
        if not path.exists():
            raise FileNotFoundError(f"Skill file missing: {path}")
        return path.read_text()


@dataclass
class Skill:
    """
    Represents an agent skill.

    The first line of the content should be the description of what the skill does.
    """

    name: str
    """Skill name (e.g., 'analyze_components')."""

    content: str
    """Skill prompt/definition, with the first line describing its purpose."""

    args: Optional[str] = None
    """Optional arguments for the skill."""

    metadata: Dict[str, Any] = field(default_factory=dict)
    """Additional metadata for the skill."""

    def __post_init__(self) -> None:
        """Validate that the skill has non-empty content and a description."""
        if not self.content:
            raise ValueError(f"Skill '{self.name}' must have content")

        lines = self.content.strip().split("\n")
        if not lines or not lines[0].strip():
            raise ValueError(
                f"Skill '{self.name}' must start with a description")

    @property
    def description(self) -> str:
        """Extract the first line as the description."""
        return self.content.strip().split("\n")[0].strip()

    @property
    def implementation(self) -> str:
        """Get everything after the description line."""
        lines = self.content.strip().split("\n")
        return "\n".join(lines[1:]).strip() if len(lines) > 1 else ""

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the skill."""
        return {
            "name": self.name,
            "content": self.content,
            "description": self.description,
            "args": self.args,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Skill":
        """Load a skill from a dictionary payload."""
        return cls(
            name=data["name"],
            content=data["content"],
            args=data.get("args"),
            metadata=data.get("metadata", {}),
        )

    @classmethod
    def from_file(cls, skill_path: Path) -> "Skill":
        """
        Load a skill from a filesystem path.

        Args:
            skill_path: Path to the skill file

        Returns:
            Skill instance
        """
        if not skill_path.exists():
            raise FileNotFoundError(f"Skill file not found: {skill_path}")

        content = skill_path.read_text()
        name = skill_path.stem

        return cls(name=name, content=content)

    @classmethod
    def from_enum(cls, skill_name: SkillName) -> "Skill":
        """
        Load a skill using the canonical skill registry.

        Args:
            skill_name: Registered SkillName

        Returns:
            Skill instance
        """
        return cls(name=skill_name.default_name, content=skill_name.load_content())

    def save(self, output_path: Path) -> None:
        """
        Persist the skill definition to disk.

        Args:
            output_path: Destination path
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(self.content)

    def __str__(self) -> str:
        return f"Skill(name='{self.name}', description='{self.description[:50]}...')"

    def __repr__(self) -> str:
        return f"Skill(name='{self.name}', args={self.args}, description='{self.description}')"
