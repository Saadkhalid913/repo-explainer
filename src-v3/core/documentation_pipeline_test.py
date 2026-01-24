"""Tests for the multi-agent documentation pipeline."""

import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.agents.project_config import AgentType, OpencodeProjectConfig
from core.models.skill import SkillName, Skill
from core.documentation_pipeline import DocumentationPipeline, run_documentation_pipeline


class TestAgentTypesAndSkills(unittest.TestCase):
    """Test that new agent types and skills are properly configured."""

    def test_new_agent_types_defined(self):
        """Test that all 3 new agent types are defined in the enum."""
        # Verify new agent types exist
        self.assertEqual(AgentType.DELEGATOR.value, "delegator")
        self.assertEqual(AgentType.SECTION_WRITER.value, "section_writer")
        self.assertEqual(AgentType.OVERVIEW_WRITER.value, "overview_writer")

        # Verify old agent types still exist
        self.assertEqual(AgentType.EXPLORATION.value, "exploration")
        self.assertEqual(AgentType.DOCUMENTATION.value, "documentation")

    def test_agent_config_files_exist(self):
        """Test that all agent config files exist."""
        # Test new agent configs
        self.assertTrue(
            AgentType.DELEGATOR.source_path.exists(),
            f"Missing config: {AgentType.DELEGATOR.source_path}"
        )
        self.assertTrue(
            AgentType.SECTION_WRITER.source_path.exists(),
            f"Missing config: {AgentType.SECTION_WRITER.source_path}"
        )
        self.assertTrue(
            AgentType.OVERVIEW_WRITER.source_path.exists(),
            f"Missing config: {AgentType.OVERVIEW_WRITER.source_path}"
        )

        # Test existing agent configs
        self.assertTrue(AgentType.EXPLORATION.source_path.exists())
        self.assertTrue(AgentType.DOCUMENTATION.source_path.exists())

    def test_agent_configs_have_content(self):
        """Test that agent config files have non-empty content."""
        for agent_type in AgentType:
            content = agent_type.load_content()
            self.assertGreater(
                len(content), 0,
                f"Agent config is empty: {agent_type.value}"
            )
            # Check for YAML frontmatter
            self.assertTrue(
                content.startswith("---"),
                f"Agent config missing YAML frontmatter: {agent_type.value}"
            )

    def test_new_skills_defined(self):
        """Test that all 5 new skills are defined in the enum."""
        # New skills
        self.assertEqual(
            SkillName.ALLOCATE_EXPLORATION_TASKS.value,
            "allocate_exploration_tasks.md"
        )
        self.assertEqual(
            SkillName.CREATE_TABLE_OF_CONTENTS.value,
            "create_table_of_contents.md"
        )
        self.assertEqual(
            SkillName.GENERATE_SECTION_WITH_DIAGRAMS.value,
            "generate_section_with_diagrams.md"
        )
        self.assertEqual(
            SkillName.CREATE_MERMAID_DIAGRAMS.value,
            "create_mermaid_diagrams.md"
        )
        self.assertEqual(
            SkillName.GENERATE_OVERVIEW_INDEX.value,
            "generate_overview_index.md"
        )

    def test_skill_files_exist(self):
        """Test that all skill files exist."""
        new_skills = [
            SkillName.ALLOCATE_EXPLORATION_TASKS,
            SkillName.CREATE_TABLE_OF_CONTENTS,
            SkillName.GENERATE_SECTION_WITH_DIAGRAMS,
            SkillName.CREATE_MERMAID_DIAGRAMS,
            SkillName.GENERATE_OVERVIEW_INDEX,
        ]

        for skill_name in new_skills:
            self.assertTrue(
                skill_name.source_path.exists(),
                f"Missing skill file: {skill_name.source_path}"
            )

    def test_skills_have_valid_structure(self):
        """Test that skill files have valid structure (first line is description)."""
        all_skills = list(SkillName)

        for skill_name in all_skills:
            skill = Skill.from_enum(skill_name)

            # Test that skill has non-empty content
            self.assertGreater(
                len(skill.content), 0,
                f"Skill has empty content: {skill.name}"
            )

            # Test that skill has a description (first line)
            self.assertGreater(
                len(skill.description), 0,
                f"Skill missing description: {skill.name}"
            )

            # Test that description is not just whitespace
            self.assertTrue(
                skill.description.strip(),
                f"Skill description is whitespace: {skill.name}"
            )


class TestOpencodeProjectConfig(unittest.TestCase):
    """Test that OpencodeProjectConfig properly applies all agents and skills."""

    def setUp(self):
        """Create a temporary directory for testing."""
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up temporary directory."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_config_applies_all_agents(self):
        """Test that config writes all agent files to workspace."""
        config = OpencodeProjectConfig.default()
        config.apply(self.test_dir)

        # Verify directories created
        agents_dir = self.test_dir / ".opencode/agents"
        self.assertTrue(agents_dir.exists())

        # Verify all agent files exist
        for agent_type in AgentType:
            agent_file = agents_dir / agent_type.filename
            self.assertTrue(
                agent_file.exists(),
                f"Agent file not created: {agent_file}"
            )

    def test_config_applies_all_skills(self):
        """Test that config writes all skill files to workspace."""
        config = OpencodeProjectConfig.default()
        config.apply(self.test_dir)

        # Verify skills directory created
        skills_dir = self.test_dir / ".opencode/skills"
        self.assertTrue(skills_dir.exists())

        # Verify all skill files exist
        for skill_name in SkillName:
            skill_file = skills_dir / skill_name.default_name / "SKILL.md"
            self.assertTrue(
                skill_file.exists(),
                f"Skill file not created: {skill_file}"
            )

    def test_config_cleanup(self):
        """Test that cleanup removes all created files."""
        config = OpencodeProjectConfig.default()
        config.apply(self.test_dir)

        # Verify files exist
        agents_dir = self.test_dir / ".opencode/agents"
        skills_dir = self.test_dir / ".opencode/skills"
        self.assertTrue(agents_dir.exists())
        self.assertTrue(skills_dir.exists())

        # Cleanup
        config.cleanup(self.test_dir)

        # Verify key files/directories removed (even if parent dir remains)
        self.assertFalse(agents_dir.exists(), "Agents directory should be removed")
        self.assertFalse(skills_dir.exists(), "Skills directory should be removed")
        self.assertFalse((self.test_dir / "AGENTS.md").exists(), "AGENTS.md should be removed")


class TestDocumentationPipelineStructure(unittest.TestCase):
    """Test the documentation pipeline structure and setup."""

    def setUp(self):
        """Create a temporary directory for testing."""
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up temporary directory."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_pipeline_initialization(self):
        """Test that pipeline initializes correctly."""
        pipeline = DocumentationPipeline(self.test_dir, verbose=False)

        self.assertEqual(pipeline.repo_path, self.test_dir)
        self.assertFalse(pipeline.verbose)
        self.assertIsNone(pipeline.wrapper)

    def test_pipeline_setup_creates_directories(self):
        """Test that setup creates required directories."""
        pipeline = DocumentationPipeline(self.test_dir, verbose=False)
        pipeline.setup()

        # Verify directories created
        self.assertTrue(pipeline.planning_dir.exists())
        self.assertTrue(pipeline.docs_dir.exists())
        self.assertTrue(pipeline.component_docs_dir.exists())
        self.assertTrue(pipeline.documentation_dir.exists())

        # Verify wrapper created
        self.assertIsNotNone(pipeline.wrapper)

    def test_pipeline_directory_structure(self):
        """Test that pipeline creates correct directory structure."""
        pipeline = DocumentationPipeline(self.test_dir, verbose=False)
        pipeline.setup()

        expected_structure = {
            "planning": self.test_dir / "planning",
            "planning/docs": self.test_dir / "planning/docs",
            "planning/documentation": self.test_dir / "planning/documentation",
            "docs": self.test_dir / "docs",
        }

        for name, path in expected_structure.items():
            self.assertTrue(
                path.exists(),
                f"Directory not created: {name} ({path})"
            )


class TestDocumentationPipelineMock(unittest.TestCase):
    """Test the documentation pipeline with mocked components."""

    def setUp(self):
        """Create a temporary directory and mock files for testing."""
        self.test_dir = Path(tempfile.mkdtemp())
        self._create_mock_files()

    def tearDown(self):
        """Clean up temporary directory."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def _create_mock_files(self):
        """Create mock files to simulate pipeline execution."""
        # Create directories
        (self.test_dir / "planning").mkdir()
        (self.test_dir / "planning/docs").mkdir()
        (self.test_dir / "planning/documentation").mkdir()
        (self.test_dir / "docs").mkdir()

        # Mock overview.md
        overview = self.test_dir / "planning/overview.md"
        overview.write_text("""# Repository Overview

This is a test repository for documentation pipeline.

## Components
- Core API
- Database Layer
""")

        # Mock task_allocation.md
        task_allocation = self.test_dir / "planning/task_allocation.md"
        task_allocation.write_text("""---
total_tasks: 2
parallel_execution: true
---

# Task Allocation Plan

## Task 1: Core API
- **Paths**: src/api/
- **Output**: planning/docs/core_api/
""")

        # Mock component docs
        component_dir = self.test_dir / "planning/docs/core_api"
        component_dir.mkdir()
        (component_dir / "overview.md").write_text("# Core API\n\nRESTful API layer.")

        # Mock TOC
        toc = self.test_dir / "planning/documentation/toc.json"
        toc.write_text(json.dumps({
            "sections": [
                {
                    "name": "architecture",
                    "title": "Architecture",
                    "components": ["core_api"],
                    "files": ["planning/docs/core_api/overview.md"]
                }
            ]
        }))

        # Mock section index
        section_dir = self.test_dir / "docs/architecture"
        section_dir.mkdir()
        (section_dir / "index.md").write_text("# Architecture\n\nArchitecture overview.")

    def test_mock_file_structure_exists(self):
        """Test that mock files are created correctly."""
        self.assertTrue((self.test_dir / "planning/overview.md").exists())
        self.assertTrue((self.test_dir / "planning/task_allocation.md").exists())
        self.assertTrue((self.test_dir / "planning/documentation/toc.json").exists())
        self.assertTrue((self.test_dir / "docs/architecture/index.md").exists())

    def test_toc_json_is_valid(self):
        """Test that mock TOC JSON is valid."""
        toc_path = self.test_dir / "planning/documentation/toc.json"
        with open(toc_path) as f:
            toc = json.load(f)

        self.assertIn("sections", toc)
        self.assertEqual(len(toc["sections"]), 1)
        self.assertEqual(toc["sections"][0]["name"], "architecture")


class TestDocumentationPipelineConvenience(unittest.TestCase):
    """Test the convenience function for running the pipeline."""

    def setUp(self):
        """Create a temporary directory."""
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        """Clean up temporary directory."""
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_convenience_function_exists(self):
        """Test that run_documentation_pipeline function exists."""
        self.assertTrue(callable(run_documentation_pipeline))


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)
