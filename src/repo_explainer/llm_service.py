"""LLM service for OpenRouter integration and prompt management."""

import json
from typing import Any, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from repo_explainer.config import get_settings


class LLMService:
    """Handles LLM interactions via OpenRouter API."""

    # Prompt templates for different analysis tasks
    PROMPTS = {
        "architecture": """\
Analyze the following repository and generate a comprehensive architecture overview.

{context}

Please provide:
1. A high-level architecture summary (2-3 paragraphs)
2. Key components and their responsibilities
3. Data flow between components
4. Technology stack identification
5. Notable design patterns observed

Format your response as structured markdown.
""",
        "components": """\
Analyze the components in this repository and document each one.

{context}

For each component, provide:
- Name and purpose
- Key responsibilities
- Dependencies (internal and external)
- Important files and entry points
- Public interfaces/APIs

Format as a markdown document with sections for each component.
""",
        "diagram_architecture": """\
Based on this repository structure, generate a Mermaid flowchart diagram
showing the high-level architecture.

{context}

Output ONLY a valid Mermaid diagram using flowchart LR or TD syntax.
Include main components and their relationships.
Keep it readable - limit to 10-15 nodes maximum.

Example format:
```mermaid
flowchart LR
    A[Component A] --> B[Component B]
    B --> C[Component C]
```
""",
        "diagram_dataflow": """\
Based on this repository, generate a Mermaid diagram showing data flow.

{context}

Output ONLY a valid Mermaid diagram showing how data flows through the system.
Use flowchart syntax with descriptive edge labels.

Example format:
```mermaid
flowchart TD
    User -->|request| API
    API -->|query| Database
    Database -->|data| API
    API -->|response| User
```
""",
        "tech_stack": """\
Analyze this repository and identify the complete technology stack.

{context}

List:
1. Programming languages and versions
2. Frameworks and libraries
3. Build tools and package managers
4. Testing frameworks
5. Development tools and configurations
6. Infrastructure/deployment tools if visible

Format as a bulleted list grouped by category.
""",
    }

    def __init__(self):
        self.settings = get_settings()
        self._client: Optional[httpx.Client] = None

    @property
    def client(self) -> httpx.Client:
        """Lazy-initialize the HTTP client."""
        if self._client is None:
            self._client = httpx.Client(
                base_url=self.settings.llm_base_url,
                headers={
                    "Authorization": f"Bearer {self.settings.openrouter_api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://github.com/repo-explainer",
                    "X-Title": "Repository Explainer",
                },
                timeout=120.0,
            )
        return self._client

    def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            self._client.close()
            self._client = None

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
    )
    def complete(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        max_tokens: int = 4000,
    ) -> str:
        """Send a completion request to the LLM."""
        if not self.settings.openrouter_api_key:
            raise ValueError(
                "OpenRouter API key not configured. "
                "Set REPO_EXPLAINER_OPENROUTER_API_KEY environment variable."
            )

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        response = self.client.post(
            "/chat/completions",
            json={
                "model": self.settings.llm_model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.3,  # Lower temperature for more deterministic output
            },
        )
        response.raise_for_status()

        data = response.json()
        return data["choices"][0]["message"]["content"]

    def generate_architecture(self, context: str) -> str:
        """Generate architecture documentation."""
        prompt = self.PROMPTS["architecture"].format(context=context)
        return self.complete(
            prompt,
            system_prompt="You are a software architect analyzing codebases. "
            "Provide clear, accurate, and well-structured documentation.",
        )

    def generate_component_docs(self, context: str) -> str:
        """Generate component documentation."""
        prompt = self.PROMPTS["components"].format(context=context)
        return self.complete(prompt)

    def generate_architecture_diagram(self, context: str) -> str:
        """Generate a Mermaid architecture diagram."""
        prompt = self.PROMPTS["diagram_architecture"].format(context=context)
        response = self.complete(prompt, max_tokens=2000)
        return self._extract_mermaid(response)

    def generate_dataflow_diagram(self, context: str) -> str:
        """Generate a Mermaid dataflow diagram."""
        prompt = self.PROMPTS["diagram_dataflow"].format(context=context)
        response = self.complete(prompt, max_tokens=2000)
        return self._extract_mermaid(response)

    def generate_tech_stack(self, context: str) -> str:
        """Generate technology stack documentation."""
        prompt = self.PROMPTS["tech_stack"].format(context=context)
        return self.complete(prompt, max_tokens=2000)

    def _extract_mermaid(self, response: str) -> str:
        """Extract Mermaid diagram code from LLM response."""
        # Try to find mermaid code block
        if "```mermaid" in response:
            start = response.find("```mermaid") + len("```mermaid")
            end = response.find("```", start)
            if end != -1:
                return response[start:end].strip()

        # Try plain code block
        if "```" in response:
            start = response.find("```") + 3
            # Skip language identifier if present
            newline = response.find("\n", start)
            if newline != -1:
                start = newline + 1
            end = response.find("```", start)
            if end != -1:
                return response[start:end].strip()

        # Return as-is if no code block found
        return response.strip()

    def validate_mermaid(self, diagram: str) -> bool:
        """Basic validation of Mermaid diagram syntax."""
        # Check for common diagram types
        valid_starts = [
            "flowchart",
            "graph",
            "sequenceDiagram",
            "classDiagram",
            "erDiagram",
            "stateDiagram",
            "gantt",
            "pie",
        ]
        first_line = diagram.strip().split("\n")[0].lower()
        return any(first_line.startswith(start.lower()) for start in valid_starts)
