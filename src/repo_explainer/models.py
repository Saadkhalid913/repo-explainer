"""Data models for repo-explainer using Pydantic and dataclasses."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional

from pydantic import BaseModel


class LanguageType(str, Enum):
    """Supported programming languages."""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"


class SizeCategory(str, Enum):
    """Repository size categories."""

    SMALL = "small"  # < 100 files
    MEDIUM = "medium"  # 100-1000 files
    LARGE = "large"  # 1000-10000 files
    VERY_LARGE = "very_large"  # > 10000 files


class DiagramType(str, Enum):
    """Types of diagrams that can be generated."""

    ARCHITECTURE = "architecture"
    COMPONENT = "component"
    DATAFLOW = "dataflow"
    SEQUENCE = "sequence"
    ER = "er"
    CALL_GRAPH = "call-graph"
    DEPENDENCY = "dependency"
    CLASS = "class"


@dataclass
class FileInfo:
    """Information about a single file."""

    path: Path
    language: Optional[LanguageType] = None
    size_bytes: int = 0
    line_count: int = 0


@dataclass
class RepositoryInfo:
    """Repository metadata and analysis info."""

    path: Path
    name: str
    primary_language: Optional[LanguageType] = None
    languages: list[LanguageType] = field(default_factory=list)
    size_category: SizeCategory = SizeCategory.SMALL
    file_count: int = 0
    total_lines: int = 0
    last_analyzed: Optional[datetime] = None
    git_remote: Optional[str] = None
    git_branch: Optional[str] = None
    git_commit: Optional[str] = None


@dataclass
class ComponentInfo:
    """Information about a code component."""

    id: str
    name: str
    component_type: str  # service, module, package, class
    path: Path
    description: str = ""
    responsibilities: list[str] = field(default_factory=list)
    dependencies: list[str] = field(default_factory=list)
    external_dependencies: list[str] = field(default_factory=list)
    files: list[Path] = field(default_factory=list)


@dataclass
class DiagramInfo:
    """Generated diagram information."""

    diagram_type: DiagramType
    title: str
    mermaid_code: str
    output_path: Optional[Path] = None
    related_components: list[str] = field(default_factory=list)


class AnalysisResult(BaseModel):
    """Complete analysis result from a run."""

    repository: dict  # Serialized RepositoryInfo
    components: list[dict]  # Serialized ComponentInfo list
    diagrams: list[dict]  # Serialized DiagramInfo list
    tech_stack: list[str]
    patterns_detected: list[str]
    analysis_timestamp: datetime
    opencode_session_id: Optional[str] = None
    errors: list[str] = []


@dataclass
class OpenCodeSession:
    """Tracks an OpenCode CLI session."""

    session_id: str
    command: str
    started_at: datetime
    ended_at: Optional[datetime] = None
    exit_code: Optional[int] = None
    output_files: list[Path] = field(default_factory=list)
    stdout: str = ""
    stderr: str = ""
